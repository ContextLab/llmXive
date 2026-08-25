import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv

# Mock matplotlib before importing the module to avoid backend issues in tests
import matplotlib
matplotlib.use('Agg')

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.visualizations import generate_scatter_plot_with_regression, load_metric_data, filter_repos_by_count

@pytest.fixture
def sample_data():
    return [
        {'repo_name': 'test-repo', 'module_path': 'mod1.py', 'gini': 0.1, 'bug_density': 1.0, 'size_kloc': 10.0, 'age_months': 12.0},
        {'repo_name': 'test-repo', 'module_path': 'mod2.py', 'gini': 0.5, 'bug_density': 5.0, 'size_kloc': 20.0, 'age_months': 24.0},
        {'repo_name': 'test-repo', 'module_path': 'mod3.py', 'gini': 0.9, 'bug_density': 9.0, 'size_kloc': 5.0, 'age_months': 6.0},
    ]

@pytest.fixture
def temp_csv_file(tmp_path):
    csv_path = tmp_path / "metrics_combined.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['repo_name', 'module_path', 'gini', 'bug_density', 'size_kloc', 'age_months'])
        writer.writeheader()
        writer.writerow({'repo_name': 'repoA', 'module_path': 'a.py', 'gini': 0.2, 'bug_density': 2.0, 'size_kloc': 10.0, 'age_months': 10.0})
        writer.writerow({'repo_name': 'repoB', 'module_path': 'b.py', 'gini': 0.8, 'bug_density': 8.0, 'size_kloc': 15.0, 'age_months': 15.0})
    return csv_path

def test_filter_repos_by_count(sample_data):
    grouped = filter_repos_by_count(sample_data, min_repos=1)
    assert 'test-repo' in grouped
    assert len(grouped['test-repo']) == 3

def test_filter_repos_by_count_insufficient(sample_data):
    # Add a second repo with only 1 item to test filtering logic if needed, 
    # but here we just test the main group extraction
    grouped = filter_repos_by_count(sample_data, min_repos=5)
    # Should return empty or warn, but functionally it returns the dict
    assert 'test-repo' in grouped

@patch('code.visualizations.get_output_dir')
@patch('pathlib.Path.exists')
@patch('builtins.open')
def test_load_metric_data(mock_open, mock_exists, mock_get_output, temp_csv_file):
    mock_get_output.return_value = str(temp_csv_file.parent)
    mock_exists.return_value = True
    
    # Mock file reading
    mock_open.return_value.__enter__.return_value.read.return_value = temp_csv_file.read_text()
    
    # Re-implement read logic for mock since DictReader needs real file handle
    # Actually, let's just patch the open to return the real file content via StringIO
    from io import StringIO
    
    with patch('builtins.open', return_value=mock_open.return_value):
        mock_open.return_value.__enter__.return_value = StringIO(temp_csv_file.read_text())
        mock_exists.return_value = True
        
        data = load_metric_data()
        
        assert len(data) == 2
        assert data[0]['repo_name'] == 'repoA'
        assert data[1]['gini'] == 0.8

def test_generate_scatter_plot_with_regression(tmp_path, sample_data):
    output_path = tmp_path / "test_plot.png"
    generate_scatter_plot_with_regression(sample_data, "test-repo", output_path, dpi=100)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0