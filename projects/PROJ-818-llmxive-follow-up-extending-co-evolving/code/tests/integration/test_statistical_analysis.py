"""
Integration tests for the statistical analysis module.
Tests the full pipeline: data loading -> ANOVA -> Tukey HSD -> Report generation.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.analysis.statistical_tests import (
    StatisticalAnalysisError,
    load_forgetting_data,
    perform_mixed_design_anova,
    perform_tukey_hsd,
    run_statistical_analysis
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock forgetting data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        
        # Create mock data for 3 conditions
        conditions = ['sequential', 'mixed', 'coevolving']
        
        for cond in conditions:
            # Generate 35 runs per condition (N >= 30 as per SC-004)
            run_data = []
            for i in range(35):
                # Simulate forgetting rates with some variation
                # Sequential: ~0.15, Mixed: ~0.10, Coevolving: ~0.05
                if cond == 'sequential':
                    rate = 0.15 + (i * 0.001) + (0.01 * (i % 5))
                elif cond == 'mixed':
                    rate = 0.10 + (i * 0.0005) + (0.005 * (i % 3))
                else: # coevolving
                    rate = 0.05 + (i * 0.0002) + (0.002 * (i % 2))
                
                run_data.append({
                    'condition': cond,
                    'run_id': i,
                    'forgetting_rate': rate,
                    'retention_rate': 1.0 - rate
                })
            
            # Write to a JSON file
            file_path = data_dir / f"{cond}_results.json"
            with open(file_path, 'w') as f:
                json.dump(run_data, f)
        
        yield data_dir


def test_load_forgetting_data(temp_data_dir):
    """Test that data is loaded correctly from multiple JSON files."""
    df = load_forgetting_data(str(temp_data_dir))
    
    assert len(df) == 105  # 3 conditions * 35 runs
    assert 'condition' in df.columns
    assert 'forgetting_rate' in df.columns
    assert 'retention_rate' in df.columns
    
    # Check counts per condition
    counts = df['condition'].value_counts()
    assert counts['Sequential'] == 35
    assert counts['Mixed'] == 35
    assert counts['Coevolving'] == 35


def test_perform_mixed_design_anova(temp_data_dir):
    """Test ANOVA calculation."""
    df = load_forgetting_data(str(temp_data_dir))
    result = perform_mixed_design_anova(df, 'condition', 'forgetting_rate')
    
    assert result.f_statistic > 0
    assert 0 <= result.p_value <= 1
    assert result.df_num == 2  # 3 groups - 1
    assert result.df_denom == 102  # 105 - 3
    assert result.is_significant is True  # With the distinct means we generated, it should be significant


def test_perform_tukey_hsd(temp_data_dir):
    """Test Tukey HSD post-hoc test."""
    df = load_forgetting_data(str(temp_data_dir))
    result = perform_tukey_hsd(df, 'condition', 'forgetting_rate')
    
    assert len(result.groups) == 3
    assert len(result.significant_pairs) > 0  # We expect significant differences given the data generation
    assert 'Sequential' in result.groups
    assert 'Mixed' in result.groups
    assert 'Coevolving' in result.groups


def test_run_statistical_analysis(temp_data_dir):
    """Test the full analysis pipeline and output file generation."""
    output_path = temp_data_dir / "analysis_output.json"
    
    report = run_statistical_analysis(str(temp_data_dir), str(output_path))
    
    # Verify file was created
    assert output_path.exists()
    
    # Verify report structure
    assert report.anova is not None
    assert report.tukey is not None
    assert len(report.descriptive_stats) == 3
    assert report.raw_data_summary['total_runs'] == 105
    
    # Verify JSON content
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'anova' in data
    assert 'tukey' in data
    assert 'descriptive_stats' in data
    assert data['anova']['is_significant'] is True


def test_empty_data_raises_error():
    """Test that empty data raises an appropriate error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        # Create an empty file
        (data_dir / "empty.json").write_text("[]")
        
        with pytest.raises(StatisticalAnalysisError, match="No valid forgetting data found"):
            load_forgetting_data(str(data_dir))


def test_insufficient_samples_raises_error():
    """Test that groups with < 2 samples raise an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        
        # Create data with only 1 sample for one condition
        data = [{'condition': 'Sequential', 'run_id': 0, 'forgetting_rate': 0.1}]
        with open(data_dir / "seq.json", 'w') as f:
            json.dump(data, f)
        
        # Add enough for others
        data = [{'condition': 'Mixed', 'run_id': i, 'forgetting_rate': 0.1} for i in range(5)]
        with open(data_dir / "mix.json", 'w') as f:
            json.dump(data, f)
        
        data = [{'condition': 'Coevolving', 'run_id': i, 'forgetting_rate': 0.1} for i in range(5)]
        with open(data_dir / "coe.json", 'w') as f:
            json.dump(data, f)
        
        df = load_forgetting_data(str(data_dir))
        
        with pytest.raises(StatisticalAnalysisError, match="insufficient samples"):
            perform_mixed_design_anova(df, 'condition', 'forgetting_rate')