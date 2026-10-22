"""
code/data/validate.py
---------------------

CLI wrapper that delegates to the implementation in ``src.data.validate``.
This module exists so that users can run the validation step via
``python -m code.data.validate`` while the core logic lives in the
``src`` package.
"""

from src.data.validate import main as _impl_main

def main() -> None:
    """Execute the validation script."""
    _impl_main()

if __name__ == "__main__":
    main()