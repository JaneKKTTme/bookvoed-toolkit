"""Tests for the ListParser class."""

import pytest
from bs4 import BeautifulSoup

from parsers.list_parser import ListParser
from tests.fixtures.html_fixtures import (
    CATALOG_PAGE_HTML,
    CATALOG_PAGE_EMPTY_HTML,
    CATALOG_PAGE_WITH_NEXT_BUTTON
)


class TestListParserExtraction:
    """Test extraction of book links from catalog pages."""
    
    def test_extract_book_links(self):
        """Test extracting all book links from a catalog page."""
        parser = ListParser(CATALOG_PAGE_HTML, page=1)
        links = parser.extract_book_links()
        
        assert len(links) == 3
        assert links[0] == '/book/123'
        assert links[1] == '/book/456'
        assert links[2] == '/book/789'
    
    def test_extract_book_links_empty_page(self):
        """Test extracting links from page with no books."""
        parser = ListParser(CATALOG_PAGE_EMPTY_HTML, page=1)
        links = parser.extract_book_links()
        
        assert links == []
    
    def test_extract_book_links_no_matching_class(self):
        """Test extracting links when no matching class is found."""
        html = '<div><a href="/book/123">Link</a></div>'
        parser = ListParser(html, page=1)
        links = parser.extract_book_links()
        
        assert links == []


class TestListParserPagination:
    """Test next page detection."""
    
    def test_has_next_page_with_next_link(self):
        """Test detection of 'Далее' (Next) link."""
        parser = ListParser(CATALOG_PAGE_HTML, page=1)
        assert parser.has_next_page(1) is True
    
    def test_has_next_page_with_next_button(self):
        """Test detection of 'Следующая' (Next) link."""
        parser = ListParser(CATALOG_PAGE_WITH_NEXT_BUTTON, page=1)
        assert parser.has_next_page(1) is True
    
    def test_has_next_page_with_url_parameter(self):
        """Test detection of next page via URL parameter."""
        html = '''
        <div class="pagination">
            <a href="?page=2">2</a>
            <a href="?page=3">3</a>
        </div>
        '''
        parser = ListParser(html, page=1)
        assert parser.has_next_page(1) is True
    
    def test_has_next_page_false(self):
        """Test when no next page exists."""
        html = '<div class="pagination"><a href="?page=1">1</a></div>'
        parser = ListParser(html, page=1)
        assert parser.has_next_page(1) is False
    
    def test_has_next_page_without_pagination(self):
        """Test page with no pagination elements."""
        parser = ListParser(CATALOG_PAGE_EMPTY_HTML, page=1)
        assert parser.has_next_page(1) is False


class TestListParserBookDetection:
    """Test detection of books on catalog pages."""
    
    def test_has_books_true(self):
        """Test has_books returns True when books are present."""
        parser = ListParser(CATALOG_PAGE_HTML, page=1)
        assert parser.has_books() is True
    
    def test_has_books_false(self):
        """Test has_books returns False when no books are present."""
        parser = ListParser(CATALOG_PAGE_EMPTY_HTML, page=1)
        assert parser.has_books() is False
    
    def test_has_books_with_different_container_class(self):
        """Test has_books with unexpected container class."""
        html = '<div class="different-class">Books here</div>'
        parser = ListParser(html, page=1)
        assert parser.has_books() is False
