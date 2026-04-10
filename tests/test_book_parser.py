"""Tests for the BookParser class."""

import pytest

from parsers.book_parser import BookParser
from tests.fixtures.html_fixtures import (
    BOOK_PAGE_HTML,
    BOOK_PAGE_PREORDER_HTML,
    BOOK_PAGE_LOW_STOCK_HTML,
    BOOK_PAGE_JSONLD_ONLY_HTML,
    BOOK_PAGE_COMPLEX_PRICE_HTML,
    BOOK_PAGE_WEIGHT_KG_HTML,
    BOOK_PAGE_NO_PRICE_HTML
)


class TestBookParserName:
    """Test book name extraction."""
    
    def test_parse_book_name(self):
        """Test extracting book title from page."""
        parser = BookParser(BOOK_PAGE_HTML, '/book/test')
        parser._parse_book_name()
        assert parser.book.name == 'Мастер и Маргарита'
    
    def test_parse_book_name_missing(self):
        """Test when book title element is missing."""
        html = '<div>No title here</div>'
        parser = BookParser(html, '/book/test')
        parser._parse_book_name()
        assert parser.book.name == ''


class TestBookParserPrices:
    """Test price extraction."""
    
    def test_parse_prices_with_discount(self):
        """Test extracting new price, old price, and discount."""
        parser = BookParser(BOOK_PAGE_HTML, '/book/test')
        parser._parse_prices()
        
        assert parser.book.new_price == 499.0
        assert parser.book.old_price == 799.0
        assert parser.book.discount == 38
    
    def test_parse_prices_no_discount(self):
        """Test extracting price when no discount is present."""
        html = '''
        <div class="price-block-price-info">
            <div class="price-block-price-info__price">
                <span>599 ₽</span>
            </div>
        </div>
        '''
        parser = BookParser(html, '/book/test')
        parser._parse_prices()
        
        assert parser.book.new_price == 599.0
        assert parser.book.old_price is None
        assert parser.book.discount is None
    
    def test_parse_prices_complex_block(self):
        """Test extracting prices from complex price block with extra spans."""
        parser = BookParser(BOOK_PAGE_COMPLEX_PRICE_HTML, '/book/test')
        parser._parse_prices()
        
        assert parser.book.new_price == 1299.0
        assert parser.book.old_price == 1999.0
        assert parser.book.discount == 35
    
    def test_parse_prices_missing_block(self):
        """Test when price block is completely missing."""
        parser = BookParser(BOOK_PAGE_NO_PRICE_HTML, '/book/test')
        parser._parse_prices()
        
        assert parser.book.new_price is None
        assert parser.book.old_price is None


class TestBookParserAvailability:
    """Test availability status extraction."""
    
    def test_parse_availability_in_stock(self):
        """Test parsing 'in stock' availability."""
        parser = BookParser(BOOK_PAGE_HTML, '/book/test')
        parser._parse_availability()
        
        assert parser.book.in_stock is True
        assert 'В наличии' in parser.book.availability_status
    
    def test_parse_availability_preorder(self):
        """Test parsing pre-order availability."""
        parser = BookParser(BOOK_PAGE_PREORDER_HTML, '/book/test')
        parser._parse_availability()
        
        assert parser.book.in_stock is False
        assert parser.book.availability_status == 'Предзаказ'
    
    def test_parse_availability_low_stock(self):
        """Test parsing 'low stock' availability."""
        parser = BookParser(BOOK_PAGE_LOW_STOCK_HTML, '/book/test')
        parser._parse_availability()
        
        assert parser.book.in_stock is True
        assert 'Осталось мало' in parser.book.availability_status
    
    def test_parse_availability_missing(self):
        """Test when availability block is missing."""
        html = '<div>No availability info</div>'
        parser = BookParser(html, '/book/test')
        parser._parse_availability()
        
        assert parser.book.in_stock is False
        assert parser.book.availability_status == ''


class TestBookParserCharacteristics:
    """Test characteristics extraction."""
    
    def test_parse_characteristics(self):
        """Test extracting various book characteristics."""
        parser = BookParser(BOOK_PAGE_HTML, '/book/test')
        parser._parse_characteristics()
        
        assert parser.book.author == 'Булгаков М.А.'
        assert parser.book.publisher == 'Эксмо'
        assert parser.book.number_of_pages == 416
        assert parser.book.weight == 450
        assert parser.book.edition == 10000
    
    def test_parse_characteristics_with_list(self):
        """Test extracting characteristics that contain list items."""
        parser = BookParser(BOOK_PAGE_HTML, '/book/test')
        parser._parse_characteristics()
        
        # Genre should be semicolon-separated from list items
        assert 'Классическая проза' in parser.book.genre
        assert 'Роман' in parser.book.genre
    
    def test_parse_characteristics_weight_kilograms(self):
        """Test parsing weight in kilograms (decimal value)."""
        parser = BookParser(BOOK_PAGE_WEIGHT_KG_HTML, '/book/test')
        parser._parse_characteristics()
        
        assert parser.book.weight == 750


class TestBookParserHelperMethods:
    """Test helper methods of BookParser."""
    
    def test_extract_numbers(self):
        """Test extracting numbers from text."""
        assert BookParser._extract_numbers('499 ₽') == ['499']
        assert BookParser._extract_numbers('Скидка 38%') == ['38']
        assert BookParser._extract_numbers('1 200 г') == ['1', '200']
        assert BookParser._extract_numbers(' ') == []
    
    def test_extract_numbers_with_decimals(self):
        """Test extracting decimal numbers."""
        assert BookParser._extract_numbers('0.75 кг') == ['0', '75']
    
    def test_normalize_text(self):
        """Test text normalization."""
        normalized = BookParser._normalize_text('  Кол-во   Страниц  ')
        assert normalized == 'кол-во страниц'
    
    def test_process_value_weight(self):
        """Test weight value processing."""
        parser = BookParser('', '')
        assert parser._process_value('weight', '450 г') == 450
        assert parser._process_value('weight', '0.75 кг') == 750
    
    def test_process_value_edition(self):
        """Test edition value processing with non-breaking spaces."""
        parser = BookParser('', '')
        assert parser._process_value('edition', '10\xa0000') == 10000
        assert parser._process_value('edition', '5000') == 5000
    
    def test_process_value_non_numeric(self):
        """Test processing non-numeric values."""
        parser = BookParser('', '')
        assert parser._process_value('author', 'Пушкин А.С.') == 'Пушкин А.С.'


class TestBookParserIntegration:
    """Integration tests for complete book parsing."""
    
    def test_parse_complete_book(self):
        """Test full book parsing from HTML."""
        parser = BookParser(BOOK_PAGE_HTML, '/book/test')
        book = parser.parse()
        
        assert book is not None
        assert book.name == 'Мастер и Маргарита'
        assert book.author == 'Булгаков М.А.'
        assert book.new_price == 499.0
        assert book.old_price == 799.0
        assert book.discount == 38
        assert book.in_stock is True
        assert book.publisher == 'Эксмо'
        assert book.number_of_pages == 416
        assert book.weight == 450
        assert book.rating == 4.9
        assert book.review_count == 1250
    
    def test_parse_failure_returns_none(self):
        """Test that parse returns None on critical failure."""
        # Create parser with malformed HTML
        parser = BookParser('<invalid>html</invalid>', '/book/test')
        # Force an error by manipulating the soup
        parser.soup = None
        book = parser.parse()
        assert book is None
