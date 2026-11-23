import os
import sys
import json
import pytest
from pathlib import Path

# Add code to path if running as standalone
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.verify_checksums import get_expected_artifacts, verify_directory_populated

class TestT038Verification:
    """
    Integration test for T038: Verify all artifacts are checksummed and stored.
    This test ensures that the pipeline has produced the required outputs.
    """

    def test_expected_artifacts_structure(self):
        """Verify the expected artifact map contains the required keys."""
        expected = get_expected_artifacts()
        
        assert "data/processed" in expected, "Missing data/processed in expected artifacts"
        assert "data/graphs" in expected, "Missing data/graphs in expected artifacts"
        assert "models" in expected, "Missing models in expected artifacts"

    def test_required_files_in_processed(self):
        """Check that specific required files are listed in the expected artifacts."""
        expected = get_expected_artifacts()
        processed_files = expected["data/processed"]
        
        required_files = [
            "ground_truth.csv",
            "features.csv",
            "threshold_sweep.json",
            "model_report.json"
        ]
        
        for req_file in required_files:
            assert req_file in processed_files, f"Missing required file {req_file} in expected artifacts"

    def test_model_files_required(self):
        """Check that model files are listed."""
        expected = get_expected_artifacts()
        model_files = expected["models"]
        
        required_models = [
            "logistic_regression.pkl",
            "random_forest.pkl",
            "decision_boundary.pkl"
        ]
        
        for req_model in required_models:
            assert req_model in model_files, f"Missing required model {req_model}"

    def test_directory_population_check_logic(self):
        """Test the logic for checking if a directory is populated."""
        # We can't guarantee the directory exists in the test environment without running the pipeline,
        # but we can test the logic of the function itself if we create a temp dir.
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Test empty directory
            assert verify_directory_populated(temp_dir, "*.json") is False

            # Test directory with file
            (temp_dir / "test.json").write_text("{}")
            assert verify_directory_populated(temp_dir, "*.json") is True
        finally:
            shutil.rmtree(temp_dir)

    def test_manifest_generation_completeness(self):
        """
        Verify that if the pipeline ran successfully, a manifest exists and is valid JSON.
        This test expects the pipeline to have been run (T038 task completion).
        """
        project_root = Path(__file__).parent.parent.parent
        manifest_path = project_root / "data" / "processed" / "checksum_manifest.json"
        
        # If the manifest doesn't exist, it means T038 script hasn't run or pipeline failed.
        # In a real CI/CD, this would be a failure state for the task.
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    data = json.load(f)
                assert isinstance(data, dict), "Manifest must be a JSON object"
                assert len(data) > 0, "Manifest must contain at least one artifact entry"
            except json.JSONDecodeError:
                pytest.fail("checksum_manifest.json is not valid JSON")
        else:
            # If the file doesn't exist, we assert that the task is considered incomplete
            # unless we are in a specific "dry-run" mode, but for T038 completion, it must exist.
            pytest.fail("checksum_manifest.json not found. Run code/scripts/verify_checksums.py first.")