"""
Demo script for the @limit_resources decorator.

This script defines a simple dummy function decorated with @limit_resources.
When run, it will execute the dummy function and the decorator will write
a JSON usage report to ``data/resource_usage.json`` containing the keys
``runtime_seconds`` and ``peak_ram_gb`` as required by task T001.
"""

import time
from resource_monitor import limit_resources

@limit_resources()
def dummy_function():
    """A short‑lived function to trigger resource monitoring."""
    # Simulate a tiny workload
    time.sleep(0.5)
    return "dummy completed"

if __name__ == "__main__":
    # Execute the dummy function; the decorator will handle reporting.
    result = dummy_function()
    print(f"Result: {result}")