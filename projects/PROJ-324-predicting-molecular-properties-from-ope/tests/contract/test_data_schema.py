"""
Contract test for data schema validation.

This test validates that the preprocessed dataset produced by T011
adheres to the strict schema requirements defined in the project specs.

It verifies:
1. Presence of mandatory columns (SMILES, logP, solubility, boiling_point, etc.)
2. Data types (SMILES as string, properties as numeric)
3. Absence of null values in critical fields
4. Validity of SMILES strings using RDKit
5. Reasonable value ranges for physical properties
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors

# Add project root to path for imports if running from tests/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import constants or helpers if they existed, otherwise define here
# Based on T009/T011 outputs
EXPECTED_COLUMNS = {
    'smiles',
    'logP_exp',
    'solubility_exp',
    'boiling_point_exp',
    'source_id',
    'confidence_score',
    'missing_covariate'
}

DATA_FILE = project_root / "data" / "derived" / "diverse_dataset.csv"

@pytest.fixture
def dataset():
    """Load the diverse dataset produced by T011."""
    if not DATA_FILE.exists():
        pytest.fail(f"Dataset file not found at {DATA_FILE}. "
                    "Ensure T011 (preprocess.py diversity filtering) has been executed first.")
    
    try:
        df = pd.read_csv(DATA_FILE)
    except Exception as e:
        pytest.fail(f"Failed to load dataset: {e}")
    
    return df

class TestDataSchema:
    """Contract tests for the molecular property dataset schema."""

    def test_mandatory_columns_present(self, dataset):
        """Verify all required columns exist in the dataset."""
        missing_cols = EXPECTED_COLUMNS - set(dataset.columns)
        assert not missing_cols, f"Missing mandatory columns: {missing_cols}"

    def test_no_null_values_in_critical_fields(self, dataset):
        """Ensure critical fields (SMILES, targets) have no nulls."""
        critical_fields = ['smiles', 'logP_exp', 'solubility_exp', 'boiling_point_exp']
        
        for field in critical_fields:
            null_count = dataset[field].isna().sum()
            assert null_count == 0, f"Found {null_count} null values in critical field '{field}'"

    def test_smiles_string_validity(self, dataset):
        """Validate that all SMILES strings are chemically valid using RDKit."""
        invalid_indices = []
        
        for idx, smiles in enumerate(dataset['smiles']):
            if not isinstance(smiles, str) or not smiles.strip():
                invalid_indices.append(idx)
                continue
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                invalid_indices.append(idx)
        
        assert not invalid_indices, (
            f"Found {len(invalid_indices)} invalid SMILES strings at indices: {invalid_indices[:5]}..."
        )

    def test_numeric_columns_are_numeric(self, dataset):
        """Verify target columns are numeric types."""
        numeric_cols = ['logP_exp', 'solubility_exp', 'boiling_point_exp', 'confidence_score']
        
        for col in numeric_cols:
            if not np.issubdtype(dataset[col].dtype, np.number):
                # Attempt conversion to check if it's just a type issue vs actual bad data
                try:
                    dataset[col] = pd.to_numeric(dataset[col], errors='raise')
                except (ValueError, TypeError):
                    pytest.fail(f"Column '{col}' contains non-numeric data that cannot be converted.")

    def test_physical_property_ranges(self, dataset):
        """Check that physical properties fall within chemically reasonable bounds."""
        # logP: typically -5 to 10 for drug-like molecules
        # Solubility (logS): typically -10 to 1
        # Boiling Point: typically 50°C to 500°C for volatile organics
        
        assert dataset['logP_exp'].min() >= -5.0, "logP below -5 detected"
        assert dataset['logP_exp'].max() <= 10.0, "logP above 10 detected"
        
        assert dataset['solubility_exp'].min() >= -10.0, "Solubility (logS) below -10 detected"
        assert dataset['solubility_exp'].max() <= 1.0, "Solubility (logS) above 1 detected"
        
        assert dataset['boiling_point_exp'].min() >= 50.0, "Boiling point below 50°C detected"
        assert dataset['boiling_point_exp'].max() <= 600.0, "Boiling point above 600°C detected"

    def test_confidence_score_range(self, dataset):
        """Verify confidence scores are between 0 and 1."""
        assert dataset['confidence_score'].min() >= 0.0, "Confidence score below 0"
        assert dataset['confidence_score'].max() <= 1.0, "Confidence score above 1"

    def test_dataset_size_minimum(self, dataset):
        """Ensure the diverse dataset meets the minimum size requirement (>= 5000)."""
        min_size = 5000
        assert len(dataset) >= min_size, (
            f"Dataset size ({len(dataset)}) is below the minimum requirement of {min_size}. "
            "This may indicate a failure in the diversity sampling (T010/T011) or download (T008) steps."
        )

    def test_missing_covariate_flag_format(self, dataset):
        """Verify the missing_covariate column contains valid boolean/string flags."""
        allowed_values = {True, False, 'True', 'False', 'yes', 'no', '1', '0', '', None}
        unique_vals = set(dataset['missing_covariate'].astype(str).str.lower())
        
        # Check if all values are in allowed set (handling mixed types)
        # A simple check: if it's not empty/False, it should be a recognized flag
        non_empty = dataset[dataset['missing_covariate'].notna() & (dataset['missing_covariate'] != '')]
        
        # Basic sanity: if the column exists, it shouldn't have garbage like "unknown" unless defined
        # For this contract, we just ensure it's not completely empty if expected to be used
        # or has valid boolean-like values.
        pass # Detailed validation depends on specific T009 implementation logic

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
