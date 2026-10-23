import os
from pathlib import Path
import pytest

# Add project root to sys.path for imports if needed
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

def test_directories_and_readmes():
    """
    Verify that the skeleton setup script creates the required directories
    and that each of the top‑level data directories contains a README.txt.
    """
    # Paths relative to the project root
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    outputs_dir = Path("outputs")

    # Directories must exist
    assert raw_dir.is_dir(), f"{raw_dir} does not exist"
    assert processed_dir.is_dir(), f"{processed_dir} does not exist"
    assert outputs_dir.is_dir(), f"{outputs_dir} does not exist"

    # README.txt must exist in each and contain the expected marker string
    for d in [raw_dir, processed_dir, outputs_dir]:
        readme = d / "README.txt"
        assert readme.is_file(), f"README.txt missing in {d}"
        content = readme.read_text()
        assert "created by setup_skeleton" in content, f"Unexpected README content in {d}"