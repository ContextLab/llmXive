import pytest
import json
import tempfile
from pathlib import Path
from src.cli.calculate_metrics import calculate_missing_release_proportion, write_metrics_to_file, load_dependencies_from_json

def test_calculate_missing_release_proportion_with_missing_data():
    """Test calculation when some dependencies have missing release dates."""
    dependencies = [
        {"name": "pkg1", "release_date": "2023-01-01"},
        {"name": "pkg2", "release_date": None},
        {"name": "pkg3", "release_date": ""},
        {"name": "pkg4", "release_date": "2023-06-01"},
        {"name": "pkg5"}  # Missing key entirely
    ]
    
    result = calculate_missing_release_proportion(dependencies)
    
    assert result["total_dependencies"] == 5
    assert result["missing_release_metadata"] == 3
    assert abs(result["proportion"] - 0.6) < 0.001

def test_calculate_missing_release_proportion_no_missing():
    """Test calculation when all dependencies have release dates."""
    dependencies = [
        {"name": "pkg1", "release_date": "2023-01-01"},
        {"name": "pkg2", "release_date": "2023-06-01"},
        {"name": "pkg3", "release_date": "2024-01-01"}
    ]
    
    result = calculate_missing_release_proportion(dependencies)
    
    assert result["total_dependencies"] == 3
    assert result["missing_release_metadata"] == 0
    assert result["proportion"] == 0.0

def test_calculate_missing_release_proportion_empty_list():
    """Test calculation with empty dependency list."""
    result = calculate_missing_release_proportion([])
    
    assert result["total_dependencies"] == 0
    assert result["missing_release_metadata"] == 0
    assert result["proportion"] == 0.0

def test_write_metrics_to_file():
    """Test writing metrics to a JSON file."""
    metrics = {
        "total_dependencies": 100,
        "missing_release_metadata": 25,
        "proportion": 0.25,
        "timestamp": "2024-01-01T00:00:00"
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metrics.json"
        write_metrics_to_file(metrics, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded_metrics = json.load(f)
        
        assert loaded_metrics == metrics

def test_load_dependencies_from_json():
    """Test loading dependencies from a JSON file."""
    test_data = {
        "dependencies": [
            {"name": "pkg1", "release_date": "2023-01-01"},
            {"name": "pkg2", "release_date": None}
        ]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test.json"
        with open(input_path, 'w') as f:
            json.dump(test_data, f)
        
        loaded = load_dependencies_from_json(input_path)
        
        assert len(loaded) == 2
        assert loaded[0]["name"] == "pkg1"
        assert loaded[1]["name"] == "pkg2"