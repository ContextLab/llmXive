import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import tarfile

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.archive_artifacts import (
    find_all_artifacts,
    extract_run_id,
    normalize_filename,
    compute_file_hash,
    create_archive_manifest,
    archive_artifacts
)

@pytest.fixture
def temp_artifact_dir():
    """Create a temporary directory with mock artifacts."""
    temp_dir = tempfile.mkdtemp()
    artifacts_dir = Path(temp_dir) / "artifacts"
    artifacts_dir.mkdir()
    
    # Create mock artifacts with run_id patterns
    run_id = "20231015_120000"
    files = [
        f"embeddings_{run_id}.parquet",
        f"metrics_conditioned_{run_id}.json",
        f"frozen_baseline_aggregated_{run_id}.json",
        f"correlation_report_{run_id}.json",
        "README.md", # Should be included but normalized
        "data_gap_report.json"
    ]
    
    for f in files:
        (artifacts_dir / f).write_text("mock content")
    
    yield artifacts_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_find_all_artifacts(temp_artifact_dir):
    artifacts = find_all_artifacts(temp_artifact_dir)
    # Should find all files except hidden ones
    assert len(artifacts) == 6
    
    # Verify paths are absolute
    for p in artifacts:
        assert p.is_file()
        assert str(p).startswith(str(temp_artifact_dir))

def test_extract_run_id():
    # Test valid patterns
    assert extract_run_id("embeddings_20231015_120000.parquet") == "20231015_120000"
    assert extract_run_id("metrics_conditioned_a1b2c3d4.json") == "a1b2c3d4"
    assert extract_run_id("report_1234567890.csv") == "1234567890"
    
    # Test no run_id
    assert extract_run_id("readme.md") is None
    assert extract_run_id("data.csv") is None

def test_normalize_filename(temp_artifact_dir):
    run_id = "20231015_120000"
    
    # File already has run_id
    p = temp_artifact_dir / "embeddings_20231015_120000.parquet"
    assert normalize_filename(p, run_id) == "embeddings_20231015_120000.parquet"
    
    # File missing run_id
    p = temp_artifact_dir / "README.md"
    assert normalize_filename(p, run_id) == "README_20231015_120000.md"

def test_compute_file_hash(temp_artifact_dir):
    p = temp_artifact_dir / "embeddings_20231015_120000.parquet"
    hash1 = compute_file_hash(p)
    hash2 = compute_file_hash(p)
    
    assert len(hash1) == 64 # SHA256 hex length
    assert hash1 == hash2

def test_create_archive_manifest(temp_artifact_dir):
    artifacts = [
        {"filename": "test.json", "hash": "abc123", "size": 100}
    ]
    output_path = temp_artifact_dir / "manifest.json"
    
    manifest = create_archive_manifest(artifacts, output_path)
    
    assert manifest["total_files"] == 1
    assert manifest["artifacts"][0]["filename"] == "test.json"
    assert output_path.exists()

def test_archive_artifacts(temp_artifact_dir):
    # Run the full archiving process
    archive_path = archive_artifacts(temp_artifact_dir)
    
    assert archive_path.exists()
    assert archive_path.suffix == ".gz"
    
    # Verify archive contents
    with tarfile.open(archive_path, "r:gz") as tar:
        names = tar.getnames()
        assert "artifacts/manifest.json" in names
        # Check that at least one parquet file is present
        parquet_files = [n for n in names if n.endswith(".parquet")]
        assert len(parquet_files) > 0

def test_archive_empty_directory(tmp_path):
    """Test handling of empty artifacts directory."""
    empty_dir = tmp_path / "empty_artifacts"
    empty_dir.mkdir()
    
    # This should log a warning but still create an archive (or handle gracefully)
    # Based on current implementation, it logs warning and returns path
    archive_path = archive_artifacts(empty_dir)
    
    # The function currently returns the path even if empty, but logs warning
    # We just verify it doesn't crash
    assert archive_path is not None