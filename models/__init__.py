"""Data models module for the Bookvoed parser.

This module defines the Book dataclass representing a book with all its
attributes including pricing, availability, metadata, and physical characteristics.

Example:
    >>> from models import Book
    >>> book = Book(name="Война и мир", author="Лев Толстой", url="/book/123")
"""

from .book import Book

__all__ = ['Book']
