"""
Unit tests for the report generation module (T036).
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.report import generate_report, load_json_file

class TestReportGeneration:
    
    def test_load_json_file_success(self, tmp_path):
        """Test loading a valid JSON file."""
        data = {"key": "value", "number": 42}
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_json_file(file_path)
        assert result == data
        assert result["number"] == 42

    def test_load_json_file_not_found(self, tmp_path):
        """Test loading a non-existent JSON file raises FileNotFoundError."""
        file_path = tmp_path / "non_existent.json"
        with pytest.raises(FileNotFoundError):
            load_json_file(file_path)

    def test_generate_report_with_valid_inputs(self, tmp_path):
        """Test full report generation with valid input files."""
        # Setup input files
        metrics_data = {
            "coverage_rate": 0.85,
            "details": {
                "total_records": 1000,
                "merged_records": 850,
                "year_range": "2000-2020"
            }
        }
        sensitivity_data = {
            "full_model": {
                "regime_type_coef": 0.15,
                "regime_type_pval": 0.03
            },
            "no_gdp_model": {
                "regime_type_coef": 0.12,
                "regime_type_pval": 0.04
            },
            "percent_change": 20.0
        }
        metadata_data = {
            "is_associational": True
        }

        input_dir = tmp_path / "inputs"
        input_dir.mkdir()
        
        metrics_path = input_dir / "metrics.json"
        sensitivity_path = input_dir / "sensitivity.json"
        metadata_path = input_dir / "metadata.json"

        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f)
        with open(sensitivity_path, 'w') as f:
            json.dump(sensitivity_data, f)
        with open(metadata_path, 'w') as f:
            json.dump(metadata_data, f)

        output_path = tmp_path / "output" / "report.md"

        # Execute
        generate_report(metrics_path, sensitivity_path, metadata_path, output_path)

        # Verify
        assert output_path.exists()
        content = output_path.read_text()
        
        # Check for key sections
        assert "Data Coverage" in content
        assert "Regression Analysis" in content
        assert "Associational" in content
        assert "0.85" in content # Coverage rate
        assert "0.15" in content # Coefficient
        assert "20.0%" in content # Percent change

    def test_generate_report_associational_flag_false(self, tmp_path):
        """Test report generation when is_associational is False."""
        metrics_data = {"coverage_rate": 0.5, "details": {}}
        sensitivity_data = {"full_model": {}, "no_gdp_model": {}, "percent_change": 0}
        metadata_data = {"is_associational": False}

        input_dir = tmp_path / "inputs"
        input_dir.mkdir()
        
        metrics_path = input_dir / "metrics.json"
        sensitivity_path = input_dir / "sensitivity.json"
        metadata_path = input_dir / "metadata.json"

        with open(metrics_path, 'w') as f: json.dump(metrics_data, f)
        with open(sensitivity_path, 'w') as f: json.dump(sensitivity_data, f)
        with open(metadata_path, 'w') as f: json.dump(metadata_data, f)

        output_path = tmp_path / "output" / "report.md"

        generate_report(metrics_path, sensitivity_path, metadata_path, output_path)
        
        content = output_path.read_text()
        assert "causal" in content.lower()
        assert "⚠️" not in content # Warning icon should be absent

    def test_generate_report_missing_input(self, tmp_path):
        """Test that missing input files raise an error."""
        input_dir = tmp_path / "inputs"
        input_dir.mkdir()
        output_path = tmp_path / "output" / "report.md"
        
        # Only create one file, leave others missing
        metrics_path = input_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump({"coverage_rate": 0.5}, f)

        sensitivity_path = input_dir / "sensitivity.json"
        metadata_path = input_dir / "metadata.json"

        with pytest.raises(FileNotFoundError):
            generate_report(metrics_path, sensitivity_path, metadata_path, output_path)