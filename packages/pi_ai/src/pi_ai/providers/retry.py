"""Retry utilities for LLM API calls.

This module provides exponential backoff retry logic for handling
transient API errors (rate limits, network issues, etc.).
"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, TypeVar, Optional

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, last_error: Exception, attempts: int):
        self.last_error = last_error
        self.attempts = attempts
        super().__init__(f"Failed after {attempts} attempts. Last error: {last_error}")


async def retry_with_backoff(
    func: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    initial_delay_ms: int = 1000,
    max_delay_ms: int = 32000,
    exponential_base: float = 2.0,
    jitter: bool = True,
    **kwargs: Any,
) -> T:
    """
    Retry a function with exponential backoff.

    Args:
        func: The async function to retry
        max_attempts: Maximum number of retry attempts
        initial_delay_ms: Initial delay between retries (milliseconds)
        max_delay_ms: Maximum delay between retries (milliseconds)
        exponential_base: Multiplier for delay increase
        jitter: Add random jitter to avoid thundering herd
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result of func

    Raises:
        RetryError: If all attempts are exhausted
        Exception: Any non-transient exception from func
    """
    last_exception: Optional[Exception] = None
    delay = initial_delay_ms / 1000.0  # Convert to seconds

    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            # Don't retry on non-transient errors
            if _should_not_retry(e):
                raise

            # Don't retry on last attempt
            if attempt == max_attempts - 1:
                raise RetryError(e, attempt + 1)

            # Calculate delay for next attempt
            delay = min(
                delay * exponential_base,
                max_delay_ms / 1000.0,
            )

            # Add jitter to avoid thundering herd
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)

            # Wait before next attempt
            await asyncio.sleep(delay)

            # Exponentially increase delay for next iteration
            delay = delay * exponential_base

    # This should never be reached, but just in case
    raise RetryError(last_exception or Exception("Unknown error"), max_attempts)


def _should_not_retry(error: Exception) -> bool:
    """
    Determine if an error should not be retried.

    Non-retryable errors include:
    - Authentication errors (401, 403)
    - Permission errors (403)
    - Not found errors (404)
    - Validation errors (400, 422)
    - Client errors (4xx)
    - HTTP errors (non-200 status)

    Retryable errors include:
    - Rate limit errors (429)
    - Server errors (5xx)
    - Network errors
    - Timeout errors
    """
    error_str = str(error).lower()

    # Authentication/authorization errors
    if "401" in error_str or "unauthorized" in error_str:
        return True
    if "403" in error_str or "forbidden" in error_str:
        return True

    # Not found
    if "404" in error_str or "not found" in error_str:
        return True

    # Validation errors
    if "400" in error_str or "validation" in error_str.lower():
        return True
    if "422" in error_str:
        return True

    # Client errors (4xx)
    # Note: 429 (rate limit) is an exception that should be retried
    if any(code in error_str for code in ["400", "401", "403", "404", "405", "406", "407", "408", "409", "410", "411", "412", "413", "414", "415", "416", "417", "418", "419", "420", "421", "422", "423", "424", "425", "426", "427", "428", "429"]):
        if code != "429":  # 429 should be retried
            return True

    # Network errors and server errors should be retried
    return False


def is_retryable_http_status(status_code: int) -> bool:
    """
    Check if HTTP status code indicates a retryable error.

    Args:
        status_code: HTTP status code

    Returns:
        True if retryable, False otherwise
    """
    if 500 <= status_code <= 599:
        return True
    if status_code == 429:  # Rate limit
        return True
    return False


async def retry_http_request(
    request_func: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    initial_delay_ms: int = 1000,
    **kwargs: Any,
) -> Any:
    """
    Retry HTTP request with exponential backoff.

    Args:
        request_func: Async function that makes HTTP request
        max_attempts: Maximum number of retry attempts
        initial_delay_ms: Initial delay (milliseconds)
        **kwargs: Keyword arguments to pass to request_func

    Returns:
        HTTP response object

    Raises:
        RetryError: If all attempts are exhausted
        Exception: Any non-transient exception
    """
    last_exception: Optional[Exception] = None
    delay = initial_delay_ms / 1000.0

    for attempt in range(max_attempts):
        try:
            return await request_func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            # Extract HTTP status if available
            status_code = None
            if hasattr(e, "response"):
                response = getattr(e, "response")
                if hasattr(response, "status_code"):
                    status_code = response.status_code

            # Don't retry on non-retryable errors
            if status_code is not None:
                if not is_retryable_http_status(status_code):
                    raise

            # Don't retry on last attempt
            if attempt == max_attempts - 1:
                raise RetryError(e, attempt + 1)

            # Wait before next attempt
            await asyncio.sleep(delay)

            # Exponentially increase delay
            delay = min(delay * 2.0, 32.0)

    raise RetryError(last_exception or Exception("Unknown error"), max_attempts)
