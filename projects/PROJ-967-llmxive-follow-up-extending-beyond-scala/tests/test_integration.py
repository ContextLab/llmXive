"""
Integration tests for the pipeline.
"""
import os
import tempfile
from pathlib import Path

import pytest

# Import modules
from ingest import setup_directories, validate_schema
from features import calculate_per_sample_stats


def test_end_to_end_setup(tmp_path):
    """Test that the basic directory setup and schema validation work together."""
    # Setup directories
    setup_directories(tmp_path)

    # Create a mock CSV
    csv_path = tmp_path / "data" / "raw" / "test.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("sample_id,alignment,realism,aesthetics,plausibility,human_score\n1,0.5,0.6,0.7,0.8,0.9\n")

    # Validate schema
    assert validate_schema(str(csv_path)) is True

    # Verify file exists
    assert csv_path.exists()
