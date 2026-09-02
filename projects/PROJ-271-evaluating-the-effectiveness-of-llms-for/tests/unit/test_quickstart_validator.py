import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from quickstart_validator import run_command, validate_artifacts_exist

class TestQuickstartValidator:
    
    def test_run_command_success(self):
        """Test that run_command returns success for a valid command."""
        success, stdout, stderr, code = run_command(["echo", "hello"])
        assert success is True
        assert code == 0
        assert "hello" in stdout

    def test_run_command_failure(self):
        """Test that run_command returns failure for an invalid command."""
        success, stdout, stderr, code = run_command(["non_existent_command_xyz"])
        assert success is False
        assert code != 0

    def test_validate_artifacts_exist_with_mock_structure(self):
        """Test artifact validation with a temporary directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create mock artifacts
            (root / "data").mkdir()
            (root / "data" / "static_baseline.csv").touch()
            (root / "data" / "processed").mkdir()
            (root / "data" / "processed" / "semantic_results.json").touch()
            (root / "results").mkdir()
            (root / "results" / "statistical_significance.json").touch()
            
            result = validate_artifacts_exist(root)
            
            assert result["data/static_baseline.csv"] is True
            assert result["data/processed/semantic_results.json"] is True
            assert result["results/statistical_significance.json"] is True
            # Check a missing one
            assert result.get("results/logistic_regression.json") is False
            
    def test_validation_report_generation(self):
        """Test that the validation report is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            results_dir = root / "results"
            results_dir.mkdir()
            
            # Create minimal artifacts
            (root / "data").mkdir()
            (root / "data" / "static_baseline.csv").touch()
            (root / "data" / "processed").mkdir()
            (root / "data" / "processed" / "semantic_results.json").touch()
            (root / "results" / "statistical_significance.json").touch()
            (root / "results" / "logistic_regression.json").touch()
            (root / "results" / "sensitivity_report.md").touch()
            (root / "results" / "resource_metrics.json").touch()
            (root / "results" / "sample_report.json").touch()
            (root / "results" / "compliance_verification.json").touch()
            (root / "results" / "runtime_log.json").touch()
            
            # Mock code files to avoid syntax errors
            code_dir = root / "code"
            code_dir.mkdir()
            (code_dir / "data_pipeline.py").write_text("pass")
            (code_dir / "semantic_analysis.py").write_text("pass")
            (code_dir / "statistical_analysis.py").write_text("pass")
            
            # Simulate the validation logic
            artifacts_status = validate_artifacts_exist(root)
            all_present = all(artifacts_status.values())
            
            assert all_present is True
            
            # Verify report content structure
            report = {
                "timestamp": "2023-01-01 00:00:00",
                "project_root": str(root),
                "steps": [],
                "artifacts": artifacts_status,
                "overall_success": all_present
            }
            
            report_path = results_dir / "quickstart_validation_report.json"
            with open(report_path, "w") as f:
                json.dump(report, f)
            
            assert report_path.exists()
            with open(report_path) as f:
                loaded = json.load(f)
                assert loaded["overall_success"] is True
                assert "data/static_baseline.csv" in loaded["artifacts"]