"""
Unit tests for code/viz/plots.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.viz.plots import (
    stratify_by_age,
    calculate_group_statistics,
    plot_age_stratified_metrics
)

@pytest.fixture
def sample_data():
    """Create sample regression results data."""
    data = {
        'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'],
        'age': [25, 35, 45, 55, 65, 75],
        'Global_Efficiency': [0.5, 0.48, 0.45, 0.42, 0.38, 0.35],
        'Local_Efficiency': [0.6, 0.58, 0.55, 0.52, 0.48, 0.45],
        'Clustering_Coefficient': [0.7, 0.68, 0.65, 0.62, 0.58, 0.55],
        'signal_quality_flag': ['Good'] * 6
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def test_stratify_by_age_young(sample_data):
    """Test age stratification for young participants."""
    df = stratify_by_age(sample_data)
    young_count = len(df[df['age_group'] == 'Young'])
    assert young_count == 2  # Ages 25 and 35

def test_stratify_by_age_middle(sample_data):
    """Test age stratification for middle-aged participants."""
    df = stratify_by_age(sample_data)
    middle_count = len(df[df['age_group'] == 'Middle'])
    assert middle_count == 2  # Ages 45 and 55

def test_stratify_by_age_older(sample_data):
    """Test age stratification for older participants."""
    df = stratify_by_age(sample_data)
    older_count = len(df[df['age_group'] == 'Older'])
    assert older_count == 2  # Ages 65 and 75

def test_calculate_group_statistics(sample_data):
    """Test calculation of group statistics."""
    df = stratify_by_age(sample_data)
    stats = calculate_group_statistics(df, 'Global_Efficiency')
    
    assert 'Young' in stats
    assert 'Middle' in stats
    assert 'Older' in stats
    
    # Check that statistics are reasonable
    assert stats['Young']['mean'] > 0
    assert stats['Young']['ci_lower'] <= stats['Young']['mean']
    assert stats['Young']['ci_upper'] >= stats['Young']['mean']
    assert stats['Young']['n'] == 2

def test_calculate_group_statistics_empty_group(sample_data):
    """Test calculation when a group has no data."""
    df = stratify_by_age(sample_data)
    # Remove all young participants
    df = df[df['age_group'] != 'Young']
    
    stats = calculate_group_statistics(df, 'Global_Efficiency')
    
    assert 'Young' not in stats
    assert 'Middle' in stats
    assert 'Older' in stats

def test_plot_generation(temp_output_dir, sample_data):
    """Test that plot generation creates a file."""
    df = stratify_by_age(sample_data)
    output_path = temp_output_dir / "test_plot.png"
    
    plot_age_stratified_metrics(df, ['Global_Efficiency'], output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_generation_multiple_metrics(temp_output_dir, sample_data):
    """Test plot generation with multiple metrics."""
    df = stratify_by_age(sample_data)
    output_path = temp_output_dir / "test_multi_plot.png"
    
    metrics = ['Global_Efficiency', 'Local_Efficiency', 'Clustering_Coefficient']
    plot_age_stratified_metrics(df, metrics, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0