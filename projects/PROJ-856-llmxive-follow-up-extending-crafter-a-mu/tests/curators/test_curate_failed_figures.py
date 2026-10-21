"""
Tests for the curate_failed_figures script.

The tests verify two required behaviours:

1. When the network is reported as unavailable, the script exits with
   a non‑zero status and prints the exact message
   “verified source unavailable”.

2. When ``--verify-only`` is used, the script creates exactly the
   requested number of PNG and JSON files together with a checksum
   manifest.
"""

import sys
import os
import json
from pathlib import Path

import pytest

# Import the module under test.
from src.curators import curate_failed_figures as cff

def test_network_unavailable(monkeypatch, capsys):
    """
    Simulate a network outage by forcing the network check to return False.
    The script should exit with code 1 and emit the required message.
    """
    # Force the network check to report failure.
    monkeypatch.setattr(cff, "_check_network", lambda timeout=5: False)

    # Prepare argv as the CLI would see it.
    test_args = ["curate_failed_figures", "--num", "10"]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as excinfo:
        cff.main()

    # Exit code must be non‑zero (spec says non‑zero, we use 1).
    assert excinfo.value.code == 1

    # The exact error message must be on stderr.
    captured = capsys.readouterr()
    assert "verified source unavailable" in captured.err

def test_verify_only_creates_correct_files(tmp_path, monkeypatch):
    """
    Verify that ``--verify-only`` produces the exact number of PNG/JSON
    files and a checksum manifest.
    """
    # Monkey‑patch the output directory to a temporary location.
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    # Build arguments for the synthetic path.
    test_args = [
        "curate_failed_figures",
        "--verify-only",
        "--num-tasks",
        "7",
        "--output-dir",
        str(out_dir),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run the script – it should not raise.
    cff.main()

    # Expected directories.
    figures_dir = out_dir / "figures"
    gt_dir = out_dir / "ground_truth"
    checksum_file = out_dir / "checksums.txt"

    # Verify directories exist.
    assert figures_dir.is_dir()
    assert gt_dir.is_dir()
    assert checksum_file.is_file()

    # Verify exact number of files.
    png_files = sorted(figures_dir.glob("figure_*.png"))
    json_files = sorted(gt_dir.glob("ground_truth_*.json"))
    assert len(png_files) == 7
    assert len(json_files) == 7

    # Verify each JSON contains a ``vector`` field with three integers.
    for jf in json_files:
        with jf.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert "vector" in data
        assert isinstance(data["vector"], list)
        assert len(data["vector"]) == 3
        assert all(isinstance(v, int) for v in data["vector"])

    # Verify checksum file has 2 * N lines.
    lines = checksum_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 14  # 7 PNG + 7 JSON
