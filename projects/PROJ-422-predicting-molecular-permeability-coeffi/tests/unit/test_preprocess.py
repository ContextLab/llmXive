import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from llmxive_toolkit import paths
from code.data.preprocess import MoleculeProcessor

@pytest.fixture
def sample_dataframe():
    """Mix of valid/invalid SMILES and missing targets."""
    return pd.DataFrame({
        'SMILES': ['CCO', 'C1CC1', 'invalid', 'CC(N)C(=O)O', None],
        'permeability': [0.85, 1.10, 0.95, None, 0.70],
        'polymer_type': ['A', 'B', 'A', 'B', 'A']
    })

def test_preprocess_writes_output(sample_dataframe):
    """Verify output files are created and schema is correct."""
    # Set threshold to 0 to avoid SystemExit during this test
    processor = MoleculeProcessor(retention_threshold=0.0)
    processed_df = processor.process(sample_dataframe)

    # Expected: CCO (valid), C1CC1 (valid). 
    # 'invalid' is invalid SMILES. 'CC(N)C(=O)O' has no target. None is invalid.
    assert len(processed_df) == 2
    
    required_cols = ['smiles', 'mol_valid', 'mw', 'logp', 'tpsa', 'hba', 'hbd', 'rotatable_bonds', 'target']
    for col in required_cols:
        assert col in processed_df.columns
    
    assert paths.data('processed', 'processed_data.csv').exists()
    assert paths.data('processed', 'processed_data.parquet').exists()
    assert isinstance(processed_df['mol_valid'].iloc[0], (bool, np.bool_))

def test_retention_check_raises():
    """Verify that low retention triggers SystemExit."""
    df = pd.DataFrame({
        'SMILES': ['invalid'] * 9 + ['CCO'],
        'permeability': [0.5] * 10
    })
    # Use default 95% threshold
    processor = MoleculeProcessor(retention_threshold=0.95)
    with pytest.raises(SystemExit):
        processor.process(df)