"""
Core module containing the main orchestrator for book parsing.

This module provides the BookvoedParser class which coordinates the entire
parsing process including page navigation, book extraction, and data storage.
"""

import asyncio
import signal
import sys
import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

from config import SERVICE, BOOK_PAGE, REQUEST_CONFIG
from core.http_client import HTTPClient
from models.book import Book
from parsers.list_parser import ListParser
from parsers.book_parser import BookParser
from storage.parquet_storage import ParquetStorage
from logging_config import logger


# ============================================================================
# PERFORMANCE NOTES:
# ============================================================================
# The semaphore limits concurrent book parsing to prevent:
#   1. Socket exhaustion (too many open connections)
#   2. Rate limiting triggers from the server
#   3. Memory overload from too many simultaneous HTML documents
#
# ThreadPoolExecutor with 4 workers is chosen because:
#   - BeautifulSoup parsing is CPU-bound (100% CPU during parse)
#   - Each parse takes 0.05-0.2 seconds depending on HTML complexity
#   - 4 workers saturate a typical CPU without causing context switching overhead
#   - I/O waiting happens in the async HTTP client, not in the executor
#
# The 0.5 second delay between page requests protects against:
#   - Aggressive crawling detection
#   - Server overload during peak hours (19:00-22:00 MSK)
# ============================================================================


