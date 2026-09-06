import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions we are testing
# Note: We assume the module is importable as 'fidelity_loss'
import sys
sys.path.insert(0, 'code')
from fidelity_loss import calculate_fidelity_loss, generate_lineage_report, save_summary

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe matching the expected schema."""
    data = {
        'sample_id': ['s1', 's2', 's3', 's4', 's5'],
        'prompt': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'image_url': ['i1', 'i2', 'i3', 'i4', 'i5'],
        'teacher_scores': [
            {'Alignment': 5.0, 'Realism': 4.0, 'Aesthetics': 3.0, 'Plausibility': 4.5},
            {'Alignment': 6.0, 'Realism': 5.0, 'Aesthetics': 4.0, 'Plausibility': 5.5},
            {'Alignment': 4.0, 'Realism': 3.0, 'Aesthetics': 2.0, 'Plausibility': 3.5},
            {'Alignment': 7.0, 'Realism': 6.0, 'Aesthetics': 5.0, 'Plausibility': 6.5},
            {'Alignment': 5.5, 'Realism': 4.5, 'Aesthetics': 3.5, 'Plausibility': 5.0}
        ],
        'student_scalar': [5.2, 5.8, 4.1, 6.8, 5.6],
        'human_annotations': [
            {'Alignment': 5.0, 'Realism': 4.0, 'Aesthetics': 3.0, 'Plausibility': 4.5},
            {'Alignment': 6.0, 'Realism': 5.0, 'Aesthetics': 4.0, 'Plausibility': 5.5},
            {'Alignment': 4.0, 'Realism': 3.0, 'Aesthetics': 2.0, 'Plausibility': 3.5},
            {'Alignment': 7.0, 'Realism': 6.0, 'Aesthetics': 5.0, 'Plausibility': 6.5},
            {'Alignment': 5.5, 'Realism': 4.5, 'Aesthetics': 3.5, 'Plausibility': 5.0}
        ],
        'primary_dimension': ['Alignment', 'Realism', 'Aesthetics', 'Plausibility', 'Alignment'],
        'prompt_metadata': [
            {'primary_dimension': 'Alignment'},
            {'primary_dimension': 'Realism'},
            {'primary_dimension': 'Aesthetics'},
            {'primary_dimension': 'Plausibility'},
            {'primary_dimension': 'Alignment'}
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def logger():
    import logging
    return logging.getLogger("test_logger")

def test_calculate_fidelity_loss_valid_data(sample_dataframe, logger):
    """Test that fidelity loss is calculated correctly for valid data."""
    df, rule_hash = calculate_fidelity_loss(sample_dataframe, logger)
    
    # Check that we have the expected columns
    assert 'fidelity_loss' in df.columns
    
    # Check that no rows were excluded (all data is valid)
    assert len(df) == len(sample_dataframe)
    
    # Verify fidelity loss calculation for first row (Alignment)
    # student_scalar=5.2, human_annotations['Alignment']=5.0 -> MAE = 0.2
    assert abs(df.iloc[0]['fidelity_loss'] - 0.2) < 1e-6

def test_calculate_fidelity_loss_missing_student_scalar(sample_dataframe, logger):
    """Test that samples with missing student_scalar are excluded."""
    df_missing = sample_dataframe.copy()
    df_missing.loc[0, 'student_scalar'] = np.nan
    
    df_filtered, rule_hash = calculate_fidelity_loss(df_missing, logger)
    
    # Row 0 should be excluded
    assert len(df_filtered) == len(sample_dataframe) - 1
    assert 0 not in df_filtered.index

def test_calculate_fidelity_loss_missing_human_annotation(sample_dataframe, logger):
    """Test that samples with missing human_annotation for primary_dimension are excluded."""
    df_missing = sample_dataframe.copy()
    # Make human_annotations for primary_dimension missing for row 1 (Realism)
    df_missing.loc[1, 'human_annotations'] = {'Alignment': 6.0, 'Aesthetics': 4.0, 'Plausibility': 5.5}
    # 'Realism' is missing from the dict
    
    df_filtered, rule_hash = calculate_fidelity_loss(df_missing, logger)
    
    # Row 1 should be excluded
    assert len(df_filtered) == len(sample_dataframe) - 1
    assert 1 not in df_filtered.index

def test_generate_lineage_report(sample_dataframe, logger):
    """Test that lineage report is generated correctly."""
    df, rule_hash = calculate_fidelity_loss(sample_dataframe, logger)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'lineage_report.json')
        generate_lineage_report(df, rule_hash, output_path, logger)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert isinstance(report, list)
        assert len(report) == len(df)
        
        # Check structure of first entry
        entry = report[0]
        assert 'sample_id' in entry
        assert 'source_type' in entry
        assert 'dimension' in entry
        assert 'derivation_rule_hash' in entry
        
        # Verify source_type is 'metadata' for all entries
        for e in report:
            assert e['source_type'] == 'metadata'
        
        # Verify derivation_rule_hash is consistent
        for e in report:
            assert e['derivation_rule_hash'] == rule_hash

def test_save_summary(sample_dataframe, logger):
    """Test that summary statistics are saved correctly."""
    df, rule_hash = calculate_fidelity_loss(sample_dataframe, logger)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        summary_path = os.path.join(tmpdir, 'summary.json')
        save_summary(df, summary_path, 0, logger)
        
        assert os.path.exists(summary_path)
        
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        assert 'mean_fidelity_loss' in summary
        assert 'median_fidelity_loss' in summary
        assert 'count' in summary
        assert 'excluded_count' in summary
        assert summary['count'] == len(df)
        assert summary['excluded_count'] == 0
