"""
Thin wrapper module providing the public API expected by the test suite.
It forwards calls to the implementation in ``code.setup_directories`` but
adapts the return values to match the unit‑test expectations.
"""

from pathlib import Path
from typing import Optional

# Import the actual implementation
from code.setup_directories import ensure_directories as _ensure_directories
from code.setup_directories import validate_paths as _validate_paths

def ensure_directories(root_dir: Optional[Path] = None) -> bool:
    """
    Create the required project directories and return ``True`` on success.
    
    The underlying implementation returns a list of created paths; the
    test suite expects a boolean, so we discard the list and return ``True``.
    """
    _ensure_directories(root_dir)
    return True

def validate_paths(root_dir: Optional[Path] = None) -> bool:
    """
    Validate that all required directories exist.
    """
    return _validate_paths(root_dir)

def main() -> int:
    """
    Simple CLI entry point used by developers; returns ``0`` on success.
    """
    if ensure_directories():
        return 0
    return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
