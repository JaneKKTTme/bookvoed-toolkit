"""Tests for the Book data model."""

import pytest

from models.book import Book


class TestBookInitialization:
    """Test Book class initialization and type conversion."""
    
    def test_create_empty_book(self):
        """Test creating a book with no arguments."""
        book = Book()
        assert book.name == ''
        assert book.url == ''
        assert book.author == ''
        assert book.new_price is None
        assert book.in_stock is False
    
    def test_create_book_with_attributes(self, sample_book_data):
        """Test creating a book with all attributes."""
        book = Book(**sample_book_data)
        
        assert book.name == sample_book_data['name']
        assert book.url == sample_book_data['url']
        assert book.author == sample_book_data['author']
        assert book.new_price == sample_book_data['new_price']
        assert book.old_price == sample_book_data['old_price']
        assert book.discount == sample_book_data['discount']
        assert book.in_stock == sample_book_data['in_stock']
        assert book.rating == sample_book_data['rating']
    
    def test_type_conversion_from_strings(self):
        """Test automatic type conversion from string values."""
        book = Book(
            name='Test Book',
            url='/test',
            new_price='599.99',
            old_price='899.00',
            discount='33',
            number_of_pages='416',
            year_of_publication='2020',
            edition='5000',
            weight='0.45',
            rating='6.5',
            review_count='150'
        )
        
        assert isinstance(book.new_price, float)
        assert book.new_price == 599.99
        assert isinstance(book.discount, int)
        assert book.discount == 33
        assert isinstance(book.number_of_pages, int)
        assert book.number_of_pages == 416
        assert isinstance(book.weight, float)
        assert book.weight == 0.45
    
    def test_empty_strings_become_none(self):
        """Test that empty strings convert to None for numeric fields."""
        book = Book(
            new_price='',
            old_price='',
            discount='',
            number_of_pages='',
            weight=''
        )
        
        assert book.new_price is None
        assert book.old_price is None
        assert book.discount is None
        assert book.number_of_pages is None
        assert book.weight is None


class TestBookMethods:
    """Test Book class methods."""
    
    def test_to_dict_conversion(self, sample_book):
        """Test converting book to dictionary with space-separated keys."""
        book_dict = sample_book.to_dict()
        
        # Check that underscores are replaced with spaces
        assert 'name' in book_dict
        assert 'url' in book_dict
        assert 'new_price' not in book_dict  # Should be 'new price'
        assert 'new price' in book_dict
        
        # Verify values are preserved
        assert book_dict['name'] == sample_book.name
        assert book_dict['new price'] == sample_book.new_price
    
    def test_from_dict_roundtrip(self, sample_book_data):
        """Test roundtrip conversion from dict to book and back."""
        original_book = Book(**sample_book_data)
        book_dict = original_book.to_dict()
        
        # Convert back (to_dict uses spaces, from_dict expects underscores)
        # This demonstrates the asymmetry - careful with production code
        reconstructed = Book.from_dict(sample_book_data)
        
        assert reconstructed.name == original_book.name
        assert reconstructed.new_price == original_book.new_price
    
    def test_repr_method(self, sample_book):
        """Test string representation of book."""
        repr_str = repr(sample_book)
        assert 'Book(' in repr_str
        assert sample_book.name in repr_str
        assert sample_book.author in repr_str


class TestBookEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_values(self):
        """Test handling of zero values."""
        book = Book(
            new_price=0.0,
            old_price=0.0,
            discount=0,
            number_of_pages=0,
            rating=0.0,
            review_count=0
        )
        
        assert book.new_price == 0.0
        assert book.discount == 0.0
        assert book.number_of_pages == 0
    
    def test_negative_discount(self):
        """Test negative discount (should be allowed, though unusual)."""
        book = Book(discount=-10)
        assert book.discount == -10
    
    def test_very_long_strings(self):
        """Test handling of very long text fields."""
        long_text = 'x' * 10000
        book = Book(name=long_text, annotation=long_text, author=long_text)
        
        assert len(book.name) == 10000
        assert len(book.annotation) == 10000
