"""
Unit tests for verify_metadata.py
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.verify_metadata import (
    fetch_sra_metadata,
    extract_required_metadata,
    verify_metadata_requirements,
    verify_fastq_metadata,
    verify_synthetic_metadata,
    save_verification_report,
    main
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_sra_metadata():
    return {
        "tissue": "leaf",
        "sample_attribute": [
            {"field": "treatment", "value": "herbivore_attack"},
            {"field": "organism", "value": "Arabidopsis thaliana"}
        ],
        "replicates": 3
    }

@pytest.fixture
def sample_fastq_files(temp_dir):
    # Create dummy FASTQ files
    fastq_dir = temp_dir / "raw"
    fastq_dir.mkdir()
    files = []
    for i in range(3):
        file_path = fastq_dir / f"SRX12345{i}.fastq.gz"
        file_path.touch()
        files.append(file_path)
    return files

@pytest.fixture
def sample_manifest(temp_dir):
    manifest_path = temp_dir / "manifest.json"
    data = {
        "entries": [
            {
                "accession_id": "SRX123450",
                "metadata": {
                    "tissue": "leaf",
                    "herbivore_type": "chewing",
                    "replicates": 3
                }
            },
            {
                "accession_id": "SRX123451",
                "metadata": {
                    "tissue": "root",
                    "herbivore_type": "sucking",
                    "replicates": 1
                }
            }
        ]
    }
    with open(manifest_path, 'w') as f:
        json.dump(data, f)
    return manifest_path

def test_extract_required_metadata(sample_sra_metadata):
    """Test extraction of required metadata fields"""
    result = extract_required_metadata(sample_sra_metadata)
    
    assert "tissue" in result
    assert result["tissue"] == "leaf"
    assert "herbivore_type" in result
    assert result["herbivore_type"] == "herbivore_attack"
    assert result["replicates"] == 3

def test_verify_metadata_requirements_valid():
    """Test verification with valid metadata"""
    metadata = {
        "tissue": "leaf",
        "herbivore_type": "chewing",
        "replicates": 3
    }
    is_valid, reasons = verify_metadata_requirements(metadata)
    
    assert is_valid
    assert len(reasons) == 0

def test_verify_metadata_requirements_missing_tissue():
    """Test verification with missing tissue"""
    metadata = {
        "herbivore_type": "chewing",
        "replicates": 3
    }
    is_valid, reasons = verify_metadata_requirements(metadata)
    
    assert not is_valid
    assert any("Missing tissue" in reason for reason in reasons)

def test_verify_metadata_requirements_insufficient_replicates():
    """Test verification with insufficient replicates"""
    metadata = {
        "tissue": "leaf",
        "herbivore_type": "chewing",
        "replicates": 1
    }
    is_valid, reasons = verify_metadata_requirements(metadata)
    
    assert not is_valid
    assert any("Insufficient biological replicates" in reason for reason in reasons)

def test_verify_fastq_metadata_with_manifest(sample_fastq_files, sample_manifest):
    """Test FASTQ metadata verification using manifest"""
    results = verify_fastq_metadata(sample_fastq_files, sample_manifest)
    
    assert len(results) == 3
    # First file should be valid
    assert results[0]["is_valid"]
    # Second file should be invalid (replicates < 2)
    assert not results[1]["is_valid"]
    assert any("Insufficient biological replicates" in reason for reason in results[1]["exclusion_reasons"])

def test_verify_synthetic_metadata(temp_dir):
    """Test synthetic metadata verification"""
    manifest_path = temp_dir / "synthetic_manifest.json"
    data = {
        "file_name": "synthetic_data.json",
        "provenance": {
            "accession_id": "SYNTH_001",
            "generated_at": "2023-01-01T00:00:00"
        }
    }
    with open(manifest_path, 'w') as f:
        json.dump(data, f)
    
    results = verify_synthetic_metadata(manifest_path)
    
    assert len(results) == 1
    assert results[0]["is_valid"]
    assert results[0]["is_synthetic"]
    assert results[0]["metadata"]["tissue"] == "leaf"

def test_save_verification_report(temp_dir):
    """Test saving verification report"""
    results = [
        {
            "file": "test.fastq.gz",
            "accession_id": "SRX123456",
            "metadata": {"tissue": "leaf", "herbivore_type": "chewing"},
            "is_valid": True,
            "exclusion_reasons": []
        }
    ]
    output_path = temp_dir / "report.json"
    
    save_verification_report(results, output_path, mode="real")
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report["mode"] == "real"
    assert report["summary"]["total_studies"] == 1
    assert report["summary"]["valid_studies"] == 1

@patch('src.data.verify_metadata.fetch_sra_metadata')
def test_main_real_mode(mock_fetch, temp_dir, sample_fastq_files, sample_manifest):
    """Test main function in real mode"""
    mock_fetch.return_value = {
        "tissue": "leaf",
        "sample_attribute": [{"field": "treatment", "value": "herbivore"}],
        "replicates": 3
    }
    
    # Create a temporary manifest
    manifest_path = temp_dir / "real_manifest.json"
    data = {
        "entries": [
            {
                "accession_id": "SRX123450",
                "metadata": {
                    "tissue": "leaf",
                    "herbivore_type": "chewing",
                    "replicates": 3
                }
            }
        ]
    }
    with open(manifest_path, 'w') as f:
        json.dump(data, f)
    
    exit_code = main(
        mode="real",
        fastq_dir=str(sample_fastq_files[0].parent),
        manifest_path=str(manifest_path)
    )
    
    assert exit_code == 0

def test_main_synthetic_mode(temp_dir):
    """Test main function in synthetic mode"""
    synthetic_manifest = temp_dir / "synthetic_manifest.json"
    data = {
        "provenance": {"accession_id": "SYNTH_001"}
    }
    with open(synthetic_manifest, 'w') as f:
        json.dump(data, f)
    
    exit_code = main(
        mode="synthetic",
        synthetic_manifest_path=str(synthetic_manifest)
    )
    
    assert exit_code == 0