class BookvoedParser:
    """Asynchronous parser for bookvoed.ru website.
    
    This class orchestrates the entire parsing process including catalog page
    navigation, book link extraction, parallel book parsing, and data storage.
    It handles graceful shutdown, progress tracking, and error recovery.
    
    Attributes:
        semaphore (asyncio.Semaphore): Limits concurrent parsing tasks.
        shutdown_event (asyncio.Event): Event for graceful shutdown signaling.
        http_client (HTTPClient): HTTP client for making requests.
        storage (ParquetStorage): Storage handler for saving books.
        executor (ThreadPoolExecutor): Executor for CPU-bound HTML parsing.
        
    Example:
        >>> async with BookvoedParser() as parser:
        ...  await parser.parse_bookvoed(start_page=1)
    """

    def __init__(self, max_concurrent_tasks: int = REQUEST_CONFIG['concurrent_tasks'],
                 delay: float = REQUEST_CONFIG['delay_between_requests']):
        """Initialize the BookvoedParser with configuration parameters.
        
        Args:
            max_concurrent_tasks (int): Maximum number of concurrent book parsing tasks.
                Defaults to value from REQUEST_CONFIG.
            delay (float): Delay between HTTP requests in seconds.
                Defaults to value from REQUEST_CONFIG.
        """
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.shutdown_event = asyncio.Event()
        
        self.http_client = HTTPClient(delay=delay)
        self.storage = ParquetStorage()

        self.executor = ThreadPoolExecutor(max_workers=4)
        # BeautifulSoup parsing is CPU-bound and blocks the event loop.
        # Using ThreadPoolExecutor prevents blocking while allowing concurrency.
        # 4 workers is optimal: balances CPU usage vs I/O waiting.
        
        if sys.platform != 'win32':
            self._setup_signal_handlers()
            # Windows doesn't support add_signal_handler asyncio method
            # Users on Windows can use Ctrl+Break instead of Ctrl+C

    async def __aenter__(self):
        """Enter async context manager, setting up HTTP client."""
        await self.http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager, cleaning up resources."""
        await self.close()

    async def parse_bookvoed(self, start_page: int = 1) -> None:
        """Start parsing books from the catalog starting at specified page.
        
        This method iterates through catalog pages, extracts book links,
        parses book details, and saves them to storage. Progress is displayed
        using tqdm progress bar. Continues until no next page or shutdown signal.
        
        Args:
            start_page (int): Catalog page number to start parsing from.
                Defaults to 1.
                
        Raises:
            KeyboardInterrupt: If interrupted by user (handled gracefully).
        """
        page = start_page
        has_next_page = True
        total_books = 0
        start_time = time.time()

        with tqdm(desc='Total pages processed', unit='page') as pbar:
            while has_next_page and not self.shutdown_event.is_set():
                books_on_page, has_next_page = await self._parse_book_list(page)

                if books_on_page:
                    added_books = self.storage.save_books(books_on_page)
                    total_books += added_books

                    elapsed = time.time() - start_time
                    books_per_second = total_books / elapsed if elapsed > 0 else 0
                    pbar.set_postfix({
                        'books': total_books,
                        'speed': f'{books_per_second:.1f} books/s'
                    })

                    logger.info(f'Page {page} processed. Found: {len(books_on_page)}, '
                              f'Added: {added_books}, Next: {has_next_page}')

                pbar.update(1)
                page += 1
                await asyncio.sleep(0.5)  # Delay between page requests to avoid rate limiting

    async def close(self):
        """Close all resources and clean up connections.
        
        Shuts down the thread pool executor and closes the HTTP client session.
        Should be called when parsing is complete or interrupted.
        """
        self.executor.shutdown(wait=True)
        await self.http_client.close()

    async def shutdown(self):
        """Initiate graceful shutdown of the parser.
        
        Sets the shutdown event flag, signaling all loops to stop processing.
        This method is called by signal handlers for SIGTERM and SIGINT.
        """
        logger.info('Shutting down gracefully...')
        self.shutdown_event.set()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown on Unix-like systems.
        
        Registers handlers for SIGTERM and SIGINT signals to trigger
        graceful shutdown. Not available on Windows platforms.
        """
        loop = asyncio.get_event_loop()

        def _shutdown():
            # Schedule shutdown in the event loop thread
            asyncio.ensure_future(self.shutdown(), loop=loop)

        for s in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(s, _shutdown)

    async def _parse_book_list(self, page: int) -> tuple[List[Book], bool]:
        """Parse a single catalog page and extract all book links.
        
        This method fetches the catalog page HTML, extracts book links,
        and initiates batch parsing of all books found on the page.
        
        Args:
            page (int): Catalog page number to parse.
            
        Returns:
            Tuple[List[Book], bool]: A tuple containing:
                - List of parsed Book objects from this page
                - Boolean indicating whether a next page exists
        """
        curr_url = SERVICE + BOOK_PAGE + str(page)
        
        try:
            html = await self.http_client.get(curr_url)
            if not html:
                return [], False

            list_parser = ListParser(html, page)
            
            if not list_parser.has_books():
                logger.info(f'No books found on page {page}')
                return [], False

            book_links = list_parser.extract_book_links()
            if not book_links:
                return [], False

            has_next_page = list_parser.has_next_page(page)

            books = await self._parse_books_batch(book_links)

            return books, has_next_page
            
        except Exception as e:
            logger.error(f'Error loading {curr_url}: {e}')
            return [], False

    async def _parse_books_batch(self, book_links: List[str]) -> List[Book]:
        """Parse multiple books concurrently from their URLs.
        
        Creates asynchronous tasks for each book link and executes them
        concurrently using asyncio.gather. Handles exceptions gracefully
        without failing the entire batch.
        
        Args:
            book_links (List[str]): List of relative URLs for book detail pages.
            
        Returns:
            List[Book]: List of successfully parsed Book objects.
                Failed parses are excluded from the result.
        """
        tasks = [self._parse_single_book(link) for link in book_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        books = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Error in batch: {result}')
            elif result is not None:
                books.append(result)

        return books

    async def _parse_single_book(self, url: str) -> Optional[Book]:
        """Parse a single book page and extract all information.
        
        Fetches the book detail page HTML, parses it using BookParser,
        and returns a Book object. Uses semaphore to limit concurrency
        and thread pool executor for CPU-bound parsing operations.
        
        Args:
            url (str): Relative URL of the book detail page.
            
        Returns:
            Optional[Book]: Parsed Book object, or None if parsing failed.

        CRITICAL: The semaphore context manager MUST be used here.
            Without it, concurrent tasks would be unbounded, leading to:
               - Memory exhaustion (storing 50+ HTML responses simultaneously)
               - Connection pool depletion
               - Potential IP ban from aggressive requests
            
            The thread pool executor is necessary because BeautifulSoup's parse()
            blocks the event loop. Running it in a separate thread prevents:
               - Event loop starvation
               - Increased latency for other concurrent tasks
        """
        async with self.semaphore:  # CRITICAL: Limits concurrency
            try:
                full_url = SERVICE + url
                html = await self.http_client.get(full_url)
                
                if not html:
                    return None

                loop = asyncio.get_event_loop()
                book = await loop.run_in_executor(
                    self.executor,
                    lambda: BookParser(html, url).parse()
                )
                
                return book
                
            except Exception as e:
                logger.error(f'Error parsing book {url}: {e}', exc_info=True)
                return None
