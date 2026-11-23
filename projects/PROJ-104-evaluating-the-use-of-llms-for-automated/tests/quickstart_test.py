"""Smoke‑test verification for the quick‑start command.

The test runs ``python -m code.run_pipeline --sample 5`` and checks that
the deterministic output file ``data/generated/phi3-mini/sample_test.txt``
exists and contains the expected placeholder text.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_quickstart_smoke():
    # Run the pipeline in smoke‑test mode.
    result = subprocess.run(
        [sys.executable, "-m", "code.run_pipeline", "--sample", "5"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Pipeline exited with {result.returncode}: {result.stderr}"
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    assert out_path.is_file(), f"Expected output file {out_path} not found"
    content = out_path.read_text(encoding="utf-8")
    assert "[phi3-mini] Generated documentation based on:" in content
    # Clean up for repeatability
    out_path.unlink()