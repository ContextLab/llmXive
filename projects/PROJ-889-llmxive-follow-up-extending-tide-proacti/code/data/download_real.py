"""
download_real.py
-----------------
Wrapper script that delegates to the updated real data acquisition routine.
"""

from src.data.acquire_real import main as acquire_real_main

def main() -> None:
    """Execute the real data acquisition process via src.data.acquire_real."""
    acquire_real_main()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import sys
        sys.exit(1)