import os
import socket
import threading
import logging
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class SecurityViolationError(Exception):
    """Exception raised for security violations."""
    pass


class NetworkIsolationContext:
    """Context manager for network isolation."""

    def __init__(self, allowed_hosts: Optional[list] = None):
        """Initialize the context.

        Args:
            allowed_hosts: List of allowed hostnames.
        """
        self.allowed_hosts = allowed_hosts or []
        self.original_socket = socket.socket

    def __enter__(self):
        """Enter the context."""
        def blocked_socket(*args, **kwargs):
            raise SecurityViolationError("Network access is blocked in this context")
        socket.socket = blocked_socket
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        socket.socket = self.original_socket


def ensure_no_network_access(func: Callable) -> Callable:
    """Decorator to ensure a function has no network access.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with NetworkIsolationContext():
            return func(*args, **kwargs)
    return wrapper


def validate_no_external_calls(filepath: str) -> List[str]:
    """Validate that a file has no external network calls.

    Args:
        filepath: Path to the file to check.

    Returns:
        List of violation messages.
    """
    violations = []
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Check for common network call patterns
        dangerous_patterns = [
            "requests.get",
            "requests.post",
            "urllib.request",
            "socket.connect",
            "http.client",
        ]

        for pattern in dangerous_patterns:
            if pattern in content:
                violations.append(f"Potentially dangerous pattern found: {pattern}")

    except Exception as e:
        violations.append(f"Error reading file: {str(e)}")

    return violations


def audit_all_modules(code_dir: str) -> Dict[str, List[str]]:
    """Audit all Python modules in a directory.

    Args:
        code_dir: Directory to audit.

    Returns:
        Dictionary mapping file paths to violation lists.
    """
    results = {}
    code_path = Path(code_dir)

    if not code_path.exists():
        return results

    for file_path in code_path.rglob("*.py"):
        violations = validate_no_external_calls(str(file_path))
        if violations:
            results[str(file_path)] = violations

    return results


def main() -> None:
    """Main entry point for network isolation audit."""
    import argparse

    parser = argparse.ArgumentParser(description="Network Isolation Audit")
    parser.add_argument("--dir", type=str, default="code", help="Directory to audit")

    args = parser.parse_args()

    results = audit_all_modules(args.dir)

    if results:
        print("Security violations found:")
        for filepath, violations in results.items():
            print(f"\n{filepath}:")
            for v in violations:
                print(f"  - {v}")
    else:
        print("No security violations found.")


if __name__ == "__main__":
    main()
