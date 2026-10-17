"""Test that the quickstart commands execute without error and produce expected files."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_smoke_test():
    """Run the smoke test and verify the output file exists and is not a placeholder."""
    result = subprocess.run(
        [sys.executable, "-m", "code.run_pipeline", "--sample", "1"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Smoke test failed: {result.stderr}"
    
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    assert out_path.exists(), f"Expected output not found: {out_path}"
    
    content = out_path.read_text(encoding="utf-8")
    assert len(content) > 0, "Output file is empty"
    # Verify it doesn't contain explicit "placeholder" or "synthetic" labels in the generated text
    assert "[Placeholder" not in content, "Output contains placeholder label"
    assert "synthetic output" not in content.lower(), "Output contains synthetic label"