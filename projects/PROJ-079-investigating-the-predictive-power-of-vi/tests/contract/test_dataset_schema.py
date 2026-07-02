import pytest
import pandas as pd
from pathlib import Path

# FR-004 Required columns as defined in spec.md
# Expected columns: strain_accession, isg_score, and viral sequence features
# Note: host_codon_bias is included as per T021/T018c requirements for merged dataset
REQUIRED_COLUMNS = {
    'strain_accession',
    'isg_score',
    'gc_content',
    'gc_content_3_region',
    'cai',
    'kmer_3_freq',
    'kmer_4_freq',
    'repeat_density',
    'stability_score',
    'host_codon_bias'
}

def test_schema_validates(merged_df: pd.DataFrame) -> None:
    """
    Contract test: Verify merged dataset schema matches spec.md FR-004.
    
    Args:
        merged_df: The merged dataset DataFrame produced by the pipeline.
    
    Raises:
        AssertionError: If required columns are missing or extra unexpected columns exist.
    """
    assert isinstance(merged_df, pd.DataFrame), "Input must be a pandas DataFrame"
    assert not merged_df.empty, "Input DataFrame cannot be empty"
    
    actual_columns = set(merged_df.columns)
    
    # Check for required columns
    missing_columns = REQUIRED_COLUMNS - actual_columns
    assert not missing_columns, (
        f"Missing required columns per FR-004: {missing_columns}. "
        f"Available columns: {actual_columns}"
    )
    
    # Log available columns for debugging
    print(f"Dataset schema validated. Found columns: {sorted(actual_columns)}")

# Optional: Test fixture to generate a valid mock dataset for local development
# This is not part of the contract but helps developers run tests without full pipeline
@pytest.fixture
def sample_merged_df():
    """Generate a sample DataFrame matching the expected schema."""
    data = {
        'strain_accession': ['NC_000001', 'NC_000002', 'NC_000003'],
        'isg_score': [0.5, 0.7, 0.3],
        'gc_content': [0.45, 0.55, 0.60],
        'gc_content_3_region': [0.44, 0.56, 0.59],
        'cai': [0.75, 0.82, 0.68],
        'kmer_3_freq': [0.12, 0.15, 0.11],
        'kmer_4_freq': [0.08, 0.09, 0.07],
        'repeat_density': [0.02, 0.01, 0.03],
        'stability_score': [0.65, 0.72, 0.58],
        'host_codon_bias': [0.4, 0.5, 0.35]
    }
    return pd.DataFrame(data)