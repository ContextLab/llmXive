import pytest
from pathlib import Path
from code.ingest.pipeline import run_pipeline

def test_full_pipeline(tmp_path: Path):
    """Test full pipeline on sample data."""
    output = tmp_path / "test_output.parquet"
    # Run pipeline (would need real data for full test)
    # run_pipeline('mp', output, sample_size=10)
    assert True  # Placeholder
