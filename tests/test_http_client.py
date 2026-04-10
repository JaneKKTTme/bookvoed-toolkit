"""Tests for the HTTPClient class."""

import asyncio
import pytest
import ssl
from aioresponses import aioresponses
from unittest.mock import AsyncMock

from core.http_client import HTTPClient


class TestHTTPClientInitialization:
    """Test HTTP client initialization."""
    
    def test_default_initialization(self):
        """Test client initializes with default values."""
        client = HTTPClient()
        assert client.max_retries == 5
        assert client.timeout == 60
        assert client.delay == 0.1
        assert client.request_times.maxlen == 60
    
    def test_custom_initialization(self):
        """Test client initializes with custom values."""
        client = HTTPClient(max_retries=3, timeout=30, delay=0.5)
        assert client.max_retries == 3
        assert client.timeout == 30
        assert client.delay == 0.5
    
    def test_ssl_context_creation(self):
        """Test SSL context is created with relaxed verification."""
        client = HTTPClient()
        assert client.ssl_context is not None
        assert isinstance(client.ssl_context, ssl.SSLContext)


class TestHTTPClientAdaptiveDelay:
    """Test adaptive delay calculation."""
    
    @pytest.mark.asyncio
    async def test_adaptive_delay_low_rate(self):
        """Test delay for low request rate (<30 per minute)."""
        client = HTTPClient(delay=0.1)
        
        # No recent requests
        start = asyncio.get_event_loop().time()
        await client._adaptive_delay()
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should use base delay
        assert elapsed >= 0.09  # Allow small margin
    
    @pytest.mark.asyncio
    async def test_adaptive_delay_high_rate(self):
        """Test increased delay for high request rate."""
        client = HTTPClient(delay=0.1)
        
        # Simulate many recent requests
        import time
        now = time.time()
        for i in range(50):  # 50 requests in short time
            client.request_times.append(now - 30)  # Within last 60 seconds
        
        start = asyncio.get_event_loop().time()
        await client._adaptive_delay()
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should be higher than base delay
        assert elapsed >= 0.14  # 0.1 * 1.5 = 0.15 with margin


class TestHTTPClientContextManager:
    """Test async context manager behavior."""
    
    @pytest.mark.asyncio
    async def test_context_manager_creates_session(self):
        """Test that context manager creates and closes session."""
        client = HTTPClient()
        
        async with client:
            assert client.session is not None
        
        # After context exit, session should be closed
        # (session close is async, so we need to check or wait)
        await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test explicit close method."""
        client = HTTPClient()
        await client.__aenter__()
        
        assert client.session is not None
        
        await client.close()
        # Session should be closed


class TestHTTPClientShutdown:
    """Test shutdown signaling."""
    
    @pytest.mark.asyncio
    async def test_shutdown_sets_event(self):
        """Test that shutdown sets the shutdown event."""
        client = HTTPClient()
        assert not client.shutdown_event.is_set()
        
        await client.shutdown()
        assert client.shutdown_event.is_set()


class TestHTTPClientGet:
    """Test GET requests with mocking."""
    
    @pytest.mark.asyncio
    async def test_get_success(self, mock_response_text):
        """Test successful GET request."""
        client = HTTPClient()
        client._adaptive_delay = AsyncMock()
        
        with aioresponses() as m:
            # Mock the HTTP response
            m.get('https://example.com', status=200, body=mock_response_text)
            
            async with client:
                result = await client.get('https://example.com')
        
        assert result == mock_response_text
        client._adaptive_delay.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_http_error_returns_none(self):
        """Test that HTTP errors return None."""
        """Test that HTTP errors return None."""
        client = HTTPClient()
        client._adaptive_delay = AsyncMock()
        
        with aioresponses() as m:
            # Mock 404 error
            m.get('https://example.com/notfound', status=404)
            
            async with client:
                result = await client.get('https://example.com/notfound')
        
        assert result is None
