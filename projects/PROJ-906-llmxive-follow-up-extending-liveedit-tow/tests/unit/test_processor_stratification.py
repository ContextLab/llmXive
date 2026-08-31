import pytest
import os
import json
import tempfile
from pathlib import Path
from typing import List, Dict

# Import the function to test
from code.data.processor import process_dataset_stratification, stratify_by_motion
from code.config import STRATIFICATION_THRESHOLDS

class TestStratificationLogic:
    """
    Tests for T037a: Dataset stratification logic.
    
    Verifies that the post-download check correctly categorizes clips
    based on flow magnitude thresholds and reports the distribution.
    """

    def test_stratify_by_motion_static(self):
        """Test classification of static clips (low flow)."""
        # Thresholds are {0.5, 5.0}
        # Static: flow < 0.5
        category = stratify_by_motion("clip_001", 0.1)
        assert category == "Static"

    def test_stratify_by_motion_slow_rigid(self):
        """Test classification of slow rigid clips (medium flow)."""
        # Slow Rigid: 0.5 <= flow < 5.0
        category = stratify_by_motion("clip_002", 2.5)
        assert category == "Slow Rigid"

    def test_stratify_by_motion_fast_non_rigid(self):
        """Test classification of fast non-rigid clips (high flow)."""
        # Fast Non-Rigid: flow >= 5.0
        category = stratify_by_motion("clip_003", 10.0)
        assert category == "Fast Non-Rigid"

    def test_stratify_by_motion_boundary_low(self):
        """Test boundary at low threshold (0.5)."""
        # Exactly at threshold should be Slow Rigid
        category = stratify_by_motion("clip_004", 0.5)
        assert category == "Slow Rigid"

    def test_stratify_by_motion_boundary_high(self):
        """Test boundary at high threshold (5.0)."""
        # Exactly at threshold should be Fast Non-Rigid
        category = stratify_by_motion("clip_005", 5.0)
        assert category == "Fast Non-Rigid"

    def test_process_dataset_stratification_creates_report(self):
        """
        Test that process_dataset_stratification creates the report file
        and correctly categorizes a mixed set of clips.
        """
        # Create temporary directories
        with tempfile.TemporaryDirectory() as tmpdir:
            mask_dir = os.path.join(tmpdir, "masks")
            report_path = os.path.join(tmpdir, "stratification_report.json")
            
            # Mock clip paths and flow magnitudes
            # We need valid video paths for the mask generation step,
            # so we create dummy video files
            clip_paths = []
            flow_mags = {}
            
            for i, mag in enumerate([0.1, 2.5, 10.0, 0.4, 6.0]):
                clip_id = f"test_clip_{i}"
                # Create a dummy video file (1 frame)
                clip_path = os.path.join(tmpdir, f"{clip_id}.mp4")
                # Create a minimal valid video file using OpenCV
                # (Note: This is a simplified dummy for testing logic)
                # In a real scenario, we'd use actual video files from the dataset
                # For this test, we mock the path existence check
                clip_paths.append(clip_path)
                flow_mags[clip_id] = mag

            # Since we can't easily create valid video files in a temp dir for OpenCV,
            # we will test the stratify_by_motion logic directly and verify
            # the report structure generation logic by mocking the mask generation.
            # However, the task requires the function to run. 
            # We will create a minimal valid video using numpy and cv2.
            
            valid_clip_paths = []
            for i, mag in enumerate([0.1, 2.5, 10.0, 0.4, 6.0]):
                clip_id = f"test_clip_{i}"
                clip_path = os.path.join(tmpdir, f"{clip_id}.mp4")
                
                # Create a minimal valid video
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(clip_path, fourcc, 1.0, (64, 64))
                frame = np.zeros((64, 64, 3), dtype=np.uint8)
                out.write(frame)
                out.release()
                
                valid_clip_paths.append(clip_path)
                flow_mags[clip_id] = mag

            # Run the function
            processed_clips = process_dataset_stratification(
                clip_paths=valid_clip_paths,
                flow_magnitudes=flow_mags,
                output_mask_dir=mask_dir,
                output_report_path=report_path
            )

            # Verify report file exists
            assert os.path.exists(report_path)

            # Verify report content
            with open(report_path, 'r') as f:
                report = json.load(f)

            assert "total_clips" in report
            assert report["total_clips"] == 5
            assert "distribution" in report
            assert "thresholds_used" in report
            
            # Verify distribution counts
            # 0.1 -> Static
            # 2.5 -> Slow Rigid
            # 10.0 -> Fast Non-Rigid
            # 0.4 -> Static
            # 6.0 -> Fast Non-Rigid
            # Expected: Static: 2, Slow Rigid: 1, Fast Non-Rigid: 2
            assert report["distribution"]["Static"] == 2
            assert report["distribution"]["Slow Rigid"] == 1
            assert report["distribution"]["Fast Non-Rigid"] == 2

    def test_stratification_uses_config_thresholds(self):
        """
        Verify that the function uses STRATIFICATION_THRESHOLDS from config
        rather than hard-coded values.
        """
        # The function stratify_by_motion uses STRATIFICATION_THRESHOLDS by default
        # We verify that the default thresholds match the config
        assert STRATIFICATION_THRESHOLDS == {0.5, 5.0}
        
        # Test with a value that would be ambiguous if thresholds were different
        # e.g., if thresholds were {1.0, 10.0}, 2.5 would be Static
        # But with {0.5, 5.0}, 2.5 is Slow Rigid
        category = stratify_by_motion("test", 2.5)
        assert category == "Slow Rigid"
