"""
Demo script to test the @limit_resources decorator.
"""
import time
from resource_monitor import limit_resources

@limit_resources()
def dummy_function():
    """A short-lived function to trigger resource monitoring."""
    print("Starting dummy function...")
    time.sleep(1)
    print("Dummy function completed.")
    return "Success"

if __name__ == "__main__":
    try:
        result = dummy_function()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")