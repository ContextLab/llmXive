import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.evaluation.summary_generator import (
    load_json_safe, 
    aggregate_results, 
    generate_markdown_report, 
    main
)

class TestSummaryGenerator:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    def test_load_json_safe_found(self, temp_dir):
        file_path = temp_dir / "test.json"
        data = {"key": "value"}
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_json_safe(file_path)
        assert result == data

    def test_load_json_safe_not_found(self, temp_dir):
        file_path = temp_dir / "missing.json"
        result = load_json_safe(file_path)
        assert result is None

    def test_load_json_safe_invalid(self, temp_dir):
        file_path = temp_dir / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("{ invalid json }")
        
        result = load_json_safe(file_path)
        assert result is None

    @patch('src.evaluation.summary_generator.get_data_path')
    @patch('src.evaluation.summary_generator.get_project_root')
    @patch('src.evaluation.summary_generator.load_json_safe')
    def test_aggregate_results_success(self, mock_load, mock_root, mock_data_path, temp_dir):
        # Setup mocks
        mock_root.return_value = temp_dir
        mock_data_path.return_value = temp_dir / "results"
        
        # Mock linearity success
        mock_load.side_effect = [
            {"linearity_valid": True, "correlation_coefficient": 0.85, "max_error": 0.02}, # linearity
            {"mean_success_rate": 0.75, "bh_rejected_count": 2, "power_estimate": 0.85}, # stats
            {"status": "success"} # fetch status
        ]

        result = aggregate_results()
        
        assert result["status"] == "SUCCESS"
        assert result["linearity"]["valid"] is True
        assert result["statistics"]["mean_success_rate"] == 0.75

    @patch('src.evaluation.summary_generator.get_data_path')
    @patch('src.evaluation.summary_generator.get_project_root')
    @patch('src.evaluation.summary_generator.load_json_safe')
    def test_aggregate_results_failure(self, mock_load, mock_root, mock_data_path, temp_dir):
        mock_root.return_value = temp_dir
        mock_data_path.return_value = temp_dir / "results"
        
        # Mock linearity failure
        mock_load.side_effect = [
            {"linearity_valid": False, "correlation_coefficient": 0.2, "max_error": 0.1},
            {"mean_success_rate": 0.5, "bh_rejected_count": 0, "power_estimate": 0.4},
            {"status": "failed"}
        ]

        result = aggregate_results()
        
        assert result["status"] == "FAILED"
        assert "Linearity hypothesis" in result["limitations"][0]

    def test_generate_markdown_report(self, temp_dir):
        summary = {
            "status": "SUCCESS",
            "linearity": {"valid": True, "correlation": 0.9, "max_error": 0.01, "status": "PASS"},
            "statistics": {
                "mean_success_rate": 0.8,
                "bh_rejected_count": 1,
                "power_estimate": 0.9,
                "primary_significance": {"strategy_A": 0.03},
                "sensitivity_significance": {"k_5": 0.04}
            },
            "limitations": [],
            "warnings": ["Test warning"],
            "data_integrity": "Verified"
        }
        
        output_path = temp_dir / "summary.md"
        generate_markdown_report(summary, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Key Findings" in content
        assert "Linearity Validation" in content
        assert "Statistical Significance" in content
        assert "Test warning" in content

    @patch('src.evaluation.summary_generator.aggregate_results')
    @patch('src.evaluation.summary_generator.generate_markdown_report')
    @patch('src.evaluation.summary_generator.get_project_root')
    def test_main_success(self, mock_root, mock_gen, mock_agg, temp_dir):
        mock_root.return_value = temp_dir
        mock_agg.return_value = {"status": "SUCCESS"}
        
        exit_code = main()
        assert exit_code == 0
        mock_gen.assert_called_once()

    @patch('src.evaluation.summary_generator.aggregate_results')
    @patch('src.evaluation.summary_generator.get_project_root')
    def test_main_exception(self, mock_root, mock_agg, temp_dir):
        mock_root.return_value = temp_dir
        mock_agg.side_effect = Exception("Critical Error")
        
        exit_code = main()
        assert exit_code == 1