"""Storage module for persistent book data storage.

This module provides ParquetStorage for saving and loading book data
using Apache Parquet format with automatic deduplication support.

Example:
    >>> from storage import ParquetStorage
    >>> storage = ParquetStorage('books.parquet')
    >>> storage.save_books([book1, book2])
"""

from .parquet_storage import ParquetStorage

__all__ = ['ParquetStorage']
