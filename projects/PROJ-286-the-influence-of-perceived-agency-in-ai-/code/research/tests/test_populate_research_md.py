import json
import tempfile
from pathlib import Path
import pytest
from code.research.populate_research_md import populate_research_md, validate_power_calculation_json, load_json_file

def test_validate_power_calculation_json_valid():
    data = {
        'params': {'effect_size': 0.25, 'alpha': 0.05, 'power': 0.80},
        'results': {'required_n': 128, 'calculated_n': 150}
    }
    assert validate_power_calculation_json(data) is True

def test_validate_power_calculation_json_missing_params():
    data = {
        'results': {'required_n': 128, 'calculated_n': 150}
    }
    assert validate_power_calculation_json(data) is False

def test_validate_power_calculation_json_missing_results():
    data = {
        'params': {'effect_size': 0.25, 'alpha': 0.05, 'power': 0.80}
    }
    assert validate_power_calculation_json(data) is False

def test_validate_power_calculation_json_missing_key_in_params():
    data = {
        'params': {'effect_size': 0.25, 'alpha': 0.05},
        'results': {'required_n': 128, 'calculated_n': 150}
    }
    assert validate_power_calculation_json(data) is False

def test_validate_power_calculation_json_missing_key_in_results():
    data = {
        'params': {'effect_size': 0.25, 'alpha': 0.05, 'power': 0.80},
        'results': {'required_n': 128}
    }
    assert validate_power_calculation_json(data) is False

def test_populate_research_md_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_file = tmpdir_path / "power.json"
        output_file = tmpdir_path / "research.md"
        
        data = {
            'params': {'effect_size': 0.25, 'alpha': 0.05, 'power': 0.80},
            'results': {'required_n': 128, 'calculated_n': 150}
        }
        
        with open(input_file, 'w') as f:
            json.dump(data, f)
        
        populate_research_md(input_file, output_file)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "| Effect Size | Alpha | Target Power | Required N | Calculated N |" in content
        assert "0.25" in content
        assert "0.05" in content
        assert "0.80" in content
        assert "128" in content
        assert "150" in content

def test_populate_research_md_nonexistent_input():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_file = tmpdir_path / "nonexistent.json"
        output_file = tmpdir_path / "research.md"
        
        with pytest.raises(FileNotFoundError):
            populate_research_md(input_file, output_file)