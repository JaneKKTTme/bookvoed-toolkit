"""Tests for the ParquetStorage class."""

import pytest
import pyarrow as pa
from pathlib import Path

from models.book import Book
from storage.parquet_storage import ParquetStorage


class TestParquetStorageInitialization:
    """Test storage initialization."""
    
    def test_default_filename(self):
        """Test default filename is 'books.parquet'."""
        storage = ParquetStorage()
        assert storage.filename == 'books.parquet'
    
    def test_custom_filename(self, temp_storage_dir):
        """Test custom filename."""
        custom_path = temp_storage_dir / 'custom_books.parquet'
        storage = ParquetStorage(str(custom_path))
        assert storage.filename == str(custom_path)
    
    def test_schema_creation(self):
        """Test schema has expected fields."""
        storage = ParquetStorage()
        schema = storage._schema
        
        field_names = [field.name for field in schema]
        expected_fields = ['name', 'url', 'author', 'new_price', 'old_price',
                          'discount', 'in_stock', 'availability_status']
        
        for field in expected_fields:
            assert field in field_names


class TestParquetStorageTypeConversion:
    """Test type conversion for Parquet storage."""
    
    def setup_method(self):
        self.storage = ParquetStorage()
    
    def test_convert_to_int_from_string(self):
        """Test converting string to int."""
        result = self.storage._convert_to_correct_type('123', 'int32')
        assert result == 123
    
    def test_convert_to_int_from_float(self):
        """Test converting float to int."""
        result = self.storage._convert_to_correct_type(123.45, 'int32')
        assert result == 123
    
    def test_convert_to_int_with_cleaning(self):
        """Test cleaning string before int conversion."""
        result = self.storage._convert_to_correct_type('1 234', 'int32')
        assert result == 1234
    
    def test_convert_to_float_from_string(self):
        """Test converting string to float."""
        result = self.storage._convert_to_correct_type('123.45', 'float64')
        assert result == 123.45
    
    def test_convert_to_float_from_int(self):
        """Test converting int to float."""
        result = self.storage._convert_to_correct_type(123, 'float64')
        assert result == 123.0
    
    def test_convert_to_bool_from_string_true(self):
        """Test converting truthy strings to bool."""
        assert self.storage._convert_to_correct_type('true', 'bool_') is True
        assert self.storage._convert_to_correct_type('True', 'bool_') is True
        assert self.storage._convert_to_correct_type('в наличии', 'bool_') is True
        assert self.storage._convert_to_correct_type('1', 'bool_') is True
    
    def test_convert_to_bool_from_string_false(self):
        """Test converting falsy strings to bool."""
        assert self.storage._convert_to_correct_type('false', 'bool_') is False
        assert self.storage._convert_to_correct_type('', 'bool_') is False
    
    def test_convert_none(self):
        """Test None conversion."""
        assert self.storage._convert_to_correct_type(None, 'int32') is None
        assert self.storage._convert_to_correct_type(None, 'float64') is None
        assert self.storage._convert_to_correct_type(None, 'bool_') is None


class TestParquetStorageBookConversion:
    """Test Book to dict conversion for storage."""
    
    def test_book_to_dict_conversion(self, sample_book):
        """Test converting Book to dictionary with proper types."""
        storage = ParquetStorage()
        result = storage._book_to_dict(sample_book)
        
        assert result['name'] == sample_book.name
        assert result['url'] == sample_book.url
        assert result['new_price'] == sample_book.new_price
        assert result['discount'] == sample_book.discount
        assert result['in_stock'] == sample_book.in_stock
    
    def test_book_to_dict_none_values(self):
        """Test handling of None values."""
        book = Book(name='Test Book', url='/test')
        storage = ParquetStorage()
        result = storage._book_to_dict(book)
        
        assert result['new_price'] is None
        assert result['old_price'] is None
        assert result['discount'] is None


