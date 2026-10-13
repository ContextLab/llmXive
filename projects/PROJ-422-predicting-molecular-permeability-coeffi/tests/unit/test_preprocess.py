import os
import pandas as pd
import pytest

from llmxive_toolkit import paths
from code.data.preprocess import MoleculeProcessor

@pytest.fixture
def sample_dataframe():
    """Create a tiny dataframe with a mix of valid/invalid SMILES and targets."""
    data = {
        'SMILES': [
            'CCO',                # valid ethanol
            'C1CC1',              # valid cyclopropane
            'invalid_smiles',     # invalid
            'CC(N)C(=O)O',        # valid alanine
            None                  # missing SMILES
        ],
        'permeability_coefficient': [
            0.85,
            1.10,
            0.95,
            None,   # missing target – should be excluded
            0.70
        ],
        'polymer_type': [
            'A',
            'B',
            'A',
            'B',
            'A'
        ]
    }
    return pd.DataFrame(data)

def test_preprocess_writes_output(sample_dataframe, tmp_path, caplog):
    """
    Verify that MoleculeProcessor.process creates the expected CSV,
    respects the schema, drops invalid rows, and logs warnings.
    """
    processor = MoleculeProcessor()
    processed_df = processor.process(sample_dataframe)

    # Expected number of retained rows:
    # - Row 0 (valid)
    # - Row 1 (valid)
    # - Row 3 is dropped because target is missing
    # - Row 2 invalid SMILES
    # - Row 4 missing SMILES
    assert len(processed_df) == 2

    # Check required columns exist and have correct dtypes
    required_cols = [
        'smiles', 'mol_valid', 'mw', 'logp', 'tpsa',
        'hba', 'hbd', 'rotatable_bonds', 'target',
        'node_features', 'edge_features', 'polymer_type'
    ]
    for col in required_cols:
        assert col in processed_df.columns

    # Verify that the output file was created at the correct location
    output_path = paths.data('processed', 'processed_data.csv')
    assert output_path.is_file()

    # Load the written CSV and compare with the returned DataFrame
    written_df = pd.read_csv(output_path)
    pd.testing.assert_frame_equal(written_df, processed_df, check_dtype=False)

    # Ensure a warning about the missing target was logged
    warnings = [rec.message for rec in caplog.records if rec.levelname == 'WARNING']
    assert any("missing target" in msg for msg in warnings)

def test_retention_check_raises():
    """If retention falls below the threshold, a SystemExit should be raised."""
    # Construct a dataframe where only one out of ten SMILES is valid
    data = {
        'SMILES': ['invalid'] * 9 + ['CCO'],
        'permeability_coefficient': [0.5] * 10
    }
    df = pd.DataFrame(data)

    processor = MoleculeProcessor()
    with pytest.raises(SystemExit):
        processor.process(df)