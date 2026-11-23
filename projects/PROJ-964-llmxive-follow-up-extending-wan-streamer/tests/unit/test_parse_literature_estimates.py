import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.parse_literature_estimates import parse_literature_search_results, write_estimates_json

def test_parse_variance_extraction():
    """Test that variance values are correctly extracted from the text."""
    test_content = """
    [2] Latent Space Dynamics
    Extracted Estimates:
        variance: [0.45, 0.12]
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        result = parse_literature_search_results(temp_path)
        assert "variance_estimates" in result
        assert 0.45 in result["variance_estimates"]
        assert 0.12 in result["variance_estimates"]
        assert result["variance_stats"]["count"] == 2
    finally:
        temp_path.unlink()

def test_parse_effect_size_extraction():
    """Test that effect size values are correctly extracted."""
    test_content = """
    [3] Effect Sizes in Prosodic Turn-Taking Prediction
    Extracted Estimates:
        effect_size_d: [0.78]
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        result = parse_literature_search_results(temp_path)
        assert "effect_size_estimates" in result
        assert 0.78 in result["effect_size_estimates"]
        assert result["effect_size_stats"]["count"] == 1
    finally:
        temp_path.unlink()

def test_parse_missing_file():
    """Test that FileNotFoundError is raised for missing input."""
    with pytest.raises(FileNotFoundError):
        parse_literature_search_results(Path("nonexistent_file.txt"))

def test_write_json_output():
    """Test that the JSON output is written correctly."""
    test_data = {
        "source_file": "test.txt",
        "variance_estimates": [0.5],
        "effect_size_estimates": [0.8],
        "citations": [],
        "variance_stats": {"mean": 0.5, "count": 1},
        "effect_size_stats": {"mean": 0.8, "count": 1}
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.json"
        write_estimates_json(test_data, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["variance_estimates"] == [0.5]
        assert loaded["effect_size_estimates"] == [0.8]