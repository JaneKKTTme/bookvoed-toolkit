"""Core module containing the main parser orchestrator and HTTP client.

This module exports the primary classes for interacting with the Bookvoed parser:
- BookvoedParser: Main orchestrator for parsing books from the website
- HTTPClient: Async HTTP client with retry logic and rate limiting

Example:
    >>> from core import BookvoedParser, HTTPClient
    >>> async with BookvoedParser() as parser:
    ...     await parser.parse_bookvoed()
"""

from .parser import BookvoedParser
from .http_client import HTTPClient

__all__ = ['BookvoedParser', 'HTTPClient']
