"""
Book data model module.

This module defines the Book dataclass representing a book with all its
attributes including pricing, availability, metadata, and physical characteristics.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Book:
    """Data model representing a book with all available attributes.
    
    This class stores comprehensive information about a book including
    bibliographic data, pricing, availability, physical characteristics,
    and user ratings. It provides conversion methods for serialization.
    
    Attributes:
        name (str): Book title.
        url (str): Relative URL of the book detail page.
        author (str): Book author name.
        new_price (Optional[float]): Current selling price in rubles.
        old_price (Optional[float]): Original price before discount.
        discount (Optional[int]): Discount percentage.
        in_stock (bool): Whether the book is currently in stock.
        availability_status (str): Raw availability text.
        genre (str): Book genre.
        subgenre (str): Book subgenre.
        audience (str): Target audience (e.g., children, adults).
        subject (str): Subject or topic area.
        annotation (str): Book description or summary.
        publisher (str): Publishing house.
        series (str): Book series name.
        section (str): Catalog section.
        bookbinding (str): Binding type (hardcover, paperback).
        number_of_pages (Optional[int]): Total page count.
        year_of_publication (Optional[int]): Publication year.
        edition (Optional[int]): Edition number or print run.
        size (str): Physical dimensions.
        weight (Optional[float]): Book weight in grams.
        rating (Optional[float]): Average user rating (0-5).
        review_count (Optional[int]): Number of user reviews.
        
    Example:
        >>> book = Book(
        ...  name="War and Peace",
        ...  url="/book/123",
        ...  author="Leo Tolstoy",
        ...  new_price=500.0
        ... )
        >>> print(book.to_dict())
    """

    name: str = ''
    url: str = ''
    author: str = ''

    new_price: Optional[float] = None
    old_price: Optional[float] = None
    discount: Optional[int] = None

    in_stock: bool = False
    availability_status: str = ''

    genre: str = ''
    subgenre: str = ''
    audience: str = ''
    subject: str = ''
    annotation: str = ''

    publisher: str = ''
    series: str = ''
    section: str = ''
    bookbinding: str = ''
    number_of_pages: Optional[int] = None
    year_of_publication: Optional[int] = None
    edition: Optional[int] = None
    size: str = ''
    weight: Optional[float] = None

    rating: Optional[float] = None
    review_count: Optional[int] = None


    def __init__(self, **kwargs):
        """Initialize a Book instance from keyword arguments.
        
        Performs type conversion for numeric fields to ensure proper
        data types regardless of input format.
        
        Args:
            **kwargs: Arbitrary keyword arguments corresponding to book attributes.
                Numeric fields can be passed as strings and will be converted.

        Warning:
            Some fields from the website contain non-breaking spaces (\xa0) and
            other special characters that need cleaning.
            Example: "1\xa0000" -> "1000" for edition field.
        """

        def safe_float(value):
            if value is None or value == '':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        def safe_int(value):
            if value is None or value == '':
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        self.name = kwargs.get('name', '')
        self.url = kwargs.get('url', '')
        self.author = kwargs.get('author', '')

        self.new_price = safe_float(kwargs.get('new_price', ''))
        self.old_price = safe_float(kwargs.get('old_price', ''))
        self.discount = safe_int(kwargs.get('discount', ''))

        self.in_stock = kwargs.get('in_stock', False)
        self.availability_status = kwargs.get('availability_status', '')

        self.genre = kwargs.get('genre', '')
        self.subgenre = kwargs.get('subgenre', '')
        self.audience = kwargs.get('audience', '')
        self.subject = kwargs.get('subject', '')
        self.annotation = kwargs.get('annotation', '')

        self.publisher = kwargs.get('publisher', '')
        self.series = kwargs.get('series', '')
        self.section = kwargs.get('section', '')
        self.bookbinding = kwargs.get('bookbinding', '')

        self.number_of_pages = safe_int(kwargs.get('number_of_pages', ''))
        self.year_of_publication = safe_int(kwargs.get('year_of_publication', ''))
        self.edition = safe_int(kwargs.get('edition', ''))

        self.size = kwargs.get('size', '')
        self.weight = safe_float(kwargs.get('weight', ''))
        self.rating = safe_float(kwargs.get('rating', ''))
        self.review_count = safe_int(kwargs.get('review_count', ''))

    def __repr__(self):
        """Return a string representation of the Book instance.
        
        Returns:
            str: Human-readable representation with name and author.
        """
        return f'Book(name="{self.name}", author="{self.author}")'

    @classmethod
    def from_dict(cls, data):
        """Create a Book instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing book attributes.
            
        Returns:
            Book: New Book instance populated from the dictionary.
        """
        return cls(**data)

    def to_dict(self):
        """Convert the Book instance to a dictionary.
        
        Converts underscore field names to space-separated keys
        for compatibility with Parquet storage schema.
        
        Returns:
            dict: Dictionary representation with space-separated keys.
        """
        book = {}
        for key, value in asdict(self).items():
            key = key.replace('_', ' ')
            book[key] = value
        return book
