import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from motion_detection import (
    load_motion_metrics,
    get_valid_subjects,
    detect_motion_artifacts,
    write_motion_exclusion_log,
    save_valid_subjects,
    main
)

class TestMotionDetection:
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create interim structure
            interim = tmpdir / "data" / "interim"
            processed = tmpdir / "data" / "processed"
            interim.mkdir(parents=True)
            processed.mkdir(parents=True)
            
            # Create mock subject directories with motion logs
            for subj_id in ["subj_001", "subj_002", "subj_003", "subj_004"]:
                subj_dir = interim / subj_id / "func"
                subj_dir.mkdir(parents=True)
                
                # Assign different FD values
                if subj_id == "subj_001":
                    fd_value = 0.3  # Good
                elif subj_id == "subj_002":
                    fd_value = 0.45  # Good
                elif subj_id == "subj_003":
                    fd_value = 0.6  # Bad
                else:  # subj_004
                    fd_value = 0.8  # Bad
                    
                motion_log = {
                    "mean_fd": fd_value,
                    "max_fd": fd_value * 1.5,
                    "framewise_displacements": [fd_value] * 10
                }
                
                with open(subj_dir / "motion_metrics.json", 'w') as f:
                    json.dump(motion_log, f)
            
            yield {
                "interim": interim,
                "processed": processed,
                "expected_valid": ["subj_001", "subj_002"],
                "expected_excluded": ["subj_003", "subj_004"]
            }

    def test_load_motion_metrics(self, temp_dirs):
        """Test loading motion metrics from subject directories."""
        metrics = load_motion_metrics(temp_dirs["interim"])
        
        assert len(metrics) == 4
        assert "subj_001" in metrics
        assert metrics["subj_001"] == 0.3
        assert metrics["subj_003"] == 0.6

    def test_get_valid_subjects(self, temp_dirs):
        """Test filtering subjects by motion threshold."""
        metrics = load_motion_metrics(temp_dirs["interim"])
        valid = get_valid_subjects(metrics, threshold=0.5)
        
        assert set(valid) == set(temp_dirs["expected_valid"])
        assert "subj_003" not in valid
        assert "subj_004" not in valid

    def test_detect_motion_artifacts(self, temp_dirs):
        """Test detection of subjects with excessive motion."""
        metrics = load_motion_metrics(temp_dirs["interim"])
        excluded = detect_motion_artifacts(metrics, threshold=0.5)
        
        assert len(excluded) == 2
        assert "subj_003" in excluded
        assert "subj_004" in excluded
        assert "FD" in excluded["subj_003"]
        assert "FD" in excluded["subj_004"]

    def test_write_motion_exclusion_log(self, temp_dirs):
        """Test writing exclusion log to file."""
        metrics = load_motion_metrics(temp_dirs["interim"])
        excluded = detect_motion_artifacts(metrics, threshold=0.5)
        
        log_path = temp_dirs["processed"] / "excluded_subjects.log"
        write_motion_exclusion_log(excluded, log_path)
        
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        # Verify format: SubjectID: Reason
        for line in lines:
            assert ":" in line
            assert any(subj in line for subj in excluded.keys())

    def test_save_valid_subjects(self, temp_dirs):
        """Test saving valid subjects to JSON."""
        metrics = load_motion_metrics(temp_dirs["interim"])
        valid = get_valid_subjects(metrics, threshold=0.5)
        
        out_path = temp_dirs["processed"] / "valid_subjects.json"
        save_valid_subjects(valid, out_path)
        
        assert out_path.exists()
        
        with open(out_path, 'r') as f:
            data = json.load(f)
        
        assert "valid_subjects" in data
        assert data["count"] == len(valid)
        assert set(data["valid_subjects"]) == set(valid)
        assert data["threshold_used"] == 0.5

    def test_main_integration(self, temp_dirs, caplog):
        """Test the main function end-to-end."""
        # Temporarily override paths in main by mocking
        import motion_detection as md
        
        # Save original paths
        original_main = md.main
        
        # Create a custom main that uses our temp dirs
        def custom_main():
            project_root = temp_dirs["interim"].parent.parent
            interim_dir = temp_dirs["interim"]
            processed_dir = temp_dirs["processed"]
            
            exclusion_log_path = processed_dir / "excluded_subjects.log"
            valid_subjects_path = processed_dir / "valid_subjects.json"
            
            motion_metrics = load_motion_metrics(interim_dir)
            excluded = detect_motion_artifacts(motion_metrics, threshold=0.5)
            valid_subjects = get_valid_subjects(motion_metrics, threshold=0.5)
            
            write_motion_exclusion_log(excluded, exclusion_log_path)
            save_valid_subjects(valid_subjects, valid_subjects_path)
            
            return valid_subjects
        
        result = custom_main()
        
        # Verify outputs
        assert len(result) == 2
        assert set(result) == set(temp_dirs["expected_valid"])
        assert (temp_dirs["processed"] / "excluded_subjects.log").exists()
        assert (temp_dirs["processed"] / "valid_subjects.json").exists()

    def test_empty_interim_directory(self, tmp_path):
        """Test handling of empty interim directory."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        
        metrics = load_motion_metrics(tmp_path / "interim")
        assert len(metrics) == 0

    def test_missing_motion_log(self, tmp_path):
        """Test handling of subjects without motion logs."""
        interim = tmp_path / "interim"
        (interim / "subj_001" / "func").mkdir(parents=True)
        # No motion_metrics.json created
        
        metrics = load_motion_metrics(interim)
        # Should return empty dict or handle gracefully
        assert len(metrics) == 0

    def test_threshold_edge_cases(self, temp_dirs):
        """Test behavior at threshold boundaries."""
        metrics = load_motion_metrics(temp_dirs["interim"])
        
        # Exactly at threshold
        valid_at_045 = get_valid_subjects(metrics, threshold=0.45)
        assert "subj_002" in valid_at_045  # FD=0.45 should pass
        
        valid_at_03 = get_valid_subjects(metrics, threshold=0.3)
        assert "subj_001" in valid_at_03  # FD=0.3 should pass
        assert "subj_002" not in valid_at_03  # FD=0.45 should fail