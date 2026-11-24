"""
src/data/download_real.py

Wrapper module to satisfy the task requirement of running 
'python -m src.data.download_real'. Delegates to the 
actual implementation in src.data.acquire_real.
"""
from src.data.acquire_real import main as acquire_main

def main() -> None:
    """Execute the real data acquisition process."""
    acquire_main()

if __name__ == "__main__":
    main()