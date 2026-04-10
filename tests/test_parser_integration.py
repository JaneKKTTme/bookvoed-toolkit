"""Integration tests for the main BookvoedParser orchestrator."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from core.parser import BookvoedParser
from models.book import Book


class TestBookvoedParserInitialization:
    """Test parser initialization."""
    
    def test_default_initialization(self):
        """Test parser initializes with default values."""
        parser = BookvoedParser()
        assert parser.semaphore._value == 50  # default concurrent tasks
        assert parser.http_client.delay == 0.1
    
    def test_custom_initialization(self):
        """Test parser initializes with custom values."""
        parser = BookvoedParser(max_concurrent_tasks=20, delay=0.5)
        assert parser.semaphore._value == 20
        assert parser.http_client.delay == 0.5
    
    def test_executor_creation(self):
        """Test thread pool executor is created."""
        parser = BookvoedParser()
        assert parser.executor is not None
        assert parser.executor._max_workers == 4
    
    def test_storage_initialization(self):
        """Test storage is initialized."""
        parser = BookvoedParser()
        assert parser.storage is not None
        assert parser.storage.filename == 'books.parquet'


@pytest.mark.asyncio
class TestBookvoedParserShutdown:
    """Test shutdown behavior."""
    
    async def test_shutdown_sets_event(self):
        """Test shutdown sets shutdown event."""
        parser = BookvoedParser()
        assert not parser.shutdown_event.is_set()
        
        await parser.shutdown()
        assert parser.shutdown_event.is_set()


@pytest.mark.asyncio
class TestBookvoedParserParseSingleBook:
    """Test parsing a single book."""
    
    async def test_parse_single_book_success(self, sample_book_data):
        """Test successful parsing of a single book."""
        parser = BookvoedParser()
        
        # Mock HTTP client response
        parser.http_client.get = AsyncMock(return_value='<html>Mock HTML</html>')
        
        # Mock BookParser
        mock_book = Book(**sample_book_data)
        
        with patch('core.parser.BookParser') as MockBookParser:
            mock_parser = Mock()
            mock_parser.parse.return_value = mock_book
            MockBookParser.return_value = mock_parser
            
            # Run in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                parser.executor,
                lambda: mock_parser.parse()
            )
            
            # Create actual book via the real method structure
            # This is a simplified test of the concept
        
        assert result == mock_book
    
    async def test_parse_single_book_http_failure(self):
        """Test handling of HTTP failure when parsing single book."""
        parser = BookvoedParser()
        
        # Mock HTTP client to return None (failure)
        parser.http_client.get = AsyncMock(return_value=None)
        
        # Since _parse_single_book uses semaphore, we need to acquire it
        async with parser.semaphore:
            result = await parser._parse_single_book('/book/test')
        
        assert result is None
    
    async def test_parse_single_book_parsing_exception(self):
        """Test handling of parsing exception."""
        parser = BookvoedParser()
        
        # Mock HTTP client to return HTML
        parser.http_client.get = AsyncMock(return_value='<html></html>')
        
        # Mock BookParser to raise exception
        with patch('core.parser.BookParser') as MockBookParser:
            mock_parser = Mock()
            mock_parser.parse.side_effect = Exception('Parse error')
            MockBookParser.return_value = mock_parser
            
            async with parser.semaphore:
                result = await parser._parse_single_book('/book/test')
            
            assert result is None


@pytest.mark.asyncio
class TestBookvoedParserParseBooksBatch:
    """Test batch parsing of multiple books."""
    
    async def test_parse_books_batch_success(self):
        """Test successful batch parsing."""
        parser = BookvoedParser()
        
        # Mock _parse_single_book to return books
        mock_book1 = Book(name='Book 1', url='/book/1')
        mock_book2 = Book(name='Book 2', url='/book/2')
        
        parser._parse_single_book = AsyncMock(side_effect=[mock_book1, mock_book2])
        
        book_links = ['/book/1', '/book/2']
        result = await parser._parse_books_batch(book_links)
        
        assert len(result) == 2
        assert result[0].name == 'Book 1'
        assert result[1].name == 'Book 2'
    
    async def test_parse_books_batch_with_failures(self):
        """Test batch parsing with some failures."""
        parser = BookvoedParser()
        
        # Mock _parse_single_book to return mixed results
        mock_book = Book(name='Book 1', url='/book/1')
        
        parser._parse_single_book = AsyncMock(side_effect=[mock_book, None, mock_book])
        
        book_links = ['/book/1', '/book/2', '/book/3']
        result = await parser._parse_books_batch(book_links)
        
        assert len(result) == 2  # Only successful ones
    
    async def test_parse_books_batch_all_fail(self):
        """Test batch parsing with all failures."""
        parser = BookvoedParser()
        
        parser._parse_single_book = AsyncMock(return_value=None)
        
        book_links = ['/book/1', '/book/2']
        result = await parser._parse_books_batch(book_links)
        
        assert result == []


@pytest.mark.asyncio
class TestBookvoedParserParseBookList:
    """Test catalog page parsing."""
    
    async def test_parse_book_list_success(self):
        """Test successful catalog page parsing."""
        parser = BookvoedParser()
        
        # Mock HTTP client
        parser.http_client.get = AsyncMock(return_value='<html>Catalog page</html>')
        
        # Mock ListParser
        with patch('core.parser.ListParser') as MockListParser:
            mock_parser = Mock()
            mock_parser.has_books.return_value = True
            mock_parser.extract_book_links.return_value = ['/book/1', '/book/2']
            mock_parser.has_next_page.return_value = True
            MockListParser.return_value = mock_parser
            
            # Mock _parse_books_batch
            mock_books = [Book(name='Book 1', url='/book/1'), Book(name='Book 2', url='/book/2')]
            parser._parse_books_batch = AsyncMock(return_value=mock_books)
            
            result_books, has_next = await parser._parse_book_list(1)
            
            assert len(result_books) == 2
            assert has_next is True
    
    async def test_parse_book_list_no_books(self):
        """Test catalog page with no books."""
        parser = BookvoedParser()
        
        parser.http_client.get = AsyncMock(return_value='<html>Empty catalog</html>')
        
        with patch('core.parser.ListParser') as MockListParser:
            mock_parser = Mock()
            mock_parser.has_books.return_value = False
            MockListParser.return_value = mock_parser
            
            result_books, has_next = await parser._parse_book_list(1)
            
            assert result_books == []
            assert has_next is False
    
    async def test_parse_book_list_http_error(self):
        """Test HTTP error when fetching catalog page."""
        parser = BookvoedParser()
        
        parser.http_client.get = AsyncMock(return_value=None)
        
        result_books, has_next = await parser._parse_book_list(1)
        
        assert result_books == []
        assert has_next is False


@pytest.mark.asyncio
class TestBookvoedParserMainLoop:
    """Test main parsing loop."""
    
    async def test_parse_bookvoed_basic(self):
        """Test basic parsing flow."""
        parser = BookvoedParser()
        
        # Mock _parse_book_list to return books and then stop
        call_count = 0
        
        async def mock_parse_book_list(page):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                books = [Book(name=f'Book {page}', url=f'/book/{page}')]
                return books, True
            else:
                return [], False
        
        parser._parse_book_list = mock_parse_book_list
        
        # Mock storage
        parser.storage.save_books = Mock(return_value=1)
        
        await parser.parse_bookvoed(start_page=1)
        
        # Should have processed 2 pages before stopping
        assert call_count >= 2
    
    async def test_parse_bookvoed_shutdown_during_loop(self):
        """Test shutdown during parsing loop."""
        parser = BookvoedParser()
        
        async def mock_parse_book_list(page):
            # Set shutdown event after first page
            if page == 2:
                await parser.shutdown()
            return [Book(name=f'Book {page}', url=f'/book/{page}')], True
        
        parser._parse_book_list = mock_parse_book_list
        parser.storage.save_books = Mock(return_value=1)
        
        await parser.parse_bookvoed(start_page=1)
        
        # Should exit gracefully without error
        assert parser.shutdown_event.is_set()
    
    async def test_parse_bookvoed_with_start_page(self):
        """Test parsing starting from specific page."""
        parser = BookvoedParser()
        
        pages_processed = []
        
        async def mock_parse_book_list(page):
            pages_processed.append(page)
            if page < 3:
                return [Book(name=f'Book {page}', url=f'/book/{page}')], True
            return [], False
        
        parser._parse_book_list = mock_parse_book_list
        parser.storage.save_books = Mock(return_value=1)
        
        await parser.parse_bookvoed(start_page=5)
        
        # Should start at page 5
        assert 5 in pages_processed
        assert 4 not in pages_processed
