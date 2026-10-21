"""
tests/curators/test_curate_failed_figures.py
------------------------------------------------
Unit tests for the ``src.curators.curate_failed_figures`` script.

The script must:
1. Exit with a non‑zero status and print ``verified source unavailable`` when
   the network is unreachable.
2. When ``--verify-only`` is used, generate exactly ``num`` PNG figures,
   matching JSON ground‑truth files, and a checksum manifest.

These tests exercise both behaviours without performing any real network
requests or downloading external data.
"""

import importlib
import json
import sys

import pytest

# ----------------------------------------------------------------------
# Helper to import the module under test
# ----------------------------------------------------------------------
@pytest.fixture
def curate_module():
    """Import the curation module fresh for each test."""
    # Ensure a clean import (in case of prior monkey‑patches)
    if "src.curators.curate_failed_figures" in sys.modules:
        del sys.modules["src.curators.curate_failed_figures"]
    return importlib.import_module("src.curators.curate_failed_figures")

# ----------------------------------------------------------------------
# Test: network unavailable → script exits with error message
# ----------------------------------------------------------------------
def test_network_unavailable(monkeypatch, capsys, tmp_path, curate_module):
    """
    Simulate a network outage by monkey‑patching ``_check_network`` to
    return ``False``. The script should write the exact error message to
    ``stderr`` and exit with status code 1.
    """
    # Force the network check to fail
    monkeypatch.setattr(curate_module, "_check_network", lambda timeout=5: False)

    # Build CLI arguments (using the original ``--num`` flag)
    test_args = [
        "prog",                     # dummy program name
        "--num", "50",
        "--output-dir", str(tmp_path),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Execute the entry point – it should raise SystemExit
    with pytest.raises(SystemExit) as excinfo:
        curate_module.main()
    # Exit code 1 indicates the expected failure path
    assert excinfo.value.code == 1

    # Verify the error message
    captured = capsys.readouterr()
    assert "verified source unavailable" in captured.err

# ----------------------------------------------------------------------
# Test: ``--verify-only`` produces a deterministic synthetic dataset
# ----------------------------------------------------------------------
def test_verify_only_creates_files(monkeypatch, tmp_path, curate_module):
    """
    Run the script with ``--verify-only``. It must create exactly ``num``
    PNG figures, matching JSON ground‑truth files, and a checksum file.
    """
    test_args = [
        "prog",
        "--verify-only",
        "--num", "50",
        "--output-dir", str(tmp_path),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run the script – this should complete without raising.
    curate_module.main()

    # Expected directories
    figures_dir = tmp_path / "figures"
    gt_dir = tmp_path / "ground_truth"
    checksum_path = tmp_path / "checksums.txt"

    # Verify directories exist
    assert figures_dir.is_dir(), "Figures directory was not created"
    assert gt_dir.is_dir(), "Ground‑truth directory was not created"

    # Verify exact number of files
    fig_files = sorted(figures_dir.glob("figure_*.png"))
    gt_files = sorted(gt_dir.glob("ground_truth_*.json"))
    assert len(fig_files) == 50, f"Expected 50 PNGs, found {len(fig_files)}"
    assert len(gt_files) == 50, f"Expected 50 JSONs, found {len(gt_files)}"

    # Validate JSON structure of each ground‑truth file
    for gt_path in gt_files:
        data = json.loads(gt_path.read_text(encoding="utf-8"))
        assert "vector" in data, f"Missing 'vector' key in {gt_path.name}"
        vector = data["vector"]
        assert isinstance(vector, list) and len(vector) == 3, (
            f"'vector' must be a list of three items in {gt_path.name}"
        )

    # Verify checksum manifest exists and has one line per generated file
    assert checksum_path.is_file(), "Checksum file was not created"
    checksum_lines = [
        line for line in checksum_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    # Two lines per figure (PNG + JSON)
    assert len(checksum_lines) == 100, (
        f"Expected 100 checksum lines (2 per figure), got {len(checksum_lines)}"
    )