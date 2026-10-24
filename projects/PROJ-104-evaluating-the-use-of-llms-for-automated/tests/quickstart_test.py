"""Quick‑start test.

Ensures that the two public entry points run without error and that the
smoke‑test produces the expected output file.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def _run_cmd(args: list[str]) -> None:
    """Run a command and assert a zero exit status."""
    result = subprocess.run([sys.executable, "-m"] + args, capture_output=True, text=True)
    assert result.returncode == 0, f"Command {' '.join(args)} failed: {result.stdout}\\n{result.stderr}"

def test_smoke_test():
    """Run the Phase‑0 smoke test."""
    _run_cmd(["code.run_pipeline", "--sample", "5"])
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    assert out_path.is_file(), f"Smoke‑test output missing: {out_path}"
    # Basic sanity check – the file should contain the commit message.
    content = out_path.read_text(encoding="utf-8")
    assert "Fix typo" in content

def test_full_pipeline():
    """Run the full pipeline and verify that the commit‑pair CSV is created."""
    _run_cmd(["code.run_pipeline", "--full"])
    csv_path = paths.data("raw", "commit_pairs.csv")
    assert csv_path.is_file(), f"CSV not created: {csv_path}"
    # The CSV must contain at least one row (the exact number is not enforced here).
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert rows, "CSV is empty"