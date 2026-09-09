"""
Unit tests for the Stability Verification Module (T028b).
"""
import json
import tempfile
from pathlib import Path
import pytest

from stability_verification import load_sensitivity_table, calculate_stability_metric, verify_stability

@pytest.fixture
def mock_sensitivity_data():
    """Fixture providing mock sensitivity analysis data."""
    return [
        {"threshold": 0.01, "p_value": 0.003, "coefficient": 0.5},
        {"threshold": 0.05, "p_value": 0.042, "coefficient": 0.48},
        {"threshold": 0.10, "p_value": 0.15, "coefficient": 0.45}
    ]

@pytest.fixture
def temp_json_file(mock_sensitivity_data):
    """Fixture creating a temporary JSON file with mock data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_sensitivity_data, f)
        path = Path(f.name)
    yield path
    path.unlink()

@pytest.fixture
def temp_csv_file(mock_sensitivity_data):
    """Fixture creating a temporary CSV file with mock data."""
    import pandas as pd
    df = pd.DataFrame(mock_sensitivity_data)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        path = Path(f.name)
    yield path
    path.unlink()

class TestLoadSensitivityTable:
    def test_load_json_success(self, temp_json_file, mock_sensitivity_data):
        result = load_sensitivity_table(temp_json_file)
        assert result == mock_sensitivity_data
        assert len(result) == 3

    def test_load_csv_success(self, temp_csv_file, mock_sensitivity_data):
        result = load_sensitivity_table(temp_csv_file)
        # CSV loads as dicts, floats might be slightly different but values should match
        assert len(result) == 3
        assert result[0]['threshold'] == 0.01
        
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_sensitivity_table(Path("/nonexistent/path.json"))

    def test_unsupported_format(self, temp_json_file):
        # Rename to .txt to simulate unsupported format
        txt_file = temp_json_file.with_suffix('.txt')
        temp_json_file.rename(txt_file)
        try:
            with pytest.raises(ValueError):
                load_sensitivity_table(txt_file)
        finally:
            txt_file.rename(temp_json_file) # Restore for cleanup

class TestCalculateStabilityMetric:
    def test_stable_at_two_thresholds(self, mock_sensitivity_data):
        result = calculate_stability_metric(mock_sensitivity_data, p_threshold=0.05)
        assert result['significant_count'] == 2
        assert result['total_count'] == 3
        assert result['stability_ratio'] == pytest.approx(2/3)
        assert "Stable at 2/3 thresholds" in result['summary']

    def test_all_significant(self):
        data = [
            {"threshold": 0.01, "p_value": 0.001},
            {"threshold": 0.05, "p_value": 0.002}
        ]
        result = calculate_stability_metric(data, p_threshold=0.05)
        assert result['significant_count'] == 2
        assert result['stability_ratio'] == 1.0

    def test_none_significant(self):
        data = [
            {"threshold": 0.01, "p_value": 0.10},
            {"threshold": 0.05, "p_value": 0.20}
        ]
        result = calculate_stability_metric(data, p_threshold=0.05)
        assert result['significant_count'] == 0
        assert result['stability_ratio'] == 0.0

    def test_empty_list(self):
        result = calculate_stability_metric([], p_threshold=0.05)
        assert result['significant_count'] == 0
        assert result['total_count'] == 0
        assert result['stability_ratio'] == 0.0
        assert "No sensitivity results found" in result['summary']

    def test_invalid_p_value_handling(self):
        data = [
            {"threshold": 0.01, "p_value": "invalid"},
            {"threshold": 0.05, "p_value": 0.01}
        ]
        result = calculate_stability_metric(data, p_threshold=0.05)
        # Should handle the error gracefully, likely counting only the valid one
        assert result['total_count'] == 2
        # The invalid one should not count as significant
        assert result['significant_count'] == 1

class TestVerifyStability:
    def test_full_flow_success(self, temp_json_file, tmp_path):
        output_path = tmp_path / "stability.json"
        result = verify_stability(temp_json_file, output_path)
        
        assert result['status'] == 'success'
        assert result['significant_count'] == 2
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        assert saved_result['summary'] == result['summary']

    def test_full_flow_missing_file(self, tmp_path):
        missing_path = tmp_path / "missing.json"
        output_path = tmp_path / "stability.json"
        
        result = verify_stability(missing_path, output_path)
        
        assert result['status'] == 'failed'
        assert "not found" in result['summary'].lower()
        assert output_path.exists() # Should still write the failure report