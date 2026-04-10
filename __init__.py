"""Bookvoed Parser - Async web scraper for bookvoed.ru"""

__author__ = 'JaneKKTTme'
__license__ = 'MIT'
__version__ = '1.0.0'

from core.parser import BookvoedParser
from models.book import Book

__all__ = ['BookvoedParser', 'Book']
