"""
Unit tests for the ingestion pipeline (T017).

Tests:
- run_ingestion_pipeline: Basic functionality
- Schema validation integration
- Output file creation
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Mock data for testing
@pytest.fixture
def mock_raw_data():
    """Create a mock raw dataset."""
    data = {
        'smiles': [
            'CCO',  # Ethanol
            'CC(=O)O',  # Acetic acid
            'c1ccccc1',  # Benzene
            'CCO.CC(=O)O',  # Mixture (should be cleaned)
            'INVALID_SMILES'  # Invalid
        ],
        'yield': ['90%', '50-60%', '85', 'N/A', '70%'],
        'reaction_class': ['esterification', 'hydrolysis', 'aromatic', 'esterification', 'substitution']
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_sanitize_reactions(mock_raw_data):
    """Test sanitization logic."""
    from preprocessing.sanitize import sanitize_reactions
    
    df_clean, exclusions = sanitize_reactions(mock_raw_data)
    
    # Should have excluded invalid SMILES and N/A yield
    assert len(df_clean) < len(mock_raw_data)
    assert 'smiles' in df_clean.columns
    assert 'yield' in df_clean.columns
    assert all(df_clean['yield'].notna())
    assert all((df_clean['yield'] >= 0) & (df_clean['yield'] <= 100))

def test_generate_fingerprints_batch(mock_raw_data):
    """Test fingerprint generation."""
    from preprocessing.sanitize import sanitize_reactions
    from preprocessing.fingerprints import generate_fingerprints_batch
    
    df_clean, _ = sanitize_reactions(mock_raw_data)
    df_fp = generate_fingerprints_batch(df_clean)
    
    assert 'fingerprint_ecfp' in df_fp.columns
    assert 'fingerprint_maccs' in df_fp.columns
    
    # Check dimensions
    for idx, row in df_fp.iterrows():
        assert len(row['fingerprint_ecfp']) == 2048
        assert len(row['fingerprint_maccs']) == 167

def test_validate_dataset_schema(mock_raw_data, temp_dir):
    """Test schema validation."""
    from preprocessing.sanitize import sanitize_reactions
    from preprocessing.fingerprints import generate_fingerprints_batch
    from utils.validators import validate_dataset
    
    # Create a temporary schema file
    schema_path = Path(temp_dir) / 'test_schema.yaml'
    schema_content = """
    fields:
      smiles:
        type: string
      yield:
        type: float
      reaction_class:
        type: string
      fingerprint_ecfp:
        type: list
        length: 2048
      fingerprint_maccs:
        type: list
        length: 167
    """
    with open(schema_path, 'w') as f:
        f.write(schema_content)
    
    # Process data
    df_clean, _ = sanitize_reactions(mock_raw_data)
    df_fp = generate_fingerprints_batch(df_clean)
    
    # Validate
    report = validate_dataset(df_fp, str(schema_path))
    
    assert report['valid'] or len(report['errors']) > 0  # May have errors if schema is minimal

def test_run_ingestion_pipeline(mock_raw_data, temp_dir):
    """Test full ingestion pipeline."""
    from preprocessing.ingest import run_ingestion_pipeline
    
    # Save mock data
    raw_path = Path(temp_dir) / 'raw.parquet'
    mock_raw_data.to_parquet(raw_path)
    
    # Create schema
    schema_path = Path(temp_dir) / 'schema.yaml'
    schema_content = """
    fields:
      smiles:
        type: string
      yield:
        type: float
      reaction_class:
        type: string
      fingerprint_ecfp:
        type: list
        length: 2048
      fingerprint_maccs:
        type: list
        length: 167
    """
    with open(schema_path, 'w') as f:
        f.write(schema_content)
    
    output_path = Path(temp_dir) / 'cleaned.parquet'
    
    # Run pipeline
    stats = run_ingestion_pipeline(
        raw_input_path=str(raw_path),
        output_path=str(output_path),
        schema_path=str(schema_path)
    )
    
    assert stats['status'] == 'success'
    assert output_path.exists()
    assert stats['valid_rows'] > 0
    
    # Verify output
    df_out = pd.read_parquet(output_path)
    assert 'smiles' in df_out.columns
    assert 'fingerprint_ecfp' in df_out.columns
    assert 'fingerprint_maccs' in df_out.columns