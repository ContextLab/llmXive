import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.eval.conformer_stability import (
    load_subset_for_pilot,
    generate_multiple_conformers_and_sasa,
    run_stability_check
)
from code.config import RANDOM_SEED

def test_load_subset_for_pilot(tmp_path):
    """Test loading a subset from a parquet file."""
    # Create a dummy parquet file
    import pandas as pd
    df = pd.DataFrame({
        'smiles': ['CCO', 'CCN', 'invalid', 'CCCC'],
        'surface_area': [10.0, 20.0, 30.0, 40.0]
    })
    input_path = tmp_path / "test.parquet"
    df.to_parquet(input_path)
    
    subset = load_subset_for_pilot(str(input_path), max_samples=2)
    assert len(subset) == 2
    assert all('smiles' in item for item in subset)
    assert all('mol' in item for item in subset)
    assert all(item['mol'] is not None for item in subset)

def test_generate_multiple_conformers_and_sasa():
    """Test SASA generation for a simple molecule."""
    from rdkit import Chem
    mol = Chem.MolFromSmiles('CCO')
    mol = Chem.AddHs(mol)
    
    # Mock params
    params = {
        'numThreads': 0,
        'maxAttempts': 200,
        'energyMinimizationSteps': 0
    }
    
    sasa_values = generate_multiple_conformers_and_sasa(
        mol, 
        base_seed=RANDOM_SEED, 
        num_conformers=3,
        params=params
    )
    
    # Should generate at least some values (unless ETKDG fails completely)
    assert len(sasa_values) > 0
    assert all(isinstance(v, float) for v in sasa_values)

def test_run_stability_check(tmp_path):
    """Test the full stability check workflow."""
    import pandas as pd
    
    # Create dummy input
    df = pd.DataFrame({
        'smiles': ['CCO', 'CCN', 'CCC'],
        'surface_area': [10.0, 20.0, 30.0]
    })
    input_path = tmp_path / "input.parquet"
    df.to_parquet(input_path)
    
    # Dummy params
    params = {
        'numThreads': 0,
        'maxAttempts': 200,
        'energyMinimizationSteps': 0
    }
    
    output_path = tmp_path / "report.json"
    
    # Mock the load_subset to return a valid list
    from code.eval.conformer_stability import load_subset_for_pilot
    with patch('code.eval.conformer_stability.load_subset_for_pilot') as mock_load:
        # Mock molecule
        from rdkit import Chem
        mol = Chem.MolFromSmiles('CCO')
        mock_load.return_value = [{'smiles': 'CCO', 'mol': mol}]
        
        report = run_stability_check(
            [{'smiles': 'CCO', 'mol': mol}],
            params,
            str(output_path)
        )
        
        assert 'mean_variance' in report
        assert 'max_variance' in report
        assert 'threshold_validation' in report
        assert isinstance(report['threshold_validation'], bool)
        assert output_path.exists()
        
        # Verify file content
        with open(output_path) as f:
            saved_report = json.load(f)
            assert saved_report == report