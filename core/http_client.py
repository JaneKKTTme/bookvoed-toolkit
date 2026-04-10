"""
HTTP client module with retry logic and rate limiting.

This module provides an asynchronous HTTP client with adaptive delays,
automatic retries, and proper error handling for web scraping.
"""

import asyncio
import certifi
import random
import ssl
import time
from collections import deque
from http import HTTPStatus
from typing import Optional

import aiohttp

from config import HEADERS, USER_AGENTS, REQUEST_CONFIG, CONNECTOR_CONFIG
from logging_config import logger


class HTTPClient:
	"""Async HTTP client with retry logic and adaptive rate limiting.
	
	This client handles HTTP requests with automatic retries, exponential backoff,
	rate limit detection, and adaptive delays based on request frequency.
	It maintains a persistent session for connection reuse.
	
	Attributes:
		max_retries (int): Maximum number of retry attempts for failed requests.
		timeout (int): Request timeout in seconds.
		delay (float): Base delay between requests in seconds.
		request_times (Deque[float]): Timestamps of recent requests for rate calculation.
		shutdown_event (asyncio.Event): Event for shutdown signaling.
		session (Optional[aiohttp.ClientSession]): Active HTTP session.
		_connector (Optional[aiohttp.TCPConnector]): TCP connector for the session.
		ssl_context (ssl.SSLContext): Custom SSL context with relaxed verification.
		
	Example:
		>>> async with HTTPClient() as client:
		...	 html = await client.get('https://example.com')
	"""

	def __init__(self, max_retries: int = REQUEST_CONFIG['max_retries'],
			timeout: int = REQUEST_CONFIG['timeout'],
			delay: float = REQUEST_CONFIG['delay_between_requests']):
		"""Initialize the HTTP client with configuration parameters.
		
		Args:
			max_retries (int): Maximum number of retry attempts. Defaults to config.
			timeout (int): Request timeout in seconds. Defaults to config.
			delay (float): Base delay between requests in seconds. Defaults to config.
		"""
		self.max_retries = max_retries
		self.timeout = timeout
		self.delay = delay
		self.request_times = deque(maxlen=60)
		self.shutdown_event = asyncio.Event()
		self.session: Optional[aiohttp.ClientSession] = None
		self._connector = None
		self.ssl_context = self._create_ssl_context()

	def _create_ssl_context(self):
		"""Create a custom SSL context with relaxed certificate validation.
		
		This method disables hostname checking and certificate verification
		to avoid SSL errors with some websites. Use with caution.
		
		Returns:
			ssl.SSLContext: Configured SSL context for HTTPS requests.

		Warning:
			Disabling SSL verification makes the connection vulnerable to 
			MITM attacks. Do not use this pattern for sensitive data or other
			websites.
		"""
		context = ssl.create_default_context(cafile=certifi.where())
		return context

	async def __aenter__(self):
		"""Enter async context manager, initializing HTTP session."""
		self.connector = aiohttp.TCPConnector(**CONNECTOR_CONFIG)
		self.session = aiohttp.ClientSession(connector=self.connector)
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		"""Exit async context manager, closing HTTP session."""
		await self.close()

	async def get(self, url: str) -> Optional[str]:
		"""Perform an HTTP GET request with retry logic and rate limiting.
		
		This method applies adaptive delays based on request frequency,
		rotates User-Agent headers, and retries failed requests with
		exponential backoff. Handles rate limiting responses gracefully.
		
		Args:
			url (str): The URL to request.
			
		Returns:
			Optional[str]: Response text if successful, None if failed.
			
		Raises:
			aiohttp.ClientError: After exhausting all retry attempts for client errors.
			asyncio.TimeoutError: If request times out after all retries.
		
		Note:
			Returns None for HTTP errors like 404, 500, etc.
			Raises exceptions only for connection errors and timeouts.
		"""
		await self._adaptive_delay()

		if not self.session:
			self.session = aiohttp.ClientSession()

		timeout = aiohttp.ClientTimeout(total=self.timeout)

		for attempt in range(self.max_retries):
			try:
				headers = HEADERS.copy()
				headers['User-Agent'] = random.choice(USER_AGENTS)
				headers['Accept-Encoding'] = 'gzip, deflate, br'
				async with self.session.get(
				  url,
				  ssl=self.ssl_context,
				  timeout=timeout,
				  headers=headers
				) as response:
					if response.status == HTTPStatus.TOO_MANY_REQUESTS:
						retry_after = response.headers.get('Retry-After', self.timeout)
						wait_time = int(retry_after)
						logger.warning(f'Rate limited. Waiting {wait_time} seconds...')
						await asyncio.sleep(wait_time)
						response.raise_for_status()

					if response.status != HTTPStatus.OK:
						logger.error(f'HTTP error {response.status} for {url}')
						return None

					return await response.text()

			except aiohttp.ClientResponseError as e:
				if e.status == HTTPStatus.TOO_MANY_REQUESTS:
					logger.error(f'Rate limit exceeded for {url}. Increasing delays...')
					self.delay = min(self.delay * 1.5, 10)
					continue
				elif e.status >= 500:  # Server errors
					wait_time = 2 ** attempt
					logger.warning(f'Server error {e.status} for {url}, retrying in {wait_time}s')
					await asyncio.sleep(wait_time)
					continue  # Retry server errors
				raise

			except (aiohttp.ClientError, asyncio.TimeoutError) as e:
				if attempt == self.max_retries - 1:
					raise

				if isinstance(e, aiohttp.ClientConnectionError):
					if self.session:
						await self.session.close()
					self.session = aiohttp.ClientSession()

				wait_time = 2 ** attempt
				logger.error(f'Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}')
				await asyncio.sleep(wait_time)

		return None  # Should never reach here due to raise above

	async def _adaptive_delay(self) -> None:
		"""Apply adaptive delay based on recent request frequency.
		
		Calculates requests per second over the last minute and adjusts
		the delay proportionally to avoid overwhelming the server.
		Higher request rates result in longer delays.
		"""
		now = time.time()
		self.request_times.append(now)

		while self.request_times and now - self.request_times[0] > 60:
			self.request_times.popleft()

		requests_per_second = len(self.request_times) / 60

		if requests_per_second > 0.8:  # > 48 requests per minute - aggressive
			delay = self.delay * 1.5
		elif requests_per_second > 0.5:  # > 30 requests per minute - moderate
			delay = self.delay * 1.2
		else:  # < 30 requests per minute - safe
			delay = self.delay

		await asyncio.sleep(delay)

	async def close(self):
		"""Close the HTTP session and connector cleanly.
		
		Releases all connections and cleans up resources.
		Should be called when the client is no longer needed.
		"""
		if self.session:
			await self.session.close()
		if self._connector:
			await self._connector.close()

	async def shutdown(self):
		"""Signal graceful shutdown of the HTTP client.
		
		Sets the shutdown event flag, which can be checked by long-running
		operations to exit early.
		"""
		logger.info('Shutting down gracefully...')
		self.shutdown_event.set()
