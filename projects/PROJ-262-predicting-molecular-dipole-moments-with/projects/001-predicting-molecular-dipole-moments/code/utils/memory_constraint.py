"""Utility stub for enforcing a memory usage constraint.

The full implementation is out of scope for this task; the script
simply provides a callable that can be imported without error.
"""
import sys
import psutil


def enforce_memory_limit(max_bytes: int = 8 * 1024 ** 3) -> None:
    """Raise an error if the current process exceeds *max_bytes*.

    Args:
        max_bytes: Maximum allowed memory usage (default 8 GiB).
    """
    process = psutil.Process()
    mem = process.memory_info().rss
    if mem > max_bytes:
        raise MemoryError(
            f"Memory usage {mem / (1024 ** 3):.2f} GiB exceeds limit of {max_bytes / (1024 ** 3):.2f} GiB."
        )


if __name__ == "__main__":
    # When executed directly we simply report the current usage.
    print(f"Current memory usage: {psutil.Process().memory_info().rss / (1024 ** 3):.2f} GiB")
