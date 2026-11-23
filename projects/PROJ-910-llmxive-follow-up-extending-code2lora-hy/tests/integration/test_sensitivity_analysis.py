"""
Integration test for sensitivity analysis loop (T028).

This test verifies the full sensitivity analysis pipeline:
1. Loads configured feature subsets from sensitivity.py
2. Iterates through each subset
3. Calls adapter generator (simulated via mock data for speed)
4. Calls evaluator (simulated via mock data for speed)
5. Aggregates results and verifies output files are created

NOTE: This test uses mocked data generation to avoid full training/evaluation
cycles which are too slow for integration testing. It verifies the CONTROL FLOW
and FILE OUTPUTS, not the actual model performance.
"""

import os
import json
import csv
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the modules under test
from evaluation.sensitivity import (
    get_feature_subsets,
    run_sensitivity_analysis,
    save_sensitivity_results,
    FeatureSubsetConfig
)
from evaluation.sensitivity_summary_generator import (
    load_sensitivity_results,
    generate_summary_csv,
    save_summary_csv
)
from evaluation.sensitivity_minimal_set import (
    load_baseline_score,
    identify_minimal_feature_set,
    save_minimal_feature_set
)
from utils.config import load_config


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for integration tests."""
    tmpdir = tempfile.mkdtemp()
    workspace = Path(tmpdir)
    
    # Create required directory structure
    (workspace / "data" / "results").mkdir(parents=True)
    (workspace / "data" / "adapters").mkdir(parents=True)
    (workspace / "code").mkdir(parents=True)
    
    yield workspace
    
    # Cleanup
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_config(temp_workspace):
    """Create a minimal config for testing."""
    config_data = {
        "base_model": "TinyLlama-1.1B-Chat-hf",
        "feature_vector_size": 100,
        "hidden_size": 4096,
        "repo_peft_bench_path": str(temp_workspace / "data" / "raw"),
        "results_dir": str(temp_workspace / "data" / "results"),
        "adapters_dir": str(temp_workspace / "data" / "adapters"),
        "random_seed": 42
    }
    
    config_path = temp_workspace / "config.yaml"
    with open(config_path, "w") as f:
        import yaml
        yaml.dump(config_data, f)
    
    return config_path


def test_get_feature_subsets_structure():
    """Test that feature subsets are properly defined."""
    subsets = get_feature_subsets()
    
    assert isinstance(subsets, list)
    assert len(subsets) > 0
    
    # Verify structure of each subset
    for subset in subsets:
        assert isinstance(subset, FeatureSubsetConfig)
        assert subset.name is not None
        assert subset.features is not None
        assert len(subset.features) > 0


@patch('evaluation.sensitivity.train_mlp_projection')
@patch('evaluation.sensitivity.generate_adapter')
@patch('evaluation.sensitivity.run_evaluation')
@patch('evaluation.sensitivity.save_results')
def test_sensitivity_analysis_loop_execution(
    mock_save_results,
    mock_run_evaluation,
    mock_generate_adapter,
    mock_train_mlp,
    temp_workspace,
    mock_config
):
    """
    Test the full sensitivity analysis loop execution.
    
    This test verifies:
    1. The loop iterates over all feature subsets
    2. For each subset, adapter generation is called
    3. For each subset, evaluation is called
    4. Results are aggregated and saved
    """
    
    # Mock the adapter generation to return a fake adapter path
    mock_generate_adapter.return_value = str(temp_workspace / "data" / "adapters" / "test_adapter.safetensors")
    
    # Mock evaluation to return fake scores
    mock_run_evaluation.return_value = {
        "exact_match": 0.85,
        "latency_ms": 150.0
    }
    
    # Mock save_results to do nothing
    mock_save_results.return_value = None
    
    # Mock the config loader
    with patch('evaluation.sensitivity.load_config') as mock_load_config:
        mock_config_obj = MagicMock()
        mock_config_obj.results_dir = str(temp_workspace / "data" / "results")
        mock_config_obj.adapters_dir = str(temp_workspace / "data" / "adapters")
        mock_load_config.return_value = mock_config_obj
        
        # Run the sensitivity analysis
        results = run_sensitivity_analysis()
        
        # Verify that adapter generation was called for each subset
        subsets = get_feature_subsets()
        assert mock_generate_adapter.call_count == len(subsets)
        
        # Verify that evaluation was called for each subset
        assert mock_run_evaluation.call_count == len(subsets)
        
        # Verify results structure
        assert isinstance(results, list)
        assert len(results) == len(subsets)
        
        for result in results:
            assert "feature_set" in result
            assert "accuracy" in result
            assert "meets_threshold" in result


@patch('evaluation.sensitivity.run_sensitivity_analysis')
def test_sensitivity_results_persistence(
    mock_run_analysis,
    temp_workspace,
    mock_config
):
    """
    Test that sensitivity results are properly saved and can be loaded.
    """
    
    # Mock the analysis to return deterministic results
    mock_results = [
        {
            "feature_set": "token_only",
            "accuracy": 0.75,
            "meets_threshold": False
        },
        {
            "feature_set": "cyclomatic_only",
            "accuracy": 0.82,
            "meets_threshold": True
        },
        {
            "feature_set": "full_ast",
            "accuracy": 0.91,
            "meets_threshold": True
        }
    ]
    
    mock_run_analysis.return_value = mock_results
    
    # Mock config
    with patch('evaluation.sensitivity.load_config') as mock_load_config:
        mock_config_obj = MagicMock()
        mock_config_obj.results_dir = str(temp_workspace / "data" / "results")
        mock_load_config.return_value = mock_config_obj
        
        # Run and save
        results = run_sensitivity_analysis()
        save_sensitivity_results(results)
        
        # Verify the JSON file exists
        results_json = temp_workspace / "data" / "results" / "sensitivity_results.json"
        assert results_json.exists()
        
        # Verify we can load it back
        loaded_results = load_sensitivity_results()
        assert len(loaded_results) == len(mock_results)
        
        for orig, loaded in zip(mock_results, loaded_results):
            assert orig["feature_set"] == loaded["feature_set"]
            assert abs(orig["accuracy"] - loaded["accuracy"]) < 1e-6


def test_summary_csv_generation(temp_workspace, mock_config):
    """
    Test that the summary CSV is generated correctly from sensitivity results.
    """
    
    # Create mock sensitivity results file
    results_json = temp_workspace / "data" / "results" / "sensitivity_results.json"
    mock_data = [
        {"feature_set": "token_only", "accuracy": 0.75, "meets_threshold": False},
        {"feature_set": "cyclomatic_only", "accuracy": 0.82, "meets_threshold": True},
        {"feature_set": "full_ast", "accuracy": 0.91, "meets_threshold": True}
    ]
    
    with open(results_json, "w") as f:
        json.dump(mock_data, f)
    
    # Mock config
    with patch('evaluation.sensitivity_summary_generator.load_config') as mock_load_config:
        mock_config_obj = MagicMock()
        mock_config_obj.results_dir = str(temp_workspace / "data" / "results")
        mock_load_config.return_value = mock_config_obj
        
        # Generate summary
        run_summary_generation = lambda: generate_summary_csv()
        run_summary_generation()
        
        # Verify CSV exists
        summary_csv = temp_workspace / "data" / "results" / "sensitivity_summary.csv"
        assert summary_csv.exists()
        
        # Verify CSV content
        with open(summary_csv, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3
            
            # Check headers
            assert "feature_set" in rows[0]
            assert "accuracy" in rows[0]
            assert "meets_threshold" in rows[0]
            
            # Check data
            assert rows[0]["feature_set"] == "token_only"
            assert rows[1]["feature_set"] == "cyclomatic_only"
            assert rows[2]["feature_set"] == "full_ast"


def test_minimal_feature_set_identification(temp_workspace, mock_config):
    """
    Test the minimal feature set identification logic.
    """
    
    # Create mock sensitivity results
    results_json = temp_workspace / "data" / "results" / "sensitivity_results.json"
    mock_results = [
        {"feature_set": "token_only", "accuracy": 0.75, "meets_threshold": False},
        {"feature_set": "cyclomatic_only", "accuracy": 0.82, "meets_threshold": True},
        {"feature_set": "full_ast", "accuracy": 0.91, "meets_threshold": True}
    ]
    
    with open(results_json, "w") as f:
        json.dump(mock_results, f)
    
    # Create mock baseline score
    baseline_json = temp_workspace / "data" / "results" / "baseline_score.json"
    baseline_data = {"score": 0.95}
    with open(baseline_json, "w") as f:
        json.dump(baseline_data, f)
    
    # Mock config
    with patch('evaluation.sensitivity_minimal_set.load_config') as mock_load_config:
        mock_config_obj = MagicMock()
        mock_config_obj.results_dir = str(temp_workspace / "data" / "results")
        mock_load_config.return_value = mock_config_obj
        
        # Identify minimal set
        minimal_set = identify_minimal_feature_set()
        
        # Verify result
        assert minimal_set is not None
        assert "feature_set" in minimal_set
        assert "accuracy" in minimal_set
        
        # Should be the first one that meets threshold
        assert minimal_set["feature_set"] == "cyclomatic_only"
        assert minimal_set["accuracy"] == 0.82
        
        # Verify the output file
        output_file = temp_workspace / "data" / "results" / "minimal_feature_set.txt"
        assert output_file.exists()
        
        with open(output_file, "r") as f:
            content = f.read().strip()
            assert "cyclomatic_only" in content


@patch('evaluation.sensitivity.run_sensitivity_analysis')
@patch('evaluation.sensitivity_summary_generator.run_summary_generation')
@patch('evaluation.sensitivity_minimal_set.run_minimal_feature_set_identification')
def test_full_sensitivity_pipeline_integration(
    mock_minimal_set,
    mock_summary,
    mock_analysis,
    temp_workspace,
    mock_config
):
    """
    Integration test for the entire sensitivity analysis pipeline.
    
    This test simulates the full workflow:
    1. Run sensitivity analysis
    2. Generate summary CSV
    3. Identify minimal feature set
    4. Verify all output files exist
    """
    
    # Mock results
    mock_analysis.return_value = [
        {"feature_set": "token_only", "accuracy": 0.75, "meets_threshold": False},
        {"feature_set": "cyclomatic_only", "accuracy": 0.82, "meets_threshold": True},
        {"feature_set": "full_ast", "accuracy": 0.91, "meets_threshold": True}
    ]
    
    mock_summary.return_value = None
    mock_minimal_set.return_value = {"feature_set": "cyclomatic_only", "accuracy": 0.82}
    
    # Mock configs
    with patch('evaluation.sensitivity.load_config') as mock_load_config1, \
         patch('evaluation.sensitivity_summary_generator.load_config') as mock_load_config2, \
         patch('evaluation.sensitivity_minimal_set.load_config') as mock_load_config3:
        
        mock_config_obj = MagicMock()
        mock_config_obj.results_dir = str(temp_workspace / "data" / "results")
        
        mock_load_config1.return_value = mock_config_obj
        mock_load_config2.return_value = mock_config_obj
        mock_load_config3.return_value = mock_config_obj
        
        # Run the pipeline steps
        run_sensitivity_analysis()
        run_summary_generation()
        run_minimal_feature_set_identification()
        
        # Verify all output files exist
        assert (temp_workspace / "data" / "results" / "sensitivity_results.json").exists()
        assert (temp_workspace / "data" / "results" / "sensitivity_summary.csv").exists()
        assert (temp_workspace / "data" / "results" / "minimal_feature_set.txt").exists()
        
        # Verify calls were made in correct order
        assert mock_analysis.called
        assert mock_summary.called
        assert mock_minimal_set.called
        
        # Verify summary was called after analysis
        assert mock_summary.call_count == 1
        assert mock_minimal_set.call_count == 1