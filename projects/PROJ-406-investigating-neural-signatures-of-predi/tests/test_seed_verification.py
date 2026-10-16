"""
Tests for the global seed utility and verification script.

The test ensures that:
1. The seed can be set via ``set_global_seed``.
2. Two consecutive draws after resetting the seed are identical.
3. The verification script creates the expected log file with two identical lines.
"""

import os
import numpy as np
from pathlib import Path

from src.utils.seed import set_global_seed, DEFAULT_SEED
from src.utils import seed_verification

def test_deterministic_draws(tmp_path: Path):
    # Ensure a clean environment for the test
    set_global_seed(DEFAULT_SEED)
    first = np.random.rand()
    set_global_seed(DEFAULT_SEED)
    second = np.random.rand()
    assert first == second, "Two draws with the same seed should be identical"

def test_seed_verification_script_creates_log(tmp_path: Path, monkeypatch):
    # Redirect the outputs directory to a temporary location
    from llmxive_toolkit import paths

    # Monkey‑patch the internal base directory used by paths.outputs
    # so that it writes into the temporary directory instead of the real project folder.
    original_root = paths.root
    try:
        # Set the root to the temporary path
        monkeypatch.setattr(paths, "root", tmp_path, raising=False)
        # Run the verification script
        seed_verification.main()
        # Locate the generated log file
        log_file = tmp_path / "outputs" / "seed_verification.log"
        assert log_file.is_file(), "Log file was not created"

        # Read the two lines and ensure they are identical
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 2, "Log should contain exactly two lines"
        assert lines[0] == lines[1], "The two logged random draws must be identical"
    finally:
        # Restore the original root path to avoid side effects
        monkeypatch.setattr(paths, "root", original_root, raising=False)