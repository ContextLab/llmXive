import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add project root to path for imports if running from tests/
# This assumes the test runner is invoked from the project root or code/
# but we import relative to the package structure defined in the API surface.
try:
    from report_generator import (
        load_metrics_data,
        extract_metric_values,
        calculate_summary_stats,
        ensure_figures_dir,
        generate_all_plots,
        generate_markdown_report
    )
except ImportError:
    # Fallback for direct execution if path isn't set up
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from report_generator import (
        load_metrics_data,
        extract_metric_values,
        calculate_summary_stats,
        ensure_figures_dir,
        generate_all_plots,
        generate_markdown_report
    )

@pytest.fixture
def sample_data():
    return [
        {"id": 1, "cyclomatic_complexity": 5.0, "halstead_volume": 100.0, "branch_coverage_pct": 80.0, "pass_rate": 1},
        {"id": 2, "cyclomatic_complexity": 10.0, "halstead_volume": 200.0, "branch_coverage_pct": 60.0, "pass_rate": 0},
        {"id": 3, "cyclomatic_complexity": 3.0, "halstead_volume": 50.0, "branch_coverage_pct": 90.0, "pass_rate": 1},
    ]

@pytest.fixture
def temp_metrics_file(sample_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_metrics_data(temp_metrics_file, sample_data):
    result = load_metrics_data(temp_metrics_file)
    assert len(result) == len(sample_data)
    assert result[0]["id"] == 1

def test_extract_metric_values(sample_data):
    values = extract_metric_values(sample_data, "cyclomatic_complexity")
    assert values == [5.0, 10.0, 3.0]
    
    values_coverage = extract_metric_values(sample_data, "branch_coverage_pct")
    assert values_coverage == [80.0, 60.0, 90.0]

def test_extract_metric_values_missing_key(sample_data):
    # Add an item with missing key
    data = sample_data + [{"id": 4}]
    values = extract_metric_values(data, "cyclomatic_complexity")
    assert len(values) == 3  # Should skip the missing one

def test_calculate_summary_stats():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    stats = calculate_summary_stats(values)
    assert stats["mean"] == 3.0
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["median"] == 3.0

def test_calculate_summary_stats_empty():
    stats = calculate_summary_stats([])
    assert stats["mean"] == 0
    assert stats["std"] == 0

@patch('report_generator.os.makedirs')
def test_ensure_figures_dir(mock_makedirs):
    result = ensure_figures_dir()
    assert result == "results/figures"
    mock_makedirs.assert_called_once_with("results/figures", exist_ok=True)

@patch('report_generator.HAS_MATPLOTLIB', False)
def test_generate_all_plots_no_matplotlib(sample_data, tmp_path):
    plots = generate_all_plots(sample_data, str(tmp_path))
    assert plots == {}

@patch('report_generator.HAS_MATPLOTLIB', True)
@patch('report_generator.plot_histogram')
@patch('report_generator.plot_boxplot')
def test_generate_all_plots_with_mocking(mock_box, mock_hist, sample_data, tmp_path):
    mock_hist.return_value = "hist.png"
    mock_box.return_value = "box.png"
    
    plots = generate_all_plots(sample_data, str(tmp_path))
    
    # Should attempt to plot for each metric (3 metrics * 2 plot types)
    assert len(plots) == 6
    assert "cyclomatic_complexity_hist" in plots

@patch('report_generator.HAS_JINJA', False)
def test_generate_markdown_report_fallback(tmp_path, sample_data):
    output_file = os.path.join(tmp_path, "report.md")
    # Pass empty stats and plots for fallback test
    generate_markdown_report(sample_data, {}, None, output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "Summary Statistics" in content
    assert "cyclomatic_complexity" in content
    assert "Overall Pass Rate" in content

@patch('report_generator.HAS_JINJA', True)
@patch('report_generator.jinja2.Environment')
def test_generate_markdown_report_jinja(mock_env_class, tmp_path, sample_data):
    # Setup mock template
    mock_template = MagicMock()
    mock_template.render.return_value = "Mocked Report Content"
    
    mock_env = MagicMock()
    mock_env.from_string.return_value = mock_template
    mock_env_class.return_value = mock_env
    
    output_file = os.path.join(tmp_path, "report.md")
    
    # Mock plots to avoid needing actual image files for this test
    plots = {
        "cyclomatic_complexity_hist": "hist.png",
        "cyclomatic_complexity_box": "box.png"
    }
    
    # Calculate stats to pass to function
    stats = {
        "cyclomatic_complexity": calculate_summary_stats([5.0, 10.0, 3.0]),
        "halstead_volume": calculate_summary_stats([100.0, 200.0, 50.0]),
        "branch_coverage_pct": calculate_summary_stats([80.0, 60.0, 90.0]),
        "pass_rate": calculate_summary_stats([1.0, 0.0, 1.0])
    }
    
    generate_markdown_report(sample_data, plots, stats, output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "Mocked Report Content" in content
    assert "hist.png" in content  # Check if figure reference is included in the rendered template

@patch('report_generator.plot_histogram')
@patch('report_generator.plot_boxplot')
def test_plot_histogram_call(mock_box, mock_hist, tmp_path):
    mock_hist.return_value = "test_hist.png"
    mock_box.return_value = "test_box.png"
    
    # Just verify the functions are called correctly by the wrapper
    plots = generate_all_plots([{"cyclomatic_complexity": 5.0}], str(tmp_path))
    
    # Verify plot_histogram was called
    assert mock_hist.called
    # Verify plot_boxplot was called
    assert mock_box.called

def test_extract_metric_values_handles_non_numeric():
    data = [
        {"id": 1, "val": 10.0},
        {"id": 2, "val": "not a number"}, # Should be skipped or handled
        {"id": 3, "val": 20.0}
    ]
    values = extract_metric_values(data, "val")
    # Depending on implementation, this might return [10.0, 20.0] or raise
    # Assuming the implementation skips non-numeric or filters them
    assert len(values) == 2
    assert 10.0 in values
    assert 20.0 in values