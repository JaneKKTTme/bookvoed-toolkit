"""Pytest configuration and shared fixtures for Bookvoed parser tests."""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from models.book import Book


@pytest.fixture
def sample_book_data() -> Dict[str, Any]:
    """Return sample book data for testing.
    
    Returns:
        Dict[str, Any]: Sample book attributes including name, author, prices.
    """
    return {
        'name': 'Точка зрения Всеведущего читателя. Том 3 (Всеведущий читатель / Omniscient Reader\'s Viewpoint). Новелла + официальный мерч',
        'url': '/product/tocka-zrenia-vsevedusego-citatela-tom-3-oficial-nyj-merc-8795568',
        'author': 'singNsong',
        'new_price': 1649,
        'old_price': 1953,
        'discount': 16,
        'in_stock': False,
        'availability_status': 'Доставим после начала продаж',
        'genre': 'Зарубежное фэнтези',
        'subgenre': 'Психологический',
        'audience': 'Young Adult',
        'subject': 'Спасение мира;Борьба за власть;LitRPG',
        'annotation': 'Эксклюзивно! Лимитированный тираж новеллы «singNsong. Точка зрения Всеведущего читателя...',
        'publisher': 'О2 Young adult книги',
        'series': 'Точка зрения Всеведущего читателя',
        'section': 'Зарубежное фэнтези',
        'bookbinding': 'Твёрдый переплёт',
        'number_of_pages': 320,
        'year_of_publication': None,
        'edition': 19000,
        'size': '2.2 см × 14.5 см × 22 см',
        'weight': 0.5,
        'rating': 9.1,
        'review_count': 23
    }


@pytest.fixture
def sample_book(sample_book_data: Dict[str, Any]) -> Book:
    """Create a sample Book instance from fixture data.
    
    Args:
        sample_book_data: Sample book data dict.
        
    Returns:
        Book: Populated Book instance.
    """
    return Book(**sample_book_data)


@pytest.fixture
def temp_storage_dir() -> Path:
    """Create a temporary directory for test storage.
    
    Yields:
        Path: Path to temporary directory. Directory is cleaned up after test.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def event_loop():
    """Create a fresh event loop for each async test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_response_text() -> str:
    """Return a minimal HTML response for HTTP client tests.
    
    Returns:
        str: Simple HTML document string.
    """
    return """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body><h1>Hello, World!</h1></body>
        </html>
    """
