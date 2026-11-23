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

def test_load_sensitivity_analysis_valid():
    """Test loading a valid sensitivity analysis CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=['threshold', 'robustness_metric'])
        writer.writeheader()
        writer.writerow({'threshold': 0.1, 'robustness_metric': 95.0})
        writer.writerow({'threshold': 0.2, 'robustness_metric': 92.5})
        writer.writerow({'threshold': 0.3, 'robustness_metric': 88.0})
        temp_path = f.name

    try:
        data = load_sensitivity_analysis(temp_path)
        assert len(data) == 3
        assert data[0]['threshold'] == 0.1
        assert data[0]['robustness_metric'] == 95.0
    finally:
        Path(temp_path).unlink()

def test_load_sensitivity_analysis_empty():
    """Test loading an empty CSV raises error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("threshold,robustness_metric\n")
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            load_sensitivity_analysis(temp_path)
    finally:
        Path(temp_path).unlink()

def test_load_sensitivity_analysis_file_not_found():
    """Test loading non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_analysis("non_existent_file.csv")

def test_calculate_final_robustness_index():
    """Test calculation of final robustness index."""
    data = [
        {'threshold': 0.1, 'robustness_metric': 100.0},
        {'threshold': 0.2, 'robustness_metric': 100.0},
        {'threshold': 0.3, 'robustness_metric': 100.0}
    ]
    
    result = calculate_final_robustness_index(data)
    
    assert result['final_robustness_index'] == 100.0
    assert result['is_stable'] is True
    assert result['has_instability'] is False

def test_calculate_final_robustness_index_unstable():
    """Test calculation when stability is low."""
    data = [
        {'threshold': 0.1, 'robustness_metric': 40.0},
        {'threshold': 0.2, 'robustness_metric': 45.0},
        {'threshold': 0.3, 'robustness_metric': 50.0}
    ]
    
    result = calculate_final_robustness_index(data)
    
    assert result['final_robustness_index'] == 45.0
    assert result['is_stable'] is False
    assert result['has_instability'] is True

def test_generate_robustness_report(tmp_path):
    """Test full report generation."""
    input_file = tmp_path / "sensitivity.csv"
    output_file = tmp_path / "robustness.json"
    
    with open(input_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['threshold', 'robustness_metric'])
        writer.writeheader()
        writer.writerow({'threshold': 0.1, 'robustness_metric': 95.0})
        writer.writerow({'threshold': 0.2, 'robustness_metric': 95.0})
    
    report = generate_robustness_report(str(input_file), str(output_file))
    
    assert output_file.exists()
    assert report['summary']['status'] == 'STABLE'
    assert 'final_robustness_index' in report['metrics']
    
    # Verify JSON content on disk
    with open(output_file, 'r') as f:
        disk_report = json.load(f)
        
    assert disk_report['summary']['status'] == 'STABLE'