"""
Tests for code/reports/generate_final_report.py
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from reports.generate_final_report import (
    load_json_file,
    load_manifest_file,
    determine_mode,
    generate_markdown_report,
    main
)
from config import get_artifacts_path, get_data_path


class TestLoadJsonFile:
    def test_load_existing_json(self, tmp_path):
        """Test loading an existing JSON file."""
        # Setup
        reports_dir = tmp_path / "artifacts" / "reports"
        reports_dir.mkdir(parents=True)
        test_file = reports_dir / "test.json"
        test_data = {"key": "value", "number": 123}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Mock get_artifacts_path to return tmp_path
        with patch('reports.generate_final_report.get_artifacts_path', return_value=tmp_path):
            result = load_json_file("test.json")
            assert result == test_data

    def test_load_missing_json(self, tmp_path):
        """Test loading a missing JSON file returns None."""
        with patch('reports.generate_final_report.get_artifacts_path', return_value=tmp_path):
            result = load_json_file("nonexistent.json")
            assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON returns None and logs error."""
        reports_dir = tmp_path / "artifacts" / "reports"
        reports_dir.mkdir(parents=True)
        test_file = reports_dir / "invalid.json"
        with open(test_file, 'w') as f:
            f.write("{ invalid json }")
        
        with patch('reports.generate_final_report.get_artifacts_path', return_value=tmp_path):
            result = load_json_file("invalid.json")
            assert result is None


class TestLoadManifestFile:
    def test_load_existing_yaml(self, tmp_path):
        """Test loading an existing YAML manifest."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        manifest_file = data_dir / "data_manifest.yaml"
        test_data = {"source": "SIMULATED", "sample_count": 150}
        with open(manifest_file, 'w') as f:
            yaml.dump(test_data, f)
        
        with patch('reports.generate_final_report.get_data_path', return_value=tmp_path / "data"):
            result = load_manifest_file()
            assert result == test_data

    def test_load_missing_manifest(self, tmp_path):
        """Test loading a missing manifest returns None."""
        with patch('reports.generate_final_report.get_data_path', return_value=tmp_path / "data"):
            result = load_manifest_file()
            assert result is None


class TestDetermineMode:
    def test_simulated_mode(self):
        """Test detection of SIMULATED mode."""
        manifest = {"source": "SIMULATED"}
        assert determine_mode(manifest) == "SIMULATION_MODE"
        
        manifest = {"source": "SIMULATED_DATA"}
        assert determine_mode(manifest) == "SIMULATION_MODE"

    def test_real_data_mode(self):
        """Test detection of REAL_DATA mode."""
        manifest = {"source": "REAL_DATA"}
        assert determine_mode(manifest) == "REAL_DATA_MODE"
        
        manifest = {"source": "NCBI_SRA"}
        assert determine_mode(manifest) == "REAL_DATA_MODE"
        
        manifest = {"source": "METABOLIGHTS"}
        assert determine_mode(manifest) == "REAL_DATA_MODE"

    def test_unknown_mode(self):
        """Test detection of unknown mode."""
        assert determine_mode(None) == "UNKNOWN_MODE"
        assert determine_mode({}) == "UNKNOWN_MODE"
        assert determine_mode({"source": "UNKNOWN"}) == "UNKNOWN_MODE"


class TestGenerateMarkdownReport:
    def test_generates_header_with_simulation_warning(self):
        """Test that the report includes the Simulation Mode warning."""
        report = generate_markdown_report({}, {}, {}, {}, "SIMULATION_MODE")
        assert "## ⚠️ SIMULATION MODE" in report
        assert "synthetic data" in report.lower()
        assert "do not represent biological findings" in report.lower()

    def test_generates_header_with_real_data(self):
        """Test that the report includes Real Data indicator."""
        report = generate_markdown_report({}, {}, {}, {}, "REAL_DATA_MODE")
        assert "## ✅ REAL DATA MODE" in report
        assert "real biological data" in report.lower()

    def test_includes_metrics_section(self):
        """Test that metrics are included in the report."""
        metrics = {"cv_metrics": {"accuracy": 0.95, "auc_r2": 0.92}}
        report = generate_markdown_report(metrics, {}, {}, {}, "SIMULATION_MODE")
        assert "## 1. Model Performance (Cross-Validation)" in report
        assert "Accuracy" in report
        assert "0.95" in report

    def test_includes_permutation_p_value(self):
        """Test that permutation p-value is included and status is calculated."""
        holdout = {"observed_metric": 0.85, "permutation_p_value": 0.01}
        report = generate_markdown_report({}, holdout, {}, {}, "SIMULATION_MODE")
        assert "## 3. Hold-out Set Validation (Permutation Test)" in report
        assert "0.01" in report
        assert "✅ Statistically Significant" in report

    def test_includes_biomarker_summary(self):
        """Test that biomarker summary is included."""
        biomarker = {"snps_count": 15, "metabolites_count": 12, "thresholds_tested": [0.01, 0.05]}
        report = generate_markdown_report({}, {}, {}, biomarker, "SIMULATION_MODE")
        assert "## 5. Biomarker Discovery Summary" in report
        assert "15" in report
        assert "✅ Met" in report

    def test_includes_biomarker_failure(self):
        """Test that biomarker failure is reported if counts are low."""
        biomarker = {"snps_count": 5, "metabolites_count": 3}
        report = generate_markdown_report({}, {}, {}, biomarker, "SIMULATION_MODE")
        assert "❌ Not Met" in report


class TestMain:
    def test_main_executes_successfully(self, tmp_path):
        """Test that main() runs without error and creates the report file."""
        # Setup directories
        artifacts_dir = tmp_path / "artifacts" / "reports"
        artifacts_dir.mkdir(parents=True)
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        
        # Create dummy input files
        with open(artifacts_dir / "metrics.json", 'w') as f:
            json.dump({"cv_metrics": {"accuracy": 0.8}}, f)
        with open(artifacts_dir / "holdout_metrics.json", 'w') as f:
            json.dump({"permutation_p_value": 0.03}, f)
        with open(artifacts_dir / "external_metrics.json", 'w') as f:
            json.dump({"accuracy": 0.82}, f)
        with open(artifacts_dir / "biomarker_summary.json", 'w') as f:
            json.dump({"snps_count": 12, "metabolites_count": 10, "thresholds_tested": [0.05]}, f)
        with open(data_dir / "data_manifest.yaml", 'w') as f:
            yaml.dump({"source": "SIMULATED"}, f)
        
        # Patch paths
        with patch('reports.generate_final_report.get_artifacts_path', return_value=tmp_path / "artifacts"):
            with patch('reports.generate_final_report.get_data_path', return_value=tmp_path / "data"):
                # Run main
                result = main()
                
                # Verify return code
                assert result == 0
                
                # Verify output file exists
                output_file = artifacts_dir / "final_validation_report.md"
                assert output_file.exists()
                
                # Verify content
                content = output_file.read_text()
                assert "Final Validation Report" in content
                assert "SIMULATION MODE" in content
                assert "0.03" in content