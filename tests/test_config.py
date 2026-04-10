"""Tests for configuration module."""

import pytest

from config import SERVICE, BOOK_PAGE, USER_AGENTS, HEADERS, REQUEST_CONFIG, CONNECTOR_CONFIG


class TestConfigConstants:
    """Test configuration constants."""
    
    def test_service_url(self):
        """Test service URL constant."""
        assert SERVICE == 'https://www.bookvoed.ru'
        assert isinstance(SERVICE, str)
    
    def test_book_page_path(self):
        """Test book page path constant."""
        assert BOOK_PAGE == '/catalog/books-18030?page='
        assert isinstance(BOOK_PAGE, str)
    
    def test_user_agents_list(self):
        """Test user agents list."""
        assert isinstance(USER_AGENTS, list)
        assert len(USER_AGENTS) > 0
        assert all(isinstance(ua, str) for ua in USER_AGENTS)
    
    def test_user_agents_contain_common_browsers(self):
        """Test that user agents include common browser strings."""
        user_agents_str = ' '.join(USER_AGENTS).lower()
        assert 'chrome' in user_agents_str or 'firefox' in user_agents_str
    
    def test_headers_dict(self):
        """Test headers dictionary."""
        assert isinstance(HEADERS, dict)
        assert 'Accept' in HEADERS
        assert 'Accept-Language' in HEADERS
        assert 'ru-RU' in HEADERS['Accept-Language']


class TestRequestConfig:
    """Test request configuration settings."""
    
    def test_request_config_keys(self):
        """Test that all expected keys are present."""
        expected_keys = {'max_retries', 'timeout', 'delay_between_requests', 'concurrent_tasks'}
        assert expected_keys.issubset(REQUEST_CONFIG.keys())
    
    def test_max_retries(self):
        """Test max retries value."""
        assert REQUEST_CONFIG['max_retries'] == 5
        assert isinstance(REQUEST_CONFIG['max_retries'], int)
        assert REQUEST_CONFIG['max_retries'] > 0
    
    def test_timeout(self):
        """Test timeout value."""
        assert REQUEST_CONFIG['timeout'] == 60
        assert isinstance(REQUEST_CONFIG['timeout'], int)
        assert REQUEST_CONFIG['timeout'] > 0
    
    def test_delay_between_requests(self):
        """Test delay between requests value."""
        assert REQUEST_CONFIG['delay_between_requests'] == 0.1
        assert isinstance(REQUEST_CONFIG['delay_between_requests'], float)
    
    def test_concurrent_tasks(self):
        """Test concurrent tasks value."""
        assert REQUEST_CONFIG['concurrent_tasks'] == 50
        assert isinstance(REQUEST_CONFIG['concurrent_tasks'], int)


class TestConnectorConfig:
    """Test connector configuration settings."""
    
    def test_connector_config_keys(self):
        """Test that all expected keys are present."""
        expected_keys = {'limit', 'ttl_dns_cache', 'use_dns_cache', 'force_close', 'enable_cleanup_closed'}
        assert expected_keys.issubset(CONNECTOR_CONFIG.keys())
    
    def test_connection_limit(self):
        """Test connection limit setting."""
        assert CONNECTOR_CONFIG['limit'] == 0
    
    def test_dns_cache(self):
        """Test DNS cache settings."""
        assert CONNECTOR_CONFIG['ttl_dns_cache'] == 300
        assert CONNECTOR_CONFIG['use_dns_cache'] is True
    
    def test_connection_behavior(self):
        """Test connection behavior settings."""
        assert CONNECTOR_CONFIG['force_close'] is False
        assert CONNECTOR_CONFIG['enable_cleanup_closed'] is True
