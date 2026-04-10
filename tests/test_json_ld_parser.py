"""Tests for the JSON-LD parser."""

import pytest
from bs4 import BeautifulSoup

from models.book import Book
from parsers.json_ld_parser import JsonLdParser
from tests.fixtures.html_fixtures import (
    BOOK_PAGE_HTML,
    BOOK_PAGE_JSONLD_ONLY_HTML
)


class TestJsonLdParser:
    """Test JSON-LD structured data extraction."""
    
    def test_parse_json_ld_from_book_page(self):
        """Test extracting JSON-LD data from complete book page."""
        soup = BeautifulSoup(BOOK_PAGE_HTML, 'lxml')
        book = Book()
        
        result = JsonLdParser.parse(soup, book)
        
        assert result is book  # Returns the same instance
        assert book.annotation == 'Знаменитый роман Михаила Булгакова'
        assert book.genre == 'Классическая проза'
        assert book.number_of_pages == 416
        assert book.publisher == 'Эксмо'
        assert book.year_of_publication == 2020
        assert book.bookbinding == 'Твёрдый переплёт'
        assert book.rating == 4.9
        assert book.review_count == 1250
    
    def test_parse_json_ld_only_page(self):
        """Test extracting JSON-LD from page with only JSON-LD data."""
        soup = BeautifulSoup(BOOK_PAGE_JSONLD_ONLY_HTML, 'lxml')
        book = Book()
        
        JsonLdParser.parse(soup, book)
        
        assert book.name == ''  # Name not extracted from JSON-LD
        assert book.annotation == 'Тестовое описание'
        assert book.genre == 'Тестовый жанр'
        assert book.number_of_pages == 300
        assert book.publisher == 'ТестИздат'
        assert book.year_of_publication == 2023
        assert book.bookbinding == 'Мягкая обложка'  # Paperback mapped
    
    def test_parse_no_json_ld(self):
        """Test parsing page with no JSON-LD script tags."""
        html = '<html><body>No JSON-LD here</body></html>'
        soup = BeautifulSoup(html, 'lxml')
        book = Book()
        
        # Should not raise any exception
        JsonLdParser.parse(soup, book)
        
        # Book should remain unchanged
        assert book.annotation == ''
        assert book.genre == ''
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON in script tag."""
        html = '<script type="application/ld+json">{invalid json}</script>'
        soup = BeautifulSoup(html, 'lxml')
        book = Book()
        
        # Should handle gracefully without exception
        JsonLdParser.parse(soup, book)
    
    def test_parse_multiple_scripts(self):
        """Test parsing multiple JSON-LD script tags."""
        html = '''
        <script type="application/ld+json">{"@type":"Book","name":"Book 1"}</script>
        <script type="application/ld+json">{"@type":"Product","name":"Product 1"}</script>
        '''
        soup = BeautifulSoup(html, 'lxml')
        book = Book()
        
        JsonLdParser.parse(soup, book)
    
    def test_format_mapping(self):
        """Test mapping of bookFormat URLs to Russian names."""
        assert JsonLdParser.FORMAT_MAP['https://schema.org/Hardcover'] == 'Твёрдый переплёт'
        assert JsonLdParser.FORMAT_MAP['https://schema.org/Paperback'] == 'Мягкая обложка'
    
    def test_unknown_format_preserved(self):
        """Test that unknown bookFormat values are preserved as-is."""
        html = '''
            <script type="application/ld+json">
            {"@type":"Book","bookFormat":"https://schema.org/Ebook"}
            </script>
        '''
        soup = BeautifulSoup(html, 'lxml')
        book = Book()
        
        JsonLdParser.parse(soup, book)
        assert book.bookbinding == 'https://schema.org/Ebook'
