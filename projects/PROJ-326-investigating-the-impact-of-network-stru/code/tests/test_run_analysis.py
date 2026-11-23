"""
Tests for the master analysis script (T037).
Verifies that the script aggregates results and produces the final JSON.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from code.src.analysis.run_analysis import (
    main,
    load_results,
    run_regression_analysis,
    run_anova_analysis,
    run_sensitivity_analysis,
    generate_plots,
    aggregate_final_results
)


@pytest.fixture
def mock_simulation_results():
    """Mock data simulating the output of T029."""
    return [
        {
            "network_id": "net_001",
            "topology_class": "erdos_renyi",
            "clustering_coefficient": 0.15,
            "diffusion_rate": 0.45,
            "seed": 123
        },
        {
            "network_id": "net_002",
            "topology_class": "watts_strogatz",
            "clustering_coefficient": 0.65,
            "diffusion_rate": 0.82,
            "seed": 124
        },
        {
            "network_id": "net_003",
            "topology_class": "barabasi_albert",
            "clustering_coefficient": 0.30,
            "diffusion_rate": 0.55,
            "seed": 125
        },
        {
            "network_id": "net_004",
            "topology_class": "erdos_renyi",
            "clustering_coefficient": 0.12,
            "diffusion_rate": 0.41,
            "seed": 126
        },
        {
            "network_id": "net_005",
            "topology_class": "watts_strogatz",
            "clustering_coefficient": 0.70,
            "diffusion_rate": 0.88,
            "seed": 127
        }
    ]


@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_results_file_not_found(temp_output_dir):
    """Test that load_results raises FileNotFoundError if file is missing."""
    config = {"paths": {"simulation_results": str(temp_output_dir / "missing.json")}}
    with pytest.raises(FileNotFoundError):
        load_results(config)


def test_load_results_success(mock_simulation_results, temp_output_dir):
    """Test loading results from a valid JSON file."""
    results_path = temp_output_dir / "simulation_results.json"
    with open(results_path, 'w') as f:
        json.dump(mock_simulation_results, f)
    
    config = {"paths": {"simulation_results": str(results_path)}}
    results = load_results(config)
    
    assert len(results) == 5
    assert results[0]["topology_class"] == "erdos_renyi"


@patch('code.src.analysis.run_analysis.fit_linear_regression')
@patch('code.src.analysis.run_analysis.fit_polynomial_regression')
@patch('code.src.analysis.run_analysis.compare_models')
@patch('code.src.analysis.run_analysis.analyze_correlation')
def test_run_regression_analysis(
    mock_corr, mock_compare, mock_poly, mock_linear, mock_simulation_results
):
    """Test regression analysis execution."""
    # Setup mocks
    mock_linear.return_value = MagicMock(slope=0.5, intercept=0.1, r_squared=0.8, p_value=0.01)
    mock_poly.return_value = MagicMock(degree=2, coefficients=[1, 2, 3], r_squared=0.85, p_value=0.005)
    mock_compare.return_value = {"best": "polynomial"}
    mock_corr.return_value = {"r": 0.9, "p": 0.001}
    
    config = {}
    result = run_regression_analysis(mock_simulation_results, config)
    
    assert result["status"] == "completed"
    assert result["sample_size"] == 5
    assert "linear_regression" in result
    assert "polynomial_regression" in result


@patch('code.src.analysis.run_analysis.run_anova_on_diffusion_by_topology')
@patch('code.src.analysis.run_analysis.apply_multiple_comparison_correction')
def test_run_anova_analysis(mock_correct, mock_anova, mock_simulation_results):
    """Test ANOVA analysis execution."""
    mock_anova.return_value = {
        "f_statistic": 12.5,
        "p_value": 0.001,
        "groups_compared": ["erdos_renyi", "watts_strogatz", "barabasi_albert"],
        "pairwise_results": []
    }
    mock_correct.return_value = {
        "method": "bonferroni",
        "corrected_p_values": [0.003],
        "is_significant": True
    }
    
    config = {"analysis": {"correction_method": "bonferroni"}}
    result = run_anova_analysis(mock_simulation_results, config)
    
    assert result["status"] == "completed"
    assert result["f_statistic"] == 12.5
    assert result["is_significant_after_correction"] is True


@patch('code.src.analysis.run_analysis.run_sensitivity_sweep')
def test_run_sensitivity_analysis(mock_sweep, mock_simulation_results):
    """Test sensitivity analysis execution."""
    mock_sweep.return_value = {
        "status": "completed",
        "cutoffs_tested": 5,
        "results": []
    }
    
    config = {}
    result = run_sensitivity_analysis(mock_simulation_results, config)
    
    assert result["status"] == "completed"
    assert result["cutoffs_tested"] == 5


@patch('code.src.analysis.run_analysis.generate_all_figures')
def test_generate_plots(mock_gen_figures, mock_simulation_results, temp_output_dir):
    """Test plot generation."""
    mock_gen_figures.return_value = [
        {"name": "scatter.png", "path": str(temp_output_dir / "scatter.png")},
        {"name": "heatmap.png", "path": str(temp_output_dir / "heatmap.png")}
    ]
    
    config = {"paths": {"figures": str(temp_output_dir)}}
    result = generate_plots(config, mock_simulation_results)
    
    assert result["status"] == "completed"
    assert len(result["figures_generated"]) == 2


def test_aggregate_final_results(mock_simulation_results):
    """Test aggregation of all analysis outputs."""
    reg_out = {"status": "completed", "data": 1}
    anova_out = {"status": "completed", "data": 2}
    sens_out = {"status": "completed", "data": 3}
    plots_out = {"status": "completed", "data": 4}
    
    final = aggregate_final_results(reg_out, anova_out, sens_out, plots_out, "run_123", {})
    
    assert final["run_id"] == "run_123"
    assert final["summary"]["regression"] == "completed"
    assert "detailed_results" in final
    assert "regression" in final["detailed_results"]


@patch('code.src.analysis.run_analysis.load_config')
@patch('code.src.analysis.run_analysis.load_results')
@patch('code.src.analysis.run_analysis.run_regression_analysis')
@patch('code.src.analysis.run_analysis.run_anova_analysis')
@patch('code.src.analysis.run_analysis.run_sensitivity_analysis')
@patch('code.src.analysis.run_analysis.generate_plots')
@patch('code.src.analysis.run_analysis.aggregate_final_results')
@patch('code.src.analysis.run_analysis.ensure_data_directory')
@patch('builtins.open')
def test_main_success(
    mock_open, mock_ensure_dir, mock_agg, mock_gen_plots, mock_sens, mock_anova, 
    mock_reg, mock_load_results, mock_load_config, mock_simulation_results, temp_output_dir
):
    """Test the full main execution flow."""
    # Setup mocks
    mock_load_config.return_value = {"paths": {"simulation_results": "dummy", "figures": str(temp_output_dir)}}
    mock_load_results.return_value = mock_simulation_results
    mock_reg.return_value = {"status": "completed", "linear_regression": {"r_squared": 0.8}}
    mock_anova.return_value = {"status": "completed", "p_value": 0.01}
    mock_sens.return_value = {"status": "completed", "cutoffs_tested": 5}
    mock_gen_plots.return_value = {"status": "completed", "figures_generated": []}
    mock_agg.return_value = {"run_id": "test", "summary": {}}
    
    output_path = temp_output_dir / "final_results.json"
    
    # Run main
    exit_code = main(["--output", str(output_path)])
    
    assert exit_code == 0
    mock_open.assert_called_once()
    # Verify JSON was written
    call_args = mock_open.call_args
    assert call_args[0][0] == output_path
    assert call_args[1]['mode'] == 'w'