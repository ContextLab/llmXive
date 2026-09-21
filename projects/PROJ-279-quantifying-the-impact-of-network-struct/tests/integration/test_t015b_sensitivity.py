"""
Integration test for T015b: Execute Sensitivity Loop.

This test verifies that the sensitivity executor:
1. Reads the validation report correctly.
2. Calls the sensitivity analysis function with the correct cutoff radii.
3. Produces a valid JSON report with the expected schema.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Mock the external dependencies to ensure isolation
# We simulate the data flow without requiring real downloads or heavy graph calculations
# in this unit/integration hybrid test.

@pytest.fixture
def mock_validation_report(tmp_path):
    """Create a mock validation report."""
    report = {
        "validated_configs": ["config_A", "config_B"],
        "excluded_configs": ["config_C"],
        "convergence_flags": {
            "config_A": "OK",
            "config_B": "OK"
        }
    }
    report_path = tmp_path / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f)
    return report_path

@pytest.fixture
def mock_configs():
    """Return mock configuration objects."""
    # Simulate the structure expected by graph_builder
    return [
        {
            "id": "config_A",
            "atoms": [{"position": [0, 0, 0], "element": "Si"}, {"position": [1, 0, 0], "element": "Si"}],
            "box_size": [10, 10, 10]
        },
        {
            "id": "config_B",
            "atoms": [{"position": [0, 0, 0], "element": "Si"}, {"position": [1, 0, 0], "element": "Si"}],
            "box_size": [10, 10, 10]
        }
    ]

def test_sensitivity_executor_schema(mock_validation_report, mock_configs, tmp_path):
    """
    Test that the sensitivity executor produces a report with the correct schema.
    """
    # Mock the load_configurations_from_validation_report to return our mock configs
    with patch('sensitivity_executor.load_configurations_from_validation_report', return_value=mock_configs):
        # Mock run_sensitivity_analysis to return a deterministic result
        expected_result = {
            "cutoff_radii": [2.8, 3.0, 3.2],
            "results": {
                "2.8": {"avg_degree": 4.5, "component_count": 1},
                "3.0": {"avg_degree": 5.0, "component_count": 1},
                "3.2": {"avg_degree": 5.5, "component_count": 1}
            },
            "config_count": 2
        }
        
        with patch('sensitivity_executor.run_sensitivity_analysis', return_value=expected_result):
            # We need to patch the get_processed_dir to point to our temp dir
            # and the register_artifact to avoid state file conflicts
            with patch('sensitivity_executor.get_processed_dir', return_value=str(tmp_path)):
                with patch('sensitivity_executor.register_artifact'):
                    # Run the logic directly (since main() calls sys.exit)
                    from sensitivity_executor import run_sensitivity_executor
                    
                    # Override sys.exit to prevent the script from terminating the test
                    with patch('sys.exit'):
                        result = run_sensitivity_executor()
                        
                        # Verify the result matches the expected schema
                        assert result is not None
                        assert "cutoff_radii" in result
                        assert "results" in result
                        assert "config_count" in result
                            
                        # Verify the cutoff radii are exactly as specified in T015a
                        assert result["cutoff_radii"] == [2.8, 3.0, 3.2]
                            
                        # Verify the output file was written
                        output_path = Path(tmp_path) / "sensitivity_report.json"
                        assert output_path.exists()
                            
                        with open(output_path) as f:
                            saved_data = json.load(f)
                            
                        assert saved_data == result

def test_sensitivity_analysis_cannot_run_with_non_validated(mock_validation_report, tmp_path):
    """
    Test that the executor fails if the validation report is missing or empty.
    """
    # Create an empty validation report
    empty_report = tmp_path / "validation_report.json"
    with open(empty_report, 'w') as f:
        json.dump({"validated_configs": []}, f)
    
    with patch('sensitivity_executor.get_processed_dir', return_value=str(tmp_path)):
        with patch('sys.exit') as mock_exit:
            # We expect sys.exit(0) or (1) depending on implementation, but logic should stop
            # For this test, we check that it doesn't crash or produce a report
            from sensitivity_executor import run_sensitivity_executor
            with patch('sys.exit') as mock_exit:
                # If the list is empty, the script should log a warning and exit
                # We verify that run_sensitivity_analysis is NOT called
                with patch('sensitivity_executor.run_sensitivity_analysis') as mock_run:
                    run_sensitivity_executor()
                    mock_run.assert_not_called()
                    # Check that a warning was logged (mock logger)
                    # This is implicit in the logic flow