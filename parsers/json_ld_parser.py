"""
JSON-LD metadata parser module.

This module provides the JsonLdParser class for extracting structured data
from JSON-LD script tags embedded in book pages.
"""

import json
from bs4 import BeautifulSoup

from models.book import Book
from logging_config import logger


class JsonLdParser:
    """Parser for extracting book metadata from JSON-LD structured data.
    
    This class extracts information from application/ld+json script tags
    which contain structured data following schema.org vocabulary.
    
    Attributes:
        FORMAT_MAP (Dict[str, str]): Mapping of schema.org book formats
            to Russian binding type names.
            
    Example:
        >>> soup = BeautifulSoup(html, 'lxml')
        >>> book = Book()
        >>> JsonLdParser.parse(soup, book)
    """

    FORMAT_MAP = {
        'https://schema.org/Hardcover': 'Твёрдый переплёт',
        'https://schema.org/Paperback': 'Мягкая обложка'
    }

    @classmethod
    def parse(cls, soup: BeautifulSoup, book: Book) -> Book:
        """Parse JSON-LD script tags and extract book metadata.
        
        Searches for all script tags with type application/ld+json,
        parses the JSON content, and extracts book-related fields.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content of the book page.
            book (Book): Book instance to populate with extracted data.
            
        Returns:
            Book: The populated Book instance (same as input for chaining).
        """
        script_tags = soup.find_all('script', type='application/ld+json')
        # NOTE: Bookvoed.ru sometimes has multiple JSON-LD blocks.
        # We check all of them because book data might be split across blocks.
        # If the site changes structure, this parser will need updates.

        for script in script_tags:
            try:
                if not script.string:
                    continue

                data = json.loads(script.string)

                if isinstance(data, dict):
                    if '@graph' in data:
                        for item in data['@graph']:
                            if item.get('@type') == 'Book':
                                cls._extract_book_data(item, book)
                    elif data.get('@type') == 'Book':
                        cls._extract_book_data(data, book)

            except (json.JSONDecodeError, AttributeError) as e:
                logger.debug(f'Error parsing JSON-LD: {e}')
                continue

        return book

    @classmethod
    def _extract_book_data(cls, item: dict, book: Book):
        """Extract specific book fields from JSON-LD item.
        
        Maps JSON-LD fields to Book model attributes including description,
        genre, book format, page count, publisher, publication date, and ratings.
        
        Args:
            item (Dict[str, Any]): Parsed JSON-LD object for a Book.
            book (Book): Book instance to populate.
        """
        if 'description' in item:
            book.annotation = item.get('description', '').replace('\xA0', '')

        if 'genre' in item:
            book.genre = item.get('genre', '')

        if 'bookFormat' in item:
            book.bookbinding = cls.FORMAT_MAP.get(item.get('bookFormat'), item.get('bookFormat', ''))

        if 'numberOfPages' in item:
            pages = item.get('numberOfPages', '')
            try:
                book.number_of_pages = int(pages)
            except (ValueError, TypeError):
                book.number_of_pages = pages

        if 'publisher' in item:
            book.publisher = item.get('publisher', '')

        if 'datePublished' in item:
            year = item.get('datePublished', '')
            try:
                book.year_of_publication = int(year) if str(year).isdigit() else year
            except (ValueError, TypeError):
                book.year_of_publication = year

        aggregate_rating = item.get('aggregateRating', {})
        if isinstance(aggregate_rating, dict):
            book.rating = aggregate_rating.get('ratingValue', '')
            book.review_count = aggregate_rating.get('reviewCount', '')
