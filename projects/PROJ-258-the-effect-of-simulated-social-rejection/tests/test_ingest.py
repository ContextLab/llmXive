"""
Unit tests for the T002 ingestion script.

The tests verify that:
  * The script exits with code 0 on a successful download.
  * The parquet file contains a ``task`` column with the expected value.
  * The metadata JSON includes a SHA‑256 checksum.
  * The citation file exists and contains the OpenNeuro citation.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# The URL used in the quick‑start is a small verified parquet file.
# It is publicly reachable; the test will download it for real.
TEST_URL = "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet"

@pytest.fixture(scope="module")
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

def run_ingest(temp_dir: Path):
    """Helper to invoke the ingestion script."""
    cmd = [
        sys.executable,
        "code/ingest.py",
        "--dataset-url",
        TEST_URL,
        "--output-dir",
        str(temp_dir),
        "--dataset-id",
        "ds000208",
    ]
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parents[1],  # project root
        capture_output=True,
        text=True,
    )
    return result

def test_ingest_success(temp_dir):
    result = run_ingest(temp_dir)
    assert result.returncode == 0, f"stderr: {result.stderr}"

    # Check parquet exists
    parquet_path = temp_dir / "ds000208.parquet"
    assert parquet_path.is_file()

    # Verify ``task`` column
    df = pd.read_parquet(parquet_path)
    assert "task" in df.columns
    assert set(df["task"].unique()) == {"cyberball"}

    # Check metadata JSON
    meta_path = temp_dir / "metadata_ds000208.json"
    assert meta_path.is_file()
    meta = json.loads(meta_path.read_text())
    assert meta["dataset_id"] == "ds000208"
    assert "sha256" in meta
    assert len(meta["sha256"]) == 64  # SHA‑256 length

    # Check citation
    citation_path = temp_dir / "CITATION.md"
    assert citation_path.is_file()
    content = citation_path.read_text()
    assert "OpenNeuro" in content and "ds000208" in content

# The following test ensures that the size guard works.  We cannot
# realistically download a >7 GB file in CI, so we simulate the guard
# by monkey‑patching ``requests.head`` to return an exaggerated size.
def test_size_guard(monkeypatch, temp_dir):
    class DummyResponse:
        headers = {"Content-Length": str(8 * 1024 ** 3)}  # 8 GB
        def raise_for_status(self): pass

    monkeypatch.setattr("requests.head", lambda *args, **kwargs: DummyResponse())
    result = run_ingest(temp_dir)
    assert result.returncode == 1
    assert "exceeds RAM limit" in result.stderr.lower()