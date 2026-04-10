"""Test suite for the Bookvoed parser.

This package contains unit tests and integration tests for all modules:
- test_book_model.py: Tests for the Book data model
- test_http_client.py: Tests for HTTP client with retry logic
- test_list_parser.py: Tests for catalog page parsing
- test_book_parser.py: Tests for book detail page parsing
- test_json_ld_parser.py: Tests for JSON-LD metadata extraction
- test_parquet_storage.py: Tests for Parquet storage with deduplication
- test_parser_integration.py: Integration tests for the main orchestrator
- test_config.py: Tests for configuration constants

Run all tests with:
    pytest tests/ -v

Run with coverage:
    pytest tests/ --cov=. --cov-report=html
"""

# Test fixtures are available in conftest.py and fixtures/html_fixtures.py
