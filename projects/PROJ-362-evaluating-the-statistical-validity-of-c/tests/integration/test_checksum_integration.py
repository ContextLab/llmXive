"""
Integration tests for checksum generation workflow.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

import sys
# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from checksums import generate_checksums_manifest, verify_checksums


@pytest.fixture
def project_structure():
    """Create a temporary project structure mimicking the real one."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # Create data/raw directory with sample files
        data_raw = base / "data" / "raw"
        data_raw.mkdir(parents=True)
        
        (data_raw / "qrels.json").write_text('{"query": 1, "doc": 2, "rel": 3}')
        (data_raw / "trec_robust.csv").write_text("qid,doc,score\n1,2,0.5")
        
        # Create results directory with sample files
        results = base / "results"
        results.mkdir()
        (results / "summary.csv").write_text("metric,value\nndcg,0.8")
        
        (results / "null_distributions").mkdir()
        (results / "null_distributions" / "ndcg.csv").write_text("score\n0.1\n0.2")
        
        (results / "p_values").mkdir()
        (results / "p_values" / "raw_p_values.csv").write_text("query_id,p_value\n1,0.03")
        
        yield base
        
        # Cleanup happens automatically via TemporaryDirectory


def test_full_checksum_workflow(project_structure):
    """Test the full checksum generation and verification workflow."""
    data_dir = project_structure / "data"
    results_dir = project_structure / "results"
    manifest_path = data_dir / "checksums_manifest.json"
    
    # Generate checksums
    manifest = generate_checksums_manifest(
        data_dir=data_dir,
        results_dir=results_dir,
        output_path=manifest_path
    )
    
    # Verify all expected files are in manifest
    expected_files = [
        "raw/qrels.json",
        "raw/trec_robust.csv",
        "results/summary.csv",
        "results/null_distributions/ndcg.csv",
        "results/p_values/raw_p_values.csv"
    ]
    
    manifest_paths = [f["path"] for f in manifest["files"]]
    
    for expected in expected_files:
        assert expected in manifest_paths, f"Expected {expected} in manifest"
    
    # Verify checksums
    assert verify_checksums(
        manifest_path=manifest_path,
        data_dir=data_dir,
        results_dir=results_dir
    ) is True
    
    # Verify file sizes are recorded
    for file_entry in manifest["files"]:
        assert "size_bytes" in file_entry
        assert file_entry["size_bytes"] > 0


def test_checksum_verification_fails_on_modification(project_structure):
    """Test that checksum verification fails when a file is modified."""
    data_dir = project_structure / "data"
    results_dir = project_structure / "results"
    manifest_path = data_dir / "checksums_manifest.json"
    
    # Generate checksums
    generate_checksums_manifest(
        data_dir=data_dir,
        results_dir=results_dir,
        output_path=manifest_path
    )
    
    # Modify a file
    (results_dir / "summary.csv").write_text("metric,VALUE\nndcg,0.9")
    
    # Verification should fail
    assert verify_checksums(
        manifest_path=manifest_path,
        data_dir=data_dir,
        results_dir=results_dir
    ) is False


def test_checksum_verification_fails_on_missing_file(project_structure):
    """Test that checksum verification fails when a file is missing."""
    data_dir = project_structure / "data"
    results_dir = project_structure / "results"
    manifest_path = data_dir / "checksums_manifest.json"
    
    # Generate checksums
    generate_checksums_manifest(
        data_dir=data_dir,
        results_dir=results_dir,
        output_path=manifest_path
    )
    
    # Delete a file
    (results_dir / "summary.csv").unlink()
    
    # Verification should fail
    assert verify_checksums(
        manifest_path=manifest_path,
        data_dir=data_dir,
        results_dir=results_dir
    ) is False
