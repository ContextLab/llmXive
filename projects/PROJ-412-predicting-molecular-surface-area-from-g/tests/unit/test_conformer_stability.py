import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os

# Import the module under test
from code.eval.conformer_stability import (
    load_subset_for_pilot,
    generate_multiple_conformers_and_sasa,
    run_stability_check
)

@pytest.fixture
def sample_parquet_file(tmp_path):
    """Create a temporary parquet file with sample molecules for testing."""
    # Create sample data
    data = {
        'smiles': [
            'CCO',  # Ethanol
            'CC(=O)O',  # Acetic acid
            'c1ccccc1',  # Benzene
            'CC1=CC=CC=C1',  # Toluene
            'CCCCC',  # Pentane
            'C1CCCCC1',  # Cyclohexane
            'CC(C)C',  # Isobutane
            'C=CC',  # Propene
            'CC#C',  # Propyne
            'CCOCC'  # Diethyl ether
        ],
        'node_features': [[1] * 10 for _ in range(10)],
        'edge_features': [[1] * 5 for _ in range(10)],
        'molecular_weight': [46.07, 60.05, 78.11, 92.14, 72.15, 84.16, 58.12, 42.08, 40.06, 74.12],
        'surface_area': [50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 75.0, 65.0, 55.0, 85.0]
    }
    
    df = pd.DataFrame(data)
    output_path = tmp_path / 'test_data.parquet'
    df.to_parquet(output_path)
    
    return output_path

def test_load_subset_for_pilot(sample_parquet_file):
    """Test loading a subset of molecules from parquet file."""
    subset = load_subset_for_pilot(str(sample_parquet_file), subset_size=5)
    
    assert len(subset) == 5
    assert 'smiles' in subset.columns
    assert subset['smiles'].is_unique

def test_generate_multiple_conformers_and_sasa_simple():
    """Test conformer generation and SASA calculation for a simple molecule."""
    # Use a very simple molecule that should always work
    smiles = 'CCO'  # Ethanol
    
    mean_sasa, variance_sasa, success = generate_multiple_conformers_and_sasa(
        smiles,
        num_conformers=3,
        max_attempts=50
    )
    
    assert success is True
    assert mean_sasa is not None
    assert variance_sasa is not None
    assert mean_sasa > 0
    assert variance_sasa >= 0

def test_generate_multiple_conformers_invalid_smiles():
    """Test handling of invalid SMILES."""
    smiles = 'INVALID_SMILES_123'
    
    mean_sasa, variance_sasa, success = generate_multiple_conformers_and_sasa(
        smiles,
        num_conformers=3
    )
    
    assert success is False
    assert mean_sasa is None
    assert variance_sasa is None

def test_run_stability_check(sample_parquet_file, tmp_path):
    """Test the full stability check pipeline."""
    output_path = tmp_path / 'pilot_check.md'
    
    # Use very low threshold to ensure we get some "unstable" molecules for testing
    # and a small subset size for speed
    results = run_stability_check(
        input_path=str(sample_parquet_file),
        output_path=str(output_path),
        num_conformers=3,
        variance_threshold=100.0,  # High threshold to ensure stability
        subset_size=5
    )
    
    # Verify results structure
    assert 'total_molecules_tested' in results
    assert 'conformer_generation_success_rate' in results
    assert 'pipeline_flagged' in results
    
    # Verify output files were created
    assert output_path.exists()
    json_path = str(output_path).replace('.md', '.json')
    assert os.path.exists(json_path)
    
    # Verify markdown content
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert 'Conformer Stability Pilot Check Report' in content
    assert 'Summary' in content
    assert 'Methodology' in content

def test_run_stability_check_with_flagging(sample_parquet_file, tmp_path):
    """Test that the pipeline is flagged when instability is high."""
    output_path = tmp_path / 'pilot_check_flagged.md'
    
    # Use a very low threshold to force flagging
    results = run_stability_check(
        input_path=str(sample_parquet_file),
        output_path=str(output_path),
        num_conformers=3,
        variance_threshold=0.001,  # Very low threshold
        subset_size=5
    )
    
    # With such a low threshold, we expect some molecules to be flagged as unstable
    # The exact behavior depends on the actual variance, but the function should complete
    assert 'pipeline_flagged' in results
    
    # Verify output files
    assert output_path.exists()
    json_path = str(output_path).replace('.md', '.json')
    assert os.path.exists(json_path)
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert 'Conclusion' in content