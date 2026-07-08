"""
Contract test for code/download_data.py.
Verifies that the Zenodo fetch and data validity are correct.
"""
import os
import sys
import hashlib
import tarfile
from pathlib import Path
import pandas as pd

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_data import compute_sha256, download_file, extract_tarball, convert_to_csv, main
from validators.data_validator import validate_full, ValidationError

def test_download_data_exists():
    """Test that the download script runs and produces the expected file."""
    # Run the download script
    import subprocess
    result = subprocess.run(
        [sys.executable, "code/download_data.py"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Download script failed: {result.stderr}"
    
    # Check if the output file exists
    output_file = Path("data/barrier_dataset.csv")
    assert output_file.exists(), "Output CSV file was not created"
    
    # Check if the checksum file exists
    checksum_file = Path("data/checksums.txt")
    assert checksum_file.exists(), "Checksum file was not created"

def test_data_columns():
    """Test that the downloaded data has the required columns."""
    output_file = Path("data/barrier_dataset.csv")
    if not output_file.exists():
        # If file doesn't exist, run the download first
        import subprocess
        subprocess.run([sys.executable, "code/download_data.py"], cwd=Path(__file__).parent.parent)
    
    df = pd.read_csv(output_file)
    
    required_columns = ['SMILES', 'experimental_barrier']
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data types
    assert df['SMILES'].dtype == 'object', "SMILES column should be string"
    assert pd.api.types.is_numeric_dtype(df['experimental_barrier']), "experimental_barrier should be numeric"

def test_data_validity():
    """Test that the data contains valid SMILES and non-NaN barriers."""
    output_file = Path("data/barrier_dataset.csv")
    if not output_file.exists():
        import subprocess
        subprocess.run([sys.executable, "code/download_data.py"], cwd=Path(__file__).parent.parent)
    
    df = pd.read_csv(output_file)
    
    # Check for NaN values in critical columns
    assert not df['SMILES'].isna().any(), "SMILES column contains NaN values"
    assert not df['experimental_barrier'].isna().any(), "experimental_barrier column contains NaN values"
    
    # Check for non-empty SMILES
    assert (df['SMILES'].str.len() > 0).all(), "SMILES column contains empty strings"

def test_checksum_verification():
    """Test that the computed checksum matches the stored one."""
    output_file = Path("data/barrier_dataset.csv")
    checksum_file = Path("data/checksums.txt")
    
    if not output_file.exists():
        import subprocess
        subprocess.run([sys.executable, "code/download_data.py"], cwd=Path(__file__).parent.parent)
    
    assert checksum_file.exists(), "Checksum file should exist after download"
    
    # Read stored checksum
    stored_checksum = None
    with open(checksum_file, 'r') as f:
        for line in f:
            if line.startswith('barrier_dataset.csv:'):
                stored_checksum = line.split(':')[1].strip()
                break
    
    assert stored_checksum is not None, "Could not find checksum for barrier_dataset.csv"
    
    # Compute actual checksum
    actual_checksum = compute_sha256(output_file)
    
    assert actual_checksum == stored_checksum, f"Checksum mismatch: stored={stored_checksum}, actual={actual_checksum}"

def test_validator_integration():
    """Test that the data validator accepts the downloaded data."""
    output_file = Path("data/barrier_dataset.csv")
    if not output_file.exists():
        import subprocess
        subprocess.run([sys.executable, "code/download_data.py"], cwd=Path(__file__).parent.parent)
    
    try:
        validate_full(output_file)
    except ValidationError as e:
        assert False, f"Data validation failed: {e}"