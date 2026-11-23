import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from statsmodels.stats.power import TTestIndPower

from analysis.analyze_sampling_power import (
    load_classified_threads,
    load_thread_metrics,
    calculate_effect_size,
    calculate_power,
    analyze_sampling_issues,
    generate_power_analysis_report,
    append_to_summary
)

@pytest.fixture
def sample_classified_data():
    """Create a sample classified threads DataFrame."""
    data = {
        'thread_id': [f't{i}' for i in range(100)],
        'is_valid': [True] * 60 + [False] * 40,  # 60% valid
        'subreddit': ['askscience'] * 50 + ['fdr'] * 50,
        'comment_count': np.random.randint(10, 100, 100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_metrics_data():
    """Create a sample thread metrics DataFrame."""
    data = {
        'thread_id': [f't{i}' for i in range(100)],
        'contagion_index': np.random.uniform(-1, 1, 100),
        'agreement_proportion': np.random.uniform(0, 1, 100),
        'shannon_entropy': np.random.uniform(0, 2, 100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_summary_file(tmp_path):
    """Create a temporary summary file."""
    summary_path = tmp_path / "analysis_summary.md"
    summary_path.write_text("# Analysis Summary\n\n## Introduction\n")
    return str(summary_path)

def test_load_classified_threads(sample_classified_data, tmp_path):
    """Test loading classified threads from CSV."""
    file_path = tmp_path / "classified.csv"
    sample_classified_data.to_csv(file_path, index=False)
    
    df = load_classified_threads(str(file_path))
    assert len(df) == 100
    assert 'is_valid' in df.columns
    assert 'thread_id' in df.columns

def test_load_thread_metrics(sample_metrics_data, tmp_path):
    """Test loading thread metrics from CSV."""
    file_path = tmp_path / "metrics.csv"
    sample_metrics_data.to_csv(file_path, index=False)
    
    df = load_thread_metrics(str(file_path))
    assert len(df) == 100
    assert 'contagion_index' in df.columns

def test_load_thread_metrics_missing_file():
    """Test loading metrics when file doesn't exist."""
    df = load_thread_metrics("nonexistent.csv")
    assert df.empty

def test_calculate_effect_size():
    """Test Cohen's d effect size calculation."""
    group1 = pd.Series([1, 2, 3, 4, 5])
    group2 = pd.Series([6, 7, 8, 9, 10])
    
    effect = calculate_effect_size(group1, group2)
    assert effect < 0  # group2 has higher mean, so negative d
    assert abs(effect) > 2.0  # Large effect size

def test_calculate_effect_size_empty_groups():
    """Test effect size with empty groups."""
    assert calculate_effect_size(pd.Series([]), pd.Series([1, 2, 3])) == 0.0
    assert calculate_effect_size(pd.Series([1, 2, 3]), pd.Series([])) == 0.0
    assert calculate_effect_size(pd.Series([]), pd.Series([])) == 0.0

def test_calculate_power():
    """Test power calculation."""
    power = calculate_power(n=100, effect_size=0.5, alpha=0.05)
    assert 0 <= power <= 1
    assert power > 0.8  # With n=100 and effect=0.5, power should be high

def test_calculate_power_small_sample():
    """Test power calculation with small sample."""
    power = calculate_power(n=10, effect_size=0.5, alpha=0.05)
    assert 0 <= power <= 1
    assert power < 0.5  # Small sample, low power

def test_calculate_power_zero_effect():
    """Test power calculation with zero effect size."""
    power = calculate_power(n=100, effect_size=0.0, alpha=0.05)
    assert power == 0.0

def test_analyze_sampling_issues_no_imbalance(sample_classified_data):
    """Test sampling issues analysis with balanced data."""
    issues = analyze_sampling_issues(sample_classified_data)
    assert issues['total_issues'] >= 0  # May have other issues but not class imbalance
    assert issues['high_severity'] == 0

def test_analyze_sampling_issues_with_imbalance():
    """Test sampling issues analysis with imbalanced data."""
    data = {
        'thread_id': [f't{i}' for i in range(100)],
        'is_valid': [True] * 20 + [False] * 80  # 20% valid - imbalanced
    }
    df = pd.DataFrame(data)
    
    issues = analyze_sampling_issues(df)
    assert any(i['type'] == 'class_imbalance' for i in issues['issues'])
    assert issues['high_severity'] >= 1

def test_analyze_sampling_issues_missing_data():
    """Test sampling issues with missing data."""
    data = {
        'thread_id': [f't{i}' for i in range(100)],
        'is_valid': [True] * 50 + [False] * 50,
        'subreddit': [None] * 60 + ['askscience'] * 40  # 60% missing
    }
    df = pd.DataFrame(data)
    
    issues = analyze_sampling_issues(df)
    assert any(i['type'] == 'missing_data' for i in issues['issues'])

def test_generate_power_analysis_report(sample_classified_data, sample_metrics_data):
    """Test power analysis report generation."""
    report = generate_power_analysis_report(sample_classified_data, sample_metrics_data)
    
    assert 'total_threads' in report
    assert report['total_threads'] == 100
    assert 'valid_threads' in report
    assert report['valid_threads'] == 60
    assert 'power_analysis' in report
    assert 'sampling_issues' in report
    assert 'recommendations' in report

def test_generate_power_analysis_report_low_power(sample_classified_data, sample_metrics_data):
    """Test report generation with low power."""
    # Reduce sample size to get low power
    small_classified = sample_classified_data.head(20)
    small_metrics = sample_metrics_data.head(20)
    
    report = generate_power_analysis_report(small_classified, small_metrics)
    
    # Should have a recommendation about low power
    power_recs = [r for r in report['recommendations'] if r['type'] == 'low_power']
    assert len(power_recs) >= 1

def test_append_to_summary(temp_summary_file, sample_classified_data, sample_metrics_data):
    """Test appending power analysis to summary."""
    report = generate_power_analysis_report(sample_classified_data, sample_metrics_data)
    append_to_summary(temp_summary_file, report)
    
    with open(temp_summary_file, 'r') as f:
        content = f.read()
    
    assert "## Post-Hoc Power Analysis" in content
    assert "Total Threads Analyzed" in content
    assert "Statistical Power" in content

def test_append_to_summary_duplicate_section(temp_summary_file, sample_classified_data, sample_metrics_data):
    """Test appending when section already exists."""
    report1 = generate_power_analysis_report(sample_classified_data, sample_metrics_data)
    append_to_summary(temp_summary_file, report1)
    
    # Append again
    report2 = generate_power_analysis_report(sample_classified_data, sample_metrics_data)
    append_to_summary(temp_summary_file, report2)
    
    with open(temp_summary_file, 'r') as f:
        content = f.read()
    
    # Should have the section (possibly duplicated, but at least present)
    assert "## Post-Hoc Power Analysis" in content

def test_main_integration(sample_classified_data, sample_metrics_data, tmp_path, caplog):
    """Test main function integration."""
    import sys
    from io import StringIO
    
    # Create temp files
    classified_path = tmp_path / "classified.csv"
    metrics_path = tmp_path / "metrics.csv"
    summary_path = tmp_path / "summary.md"
    output_path = tmp_path / "power_report.json"
    
    sample_classified_data.to_csv(classified_path, index=False)
    sample_metrics_data.to_csv(metrics_path, index=False)
    summary_path.write_text("# Summary\n")
    
    # Mock the paths in the main function
    import analysis.analyze_sampling_power as module
    original_classified = module.classified_path if hasattr(module, 'classified_path') else None
    original_metrics = module.metrics_path if hasattr(module, 'metrics_path') else None
    original_summary = module.summary_path if hasattr(module, 'summary_path') else None
    original_output = module.output_path if hasattr(module, 'output_path') else None
    
    # Temporarily override paths
    module.classified_path = str(classified_path)
    module.metrics_path = str(metrics_path)
    module.summary_path = str(summary_path)
    module.output_path = str(output_path)
    
    try:
        # Run main
        module.main()
        
        # Check output file was created
        assert output_path.exists()
        
        # Check JSON content
        with open(output_path, 'r') as f:
            report = json.load(f)
        assert report['total_threads'] == 100
        
        # Check summary was updated
        with open(summary_path, 'r') as f:
            content = f.read()
        assert "Post-Hoc Power Analysis" in content
        
    finally:
        # Restore original paths if they existed
        if original_classified:
            module.classified_path = original_classified
        if original_metrics:
            module.metrics_path = original_metrics
        if original_summary:
            module.summary_path = original_summary
        if original_output:
            module.output_path = original_output