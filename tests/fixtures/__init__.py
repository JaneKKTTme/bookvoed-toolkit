"""HTML fixtures for testing parsers.

This package contains mock HTML data extracted from bookvoed.ru
for realistic testing of parser behavior without making live HTTP requests.

Available fixtures:
    BOOK_PAGE_HTML: Complete book detail page
    CATALOG_PAGE_HTML: Catalog page with multiple books
    CATALOG_PAGE_EMPTY_HTML: Empty catalog page
    BOOK_PAGE_PREORDER_HTML: Book page with pre-order status
    BOOK_PAGE_LOW_STOCK_HTML: Book page with low stock indication
    And more specialized fixtures for edge cases

Example:
    >>> from tests.fixtures.html_fixtures import BOOK_PAGE_HTML
    >>> from parsers.book_parser import BookParser
    >>> parser = BookParser(BOOK_PAGE_HTML, '/book/test')
    >>> book = parser.parse()
"""

from .html_fixtures import (
    BOOK_PAGE_HTML,
    CATALOG_PAGE_HTML,
    CATALOG_PAGE_EMPTY_HTML,
    CATALOG_PAGE_WITH_NEXT_BUTTON,
    BOOK_PAGE_PREORDER_HTML,
    BOOK_PAGE_LOW_STOCK_HTML,
    BOOK_PAGE_JSONLD_ONLY_HTML,
    BOOK_PAGE_COMPLEX_PRICE_HTML,
    BOOK_PAGE_WEIGHT_KG_HTML,
    BOOK_PAGE_NO_PRICE_HTML,
)

__all__ = [
    'BOOK_PAGE_HTML',
    'CATALOG_PAGE_HTML',
    'CATALOG_PAGE_EMPTY_HTML',
    'CATALOG_PAGE_WITH_NEXT_BUTTON',
    'BOOK_PAGE_PREORDER_HTML',
    'BOOK_PAGE_LOW_STOCK_HTML',
    'BOOK_PAGE_JSONLD_ONLY_HTML',
    'BOOK_PAGE_COMPLEX_PRICE_HTML',
    'BOOK_PAGE_WEIGHT_KG_HTML',
    'BOOK_PAGE_NO_PRICE_HTML',
]
