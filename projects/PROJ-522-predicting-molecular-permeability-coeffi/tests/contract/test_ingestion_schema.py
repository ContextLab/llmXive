import pytest
import pandas as pd
from pathlib import Path

def test_ingestion_output_schema():
    """Validate that the output files have the expected schema."""
    # This test assumes the ingestion script has run and created files.
    # It validates the schema of the parquet files.
    raw_dir = Path("data/raw")
    
    if not raw_dir.exists():
        pytest.skip("Data directory not found. Run ingestion first.")

    for source in ['nist', 'pubchem', 'mtr']:
        file_path = raw_dir / f"{source}.parquet"
        if not file_path.exists():
            pytest.skip(f"{source}.parquet not found. Run ingestion first.")
        
        df = pd.read_parquet(file_path)
        
        # Check required columns
        assert 'smiles' in df.columns, f"Missing 'smiles' column in {source}"
        assert 'target' in df.columns, f"Missing 'target' column in {source}"
        assert 'source' in df.columns, f"Missing 'source' column in {source}"
        
        # Check for nulls in critical columns
        assert not df['smiles'].isnull().any(), f"Null smiles in {source}"
        assert not df['target'].isnull().any(), f"Null target in {source}"