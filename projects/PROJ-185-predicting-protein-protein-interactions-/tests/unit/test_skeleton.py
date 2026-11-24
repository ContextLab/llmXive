"""Test that the required top‑level directories exist.

The project specification for task T001 requires the presence of the
following empty top‑level directories:

  - src
  - tests
  - data
  - results
  - docs
  - contracts

In practice the directories may contain sub‑modules (e.g., ``src/utils``)
needed for later tasks. This test therefore only checks for existence,
not emptiness.
"""

from pathlib import Path

# List of directories that must exist at the project root.
REQUIRED_DIRS = [
    Path("src"),
    Path("tests"),
    Path("data"),
    Path("results"),
    Path("docs"),
    Path("contracts"),
]

def test_required_directories_exist():
    """Assert that each required top‑level directory is present."""
    missing = [d for d in REQUIRED_DIRS if not d.is_dir()]
    assert not missing, f"Missing required directories: {', '.join(str(m) for m in missing)}"