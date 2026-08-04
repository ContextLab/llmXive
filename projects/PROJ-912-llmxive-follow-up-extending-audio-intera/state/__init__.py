"""
State package for llmXive.

This package manages state artifacts, checksums, and lineage tracking
for the automated science pipeline.
"""

from pathlib import Path

# Package root directory
PACKAGE_ROOT = Path(__file__).parent.resolve()

def get_state_path(filename: str) -> Path:
    """Get the full path for a state file within the package."""
    return PACKAGE_ROOT / filename

def ensure_state_dir() -> Path:
    """Ensure the state directory exists."""
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)
    return PACKAGE_ROOT

__all__ = [
    "PACKAGE_ROOT",
    "get_state_path",
    "ensure_state_dir",
]