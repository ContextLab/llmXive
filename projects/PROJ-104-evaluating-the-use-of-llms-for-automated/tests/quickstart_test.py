"""Tests for the Phase-0 quickstart smoke test (T001)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

from code.run_pipeline import SMOKE_TEST_PAIR, run_smoke_test


def test_smoke_test_writes_output_file():
    out_path = run_smoke_test()
    out_path = Path(out_path)
    assert out_path.exists()
    assert out_path.name == "sample_test.txt"
    assert out_path.parent.name == "phi3-mini"
    assert out_path.stat().st_size > 0


def test_smoke_test_output_mentions_synthetic_pair():
    out_path = Path(run_smoke_test())
    text = out_path.read_text(encoding="utf-8")
    assert SMOKE_TEST_PAIR.commit_hash in text
    assert "plumbing" in text


def test_smoke_test_cli_completes_quickly():
    result = subprocess.run(
        [sys.executable, "-m", "code.run_pipeline", "--sample", "5"],
        cwd=paths.root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "Smoke test OK" in result.stdout
    assert (paths.data("generated", "phi3-mini", "sample_test.txt")).exists()


def test_full_flag_runs_cleanly_while_stages_pending():
    result = subprocess.run(
        [sys.executable, "-m", "code.run_pipeline", "--full"],
        cwd=paths.root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "implemented stages" in result.stdout
    assert "power_analysis" in result.stdout
