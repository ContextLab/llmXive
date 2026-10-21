"""
Unit tests for the curate_failed_figures script.

The tests verify that:
1. The script accepts the ``--verify-only`` flag and creates the expected
   number of PNG and JSON files together with a checksum manifest.
2. When the real data source is unavailable (simulated by monkey‑patching
   ``CIFAR10`` to raise an exception), the script exits with the required
   message and a non‑zero status.
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = "src.curators.curate_failed_figures"

@pytest.fixture
def clean_data_dir(tmp_path):
    """Create a temporary data directory for each test."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir
    # Cleanup is automatic with the temporary directory.

def run_script(args, data_dir):
    """Helper to invoke the module via ``python -m``."""
    cmd = [sys.executable, "-m", SCRIPT] + args + ["--output-dir", str(data_dir)]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result

def test_verify_only_creates_files(clean_data_dir):
    """``--verify-only`` should produce 50 PNGs, 50 JSONs and a checksum file."""
    result = run_script(["--verify-only", "--num", "50"], clean_data_dir)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    figures = list((clean_data_dir / "figures").glob("figure_*.png"))
    ground = list((clean_data_dir / "ground_truth").glob("ground_truth_*.json"))
    assert len(figures) == 50
    assert len(ground) == 50
    checksum_file = clean_data_dir / "checksums.txt"
    assert checksum_file.is_file()
    # Basic sanity check: each line should contain a checksum and a filename.
    lines = checksum_file.read_text().strip().splitlines()
    assert len(lines) == 100  # 2 lines per figure (PNG + JSON)

def test_real_source_unavailable(monkeypatch, clean_data_dir):
    """If CIFAR‑10 cannot be downloaded, the script must exit with the expected message."""
    def broken_cifar10(*args, **kwargs):
        raise RuntimeError("Network unreachable")
    monkeypatch.setattr("torchvision.datasets.CIFAR10", broken_cifar10)
    result = run_script([], clean_data_dir)
    assert result.returncode != 0
    assert "verified source unavailable" in result.stderr.lower()