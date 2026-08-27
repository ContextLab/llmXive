import pytest
import json
import csv
import tempfile
from pathlib import Path
from src.stats.robustness_interpreter import (
    load_sensitivity_analysis,
    calculate_final_robustness_index,
    generate_robustness_report
)

@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with sample sensitivity data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['threshold', 'robustness_metric'])
        writer.writerow([0.0, 0.95])
        writer.writerow([0.1, 0.92])
        writer.writerow([0.2, 0.88])
        writer.writerow([0.3, 0.85])
        writer.writerow([0.4, 0.82])
        writer.writerow([0.5, 0.80])
        writer.writerow([0.6, 0.78])
        writer.writerow([0.7, 0.75])
        writer.writerow([0.8, 0.72])
        writer.writerow([0.9, 0.70])
        writer.writerow([1.0, 0.68])
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()

@pytest.fixture
def temp_output_file():
    """Create a temporary path for output JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    temp_path.unlink()  # Delete the file, we just need the path
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()

def test_load_sensitivity_analysis(temp_csv_file):
    """Test loading sensitivity analysis CSV."""
    data = load_sensitivity_analysis(temp_csv_file)
    assert len(data) == 11
    assert data[0]['threshold'] == 0.0
    assert data[0]['robustness_metric'] == 0.95
    assert data[-1]['threshold'] == 1.0
    assert data[-1]['robustness_metric'] == 0.68

def test_load_sensitivity_analysis_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_analysis(Path('nonexistent.csv'))

def test_calculate_final_robustness_index(temp_csv_file):
    """Test calculation of final robustness index."""
    data = load_sensitivity_analysis(temp_csv_file)
    analysis = calculate_final_robustness_index(data)
    
    assert 'final_robustness_index' in analysis
    assert 'stability_status' in analysis
    assert 'min_metric' in analysis
    assert 'max_metric' in analysis
    assert 'threshold_range' in analysis
    assert 'sample_count' in analysis
    
    # Check that the index is the average of the metrics
    expected_avg = sum(d['robustness_metric'] for d in data) / len(data)
    assert abs(analysis['final_robustness_index'] - expected_avg) < 1e-6
    
    assert analysis['stability_status'] == 'STABLE'  # Since avg > 0.8
    assert analysis['min_metric'] == 0.68
    assert analysis['max_metric'] == 0.95
    assert analysis['sample_count'] == 11

def test_calculate_final_robustness_index_empty_data(temp_csv_file):
    """Test that ValueError is raised for empty data."""
    with pytest.raises(ValueError):
        calculate_final_robustness_index([])

def test_generate_robustness_report(temp_csv_file, temp_output_file):
    """Test generation of robustness report JSON."""
    data = load_sensitivity_analysis(temp_csv_file)
    generate_robustness_report(data, temp_output_file)
    
    assert temp_output_file.exists()
    
    with open(temp_output_file, 'r') as f:
        report = json.load(f)
    
    assert 'summary' in report
    assert 'metrics' in report
    assert 'interpretation' in report
    assert 'raw_data_summary' in report
    
    # Check summary fields
    assert report['summary']['final_robustness_index'] > 0
    assert report['summary']['stability_status'] in ['STABLE', 'MODERATE', 'UNSTABLE']
    assert 'production_ready' in report['summary']
    
    # Check interpretation
    assert report['interpretation']['status'] == report['summary']['stability_status']
    assert 'message' in report['interpretation']

def test_robustness_status_classification():
    """Test that robustness status is correctly classified."""
    # Create test data for different stability levels
    stable_data = [{'threshold': i, 'robustness_metric': 0.9} for i in range(10)]
    moderate_data = [{'threshold': i, 'robustness_metric': 0.6} for i in range(10)]
    unstable_data = [{'threshold': i, 'robustness_metric': 0.4} for i in range(10)]
    
    assert calculate_final_robustness_index(stable_data)['stability_status'] == 'STABLE'
    assert calculate_final_robustness_index(moderate_data)['stability_status'] == 'MODERATE'
    assert calculate_final_robustness_index(unstable_data)['stability_status'] == 'UNSTABLE'