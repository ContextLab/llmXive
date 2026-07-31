import json
import os
import sys
from pathlib import Path
import hashlib
import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from analysis.generate_decomposition_results import (
    load_json_safe,
    aggregate_decomposition_results,
    main
)
from utils.state_manager import load_state, calculate_sha256


class TestDecompositionResultsGeneration:
    """Integration tests for T025: Generate decomposition_results.json"""

    @pytest.fixture
    def project_root(self):
        return Path(__file__).resolve().parent.parent.parent

    @pytest.fixture
    def output_file_path(self, project_root):
        return project_root / "data" / "processed" / "decomposition_results.json"

    @pytest.fixture
    def state_file_path(self, project_root):
        return project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

    def test_load_json_safe_handles_missing_file(self):
        """Test that load_json_safe returns None for missing files."""
        result = load_json_safe("nonexistent_file.json")
        assert result is None

    def test_load_json_safe_parses_valid_json(self, tmp_path):
        """Test that load_json_safe correctly parses valid JSON."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        result = load_json_safe(str(test_file))
        assert result == test_data

    def test_aggregate_decomposition_results_returns_dict(self, project_root):
        """Test that aggregate_decomposition_results returns a dictionary."""
        # This test will run the actual analysis if data exists
        processed_data_path = project_root / "data" / "processed" / "tag_monthly_frequencies.json"
        
        if not processed_data_path.exists():
            pytest.skip("Processed data not available. Run T013 first.")

        results = aggregate_decomposition_results()
        assert isinstance(results, dict)
        assert len(results) > 0  # Should have at least one tag

    def test_decomposition_results_contains_required_fields(self, project_root):
        """Test that decomposition results contain Ljung-Box and Rayleigh test results."""
        processed_data_path = project_root / "data" / "processed" / "tag_monthly_frequencies.json"
        
        if not processed_data_path.exists():
            pytest.skip("Processed data not available. Run T013 first.")

        results = aggregate_decomposition_results()

        # Check that we have results for at least one tag
        first_tag = next(iter(results))
        tag_data = results[first_tag]

        # Verify Ljung-Box test result exists
        assert "ljung_box" in tag_data, "Ljung-Box test result missing"
        ljung_box = tag_data["ljung_box"]
        assert "statistic" in ljung_box, "Ljung-Box statistic missing"
        assert "p_value" in ljung_box, "Ljung-Box p-value missing"
        assert "is_independent" in ljung_box, "Ljung-Box independence flag missing"

        # Verify Rayleigh test result exists
        assert "rayleigh_test" in tag_data, "Rayleigh test result missing"
        rayleigh = tag_data["rayleigh_test"]
        assert "statistic" in rayleigh, "Rayleigh statistic missing"
        assert "p_value" in rayleigh, "Rayleigh p-value missing"
        assert "alignment" in rayleigh, "Rayleigh alignment flag missing"

    def test_main_creates_output_file(self, project_root, output_file_path):
        """Test that main() creates the decomposition_results.json file."""
        processed_data_path = project_root / "data" / "processed" / "tag_monthly_frequencies.json"
        
        if not processed_data_path.exists():
            pytest.skip("Processed data not available. Run T013 first.")

        # Remove existing file if present
        if output_file_path.exists():
            output_file_path.unlink()

        # Run main
        main()

        # Verify file was created
        assert output_file_path.exists(), "decomposition_results.json was not created"

    def test_main_updates_state_file(self, project_root, output_file_path, state_file_path):
        """Test that main() updates the state file with the new artifact hash."""
        processed_data_path = project_root / "data" / "processed" / "tag_monthly_frequencies.json"
        
        if not processed_data_path.exists():
            pytest.skip("Processed data not available. Run T013 first.")

        if not state_file_path.exists():
            pytest.skip("State file not available. Run T009 first.")

        # Run main
        main()

        # Verify state file was updated
        assert state_file_path.exists(), "State file was not updated"
        
        state = load_state(str(state_file_path))
        assert "artifacts" in state, "State file missing artifacts section"
        
        # Check that decomposition_results.json is in the state
        artifact_found = False
        for artifact in state["artifacts"]:
            if "decomposition_results.json" in artifact.get("path", ""):
                artifact_found = True
                assert "hash" in artifact, "Artifact missing hash"
                assert "timestamp" in artifact, "Artifact missing timestamp"
                break

        assert artifact_found, "decomposition_results.json not found in state file"

    def test_output_file_has_valid_json(self, project_root, output_file_path):
        """Test that the output file contains valid JSON."""
        if not output_file_path.exists():
            pytest.skip("Output file not available. Run main() first.")

        with open(output_file_path, 'r') as f:
            try:
                data = json.load(f)
                assert isinstance(data, dict), "Output should be a dictionary"
            except json.JSONDecodeError as e:
                pytest.fail(f"Output file contains invalid JSON: {e}")

    def test_output_file_hash_matches_calculated(self, project_root, output_file_path):
        """Test that the stored hash matches the calculated hash."""
        if not output_file_path.exists():
            pytest.skip("Output file not available. Run main() first.")

        state_file_path = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
        if not state_file_path.exists():
            pytest.skip("State file not available.")

        # Calculate actual hash
        actual_hash = calculate_sha256(str(output_file_path))

        # Get stored hash from state
        state = load_state(str(state_file_path))
        stored_hash = None
        for artifact in state["artifacts"]:
            if "decomposition_results.json" in artifact.get("path", ""):
                stored_hash = artifact.get("hash")
                break

        if stored_hash:
            assert stored_hash == actual_hash, f"Hash mismatch: stored={stored_hash}, calculated={actual_hash}"
        else:
            pytest.skip("Hash not found in state file for verification.")