class TestParquetStorageSaveAndLoad:
    """Test saving and loading books."""
    
    def test_save_single_book(self, temp_storage_dir, sample_book):
        """Test saving a single book."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        
        count = storage.save_books([sample_book])
        
        assert count == 1
        assert storage.get_known_urls() == {sample_book.url}
    
    def test_save_books_deduplication(self, temp_storage_dir, sample_book):
        """Test that duplicates are not saved."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        
        # Save first time
        count1 = storage.save_books([sample_book])
        assert count1 == 1
        
        # Save second time (duplicate)
        count2 = storage.save_books([sample_book])
        assert count2 == 0  # No new books
    
    def test_save_multiple_books(self, temp_storage_dir, sample_book_data):
        """Test saving multiple books."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        
        book1 = Book(**sample_book_data)
        book2 = Book(name='Book 2', url='/book/2', author='Author 2')
        
        count = storage.save_books([book1, book2])
        
        assert count == 2
        assert len(storage.get_known_urls()) == 2
    
    def test_save_partial_duplicates(self, temp_storage_dir, sample_book_data):
        """Test saving mix of new and duplicate books."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        
        book1 = Book(**sample_book_data)
        book2 = Book(name='New Book', url='/book/new', author='New Author')
        
        # Save both first time
        storage.save_books([book1, book2])
        
        # Create new book plus duplicate
        book3 = Book(name='Another New', url='/book/another', author='Author')
        count = storage.save_books([book1, book3])
        
        assert count == 1  # Only book3 is new
        assert len(storage.get_known_urls()) == 3
    
    def test_read_all_books(self, temp_storage_dir, sample_book):
        """Test reading all saved books."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        storage.save_books([sample_book])
        
        table = storage.read_all()
        
        assert table.num_rows == 1
        assert table.column('name')[0].as_py() == sample_book.name
    
    def test_read_all_empty(self, temp_storage_dir):
        """Test reading when no file exists."""
        storage = ParquetStorage(str(temp_storage_dir / 'nonexistent.parquet'))
        table = storage.read_all()
        
        assert table.num_rows == 0
        assert table.schema == storage._schema


class TestParquetStorageStats:
    """Test statistics gathering."""
    
    def test_get_stats_without_file(self, temp_storage_dir):
        """Test stats when file doesn't exist."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        stats = storage.get_stats()
        
        assert stats['filename'] == str(temp_storage_dir / 'test.parquet')
        assert stats['total_books'] == 0
        assert stats['cache_loaded'] is False
    
    def test_get_stats_with_file(self, temp_storage_dir, sample_book):
        """Test stats after saving books."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        storage.save_books([sample_book])
        
        stats = storage.get_stats()
        
        assert stats['total_books'] == 1
        assert stats['file_size_mb'] > 0
        assert 'num_rows' in stats
        assert 'num_columns' in stats


class TestParquetStorageEdgeCases:
    """Test edge cases and error handling."""
    
    def test_save_empty_list(self, temp_storage_dir):
        """Test saving empty list of books."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        count = storage.save_books([])
        
        assert count == 0
    
    def test_load_known_urls_corrupted_file(self, temp_storage_dir):
        """Test loading corrupted file."""
        file_path = temp_storage_dir / 'corrupt.parquet'
        file_path.write_text('Not a valid parquet file')
        
        storage = ParquetStorage(str(file_path))
        storage.load_known_urls()
        
        # Should handle gracefully
        assert storage._known_urls == set()
        assert storage._cache_loaded is True
    
    def test_save_book_with_invalid_types(self, temp_storage_dir):
        """Test saving book with invalid type values."""
        storage = ParquetStorage(str(temp_storage_dir / 'test.parquet'))
        
        # Create book with invalid types
        book = Book(
            name='Test',
            url='/test',
            new_price='not a number',  # Will become None
            discount='not a number'    # Will become None
        )
        
        # Should not raise exception
        count = storage.save_books([book])
        assert count == 1

        assert book.new_price is None
        assert book.discount is None
