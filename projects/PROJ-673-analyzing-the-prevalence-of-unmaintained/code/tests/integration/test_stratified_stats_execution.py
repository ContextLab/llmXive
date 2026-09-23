"""
Integration test for T035: Execute Stratified Correlation.

Verifies that stratified_stats.py runs end-to-end and produces
the expected JSON output file with valid structure.
"""
import json
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from src.analysis.stratified_stats import run_stratified_analysis, filter_valid_groups


@pytest.fixture
def mock_data_file(tmp_path):
    """Create a mock CSV file with sufficient data for stratification."""
    # Create a dataframe with multiple categories, some with N < 30
    data = []
    categories = ['framework', 'utility', 'database', 'other']
    
    # Generate 50 samples for 'framework' (passes N>=30)
    for i in range(50):
        data.append({
            'name': f'pkg-framework-{i}',
            'age_in_days': 100 + i,
            'vulnerability_count': i % 5,
            'category': 'framework'
        })
    
    # Generate 20 samples for 'utility' (fails N>=30)
    for i in range(20):
        data.append({
            'name': f'pkg-utility-{i}',
            'age_in_days': 50 + i,
            'vulnerability_count': i % 3,
            'category': 'utility'
        })

    # Generate 40 samples for 'database' (passes N>=30)
    for i in range(40):
        data.append({
            'name': f'pkg-db-{i}',
            'age_in_days': 200 + i,
            'vulnerability_count': i % 10,
            'category': 'database'
        })

    df = pd.DataFrame(data)
    file_path = tmp_path / "test_deps.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)


def test_stratified_analysis_execution(mock_data_file, tmp_path):
    """
    Test that run_stratified_analysis executes without error and writes output.
    """
    output_file = tmp_path / "results_stratified.json"
    
    # Run the analysis
    result = run_stratified_analysis(
        input_path=mock_data_file,
        output_path=str(output_file),
        min_group_size=30
    )

    # Verify output file exists
    assert output_file.exists(), "Output JSON file was not created"

    # Verify content structure
    with open(output_file) as f:
        saved_data = json.load(f)

    assert saved_data['status'] == 'success'
    assert 'results' in saved_data
    assert 'framework' in saved_data['results']
    assert 'database' in saved_data['results']
    assert 'utility' not in saved_data['results']  # Should be excluded (N=20 < 30)

    # Verify correlation structure
    for cat, stats in saved_data['results'].items():
        assert 'rho' in stats
        assert 'p_value' in stats
        assert 'n' in stats
        assert isinstance(stats['rho'], (int, float, type(None)))
        assert isinstance(stats['p_value'], (int, float, type(None)))
        assert stats['n'] >= 30


def test_filter_valid_groups_logic():
    """
    Unit test for the filtering logic specifically.
    """
    df = pd.DataFrame({
        'name': ['a', 'b', 'c', 'd', 'e'],
        'age_in_days': [1, 2, 3, 4, 5],
        'vulnerability_count': [1, 2, 3, 4, 5],
        'category': ['A', 'A', 'A', 'B', 'B']
    })
    
    # A has 3 items, B has 2 items. Min size 3.
    filtered = filter_valid_groups(df, min_group_size=3)
    
    assert 'A' in filtered
    assert 'B' not in filtered
    assert len(filtered['A']) == 3
