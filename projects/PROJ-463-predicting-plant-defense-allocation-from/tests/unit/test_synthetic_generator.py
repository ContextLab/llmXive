"""
Unit tests for the synthetic generator module (T015).
"""
import pytest
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from src.data.synthetic_generator import (
    generate_synthetic_tpm_matrix,
    calculate_manifest_entry,
    save_synthetic_manifest,
    generate_synthetic_tpm_study
)
from src.utils.config import reset_config, set_seed

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_config(temp_dir):
    """Mock the configuration to use temp directories."""
    reset_config()
    # We assume the config is set up via environment or default logic, 
    # but for this test we ensure paths exist.
    # In a real scenario, we might patch get_config()
    return temp_dir

def test_generate_synthetic_tpm_matrix_structure():
    """Test that the generated matrix has the correct dimensions and types."""
    n_genes = 100
    n_samples = 10
    
    df = generate_synthetic_tpm_matrix(n_genes=n_genes, n_samples=n_samples, seed=42)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == n_genes
    assert len(df.columns) == n_samples
    
    # Check index and column names
    assert df.index.name is None  # Or whatever is expected
    # Check that values are numeric
    assert df.apply(pd.to_numeric, errors='raise').notna().all().all()
    
    # Check for non-negativity
    assert (df >= 0).all().all()

def test_generate_synthetic_tpm_matrix_housekeeping_genes():
    """Test that housekeeping genes have lower variance than random genes."""
    n_genes = 200
    n_samples = 20
    
    df = generate_synthetic_tpm_matrix(n_genes=n_genes, n_samples=n_samples, seed=42)
    
    # Calculate variance for all genes
    variances = df.var(axis=1)
    
    # Housekeeping genes are the first N genes (based on config length)
    # We can't easily check specific names without mocking config, 
    # but we can check the distribution of the first few vs last few
    # Assuming the generator puts HK genes first
    hk_variances = variances.iloc[:10] # Assume at least 10 HK genes
    random_variances = variances.iloc[-10:]
    
    # HK genes should generally have lower variance
    assert hk_variances.mean() < random_variances.mean(), \
        "Housekeeping genes should have lower variance than random genes"

def test_calculate_manifest_entry(temp_dir):
    """Test checksum calculation and manifest entry creation."""
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")
    
    entry = calculate_manifest_entry(str(test_file))
    
    assert "file_name" in entry
    assert entry["file_name"] == "test.txt"
    assert "checksum" in entry
    assert len(entry["checksum"]) == 64 # SHA256 hex length
    assert entry["source_type"] == "synthetic"
    assert "provenance" in entry
    assert "generated_at" in entry["provenance"]
    assert "tool_versions" in entry["provenance"]

def test_save_synthetic_manifest(temp_dir):
    """Test saving manifest to JSON."""
    manifest_path = Path(temp_dir) / "manifest.json"
    entries = [
        {"file_name": "a.csv", "checksum": "abc123", "source_type": "synthetic", "provenance": {}},
        {"file_name": "b.csv", "checksum": "def456", "source_type": "synthetic", "provenance": {}}
    ]
    
    save_synthetic_manifest(entries, str(manifest_path))
    
    assert manifest_path.exists()
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    assert "entries" in data
    assert len(data["entries"]) == 2

def test_generate_synthetic_tpm_study_full_pipeline(temp_dir):
    """Test the full pipeline of generating study, matrix, metadata, and manifest."""
    # Patch the config paths to use temp_dir
    # Since we can't easily mock the global CONFIG in the module without more setup,
    # we pass output_dir directly.
    
    results = generate_synthetic_tpm_study(
        output_dir=temp_dir,
        n_genes=50,
        n_samples=5
    )
    
    assert "matrix" in results
    assert "metadata" in results
    assert "manifest" in results
    
    assert Path(results["matrix"]).exists()
    assert Path(results["metadata"]).exists()
    assert Path(results["manifest"]).exists()
    
    # Verify matrix content
    df = pd.read_csv(results["matrix"], index_col=0)
    assert len(df) == 50
    assert len(df.columns) == 5
    
    # Verify manifest content
    with open(results["manifest"], 'r') as f:
        manifest = json.load(f)
    assert "entries" in manifest
    # Should have at least matrix and metadata
    assert len(manifest["entries"]) >= 2
    
    # Verify checksums in manifest match files
    for entry in manifest["entries"]:
        file_path = Path(temp_dir) / entry["file_name"]
        if file_path.exists():
            # Recalculate and compare (basic check)
            from src.data.synthetic_generator import calculate_manifest_entry
            new_entry = calculate_manifest_entry(str(file_path))
            assert new_entry["checksum"] == entry["checksum"]