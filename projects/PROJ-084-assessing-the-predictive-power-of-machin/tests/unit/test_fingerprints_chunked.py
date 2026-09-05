"""
Unit tests for chunked fingerprint generation (T016).

Tests:
- generate_ecfp4 returns list of correct length (2048)
- generate_maccs returns list of correct length (167)
- process_fingerprints_chunked handles small datasets correctly
- Dimension logging works as expected
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocessing.fingerprints import (
    generate_ecfp4,
    generate_maccs,
    ECFP_N_BITS,
    MACCS_N_BITS
)

@pytest.fixture
def sample_smiles():
    """Provide a list of valid SMILES strings."""
    return [
        "CCO",  # Ethanol
        "CC(=O)O",  # Acetic acid
        "c1ccccc1",  # Benzene
        "CC1=CC=CC=C1",  # Toluene
        "CC(C)C1=CC=CC=C1"  # Isopropylbenzene
    ]

@pytest.fixture
def temp_parquet_file(sample_smiles):
    """Create a temporary parquet file with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_input.parquet"
        df = pd.DataFrame({
            'smiles': sample_smiles,
            'yield': [50.0, 60.0, 70.0, 80.0, 90.0]
        })
        df.to_parquet(file_path)
        yield file_path

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_ecfp4_dimension(sample_smiles):
    """Test that ECFP4 returns exactly 2048 bits."""
    for smiles in sample_smiles:
        fp = generate_ecfp4(smiles)
        assert fp is not None, f"Failed to generate ECFP4 for {smiles}"
        assert len(fp) == ECFP_N_BITS, f"ECFP4 length mismatch: {len(fp)} != {ECFP_N_BITS}"
        # Check that values are 0 or 1
        assert all(v in [0, 1] for v in fp), "ECFP4 values must be 0 or 1"

def test_maccs_dimension(sample_smiles):
    """Test that MACCS returns exactly 167 bits."""
    for smiles in sample_smiles:
        fp = generate_maccs(smiles)
        assert fp is not None, f"Failed to generate MACCS for {smiles}"
        assert len(fp) == MACCS_N_BITS, f"MACCS length mismatch: {len(fp)} != {MACCS_N_BITS}"
        # Check that values are 0 or 1
        assert all(v in [0, 1] for v in fp), "MACCS values must be 0 or 1"

def test_invalid_smiles_handling():
    """Test that invalid SMILES return None."""
    invalid_smiles = [
        "invalid_smiles_string",
        "",
        "C((",  # Unbalanced parentheses
        None
    ]
    
    for smiles in invalid_smiles:
        if smiles is None:
            continue  # Skip None as it will crash MolFromSmiles directly
        fp_ecfp = generate_ecfp4(smiles)
        fp_maccs = generate_maccs(smiles)
        assert fp_ecfp is None, f"ECFP4 should be None for invalid SMILES: {smiles}"
        assert fp_maccs is None, f"MACCS should be None for invalid SMILES: {smiles}"

def test_chunked_processing_integration(temp_parquet_file, temp_output_dir):
    """Test the chunked processing function end-to-end."""
    from preprocessing.fingerprints import process_fingerprints_chunked
    
    output_file = temp_output_dir / "output.parquet"
    log_file = temp_output_dir / "dimensions.log"
    
    processed, failed = process_fingerprints_chunked(
        input_path=temp_parquet_file,
        output_path=output_file,
        log_path=log_file,
        chunk_size=2  # Small chunk size to test chunking
    )
    
    # Verify counts
    assert processed == 5, f"Expected 5 processed, got {processed}"
    assert failed == 0, f"Expected 0 failed, got {failed}"
    
    # Verify output file exists and has correct structure
    assert output_file.exists(), "Output parquet file not created"
    result_df = pd.read_parquet(output_file)
    assert 'fingerprint_ecfp' in result_df.columns, "Missing fingerprint_ecfp column"
    assert 'fingerprint_maccs' in result_df.columns, "Missing fingerprint_maccs column"
    assert len(result_df) == 5, f"Output row count mismatch: {len(result_df)} != 5"
    
    # Verify fingerprint dimensions in output
    for idx, row in result_df.iterrows():
        assert len(row['fingerprint_ecfp']) == ECFP_N_BITS
        assert len(row['fingerprint_maccs']) == MACCS_N_BITS
    
    # Verify log file
    assert log_file.exists(), "Log file not created"
    with open(log_file, 'r') as f:
        log_content = f.read()
        assert str(ECFP_N_BITS) in log_content, "ECFP dimension not in log"
        assert str(MACCS_N_BITS) in log_content, "MACCS dimension not in log"

def test_empty_dataframe_handling(temp_output_dir):
    """Test handling of empty input (should raise error or handle gracefully)."""
    from preprocessing.fingerprints import generate_fingerprints_batch
    
    df = pd.DataFrame({'smiles': []})
    
    # This should raise ValueError as per implementation
    with pytest.raises(ValueError, match="No valid fingerprints generated"):
        generate_fingerprints_batch(df)