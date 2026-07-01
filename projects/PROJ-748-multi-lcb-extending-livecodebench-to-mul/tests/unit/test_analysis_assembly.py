"""
Unit tests for the analysis assembly pipeline (T022).

Tests the integration of all analysis modules (T017-T021) into the final
statistical_results.json artifact.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

# Import the module under test
from analysis.run_analysis import (
    run_analysis_pipeline,
    assemble_results,
    load_execution_log
)
from config import get_results_path

@pytest.fixture
def sample_execution_log():
    """Create a sample execution log for testing."""
    return {
        "metadata": {
            "source_file": "test_execution_log.json",
            "generated_at": "2024-01-01T00:00:00",
            "total_tasks": 10
        },
        "tasks": [
            {
                "task_id": "test_task_1",
                "model": "gpt-4",
                "language": "python",
                "temperature": 0.2,
                "pass_1": 0.8,
                "release_date": "2023-01-01"
            },
            {
                "task_id": "test_task_2",
                "model": "gpt-4",
                "language": "cpp",
                "temperature": 0.2,
                "pass_1": 0.7,
                "release_date": "2023-01-01"
            },
            {
                "task_id": "test_task_3",
                "model": "gpt-4",
                "language": "java",
                "temperature": 0.6,
                "pass_1": 0.6,
                "release_date": "2023-01-01"
            }
        ]
    }

@pytest.fixture
def mock_pca_results():
    return {
        "model_scores": {"gpt-4": 0.75},
        "language_scores": {"python": 0.8, "cpp": 0.7, "java": 0.6},
        "pc1_variance": 0.85
    }

@pytest.fixture
def mock_glmm_results():
    return {
        "rankings": [
            {"model": "gpt-4", "score": 0.75, "rank": 1}
        ],
        "fixed_effects": {"temperature": 0.1}
    }

@pytest.fixture
def mock_correlation_results():
    return {
        "correlation_matrix": {"python_vs_pc1": 0.95},
        "p_values": {"python_vs_pc1": 0.01}
    }

@pytest.fixture
def mock_correction_results():
    return {
        "significant_tests": ["python_vs_pc1"],
        "bonferroni_threshold": 0.05
    }

@pytest.fixture
def mock_pairwise_results():
    return {
        "comparisons": [
            {"model1": "gpt-4", "model2": "llama-3", "p_value": 0.03}
        ]
    }

@pytest.fixture
def mock_sensitivity_results():
    return {
        "correlations_by_temperature": {0.2: 0.9, 0.6: 0.85, 1.0: 0.8},
        "variance_metrics": {"variance": 0.0025}
    }

@pytest.fixture
def mock_contamination_results():
    return {
        "excluded_tasks": 0,
        "included_tasks": 10
    }

def test_assemble_results_structure(
    sample_execution_log,
    mock_pca_results,
    mock_glmm_results,
    mock_correlation_results,
    mock_correction_results,
    mock_pairwise_results,
    mock_sensitivity_results,
    mock_contamination_results
):
    """Test that assemble_results creates the correct structure."""
    result = assemble_results(
        sample_execution_log,
        mock_pca_results,
        mock_glmm_results,
        mock_correlation_results,
        mock_correction_results,
        mock_pairwise_results,
        mock_sensitivity_results,
        mock_contamination_results
    )
    
    # Check top-level keys
    assert "metadata" in result
    assert "pca_analysis" in result
    assert "glmm_analysis" in result
    assert "correlation_analysis" in result
    assert "significance_correction" in result
    assert "pairwise_comparisons" in result
    assert "sensitivity_analysis" in result
    assert "contamination_filter" in result
    assert "summary" in result
    
    # Check summary structure
    assert "total_models_analyzed" in result["summary"]
    assert "top_ranked_model" in result["summary"]

def test_load_execution_log_existing_file(sample_execution_log):
    """Test loading an existing execution log."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_execution_log, f)
        temp_path = Path(f.name)
    
    try:
        loaded = load_execution_log(temp_path)
        assert loaded == sample_execution_log
    finally:
        temp_path.unlink()

def test_load_execution_log_missing_file():
    """Test loading a missing execution log raises error."""
    with pytest.raises(FileNotFoundError):
        load_execution_path(Path("/nonexistent/path.json"))

@patch('analysis.run_analysis.run_pca_pipeline')
@patch('analysis.run_analysis.run_glmm_pipeline')
@patch('analysis.run_analysis.run_correlation_pipeline')
@patch('analysis.run_analysis.run_correction_pipeline')
@patch('analysis.run_analysis.run_pairwise_pipeline')
@patch('analysis.run_analysis.run_sensitivity_pipeline')
@patch('analysis.run_analysis.run_contamination_pipeline')
@patch('analysis.run_analysis.load_execution_log')
def test_run_analysis_pipeline_integration(
    mock_load_log,
    mock_contamination,
    mock_sensitivity,
    mock_pairwise,
    mock_correction,
    mock_correlation,
    mock_glmm,
    mock_pca,
    sample_execution_log,
    mock_pca_results,
    mock_glmm_results,
    mock_correlation_results,
    mock_correction_results,
    mock_pairwise_results,
    mock_sensitivity_results,
    mock_contamination_results,
    tmp_path
):
    """Test the full pipeline integration with mocked dependencies."""
    # Setup mocks
    mock_load_log.return_value = sample_execution_log
    mock_pca.return_value = mock_pca_results
    mock_glmm.return_value = mock_glmm_results
    mock_correlation.return_value = mock_correlation_results
    mock_correction.return_value = mock_correction_results
    mock_pairwise.return_value = mock_pairwise_results
    mock_sensitivity.return_value = mock_sensitivity_results
    mock_contamination.return_value = mock_contamination_results
    
    execution_log_path = tmp_path / "execution_log.json"
    output_path = tmp_path / "statistical_results.json"
    log_path = tmp_path / "analysis.log"
    
    # Run pipeline
    results = run_analysis_pipeline(
        execution_log_path=execution_log_path,
        output_path=output_path,
        log_path=log_path
    )
    
    # Verify all mocks were called
    mock_load_log.assert_called_once()
    mock_pca.assert_called_once()
    mock_glmm.assert_called_once()
    mock_correlation.assert_called_once()
    mock_correction.assert_called_once()
    mock_pairwise.assert_called_once()
    mock_sensitivity.assert_called_once()
    mock_contamination.assert_called_once()
    
    # Verify output file was created
    assert output_path.exists()
    
    # Verify results structure
    assert "metadata" in results
    assert "summary" in results
    assert "top_ranked_model" in results["summary"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])