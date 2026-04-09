"""
Parquet storage module for persistent book data storage.

This module provides the ParquetStorage class for saving and loading
book data using Apache Parquet format with deduplication support.
"""

import pyarrow as pa
import pyarrow.parquet as pq
from typing import List, Set, Any, Dict
from pathlib import Path

from models.book import Book
from logging_config import logger


class ParquetStorage:
    """Storage handler for persisting books in Parquet format.
    
    This class manages saving books to a Parquet file with automatic
    deduplication based on book URLs. It maintains an in-memory cache
    of known URLs for efficient duplicate detection.
    
    Attributes:
        filename (str): Path to the Parquet file.
        _known_urls (Set[str]): Cache of URLs already stored.
        _cache_loaded (bool): Whether the URL cache has been initialized.
        _schema (pa.Schema): PyArrow schema defining the data structure.
        
    Example:
        >>> storage = ParquetStorage('books.parquet')
        >>> books = [book1, book2, book3]
        >>> new_count = storage.save_books(books)
    """

    def __init__(self, filename: str = 'books.parquet'):
        """Initialize the ParquetStorage with a filename.
        
        Args:
            filename (str): Path where the Parquet file will be stored.
                Defaults to 'books.parquet'.
        """
        self.filename = filename
        self._known_urls: Set[str] = set()
        # Using set() for O(1) lookup instead of list O(n).
        # With 100,000+ books, this is ~10,000x faster for duplicate detection.

        self._cache_loaded = False
        self._schema = self._create_schema()

    def _create_schema(self) -> pa.Schema:
        """Create the PyArrow schema for book data.
        
        Defines the column names and data types for the Parquet file.
        
        Returns:
            pa.Schema: PyArrow schema with appropriate field types.
        """
        return pa.schema([
            pa.field('name', pa.string()),
            pa.field('url', pa.string()),
            pa.field('author', pa.string()),
            pa.field('new_price', pa.float64()),
            pa.field('old_price', pa.float64()),
            pa.field('discount', pa.int32()),
            pa.field('in_stock', pa.bool_()),
            pa.field('availability_status', pa.string()),
            pa.field('genre', pa.string()),
            pa.field('subgenre', pa.string()),
            pa.field('audience', pa.string()),
            pa.field('subject', pa.string()),
            pa.field('annotation', pa.string()),
            pa.field('publisher', pa.string()),
            pa.field('series', pa.string()),
            pa.field('section', pa.string()),
            pa.field('bookbinding', pa.string()),
            pa.field('number_of_pages', pa.int32()),
            pa.field('year_of_publication', pa.int32()),
            pa.field('edition', pa.int32()),
            pa.field('size', pa.string()),
            pa.field('weight', pa.float64()),
            pa.field('rating', pa.float64()),
            pa.field('review_count', pa.int32()),
        ])

    def _convert_to_correct_type(self, value: Any, field_type: str) -> Any:
        """Convert a value to the appropriate type for Parquet storage.
        
        Handles conversion of strings to numbers, booleans, and other types.
        
        Args:
            value (Any): Input value to convert.
            field_type (str): Target PyArrow type name.
            
        Returns:
            Any: Converted value, or None if conversion fails.
        """
        if value is None:
            return None
            
        if field_type in ('int32', 'int64'):
            if isinstance(value, str):
                cleaned = ''.join(filter(str.isdigit, str(value)))
                if cleaned:
                    return int(cleaned)
                return None
            if isinstance(value, (int, float)):
                return int(value)
            return None
            
        elif field_type in ('float64', 'float32'):
            if isinstance(value, str):
                cleaned = ''.join(c for c in str(value) if c.isdigit() or c in '.-')
                if cleaned:
                    return float(cleaned)
                return None
            if isinstance(value, (int, float)):
                return float(value)
            return None
            
        elif field_type == 'bool_':
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'в наличии')
            return bool(value)
            
        return value

    def _book_to_dict(self, book: Book) -> dict:
        """Convert a Book object to a dictionary with proper types.
        
        Maps Book attributes to the Parquet schema field names and
        converts values to appropriate types.
        
        Args:
            book (Book): Book instance to convert.
            
        Returns:
            dict: Dictionary ready for PyArrow conversion.
        """
        data = book.to_dict()
        
        result = {}
        field_types = {
            'name': 'string',
            'url': 'string',
            'author': 'string',
            'new_price': 'float64',
            'old_price': 'float64',
            'discount': 'int32',
            'in_stock': 'bool_',
            'availability_status': 'string',
            'genre': 'string',
            'subgenre': 'string',
            'audience': 'string',
            'subject': 'string',
            'annotation': 'string',
            'publisher': 'string',
            'series': 'string',
            'section': 'string',
            'bookbinding': 'string',
            'number_of_pages': 'int32',
            'year_of_publication': 'int32',
            'edition': 'int32',
            'size': 'string',
            'weight': 'float64',
            'rating': 'float64',
            'review_count': 'int32',
        }
        
        for pyarrow_field, field_type in field_types.items():
            dict_key = pyarrow_field.replace('_', ' ')
            value = data.get(dict_key)

            converted = self._convert_to_correct_type(value, field_type)
            result[pyarrow_field] = converted
            
        return result

    def load_known_urls(self):
        """Load all existing book URLs from the Parquet file into cache.
        
        This method reads only the URL column to minimize memory usage.
        The cache is used for deduplication when saving new books.
        """
        if self._cache_loaded:
            return

        try:
            if Path(self.filename).exists():
                table = pq.read_table(self.filename, columns=['url'])
                self._known_urls = set(table.column('url').to_pylist())
                logger.info(f'Loaded {len(self._known_urls)} known URLs from parquet cache.')
        except Exception as e:
            logger.error(f'Error loading known URLs: {e}')
            self._known_urls = set()
        finally:
            self._cache_loaded = True

    def save_books(self, books: List[Book]) -> int:
        """Save a list of books to the Parquet file, skipping duplicates.
        
        Only saves books whose URLs are not already in the known URLs cache.
        Updates the cache with newly saved URLs.
        
        Args:
            books (List[Book]): List of Book objects to save.
            
        Returns:
            int: Number of new books successfully saved.

        Warning:
            This method is NOT thread-safe. If called concurrently from multiple
            threads, data corruption may occur. Use external locking if needed.
        """
        try:
            self.load_known_urls()

            new_books = [book for book in books if book.url not in self._known_urls]

            if not new_books:
                logger.info('No new books to save')
                return 0

            new_data = [self._book_to_dict(book) for book in new_books]
            new_table = pa.Table.from_pylist(new_data, schema=self._schema)

            if Path(self.filename).exists():
                existing_table = pq.read_table(self.filename)
                combined_table = pa.concat_tables([existing_table, new_table])
            else:
                combined_table = new_table

            pq.write_table(
                combined_table,
                self.filename,
                compression='SNAPPY',  # Best balance: 70% compression, fast encoding
                row_group_size=100000  # Optimal for 100-200MB files with our schema
            )

            for book in new_books:
                self._known_urls.add(book.url)

            logger.info(f'Added {len(new_books)} new books to Parquet file. '
                       f'Skipped {len(books) - len(new_books)} duplicates. '
                       f'Total books: {len(self._known_urls)}')
            
            return len(new_books)

        except Exception as e:
            logger.error(f'Error saving to Parquet file: {e}')
            return 0

    def get_known_urls(self) -> Set[str]:
        """Get a copy of the known URLs set.
        
        Returns:
            Set[str]: Copy of the cached URLs set.
        """
        if not self._cache_loaded:
            self.load_known_urls()
        return self._known_urls.copy()

    def read_all(self) -> pa.Table:
        """Read all book data from the Parquet file.
        
        Returns:
            pa.Table: PyArrow table containing all stored books.
                Returns an empty table with the schema if file doesn't exist.
        """
        if Path(self.filename).exists():
            return pq.read_table(self.filename)
        return pa.Table.from_pylist([], schema=self._schema)

    def get_stats(self) -> dict:
        """Get statistics about the storage file.
        
        Returns:
            dict: Dictionary containing file statistics including:
                - filename: Name of the storage file
                - total_books: Number of unique books in cache
                - cache_loaded: Whether cache is initialized
                - file_size_mb: Size in megabytes (if file exists)
                - num_rows: Number of rows (if file exists)
                - num_columns: Number of columns (if file exists)
                - num_row_groups: Number of row groups (if file exists)
                - compression: Compression algorithm used
        """
        stats = {
            'filename': self.filename,
            'total_books': len(self._known_urls),
            'cache_loaded': self._cache_loaded
        }
        
        if Path(self.filename).exists():
            file_size = Path(self.filename).stat().st_size
            stats['file_size_mb'] = file_size / (1024 * 1024)
            
            try:
                metadata = pq.read_metadata(self.filename)
                stats['num_rows'] = metadata.num_rows
                stats['num_columns'] = metadata.num_columns
                stats['num_row_groups'] = metadata.num_row_groups
                stats['compression'] = 'SNAPPY'
            except Exception:
                pass

        return stats
