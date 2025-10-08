"""
HTTP client for API requests
"""

import json
import logging
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import aiohttp
import asyncio

from .exceptions import APIError

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client with retry logic and error handling"""

    def __init__(self, base_url: str, timeout: int = 30, api_key: Optional[str] = None):
        """
        Initialize HTTP client

        Args:
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
            api_key: Optional API key for x-api-key header
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._api_key = api_key  # Store API key for async methods
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'HyperETH-Python-SDK/0.1.0'
        }

        # Add API key header if provided
        if api_key:
            headers['x-api-key'] = api_key

        self.session.headers.update(headers)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """
        Make HTTP request with error handling

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            JSON response data

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )

            # Try to parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = {"message": response.text}

            # Log request_id from response headers if present
            request_id = response.headers.get('x-request-id')
            if request_id:
                logger.debug(f"HTTP Response request_id: {request_id}")
            else:
                logger.debug("HTTP Response: no request_id header found")

            # Check for HTTP errors
            if not response.ok:
                raise APIError(
                    message=data.get('message', f'HTTP {response.status_code}'),
                    status_code=response.status_code,
                    response_data=data
                )

            return data

        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[Any, Any]:
        """Make POST request"""
        return self._make_request('POST', endpoint, json=data)

    def delete(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[Any, Any]:
        """Make DELETE request"""
        return self._make_request('DELETE', endpoint, json=data)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[Any, Any]:
        """Make GET request"""
        return self._make_request('GET', endpoint, params=params)

    async def _make_async_request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """
        Make async HTTP request with error handling

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters (json, params, etc.)

        Returns:
            JSON response data

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'HyperETH-Python-SDK/0.1.0'
        }

        # Add API key header if available
        if hasattr(self, 'session') and hasattr(self.session, 'headers') and 'x-api-key' in self.session.headers:
            headers['x-api-key'] = self.session.headers['x-api-key']
        elif hasattr(self, '_api_key') and self._api_key:
            headers['x-api-key'] = self._api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    **kwargs
                ) as response:

                    # Log request_id from response headers if present
                    request_id = response.headers.get('x-request-id')
                    if request_id:
                        logger.debug(f"HTTP Response request_id: {request_id}")
                    else:
                        logger.debug("HTTP Response: no request_id header found")

                    # Try to parse JSON response
                    try:
                        data = await response.json()
                    except (aiohttp.ContentTypeError, json.JSONDecodeError):
                        text = await response.text()
                        data = {"message": text}

                    # Check for HTTP errors
                    if not response.ok:
                        raise APIError(
                            message=data.get('message', f'HTTP {response.status}'),
                            status_code=response.status,
                            response_data=data
                        )

                    return data

        except aiohttp.ClientError as e:
            raise APIError(f"Request failed: {e}")
        except asyncio.TimeoutError:
            raise APIError(f"Request timed out after {self.timeout}s")

    async def post_async(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[Any, Any]:
        """Make async POST request"""
        return await self._make_async_request('POST', endpoint, json=data)

    async def delete_async(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[Any, Any]:
        """Make async DELETE request"""
        return await self._make_async_request('DELETE', endpoint, json=data)

    async def get_async(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[Any, Any]:
        """Make async GET request"""
        return await self._make_async_request('GET', endpoint, params=params)