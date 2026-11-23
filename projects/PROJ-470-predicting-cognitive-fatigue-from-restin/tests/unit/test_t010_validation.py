import os
import sys
import json
import tempfile
import shutil
import pytest

# Ensure we can import from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from check_sample_size import check_sample_size, write_validation_report, load_config

class TestT010Validation:
    """Tests for T010: Data Validation Gate."""

    def test_missing_manifest_exits_with_error(self, capsys):
        """Test that missing manifest causes exit code 1 and clear error."""
        # Use a non-existent path
        report = check_sample_size(manifest_path="data/raw/non_existent_manifest.json")
        
        assert report["status"] == "failed"
        assert any("Download manifest not found" in err for err in report["errors"])
        assert len(report["errors"]) == 1

    def test_insufficient_sample_size_exits_with_error(self, capsys):
        """Test that N < 30 causes exit code 1 and clear error."""
        # Create a temporary manifest with only 10 participants
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "manifest.json")
            # Create a list of 10 dummy participants
            participants = [f"subject_{i}.npz" for i in range(10)]
            with open(manifest_path, 'w') as f:
                json.dump(participants, f)
            
            report = check_sample_size(manifest_path=manifest_path, min_n=30)
            
            assert report["status"] == "failed"
            assert any("Sample size N < 30" in err for err in report["errors"])
            assert report["actual_n"] == 10

    def test_missing_variables_exits_with_error(self, capsys):
        """Test that missing required variables cause exit code 1 and list available vars."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "manifest.json")
            # Create a manifest pointing to a real .npz file that lacks required vars
            # We'll create a dummy npz file with only 'random_data'
            import numpy as np
            dummy_npz_path = os.path.join(tmpdir, "dummy.npz")
            np.savez(dummy_npz_path, random_data=np.array([1, 2, 3]))
            
            # Manifest points to this dummy file
            participants = [{"path": dummy_npz_path}]
            with open(manifest_path, 'w') as f:
                json.dump(participants, f)
            
            report = check_sample_size(manifest_path=manifest_path, min_n=5) # Pass N check
            
            assert report["status"] == "failed"
            assert any("Dataset lacks required variables" in err for err in report["errors"])
            assert any("Available variables:" in err for err in report["errors"])
            assert "missing_variables" in report
            assert "eeg_data" in report["missing_variables"] or "fatigue_rating" in report["missing_variables"]

    def test_valid_manifest_and_vars_succeeds(self, capsys):
        """Test that a valid manifest with sufficient N and variables passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "manifest.json")
            output_path = os.path.join(tmpdir, "report.json")
            
            # Create a dummy npz file with required variables
            import numpy as np
            dummy_npz_path = os.path.join(tmpdir, "valid_data.npz")
            # We need 'eeg_data' and 'fatigue_rating' keys to pass the strict check
            np.savez(dummy_npz_path, eeg_data=np.array([1, 2, 3]), fatigue_rating=np.array([1, 0, 1]))
            
            # Manifest with enough participants (using the same file for simplicity in test)
            # In reality, T009 would create a manifest with unique files per subject
            participants = [
                {"path": dummy_npz_path},
                {"path": dummy_npz_path}, # Duplicate for N count, acceptable for unit test
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path},
                {"path": dummy_npz_path}
            ]
            
            with open(manifest_path, 'w') as f:
                json.dump(participants, f)
            
            report = check_sample_size(manifest_path=manifest_path, min_n=30)
            
            assert report["status"] == "passed"
            assert report["actual_n"] == 30
            assert report["missing_variables"] == []
            
            # Verify report writing
            write_validation_report(report, output_path)
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            assert saved_report["status"] == "passed"

    def test_validation_report_written_on_success(self, tmp_path):
        """Assert that validation_report.json is created on success."""
        manifest_path = tmp_path / "manifest.json"
        output_path = tmp_path / "validation_report.json"
        
        import numpy as np
        dummy_npz = tmp_path / "data.npz"
        np.savez(dummy_npz, eeg_data=[1], fatigue_rating=[1])
        
        # 30 entries
        participants = [{"path": str(dummy_npz)} for _ in range(30)]
        with open(manifest_path, 'w') as f:
            json.dump(participants, f)
        
        report = check_sample_size(manifest_path=str(manifest_path), min_n=30)
        write_validation_report(report, str(output_path))
        
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["status"] == "passed"
        assert "actual_n" in data
        assert data["actual_n"] == 30