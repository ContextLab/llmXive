"""
Tests for result aggregation functionality in analysis.py
"""
import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.analysis import StatisticalAnalyzer

@pytest.fixture
def sample_inference_results(tmp_path):
    """Create sample inference result files."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    
    # Create structure: seed/strategy/model.json
    for seed in [1, 2, 3]:
        seed_dir = results_dir / str(seed)
        seed_dir.mkdir()
        
        for strategy in ["logical_ascending", "logical_random", "original_cds"]:
            strategy_dir = seed_dir / strategy
            strategy_dir.mkdir()
            
            for model in ["reasoning_model", "non_reasoning_model"]:
                result_file = strategy_dir / f"{model}.json"
                result_file.write_text(json.dumps({
                    "accuracy": 0.75 + (seed * 0.01) + (hash(strategy) % 100) / 1000,
                    "seed": seed,
                    "strategy": strategy,
                    "model_type": model,
                    "prompt_id": f"prompt_{seed}_{strategy}_{model}"
                }))
    
    return results_dir

def test_load_inference_results(sample_inference_results):
    """Test loading inference results from JSON files."""
    analyzer = StatisticalAnalyzer()
    df = analyzer.load_inference_results(sample_inference_results)
    
    assert len(df) == 18  # 3 seeds * 3 strategies * 2 models
    assert all(col in df.columns for col in ['seed', 'strategy', 'model_type', 'accuracy', 'prompt_id'])
    assert df['seed'].nunique() == 3
    assert df['strategy'].nunique() == 3
    assert df['model_type'].nunique() == 2

def test_load_inference_results_missing_directory():
    """Test that missing directory raises FileNotFoundError."""
    analyzer = StatisticalAnalyzer()
    
    with pytest.raises(FileNotFoundError):
        analyzer.load_inference_results(Path("/nonexistent/path"))

def test_load_inference_results_invalid_json(sample_inference_results):
    """Test handling of invalid JSON files."""
    # Create an invalid JSON file
    invalid_file = sample_inference_results / "1" / "logical_ascending" / "invalid.json"
    invalid_file.write_text("not valid json {{{")
    
    analyzer = StatisticalAnalyzer()
    # Should not raise, just skip invalid files
    df = analyzer.load_inference_results(sample_inference_results)
    
    assert len(df) == 18  # Still 18 valid files

def test_load_inference_results_missing_accuracy(sample_inference_results):
    """Test handling of files missing accuracy field."""
    # Create a file missing accuracy
    missing_file = sample_inference_results / "1" / "logical_ascending" / "missing_acc.json"
    missing_file.write_text(json.dumps({
        "seed": 1,
        "strategy": "logical_ascending",
        "model_type": "test"
    }))
    
    analyzer = StatisticalAnalyzer()
    df = analyzer.load_inference_results(sample_inference_results)
    
    assert len(df) == 18  # Missing accuracy file should be skipped

def test_aggregate_by_seed_strategy(sample_inference_results):
    """Test aggregation by seed and strategy."""
    analyzer = StatisticalAnalyzer()
    df = analyzer.load_inference_results(sample_inference_results)
    aggregated = analyzer.aggregate_by_seed_strategy(df)
    
    assert len(aggregated) == 9  # 3 seeds * 3 strategies
    assert all(col in aggregated.columns for col in ['seed', 'strategy', 'mean_accuracy', 'std_accuracy', 'count'])
    assert aggregated['count'].min() == 2  # 2 models per seed/strategy combination
    assert aggregated['mean_accuracy'].min() > 0
    assert aggregated['mean_accuracy'].max() <= 1.0

def test_fit_lmm_basic(sample_inference_results):
    """Test basic LMM fitting."""
    analyzer = StatisticalAnalyzer()
    df = analyzer.load_inference_results(sample_inference_results)
    
    results = analyzer.fit_lmm(df)
    
    assert "summary" in results
    assert "p_values" in results
    assert "params" in results
    assert "converged" in results

def test_fit_lmm_missing_columns(sample_inference_results):
    """Test LMM fitting with missing required columns."""
    analyzer = StatisticalAnalyzer()
    df = analyzer.load_inference_results(sample_inference_results)
    
    # Remove a required column
    df_reduced = df.drop(columns=['prompt_id'])
    
    results = analyzer.fit_lmm(df_reduced)
    
    assert "error" in results

def test_levene_test_variance_stability(sample_inference_results):
    """Test Levene's test for variance stability."""
    analyzer = StatisticalAnalyzer()
    df = analyzer.load_inference_results(sample_inference_results)
    aggregated = analyzer.aggregate_by_seed_strategy(df)
    
    results = analyzer.levene_test_variance_stability(aggregated)
    
    assert "statistic" in results
    assert "p_value" in results
    assert "stable" in results
    assert isinstance(results["statistic"], float)
    assert isinstance(results["p_value"], float)

