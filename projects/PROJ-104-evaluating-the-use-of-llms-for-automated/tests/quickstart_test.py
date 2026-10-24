import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_quickstart_smoke():
    """Run the smoke‑test command and ensure it creates the expected file."""
    cmd = [sys.executable, "-m", "code.run_pipeline", "--sample", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"Smoke test failed: {result.stderr}"
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    assert out_path.is_file(), f"Expected output not found: {out_path}"
    content = out_path.read_text(encoding="utf-8")
    assert "documentation" in content.lower(), "Output does not look like a documentation update"

def test_full_pipeline_runs():
    """Run the full pipeline; it should complete without error and produce the CSV."""
    cmd = [sys.executable, "-m", "code.run_pipeline", "--full"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, f"Full pipeline failed: {result.stderr}"
    csv_path = paths.data("raw", "commit_pairs.csv")
    assert csv_path.is_file(), "commit_pairs.csv missing after full pipeline"
    # Basic sanity check on CSV content
    with csv_path.open("r", encoding="utf-8") as f:
        header = f.readline()
    expected_header = "commit_hash,commit_message,repository_name,doc_diff,timestamp"
    assert header.strip() == expected_header, "CSV header does not match expected schema"