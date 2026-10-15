"""
acquire.py
-------------
Wrapper module that invokes the real dataset download routine.
"""

from code.data.download_real import main as _download_main

def main() -> None:
    """Execute the real CodeXGLUE download routine."""
    _download_main()

if __name__ == "__main__":
    main()
