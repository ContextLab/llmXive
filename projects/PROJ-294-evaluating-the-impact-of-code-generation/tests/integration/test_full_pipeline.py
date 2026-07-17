import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

from report_generator import main, load_metrics_data, generate_all_plots

@pytest.fixture
def mock_data_dir():
    """Create a temporary directory structure with mock data."""
    temp_dir = tempfile.mkdtemp()
    
    # Create necessary directories
    data_dir = os.path.join(temp_dir, "data", "analysis")
    os.makedirs(data_dir)
    results_dir = os.path.join(temp_dir, "results", "figures")
    os.makedirs(results_dir)
    
    # Create mock metrics.json
    mock_data = [
        {"id": 1, "cyclomatic_complexity": 5.0, "halstead_volume": 100.0, "branch_coverage_pct": 80.0, "pass_rate": 1},
        {"id": 2, "cyclomatic_complexity": 10.0, "halstead_volume": 200.0, "branch_coverage_pct": 60.0, "pass_rate": 0},
        {"id": 3, "cyclomatic_complexity": 3.0, "halstead_volume": 50.0, "branch_coverage_pct": 90.0, "pass_rate": 1},
        {"id": 4, "cyclomatic_complexity": 15.0, "halstead_volume": 300.0, "branch_coverage_pct": 40.0, "pass_rate": 0},
    ]
    
    metrics_path = os.path.join(data_dir, "metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(mock_data, f)
    
    # Create mock statistical results
    stats_path = os.path.join(temp_dir, "results", "statistical_analysis.json")
    with open(stats_path, 'w') as f:
        json.dump({
            "wilcoxon_complexity": {"statistic": 10.5, "pvalue": 0.03},
            "mcnemar_pass_rate": {"statistic": 4.0, "pvalue": 0.045}
        }, f)
    
    yield temp_dir, metrics_path, stats_path, results_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@patch('report_generator.HAS_MATPLOTLIB', False)
@patch('report_generator.HAS_JINJA', True)
def test_full_pipeline_no_plots(mock_jinja, mock_plt, mock_data_dir):
    """Test the full pipeline flow without actual plotting capabilities."""
    temp_dir, metrics_path, stats_path, results_dir = mock_data_dir
    
    # Change working directory to temp_dir to simulate project root
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Ensure paths are relative to temp_dir
        # We need to patch the hardcoded paths in main or ensure they resolve correctly
        # For this test, we'll assume the script runs from project root
        
        # Run the main function
        # Note: In a real scenario, we might need to adjust paths or mock os.getcwd
        # Here we simulate the file existence checks
        
        # Verify input files exist
        assert os.path.exists("data/analysis/metrics.json")
        assert os.path.exists("results/statistical_analysis.json")
        
        # Load data to verify
        data = load_metrics_data("data/analysis/metrics.json")
        assert len(data) == 4
        
        # Generate plots (should return empty dict since matplotlib is disabled)
        plots = generate_all_plots(data, "results/figures")
        assert plots == {}
        
        # Generate report
        output_path = "results_report.md"
        from report_generator import generate_markdown_report
        from report_generator import calculate_summary_stats, extract_metric_values, load_statistical_results
        
        stats_results = load_statistical_results("results/statistical_analysis.json")
        generate_markdown_report(data, plots, stats_results, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "Research Results" in content
        assert "Summary Statistics" in content
        assert "cyclomatic_complexity" in content
        assert "5.0" in content or "10.0" in content # Check for data presence

    finally:
        os.chdir(original_cwd)

@patch('report_generator.HAS_MATPLOTLIB', True)
@patch('report_generator.HAS_JINJA', True)
def test_full_pipeline_with_plots(mock_jinja, mock_plt, mock_data_dir):
    """Test the full pipeline with plotting enabled (mocked)."""
    temp_dir, metrics_path, stats_path, results_dir = mock_data_dir
    
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Mock the actual plotting functions to avoid creating real images
        with patch('report_generator.plot_histogram') as mock_hist, \
             patch('report_generator.plot_boxplot') as mock_box:
             
            mock_hist.return_value = "hist.png"
            mock_box.return_value = "box.png"
            
            data = load_metrics_data("data/analysis/metrics.json")
            plots = generate_all_plots(data, "results/figures")
            
            # Verify plots were generated (mocked)
            assert len(plots) == 6 # 3 metrics * 2 types
            
            # Generate report
            output_path = "results_report.md"
            from report_generator import generate_markdown_report, load_statistical_results
            
            stats_results = load_statistical_results("results/statistical_analysis.json")
            generate_markdown_report(data, plots, stats_results, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "hist.png" in content
            assert "box.png" in content
            assert "Research Results" in content

    finally:
        os.chdir(original_cwd)