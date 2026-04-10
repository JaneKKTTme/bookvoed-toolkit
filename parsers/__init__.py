"""Parsers module for extracting data from HTML pages.

This module contains three main parsers:
- ListParser: Extracts book links and pagination info from catalog pages
- BookParser: Extracts detailed book information from individual book pages
- JsonLdParser: Extracts structured metadata from JSON-LD script tags

Example:
    >>> from parsers import ListParser, BookParser, JsonLdParser
    >>> list_parser = ListParser(html_content, page=1)
    >>> book_links = list_parser.extract_book_links()
"""

from .list_parser import ListParser
from .book_parser import BookParser
from .json_ld_parser import JsonLdParser

__all__ = ['ListParser', 'BookParser', 'JsonLdParser']
