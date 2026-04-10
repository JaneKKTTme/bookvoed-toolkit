"""
Book detail page parser module.

This module provides the BookParser class for extracting book information
from individual book detail pages using BeautifulSoup.
"""

import re
from bs4 import BeautifulSoup, Tag

from models.book import Book
from parsers.json_ld_parser import JsonLdParser
from typing import Optional

from logging_config import logger


class BookParser:
    """Parser for extracting book details from individual book pages.
    
    This class parses HTML content of a book detail page and extracts
    all available information including title, author, prices, availability,
    and physical characteristics.
    
    Attributes:
        CHAR_MAPPING (Dict[str, str]): Mapping of Russian characteristic names
            to English attribute names for the Book model.
        soup (BeautifulSoup): Parsed HTML content.
        url (str): URL of the book page.
        book (Book): Book instance being populated.
        
    Example:
        >>> parser = BookParser(html_content, '/book/123')
        >>> book = parser.parse()
    """

    CHAR_MAPPING = {
        'автор': 'author',
        'жанр': 'genre',
        'поджанр': 'subgenre',
        'аудитория': 'audience',
        'тематика': 'subject',
        'издательство': 'publisher',
        'серия': 'series',
        'переплет': 'bookbinding',
        'кол-во страниц': 'number_of_pages',
        'раздел': 'section',
        'размеры': 'size',
        'вес': 'weight',
        'тираж': 'edition',
    }

    def __init__(self, html: str, url: str):
        """Initialize the BookParser with HTML content and URL.
        
        Args:
            html (str): HTML content of the book detail page.
            url (str): URL of the book page (relative or absolute).
        """
        self.soup = BeautifulSoup(html, 'lxml')
        self.url = url
        self.book = Book()
        self.book.url = url

    def parse(self) -> Optional[Book]:
        """Parse the book page and extract all available information.
        
        Orchestrates the parsing of different sections: name, JSON-LD metadata,
        prices, availability, and characteristics. Returns None on failure.
        
        Returns:
            Optional[Book]: Populated Book object, or None if parsing failed.
        """
        try:
            self._parse_book_name()
            JsonLdParser.parse(self.soup, self.book)
            self._parse_prices()
            self._parse_availability()
            self._parse_characteristics()

            return self.book
        except Exception as e:
            logger.error(f'Error parsing book {self.url}: {e}', exc_info=True)
            return None

    def _parse_book_name(self):
        """Extract the book title from the page.
        
        Looks for the title in the product-title-author__title h1 element.
        """
        name_tag = self.soup.find('h1', attrs={'class': 'product-title-author__title'})
        self.book.name = name_tag.get_text(strip=True) if name_tag else ''

    def _parse_prices(self):
        """Extract pricing information including current price, original price, and discount.
        
        Parses the price block to find new price, old price (if discounted),
        and discount percentage. Handles various price block structures.
        """
        price_block = self.soup.find('div', attrs={'class': 'price-block-price-info'})
        if price_block:
            price_container = price_block.find('div', attrs={'class': 'price-block-price-info__price'})
            if price_container:
                spans = price_container.find_all('span')

                # Note: Bookvoed.ru uses different price block structures:
                # - 1 span: just current price (no discount)
                # - 2 spans: current price (span[0]) + old price (span[1])
                # - 3+ spans: sometimes includes currency or special offers
                if len(spans) >= 1:
                    new_price = self._extract_numbers(spans[0].get_text(strip=True))
                    if new_price:
                        self.book.new_price = float(''.join(new_price))

                if len(spans) >= 2:
                    old_price = self._extract_numbers(spans[1].get_text(strip=True))
                    if old_price:
                        self.book.old_price = float(''.join(old_price))

            discount = price_block.find('div', attrs={'class': 'price-block-price-info__discount'})
            if discount:
                discount_text = discount.get_text(strip=True)
                discount_match = re.search(r'(\d+)', discount_text)
                if discount_match:
                    self.book.discount = int(discount_match.group(1))

    def _parse_availability(self):
        """Extract availability status and determine if book is in stock.
        
        Parses the availability block to get the raw status text and
        sets the in_stock boolean based on keywords like 'в наличии'.
        """
        availability_block = self.soup.find('div', attrs={'class': 'price-block-availability '
                                                              'order-info-price-block__availability'})
        if not availability_block:
            availability_block = self.soup.find('div', attrs={'class': 'price-block-preorder'})
        
        if availability_block:
            availability_text = availability_block.get_text(strip=True)
            self.book.availability_status = availability_text

            text_lower = availability_text.lower()
            self.book.in_stock = any(word in text_lower for word in ['в наличии', 'осталось мало'])

    def _parse_characteristics(self):
        """Extract physical characteristics and metadata from the characteristics table.
        
        Parses the product characteristics table and maps Russian labels
        to English Book model attributes using CHAR_MAPPING.
        """
        characteristics = self._extract_characteristics()

        for key, value in characteristics.items():
            mapped_key = self.CHAR_MAPPING.get(key.lower(), key)
            processed_value = self._process_value(mapped_key, value)
            setattr(self.book, mapped_key, processed_value)

    def _extract_characteristics(self) -> dict:
        """Extract book characteristics from the product table.
    
        Returns:
            dict: Dictionary mapping characteristic names to values.
                  Returns empty dict if no characteristics table found.
        """
        characteristics = {}

        full_char_table = self.soup.find('div', class_='product-characteristics-full')
        if full_char_table:
            rows = full_char_table.find_all('tr', class_='product-characteristics-full__row')
            for row in rows:
                th = row.find('th', class_='product-characteristics-full__cell-th')
                td = row.find('td', class_='product-characteristics-full__cell-td')

                if th and td:
                    key = self._normalize_text(th.get_text(strip=True))
                    value = self._extract_value(td)
                    
                    if key and value:
                        characteristics[key] = value
        return characteristics

    def _extract_value(self, html_block: Tag) -> str:
        """Extract text value from a characteristics cell.
    
        Handles list items by joining them with semicolons.
        
        Args:
            html_block (Tag): BeautifulSoup tag containing the value.
            
        Returns:
            str: Extracted text value. If the cell contains a list (<ul>/<li>),
                returns semicolon-separated values. Otherwise returns plain text.
                
        Examples:
            >>> # For a cell with list items
            >>> value = parser._extract_value(td_with_list)
            >>> # Returns: "Фантастика;Роман;Приключения"
            
            >>> # For a plain text cell
            >>> value = parser._extract_value(td_with_text)
            >>> # Returns: "Издательство АСТ"
        """
        list_items = html_block.find_all('li')
        if list_items:
            return ';'.join(item.get_text(strip=True).replace(',', '') for item in list_items)
        return html_block.get_text(strip=True)

    @staticmethod
    def _extract_numbers(text: str) -> list:
        """Extract text value from a characteristics cell.
        
        Uses regex pattern \\d+ to find consecutive digit sequences.
        Returns all matches as strings, preserving order of appearance.
        
        Args:
            text (str): Input string that may contain numbers.
            
        Returns:
            str: List of numeric strings found in the text.
                Returns empty list if no digits are present.

        Examples:
            >>> BookParser._extract_numbers("Цена: 499 руб.")
            ['499']
        
            >>> BookParser._extract_numbers("Скидка 25%, старая цена 699")
            ['25', '699']
        
            >>> BookParser._extract_numbers("Нет цифр здесь")
            []
        
            >>> BookParser._extract_numbers("1,234 and 56.78")
            ['1', '234', '56', '78']
        """
        return re.findall(r'\d+', text)

    def _process_value(self, key: str, value: str):
        """Process and convert characteristic values to appropriate types.
        
        Performs type conversion for numeric fields like weight and edition.
        
        Args:
            key (str): Attribute name in the Book model.
            value (str): Raw string value from the page.
            
        Returns:
            Any: Converted value (float for weight, int for edition, or original string).
                Returns None if conversion fails for numeric fields.

        Examples:
            >>> parser._process_value('weight', '320 г')
            320.0
            
            >>> parser._process_value('weight', '0.5 кг')
            0.5
            
            >>> parser._process_value('edition', '1\xa0000')
            1000
            
            >>> parser._process_value('author', 'Пушкин А.С.')
            'Пушкин А.С.'
        """
        if key == 'weight':
            # Weight formats from site: '320 г', '0.5 кг', '1 200 г'
            # Extracts first number (integer or decimal) from the string
            match = re.search(r'(\d+(?:\.\d+)?)', value.replace('\xa0', ' ').replace(',', '.'))
            if match:
                weight_value = float(match.group(1))
                if 'кг' in value.lower() and weight_value < 10:
                    return weight_value * 1000
                else:
                    return weight_value
            return None
        elif key == 'edition':
            # Edition may contain non-breaking spaces (\xa0) as thousand separators
            # Example: '1\xa0000' -> '1000'
            match = re.search(r'(\d+(?:\xA0\d+)?)', value)
            return int(match.group(1).replace('\xA0', '')) if match else None
        elif key == 'number_of_pages':
            match = re.search(r'(\d+)', value)
            return int(match.group(1)) if match else None
        return value

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text by converting to lowercase and removing extra spaces.
        
        Args:
            text (str): Text to normalize.
            
        Returns:
            str: Normalized text.
        """
        return ' '.join(text.lower().split())
