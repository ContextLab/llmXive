"""
acquire_real.py
----------------
Wrapper that invokes the real TIDE data acquisition routine.
"""

from code.data.download_real import main as _download_main

def main() -> None:
    """Run the real TIDE data acquisition process."""
    _download_main()

if __name__ == "__main__":
    main()
