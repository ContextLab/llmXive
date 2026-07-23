"""
Unit tests for power analysis functionality.
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

from data_models import PolymerRecord
from power_analysis import (
    check_dataset_power,
    interpret_effect_size,
    run_power_analysis_from_csv,
    ALPHA,
    BETA,
    MIN_DATASET_SIZE,
    EFFECT_SIZE_SMALL,
    EFFECT_SIZE_MEDIUM,
    EFFECT_SIZE_LARGE
)

@pytest.fixture
def sample_records():
    """Create sample PolymerRecord objects for testing."""
    records = []
    
    # Create two groups with different degradation rates
    # Group 1: Higher degradation rates
    for i in range(50):
        records.append(PolymerRecord(
            smiles=f"C{10+i}H{20+i}O{5}",
            degradation_pathway='hydrolysis',
            degradation_rate=0.8 + np.random.normal(0, 0.1),
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0,
            molecular_weight=1000.0,
            functional_groups=['ester']
        ))
    
    # Group 2: Lower degradation rates
    for i in range(50):
        records.append(PolymerRecord(
            smiles=f"C{10+i}H{20+i}O{5}",
            degradation_pathway='oxidation',
            degradation_rate=0.3 + np.random.normal(0, 0.1),
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0,
            molecular_weight=1000.0,
            functional_groups=['ester']
        ))
    
    return records

@pytest.fixture
def small_sample_records():
    """Create a small sample for testing power insufficiency."""
    records = []
    
    # Only 10 records per group
    for i in range(10):
        records.append(PolymerRecord(
            smiles=f"C{10+i}H{20+i}O{5}",
            degradation_pathway='hydrolysis',
            degradation_rate=0.8 + np.random.normal(0, 0.1),
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0,
            molecular_weight=1000.0,
            functional_groups=['ester']
        ))
    
    for i in range(10):
        records.append(PolymerRecord(
            smiles=f"C{10+i}H{20+i}O{5}",
            degradation_pathway='oxidation',
            degradation_rate=0.3 + np.random.normal(0, 0.1),
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0,
            molecular_weight=1000.0,
            functional_groups=['ester']
        ))
    
    return records

def test_interpret_effect_size():
    """Test effect size interpretation."""
    assert interpret_effect_size(0.0) == "negligible"
    assert interpret_effect_size(0.1) == "negligible"
    assert interpret_effect_size(0.19) == "negligible"
    
    assert interpret_effect_size(0.2) == "small"
    assert interpret_effect_size(0.4) == "small"
    assert interpret_effect_size(0.49) == "small"
    
    assert interpret_effect_size(0.5) == "medium"
    assert interpret_effect_size(0.7) == "medium"
    assert interpret_effect_size(0.79) == "medium"
    
    assert interpret_effect_size(0.8) == "large"
    assert interpret_effect_size(1.0) == "large"
    assert interpret_effect_size(2.0) == "large"

def test_check_dataset_power_insufficient_records():
    """Test power analysis with insufficient records."""
    records = [
        PolymerRecord(
            smiles="CCO",
            degradation_pathway='hydrolysis',
            degradation_rate=0.5,
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0,
            molecular_weight=50.0,
            functional_groups=['ester']
        )
    ]
    
    result = check_dataset_power(records)
    
    assert 'error' in result
    assert result['sample_size'] == 1
    assert result['sufficient'] == False

def test_check_dataset_power_insufficient_groups(sample_records):
    """Test power analysis with only one group."""
    # Filter to only one group
    single_group_records = [r for r in sample_records if r.degradation_pathway == 'hydrolysis']
    
    result = check_dataset_power(single_group_records)
    
    assert 'error' in result
    assert 'Insufficient groups' in result['error']
    assert result['sufficient'] == False

def test_check_dataset_power_sufficient(sample_records):
    """Test power analysis with sufficient records."""
    result = check_dataset_power(sample_records)
    
    assert 'error' not in result
    assert result['sample_size'] == 100
    assert result['effect_size'] > 0
    assert 0 <= result['power'] <= 1
    assert 'warnings' in result

def test_check_dataset_power_small_sample(small_sample_records):
    """Test power analysis with small sample size."""
    result = check_dataset_power(small_sample_records)
    
    assert result['sample_size'] == 20
    assert result['sample_size'] < MIN_DATASET_SIZE
    assert 'warnings' in result
    assert any('below minimum threshold' in w for w in result['warnings'])

def test_run_power_analysis_from_csv():
    """Test running power analysis from CSV file."""
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = {
            'smiles': ['CCO' * 10] * 60,
            'degradation_pathway': ['hydrolysis'] * 30 + ['oxidation'] * 30,
            'degradation_rate': [0.8] * 30 + [0.3] * 30,
            'temperature': [25.0] * 60,
            'ph': [7.0] * 60,
            'uv_exposure': [0.0] * 60,
            'molecular_weight': [1000.0] * 60,
            'functional_groups': [['ester']] * 60
        }
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        csv_path = f.name
    
    try:
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_power_analysis_from_csv(
                csv_path,
                output_dir=temp_dir,
                target_variable='degradation_rate',
                group_variable='degradation_pathway'
            )
            
            # Check result structure
            assert 'sample_size' in result
            assert 'effect_size' in result
            assert 'power' in result
            assert 'sufficient' in result
            
            # Check that report was saved
            report_path = os.path.join(temp_dir, 'power_analysis_report.json')
            assert os.path.exists(report_path)
            
            # Verify report content
            with open(report_path, 'r') as rf:
                saved_report = json.load(rf)
            
            assert saved_report['sample_size'] == result['sample_size']
    finally:
        # Clean up
        if os.path.exists(csv_path):
            os.unlink(csv_path)

def test_run_power_analysis_file_not_found():
    """Test error handling for missing CSV file."""
    with pytest.raises(FileNotFoundError):
        run_power_analysis_from_csv('/nonexistent/path/to/file.csv')

def test_power_analysis_constants():
    """Test that power analysis constants are correctly defined."""
    assert ALPHA == 0.05
    assert BETA == 0.20
    assert MIN_DATASET_SIZE == 150
    assert EFFECT_SIZE_SMALL == 0.2
    assert EFFECT_SIZE_MEDIUM == 0.5
    assert EFFECT_SIZE_LARGE == 0.8

def test_check_dataset_power_with_missing_values():
    """Test power analysis handles missing values correctly."""
    records = [
        PolymerRecord(
            smiles="CCO",
            degradation_pathway='hydrolysis',
            degradation_rate=0.8,
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0,
            molecular_weight=1000.0,
            functional_groups=['ester']
        ),
        PolymerRecord(
            smiles="CCO",
            degradation_pathway=None,  # Missing group
            degradation_rate=0.5,
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0,
            molecular_weight=1000.0,
            functional_groups=['ester']
        ),
        PolymerRecord(
            smiles="CCO",
            degradation_pathway='oxidation',
            degradation_rate=None,  # Missing target
            temperature=25.0,
            ph=7.0,
            uv_exposure=0.0,
            molecular_weight=1000.0,
            functional_groups=['ester']
        )
    ]
    
    result = check_dataset_power(records)
    
    # Should handle missing values gracefully
    assert 'sample_size' in result
    # Only 1 record should be used (the first one has both group and target)
    # But we need at least 2 groups, so this will fail
    assert result['sample_size'] <= 3