def test_levene_test_insufficient_groups(sample_inference_results):
    """Test Levene's test with insufficient groups."""
    analyzer = StatisticalAnalyzer()
    df = analyzer.load_inference_results(sample_inference_results)
    aggregated = analyzer.aggregate_by_seed_strategy(df)
    
    # Filter to only one strategy
    single_strategy_df = aggregated[aggregated['strategy'] == 'logical_ascending']
    
    results = analyzer.levene_test_variance_stability(single_strategy_df)
    
    assert "error" in results

def test_bonferroni_correction():
    """Test Bonferroni correction."""
    analyzer = StatisticalAnalyzer()
    p_values = {
        "test1": 0.01,
        "test2": 0.03,
        "test3": 0.07,
        "test4": 0.15
    }
    
    results = analyzer.bonferroni_correction(p_values, alpha=0.05)
    
    assert len(results["corrected_p_values"]) == 4
    assert len(results["significant"]) == 4
    assert results["n_tests"] == 4
    assert results["alpha"] == 0.05
    
    # Check that corrected p-values are larger
    for k, v in results["corrected_p_values"].items():
        assert v >= p_values[k]

def test_power_analysis():
    """Test power analysis calculation."""
    analyzer = StatisticalAnalyzer()
    results = analyzer.power_analysis(effect_size=0.25, alpha=0.05, power=0.8)
    
    assert "required_n_per_group" in results
    assert "total_required_n" in results
    assert "justification" in results
    assert results["effect_size"] == 0.25

def test_generate_report(sample_inference_results):
    """Test report generation."""
    analyzer = StatisticalAnalyzer()
    df = analyzer.load_inference_results(sample_inference_results)
    
    lmm_results = analyzer.fit_lmm(df)
    effect_size = analyzer.calculate_effect_size(lmm_results, df)
    aggregated = analyzer.aggregate_by_seed_strategy(df)
    levene_results = analyzer.levene_test_variance_stability(aggregated)
    
    report = analyzer.generate_report(lmm_results, effect_size, levene_results)
    
    assert "Statistical Analysis Report" in report
    assert "LMM Results" in report
    assert "Effect Size" in report
    assert "Variance Stability" in report
    assert "Deviation Note" in report

def test_run_full_analysis(sample_inference_results, tmp_path):
    """Test full analysis pipeline."""
    analyzer = StatisticalAnalyzer()
    output_path = tmp_path / "report.md"
    
    results = analyzer.run_full_analysis(sample_inference_results, output_path)
    
    assert "df" in results
    assert "lmm_results" in results
    assert "effect_size" in results
    assert "levene_results" in results
    assert "report_path" in results
    assert output_path.exists()
    
    # Check report content
    with open(output_path, 'r') as f:
        content = f.read()
    assert "Statistical Analysis Report" in content

def test_run_full_analysis_with_lmm_error(sample_inference_results, tmp_path):
    """Test full analysis when LMM fails."""
    analyzer = StatisticalAnalyzer()
    output_path = tmp_path / "report.md"
    
    # Create a DataFrame that will cause LMM to fail (e.g., single row)
    bad_df = pd.DataFrame([{
        'accuracy': 0.5,
        'strategy': 'test',
        'model_type': 'test',
        'seed': '1',
        'prompt_id': '1'
    }])
    
    with patch.object(analyzer, 'load_inference_results', return_value=bad_df):
        results = analyzer.run_full_analysis(sample_inference_results, output_path)
    
    # Should still generate a report, but with error noted
    assert "lmm_results" in results
    assert output_path.exists()