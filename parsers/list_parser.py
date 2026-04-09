"""
Catalog page parser module.

This module provides the ListParser class for extracting book links
and navigation information from catalog listing pages.
"""

import re
from bs4 import BeautifulSoup
from typing import List

from logging_config import logger


class ListParser:
    """Parser for catalog listing pages.
    
    This class extracts book links from catalog pages and determines
    whether a next page exists for pagination navigation.
    
    Attributes:
        soup (BeautifulSoup): Parsed HTML content.
        page (int): Current catalog page number.
        
    Example:
        >>> parser = ListParser(html_content, page=1)
        >>> links = parser.extract_book_links()
        >>> has_next = parser.has_next_page(1)
    """

    def __init__(self, html: str, page: int):
        """Initialize the ListParser with HTML content and page number.
        
        Args:
            html (str): HTML content of the catalog page.
            page (int): Current catalog page number.
        """
        self.soup = BeautifulSoup(html, 'lxml')
        self.page = page

    def extract_book_links(self) -> List[str]:
        """Extract all book detail page links from the catalog page.
        
        Searches for product card links with the appropriate CSS class
        and extracts the href attributes.
        
        Returns:
            List[str]: List of relative URLs to book detail pages.
                Returns empty list if no links are found.
        """
        book_links = []
        
        # 'product-card__image-link base-link' - observed class pattern from site
        # As of 2024-12, this is stable. Monitor for changes.
        for book_card in self.soup.find_all('a', attrs={'class': 'product-card__image-link base-link'}):
            href = book_card.get('href')
            if href:
                book_links.append(href)

        if not book_links:
            logger.warning(f'No book links found on page {self.page}')
            
        return book_links

    def has_next_page(self, current_page: int) -> bool:
        """Determine if there is a next page in the catalog.
        
        Checks for pagination links containing "Далее" (Next) or
        URL parameters with the next page number.
        
        Args:
            current_page (int): Current page number being processed.
            
        Returns:
            bool: True if a next page exists, False otherwise.
        """
        next_buttons = self.soup.find_all('a', string=re.compile(r'Далее|Следующая|Вперед|>', re.I))
        if next_buttons:
            return True

        pagination_links = self.soup.find_all('a', href=True)
        for link in pagination_links:
            href = link.get('href', '')
            if f'page={current_page + 1}' in href:
                return True

        return False

    def has_books(self) -> bool:
        """Check if the catalog page contains any books.
        
        Looks for the product list container element which indicates
        that books are present on the page.
        
        Returns:
            bool: True if books are found on the page, False otherwise.
        """
        container = self.soup.find('div', attrs={'class': 'product-list app-catalog__products'})
        return container is not None
