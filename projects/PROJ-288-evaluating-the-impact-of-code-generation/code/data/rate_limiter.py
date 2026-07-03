"""
Rate limiting infrastructure using the Token Bucket algorithm.

Implements exponential backoff logic as per FR-007:
- Initial backoff: 1 second
- Max backoff: 60 seconds
"""
import time
from typing import Optional

from ..config import (
    BACKOFF_INITIAL,
    BACKOFF_MAX,
    RATE_LIMIT_HOURLY,
)


class TokenBucketRateLimiter:
    """
    Token Bucket rate limiter implementation.

    Attributes:
        capacity (int): Maximum tokens the bucket can hold (hourly limit).
        refill_rate (float): Tokens added per second.
        tokens (float): Current number of tokens in the bucket.
        last_refill (float): Timestamp of the last refill operation.
    """

    def __init__(
        self,
        capacity: Optional[int] = None,
        backoff_initial: Optional[float] = None,
        backoff_max: Optional[float] = None,
    ):
        """
        Initialize the rate limiter.

        Args:
            capacity: Max requests allowed per window (defaults to RATE_LIMIT_HOURLY).
            backoff_initial: Initial backoff seconds (defaults to BACKOFF_INITIAL).
            backoff_max: Maximum backoff seconds (defaults to BACKOFF_MAX).
        """
        self.capacity = capacity if capacity is not None else RATE_LIMIT_HOURLY
        self.refill_rate = self.capacity / 3600.0  # Tokens per second
        self.backoff_initial = (
            backoff_initial if backoff_initial is not None else BACKOFF_INITIAL
        )
        self.backoff_max = (
            backoff_max if backoff_max is not None else BACKOFF_MAX
        )

        self.tokens = float(self.capacity)
        self.last_refill = time.time()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity, self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        """
        Attempt to acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire (default 1).

        Returns:
            True if tokens were acquired, False otherwise.
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_for_token(self, tokens: int = 1) -> float:
        """
        Block until tokens are available, using exponential backoff.

        Args:
            tokens: Number of tokens needed.

        Returns:
            Total time waited in seconds.
        """
        total_wait = 0.0
        current_backoff = self.backoff_initial

        while True:
            if self.acquire(tokens):
                return total_wait

            # Calculate wait time based on token deficit
            self._refill()
            needed = tokens - self.tokens
            wait_time = needed / self.refill_rate

            # Apply backoff logic
            sleep_time = min(wait_time, current_backoff)
            time.sleep(sleep_time)
            total_wait += sleep_time

            # Exponential backoff logic
            current_backoff = min(current_backoff * 2, self.backoff_max)

    def get_tokens(self) -> float:
        """Return the current number of tokens available."""
        self._refill()
        return self.tokens

def create_limiter() -> TokenBucketRateLimiter:
    """
    Factory function to create a configured rate limiter.

    Returns:
        A new TokenBucketRateLimiter instance.
    """
    return TokenBucketRateLimiter()