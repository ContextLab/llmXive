"""
Global Attempt Counter Logic for the Self-Improving LLM Pipeline.

This module implements the logic to track and enforce the global attempt limit
as defined in the project specification (FR-007: 3-attempt hard stop).
"""

class AttemptLimitExceeded(Exception):
    """
    Exception raised when the number of attempts exceeds the maximum allowed.

    This enforces the hard stop condition for the recursive refinement cycle.
    """
    def __init__(self, current_attempt: int, max_attempts: int):
        self.current_attempt = current_attempt
        self.max_attempts = max_attempts
        message = (
            f"Attempt limit exceeded: Current attempt {current_attempt} >= "
            f"Maximum allowed {max_attempts}. Terminating cycle."
        )
        super().__init__(message)


def check_attempt_limit(current_attempt: int, max_attempts: int = 3) -> None:
    """
    Check if the current attempt count has reached or exceeded the limit.

    Args:
        current_attempt (int): The current attempt number (1-indexed).
        max_attempts (int): The maximum allowed attempts (default 3).

    Raises:
        AttemptLimitExceeded: If current_attempt >= max_attempts.
    """
    if current_attempt >= max_attempts:
        raise AttemptLimitExceeded(current_attempt, max_attempts)


def get_attempt_message(current_attempt: int, max_attempts: int = 3) -> str:
    """
    Generate a status message regarding the current attempt count.

    Args:
        current_attempt (int): The current attempt number.
        max_attempts (int): The maximum allowed attempts.

    Returns:
        str: A human-readable status string.
    """
    if current_attempt >= max_attempts:
        return f"Attempt limit reached ({current_attempt}/{max_attempts}). Terminating."
    elif current_attempt == max_attempts - 1:
        return f"Final attempt allowed ({current_attempt}/{max_attempts})."
    else:
        return f"Attempt {current_attempt}/{max_attempts}."
