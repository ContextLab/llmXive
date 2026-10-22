"""
code/data/download.py
---------------------
Wrapper for the data download implementation.
"""
from src.data.download import main as _impl_main

def main() -> None:
    """
    CLI entry point used by `python -m code.data.download`.
    """
    _impl_main()

if __name__ == "__main__":
    main()