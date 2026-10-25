"""Execute the dataset loader to verify it runs end‑to‑end.

This test is not part of the contract suite; it simply runs the
``code.src.data.load_dataset`` module as a script to ensure that the
declared output files are created without error.  It will be executed
by the CI after the implementation of T001.
"""
import subprocess
import sys
from pathlib import Path

# Run the loader as a module
result = subprocess.run(
    [sys.executable, "-m", "code.src.data.load_dataset"],
    capture_output=True,
    text=True,
    timeout=300,
)
assert result.returncode == 0, f"Loader exited with {result.returncode}: {result.stderr}"
# Verify expected output files exist
for rel in [
    "data/raw/video_metadata.jsonl",
    "data/raw/checksums.json",
    "data/raw/dataset_stats.json",
]:
    assert Path(rel).exists(), f"Expected {rel} to exist"