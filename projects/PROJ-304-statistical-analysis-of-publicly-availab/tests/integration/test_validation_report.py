"""
Integration test for T034: Generate final comparison report.

Verifies that the validation report is generated correctly and contains
the expected structure and data from previous tasks.
"""
import json
import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logger import get_project_root
from validation_report import generate_final_report, save_report

class TestValidationReport:
    """Integration tests for the final validation report generation."""

    @pytest.fixture
    def project_root(self):
        """Fixture to get the project root."""
        return get_project_root()

    @pytest.fixture
    def report_path(self, project_root):
        """Fixture to get the expected report path."""
        return project_root / "data" / "processed" / "validation_report.json"

    def test_report_generation_structure(self, project_root):
        """
        Test that the generated report has the correct top-level structure.
        """
        # Ensure prerequisite files exist (mocked or from previous runs)
        # In a real scenario, T026, T031, T032, T033 should be complete.
        # Here we test the structure of the generated report.
        
        report = generate_final_report()
        
        assert isinstance(report, dict), "Report should be a dictionary"
        assert "report_metadata" in report, "Missing report_metadata"
        assert "best_model" in report, "Missing best_model"
        assert "success_criteria" in report, "Missing success_criteria"
        assert "cross_validation" in report, "Missing cross_validation"
        assert "permutation_test" in report, "Missing permutation_test"
        assert "recommendations" in report, "Missing recommendations"
        assert isinstance(report["recommendations"], list), "Recommendations should be a list"

    def test_report_metadata_fields(self, project_root):
        """
        Test that the report metadata contains required fields.
        """
        report = generate_final_report()
        metadata = report["report_metadata"]
        
        assert "task_id" in metadata, "Missing task_id in metadata"
        assert metadata["task_id"] == "T034", "Incorrect task_id"
        assert "user_story" in metadata, "Missing user_story in metadata"
        assert metadata["user_story"] == "US3", "Incorrect user_story"
        assert "description" in metadata, "Missing description in metadata"
        assert "generated_at" in metadata, "Missing generated_at in metadata"

    def test_report_file_creation(self, project_root, report_path):
        """
        Test that the report file is actually created on disk.
        """
        # Generate and save the report
        report = generate_final_report()
        saved_path = save_report(report)
        
        assert saved_path.exists(), f"Report file not created at {saved_path}"
        assert saved_path == report_path, f"Report saved to wrong path: {saved_path}"
        
        # Verify it's valid JSON
        with open(saved_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report == report, "Saved report does not match generated report"

    def test_best_model_structure(self, project_root):
        """
        Test that the best_model section has the expected structure.
        """
        report = generate_final_report()
        best_model = report["best_model"]
        
        # If model results are missing, it should contain an error key
        if "error" in best_model:
            assert isinstance(best_model["error"], str), "Error message should be a string"
        else:
            # Otherwise, it should have model_name and details
            assert "model_name" in best_model, "Missing model_name in best_model"
            assert "details" in best_model, "Missing details in best_model"
            assert "selection_criteria" in best_model, "Missing selection_criteria in best_model"

    def test_success_criteria_structure(self, project_root):
        """
        Test that the success_criteria section has the expected structure.
        """
        report = generate_final_report()
        sc = report["success_criteria"]
        
        if "error" in sc:
            assert isinstance(sc["error"], str), "Error message should be a string"
        else:
            # Expecting a boolean for all_criteria_met
            assert "all_criteria_met" in sc, "Missing all_criteria_met in success_criteria"
            assert isinstance(sc["all_criteria_met"], bool), "all_criteria_met should be a boolean"

    def test_cross_validation_structure(self, project_root):
        """
        Test that the cross_validation section has the expected structure.
        """
        report = generate_final_report()
        cv = report["cross_validation"]
        
        if "error" in cv:
            assert isinstance(cv["error"], str), "Error message should be a string"
        else:
            # Should contain at least a status or models
            assert "status" in cv or "models" in cv, "Cross-validation section is empty or malformed"

    def test_permutation_test_structure(self, project_root):
        """
        Test that the permutation_test section has the expected structure.
        """
        report = generate_final_report()
        perm = report["permutation_test"]
        
        assert "status" in perm or "p_value" in perm or "note" in perm, \
            "Permutation test section is malformed"

    def test_recommendations_logic(self, project_root):
        """
        Test that recommendations are generated based on success criteria.
        """
        report = generate_final_report()
        recommendations = report["recommendations"]
        
        assert len(recommendations) > 0, "Should have at least one recommendation"
        
        # If all criteria are met, there should be a deployment recommendation
        sc = report["success_criteria"]
        if sc.get("all_criteria_met", False):
            deployment_recs = [r for r in recommendations if "deploy" in r.lower()]
            assert len(deployment_recs) > 0, "Missing deployment recommendation when criteria are met"