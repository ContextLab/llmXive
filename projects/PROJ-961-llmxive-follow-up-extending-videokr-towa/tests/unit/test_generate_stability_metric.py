import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to add the code directory to the path temporarily if running standalone
# but in the project context, it should be importable as analysis.generate_stability_metric
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.generate_stability_metric import calculate_robustness, load_sensitivity_results, save_stability_metric

@pytest.fixture
def sample_sensitivity_data():
    """Sample sensitivity data for testing."""
    return [
        {'threshold_hop': 2, 'p_value': 0.01, 'effect_size': 0.15, 'is_significant': True},
        {'threshold_hop': 3, 'p_value': 0.03, 'effect_size': 0.12, 'is_significant': True},
        {'threshold_hop': 4, 'p_value': 0.08, 'effect_size': 0.05, 'is_significant': False},
    ]

@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file with sensitivity results."""
    csv_path = tmp_path / "sensitivity_thresholds.csv"
    content = """threshold_hop,p_value,effect_size,is_significant
2,0.01,0.15,True
3,0.03,0.12,True
4,0.08,0.05,False
"""
    csv_path.write_text(content)
    return csv_path

class TestCalculateRobustness:
    def test_pass_condition(self, sample_sensitivity_data):
        """Test that PASS is returned when count >= 2."""
        result = calculate_robustness(sample_sensitivity_data, alpha=0.05)
        
        assert result['count_significant_thresholds'] == 2
        assert result['total_thresholds_tested'] == 3
        assert result['robustness_status'] == 'PASS'
        assert result['alpha'] == 0.05

    def test_fail_condition(self, sample_sensitivity_data):
        """Test that FAIL is returned when count < 2."""
        # Modify data to have only 1 significant
        modified_data = [
            {'threshold_hop': 2, 'p_value': 0.01, 'effect_size': 0.15, 'is_significant': True},
            {'threshold_hop': 3, 'p_value': 0.06, 'effect_size': 0.12, 'is_significant': False},
            {'threshold_hop': 4, 'p_value': 0.08, 'effect_size': 0.05, 'is_significant': False},
        ]
        result = calculate_robustness(modified_data, alpha=0.05)
        
        assert result['count_significant_thresholds'] == 1
        assert result['robustness_status'] == 'FAIL'

    def test_all_significant(self, sample_sensitivity_data):
        """Test when all thresholds are significant."""
        all_sig_data = [
            {'threshold_hop': 2, 'p_value': 0.01, 'effect_size': 0.15, 'is_significant': True},
            {'threshold_hop': 3, 'p_value': 0.02, 'effect_size': 0.12, 'is_significant': True},
            {'threshold_hop': 4, 'p_value': 0.04, 'effect_size': 0.05, 'is_significant': True},
        ]
        result = calculate_robustness(all_sig_data, alpha=0.05)
        
        assert result['count_significant_thresholds'] == 3
        assert result['robustness_status'] == 'PASS'

    def test_edge_case_boundary(self, sample_sensitivity_data):
        """Test boundary condition where p_value equals alpha."""
        boundary_data = [
            {'threshold_hop': 2, 'p_value': 0.05, 'effect_size': 0.15, 'is_significant': False}, # Not < 0.05
            {'threshold_hop': 3, 'p_value': 0.049, 'effect_size': 0.12, 'is_significant': True},
            {'threshold_hop': 4, 'p_value': 0.051, 'effect_size': 0.05, 'is_significant': False},
        ]
        result = calculate_robustness(boundary_data, alpha=0.05)
        
        assert result['count_significant_thresholds'] == 1
        assert result['robustness_status'] == 'FAIL'

class TestSaveStabilityMetric:
    def test_save_creates_file(self, tmp_path, sample_sensitivity_data):
        """Test that save_stability_metric creates the JSON file correctly."""
        output_path = tmp_path / "stability_metric.json"
        metric_data = calculate_robustness(sample_sensitivity_data)
        
        save_stability_metric(metric_data, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['robustness_status'] == 'PASS'
        assert saved_data['count_significant_thresholds'] == 2

class TestLoadSensitivityResults:
    def test_load_from_csv(self, temp_csv_file):
        """Test loading sensitivity results from a CSV file."""
        # Mock the get_project_root to return the temp directory
        with patch('analysis.generate_stability_metric.get_project_root') as mock_root:
            mock_root.return_value = temp_csv_file.parent
            # We need to patch the path construction inside the function
            # The function constructs root / "data" / "processed" / "sensitivity_thresholds.csv"
            # So we need to ensure the mock root leads to the temp file
            # This is tricky because the function builds the path.
            # Let's mock the file reading directly instead of relying on get_project_root
            pass
        
        # Direct test of the file reading logic by mocking the path
        import analysis.generate_stability_metric as module
        
        original_get_path = module.get_path
        
        def mock_get_path(key):
            if key == "sensitivity_thresholds":
                return str(temp_csv_file)
            return original_get_path(key)
        
        with patch.object(module, 'get_path', side_effect=mock_get_path):
            # We also need to mock get_project_root to avoid path issues
            with patch.object(module, 'get_project_root') as mock_root:
                mock_root.return_value = temp_csv_file.parent
                
                # The function uses root / "data" / "processed" / "sensitivity_thresholds.csv"
                # But we mocked get_path to return the temp file directly? 
                # No, the function doesn't use get_path, it constructs the path manually.
                # Let's just test the logic by creating a temporary file in the expected location
                # relative to a mock root.
                pass

        # Simpler approach: create the file in a temp dir and mock get_project_root
        # to return that temp dir.
        temp_root = temp_csv_file.parent
        # The expected path is temp_root / "data" / "processed" / "sensitivity_thresholds.csv"
        # But our temp_csv_file is directly in temp_root.
        # Let's restructure the test.
        
        # Create a proper temp directory structure
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            data_processed = tmp_path / "data" / "processed"
            data_processed.mkdir(parents=True)
            csv_path = data_processed / "sensitivity_thresholds.csv"
            csv_path.write_text("""threshold_hop,p_value,effect_size,is_significant
2,0.01,0.15,True
3,0.03,0.12,True
4,0.08,0.05,False
""")
            
            with patch('analysis.generate_stability_metric.get_project_root') as mock_root:
                mock_root.return_value = tmp_path
                
                results = load_sensitivity_results()
                
                assert len(results) == 3
                assert results[0]['threshold_hop'] == 2
                assert results[0]['p_value'] == 0.01
                assert results[0]['is_significant'] == True
                
                assert results[1]['threshold_hop'] == 3
                assert results[1]['p_value'] == 0.03
                assert results[1]['is_significant'] == True
                
                assert results[2]['threshold_hop'] == 4
                assert results[2]['p_value'] == 0.08
                assert results[2]['is_significant'] == False
                
        # Test missing file
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            with patch('analysis.generate_stability_metric.get_project_root') as mock_root:
                mock_root.return_value = tmp_path
                with pytest.raises(FileNotFoundError):
                    load_sensitivity_results()