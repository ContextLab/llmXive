"""
Custom exception classes for the llmXive simulation pipeline.
"""
from typing import Dict, Optional


class SimulationError(Exception):
    """Base exception for simulation-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        base = super().__str__()
        if self.details:
            return f"{base} | Details: {self.details}"
        return base


class MemoryLimitExceeded(SimulationError):
    """Raised when the simulation exceeds the configured memory limit."""

    def __init__(
        self,
        current_usage: int,
        limit: int,
        message: Optional[str] = None,
    ):
        msg = message or (
            f"Memory limit exceeded. Current: {current_usage:,} bytes, "
            f"Limit: {limit:,} bytes."
        )
        super().__init__(
            msg,
            {
                "current_usage": current_usage,
                "limit": limit,
                "excess": current_usage - limit,
            },
        )
        self.current_usage = current_usage
        self.limit = limit