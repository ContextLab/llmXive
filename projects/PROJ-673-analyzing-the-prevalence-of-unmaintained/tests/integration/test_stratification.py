"""
Integration test for stratified analysis filtering (N < 30 exclusion).

This test verifies that the stratified analysis logic correctly:
1. Groups dependencies by category
2. Excludes categories with fewer than 30 samples from correlation calculation
3. Includes categories with 30 or more samples
4. Returns appropriate metadata about excluded groups
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
from src.analysis.stratified_stats import run_stratified_analysis
from src.analysis.categorizer import categorize_dependencies
from src.models.data_models import Dependency


@pytest.fixture
def small_sample_dataset():
    """
    Create a synthetic dataset with known category distributions:
    - 'framework': 40 samples (should be included)
    - 'utility': 25 samples (should be excluded)
    - 'database': 35 samples (should be included)
    - 'tooling': 15 samples (should be excluded)
    """
    data = []
    
    # Framework category (40 samples)
    for i in range(40):
        data.append({
            'package_name': f'framework-pkg-{i}',
            'category': 'framework',
            'age_in_days': np.random.randint(0, 1000),
            'vulnerability_count': np.random.randint(0, 5),
            'last_release_date': '2023-01-01',
            'last_commit_date': '2023-06-01'
        })
    
    # Utility category (25 samples - too small)
    for i in range(25):
        data.append({
            'package_name': f'utility-pkg-{i}',
            'category': 'utility',
            'age_in_days': np.random.randint(0, 1000),
            'vulnerability_count': np.random.randint(0, 5),
            'last_release_date': '2023-01-01',
            'last_commit_date': '2023-06-01'
        })
    
    # Database category (35 samples)
    for i in range(35):
        data.append({
            'package_name': f'database-pkg-{i}',
            'category': 'database',
            'age_in_days': np.random.randint(0, 1000),
            'vulnerability_count': np.random.randint(0, 5),
            'last_release_date': '2023-01-01',
            'last_commit_date': '2023-06-01'
        })
    
    # Tooling category (15 samples - too small)
    for i in range(15):
        data.append({
            'package_name': f'tooling-pkg-{i}',
            'category': 'tooling',
            'age_in_days': np.random.randint(0, 1000),
            'vulnerability_count': np.random.randint(0, 5),
            'last_release_date': '2023-01-01',
            'last_commit_date': '2023-06-01'
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def min_threshold():
    """Minimum sample size threshold for inclusion."""
    return 30


def test_stratification_excludes_small_categories(small_sample_dataset, min_threshold):
    """
    Test that categories with N < 30 are excluded from stratified analysis.
    
    Expected behavior:
    - 'framework' (N=40) should be included
    - 'database' (N=35) should be included
    - 'utility' (N=25) should be excluded
    - 'tooling' (N=15) should be excluded
    """
    result = run_stratified_analysis(
        df=small_sample_dataset,
        min_sample_size=min_threshold,
        age_column='age_in_days',
        vulnerability_column='vulnerability_count',
        category_column='category'
    )
    
    # Verify that excluded categories are reported
    assert 'excluded_categories' in result
    assert 'utility' in result['excluded_categories']
    assert 'tooling' in result['excluded_categories']
    
    # Verify that included categories have correlation results
    assert 'included_categories' in result
    assert 'framework' in result['included_categories']
    assert 'database' in result['included_categories']
    
    # Verify excluded categories do NOT appear in correlation results
    for cat_name, cat_result in result['included_categories'].items():
        assert cat_name not in result['excluded_categories']


def test_stratification_returns_valid_correlation_coefficients(small_sample_dataset, min_threshold):
    """
    Test that included categories have valid correlation coefficients.
    
    Spearman correlation should be in range [-1, 1].
    """
    result = run_stratified_analysis(
        df=small_sample_dataset,
        min_sample_size=min_threshold,
        age_column='age_in_days',
        vulnerability_column='vulnerability_count',
        category_column='category'
    )
    
    for category, stats in result['included_categories'].items():
        rho = stats['rho']
        p_value = stats['p_value']
        n_samples = stats['n_samples']
        
        # Verify correlation coefficient bounds
        assert -1.0 <= rho <= 1.0, f"Correlation coefficient {rho} out of bounds for {category}"
        
        # Verify p-value bounds
        assert 0.0 <= p_value <= 1.0, f"P-value {p_value} out of bounds for {category}"
        
        # Verify sample size meets threshold
        assert n_samples >= min_threshold, f"Sample size {n_samples} below threshold for {category}"


def test_stratification_metadata_accuracy(small_sample_dataset, min_threshold):
    """
    Test that metadata about excluded/included counts is accurate.
    """
    result = run_stratified_analysis(
        df=small_sample_dataset,
        min_sample_size=min_threshold,
        age_column='age_in_days',
        vulnerability_column='vulnerability_count',
        category_column='category'
    )
    
    # Verify counts
    assert len(result['excluded_categories']) == 2  # utility, tooling
    assert len(result['included_categories']) == 2  # framework, database
    
    # Verify total sample count matches original dataset
    total_included = sum(
        stats['n_samples'] 
        for stats in result['included_categories'].values()
    )
    assert total_included == 75  # 40 (framework) + 35 (database)


def test_stratification_with_all_categories_below_threshold():
    """
    Test behavior when ALL categories have N < 30.
    Expected: All categories excluded, empty included_categories.
    """
    # Create dataset with all small categories
    data = []
    for i in range(20):
        data.append({
            'package_name': f'pkg-{i}',
            'category': 'small-cat',
            'age_in_days': np.random.randint(0, 1000),
            'vulnerability_count': np.random.randint(0, 5),
            'last_release_date': '2023-01-01',
            'last_commit_date': '2023-06-01'
        })
    
    df = pd.DataFrame(data)
    
    result = run_stratified_analysis(
        df=df,
        min_sample_size=30,
        age_column='age_in_days',
        vulnerability_column='vulnerability_count',
        category_column='category'
    )
    
    assert len(result['included_categories']) == 0
    assert len(result['excluded_categories']) == 1
    assert 'small-cat' in result['excluded_categories']


def test_stratification_with_all_categories_above_threshold():
    """
    Test behavior when ALL categories have N >= 30.
    Expected: No categories excluded.
    """
    # Create dataset with all large categories
    data = []
    for cat in ['cat-a', 'cat-b', 'cat-c']:
        for i in range(35):
            data.append({
                'package_name': f'{cat}-pkg-{i}',
                'category': cat,
                'age_in_days': np.random.randint(0, 1000),
                'vulnerability_count': np.random.randint(0, 5),
                'last_release_date': '2023-01-01',
                'last_commit_date': '2023-06-01'
            })
    
    df = pd.DataFrame(data)
    
    result = run_stratified_analysis(
        df=df,
        min_sample_size=30,
        age_column='age_in_days',
        vulnerability_column='vulnerability_count',
        category_column='category'
    )
    
    assert len(result['excluded_categories']) == 0
    assert len(result['included_categories']) == 3
    assert set(result['included_categories'].keys()) == {'cat-a', 'cat-b', 'cat-c'}


def test_stratification_edge_case_exact_threshold():
    """
    Test that categories with exactly N=30 are INCLUDED.
    """
    data = []
    # Exactly 30 samples
    for i in range(30):
        data.append({
            'package_name': f'exact-threshold-pkg-{i}',
            'category': 'exact-threshold',
            'age_in_days': np.random.randint(0, 1000),
            'vulnerability_count': np.random.randint(0, 5),
            'last_release_date': '2023-01-01',
            'last_commit_date': '2023-06-01'
        })
    
    df = pd.DataFrame(data)
    
    result = run_stratified_analysis(
        df=df,
        min_sample_size=30,
        age_column='age_in_days',
        vulnerability_column='vulnerability_count',
        category_column='category'
    )
    
    assert 'exact-threshold' in result['included_categories']
    assert 'exact-threshold' not in result['excluded_categories']
    assert result['included_categories']['exact-threshold']['n_samples'] == 30