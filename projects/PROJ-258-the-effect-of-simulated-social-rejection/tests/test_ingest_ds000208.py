import pandas as pd
import json
from pathlib import Path
from config import get_path

def test_ingest_artifacts_exist():
    """Verify that the required T002 artifacts are present on disk."""
    raw_dir = Path(get_path("raw"))
    
    parquet_file = raw_dir / "ds000208.parquet"
    metadata_file = raw_dir / "metadata_ds000208.json"
    citation_file = raw_dir / "CITATION.md"
    
    assert parquet_file.exists(), "ds000208.parquet is missing"
    assert metadata_file.exists(), "metadata_ds000208.json is missing"
    assert citation_file.exists(), "CITATION.md is missing"

def test_metadata_content():
    """Verify metadata contains expected keys."""
    raw_dir = Path(get_path("raw"))
    metadata_file = raw_dir / "metadata_ds000208.json"
    
    with open(metadata_file, "r") as f:
        meta = json.load(f)
    
    assert meta["dataset_id"] == "ds000208"
    assert "sha256" in meta
    assert "size_bytes" in meta

def test_parquet_task_column():
    """Verify the 'task' column was added to the parquet file."""
    raw_dir = Path(get_path("raw"))
    parquet_file = raw_dir / "ds000208.parquet"
    
    df = pd.read_parquet(parquet_file)
    assert "task" in df.columns, "Column 'task' missing from parquet file"
    assert (df["task"] == "cyberball").all(), "All rows in 'task' column should be 'cyberball'"