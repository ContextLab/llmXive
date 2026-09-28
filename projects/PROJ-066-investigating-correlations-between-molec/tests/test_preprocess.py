import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.preprocess import (
    load_schema,
    validate_dataframe_against_schema,
    sanitize_molecules,
    deduplicate_smiles,
    filter_targets,
    sample_dataset,
    calculate_descriptors,
    write_processed_data
)
from code.utils.config import RANDOM_SEED

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        'smiles': [
            'CCO',  # Ethanol
            'CC(=O)O',  # Acetic acid
            'CCO',  # Duplicate
            'invalid_smiles',
            'CC(C)C1=CC=CC=C1C(C)C'  # Valid
        ],
        'experimental_value': [10.5, 20.0, 15.0, 30.0, 25.0],
        'target': ['oral_bioavailability', 'clearance', 'Papp', 'oral_bioavailability', 'clearance'],
        'assay_date': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01']
    })

@pytest.fixture
def sample_df_no_date():
    """Create a sample dataframe without assay_date for deduplication test."""
    return pd.DataFrame({
        'smiles': ['CCO', 'CCO', 'CC(=O)O'],
        'experimental_value': [10.5, 15.0, 20.0],
        'target': ['oral_bioavailability', 'oral_bioavailability', 'clearance']
    })

def test_load_schema():
    """Test loading the schema from the contracts directory."""
    schema = load_schema()
    assert isinstance(schema, dict)
    assert 'properties' in schema
    assert 'required' in schema

def test_validate_dataframe_against_schema(sample_df):
    """Test validation of a dataframe against the schema."""
    # Add required descriptor columns to make it valid
    sample_df['mw'] = [46.07, 60.05, 46.07, 0, 178.23]
    sample_df['logp'] = [-0.31, -0.17, -0.31, 0, 2.5]
    sample_df['tpsa'] = [20.23, 37.3, 20.23, 0, 0]
    sample_df['hbd'] = [1, 1, 1, 0, 0]
    sample_df['hba'] = [1, 2, 1, 0, 0]
    sample_df['rotatable_bonds'] = [0, 0, 0, 0, 1]
    sample_df['ring_count'] = [0, 0, 0, 0, 1]
    
    is_valid, errors = validate_dataframe_against_schema(sample_df, load_schema())
    assert is_valid is True
    assert len(errors) == 0

def test_validate_dataframe_with_errors():
    """Test validation with missing required fields."""
    df = pd.DataFrame({
        'smiles': ['CCO'],
        'experimental_value': [10.5]
    })
    is_valid, errors = validate_dataframe_against_schema(df, load_schema())
    assert is_valid is False
    assert len(errors) > 0

def test_sanitize_molecules(sample_df):
    """Test molecule sanitization."""
    # Remove invalid SMILES
    valid_df = sanitize_molecules(sample_df)
    assert len(valid_df) < len(sample_df)
    assert 'invalid_smiles' not in valid_df['smiles'].values

def test_deduplicate_smiles_with_date(sample_df):
    """Test deduplication with assay_date."""
    deduped_df = deduplicate_smiles(sample_df)
    assert len(deduped_df) < len(sample_df)
    # The duplicate 'CCO' should be kept with the most recent date (2023-03-01)
    cco_row = deduped_df[deduped_df['smiles'] == 'CCO']
    assert len(cco_row) == 1
    assert cco_row.iloc[0]['assay_date'] == '2023-03-01'

def test_deduplicate_smiles_without_date(sample_df_no_date):
    """Test deduplication without assay_date."""
    deduped_df = deduplicate_smiles(sample_df_no_date)
    assert len(deduped_df) < len(sample_df_no_date)
    # Should keep the first occurrence
    cco_rows = deduped_df[deduped_df['smiles'] == 'CCO']
    assert len(cco_rows) == 1

def test_filter_targets(sample_df):
    """Test target filtering."""
    # Filter for a specific target
    filtered_df = filter_targets(sample_df, targets=['clearance'])
    assert len(filtered_df) < len(sample_df)
    assert all(filtered_df['target'] == 'clearance')

def test_filter_targets_missing_values(sample_df):
    """Test filtering removes missing target values."""
    sample_df.loc[0, 'target'] = None
    filtered_df = filter_targets(sample_df)
    assert sample_df.iloc[0].name not in filtered_df.index.values

def test_sample_dataset(sample_df):
    """Test dataset sampling."""
    sampled_df = sample_dataset(sample_df, max_samples=2)
    assert len(sampled_df) == 2
    assert set(sampled_df['smiles']).issubset(set(sample_df['smiles']))

def test_calculate_descriptors(sample_df):
    """Test descriptor calculation."""
    # Remove invalid SMILES first
    valid_df = sanitize_molecules(sample_df)
    desc_df = calculate_descriptors(valid_df)
    
    # Check that descriptor columns are present
    assert 'mw' in desc_df.columns
    assert 'logp' in desc_df.columns
    assert 'tpsa' in desc_df.columns
    assert 'hbd' in desc_df.columns
    assert 'hba' in desc_df.columns
    assert 'rotatable_bonds' in desc_df.columns
    assert 'ring_count' in desc_df.columns
    
    # Check that values are not all None
    assert desc_df['mw'].notna().any()

def test_write_processed_data(sample_df):
    """Test writing processed data to CSV and updating state."""
    # Prepare a valid dataframe
    valid_df = sanitize_molecules(sample_df)
    valid_df = deduplicate_smiles(valid_df)
    valid_df = filter_targets(valid_df)
    valid_df = calculate_descriptors(valid_df)
    
    # Create a temporary output path
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        result_path = write_processed_data(valid_df, output_path)
        
        assert result_path.exists()
        assert result_path == output_path
        
        # Verify CSV content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(valid_df)
        assert 'smiles' in loaded_df.columns
        assert 'mw' in loaded_df.columns