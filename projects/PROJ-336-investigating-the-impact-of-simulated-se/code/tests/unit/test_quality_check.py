"""
Unit tests for the quality_check module.
"""
import unittest
import json
import tempfile
from pathlib import Path
import sys
import os
import logging

# Add parent directory to path to import src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data import quality_check

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

class TestQualityCheck(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / "bids_dataset"
        self.data_dir.mkdir()
        
        # Create a mock subject directory
        self.subject_dir = self.data_dir / "sub-01" / "func"
        self.subject_dir.mkdir(parents=True)
        
        # Create a mock motion JSON file
        self.motion_json = self.subject_dir / "sub-01_task-rest_bold_motion.json"
        
        # Generate realistic motion parameters
        # Format: list of lists [tx, ty, tz, rx, ry, rz]
        self.motion_data = {
            "trans_x": [0.0, 0.1, 0.2, 0.15, 0.05, 0.0, -0.1, -0.05, 0.0, 0.0],
            "trans_y": [0.0, 0.05, 0.1, 0.05, 0.0, -0.05, -0.1, -0.05, 0.0, 0.0],
            "trans_z": [0.0, 0.0, 0.05, 0.0, -0.05, -0.05, 0.0, 0.05, 0.0, 0.0],
            "rot_x": [0.0, 0.001, 0.002, 0.0015, 0.0005, 0.0, -0.001, -0.0005, 0.0, 0.0],
            "rot_y": [0.0, 0.0005, 0.001, 0.0005, 0.0, -0.0005, -0.001, -0.0005, 0.0, 0.0],
            "rot_z": [0.0, 0.0, 0.0005, 0.0, -0.0005, -0.0005, 0.0, 0.0005, 0.0, 0.0]
        }
        
        with open(self.motion_json, 'w') as f:
            json.dump(self.motion_data, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_motion_json(self):
        """Test loading motion JSON file."""
        data = quality_check.load_motion_json(self.motion_json)
        self.assertIn("trans_x", data)
        self.assertEqual(len(data["trans_x"]), 10)
    
    def test_load_motion_json_file_not_found(self):
        """Test loading non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            quality_check.load_motion_json(Path("/nonexistent/file.json"))
    
    def test_calculate_fd(self):
        """Test FD calculation."""
        # Simple case: no motion
        fd = quality_check.calculate_fd([0, 0, 0, 0, 0, 0])
        self.assertEqual(fd, 0.0)
        
        # Case with motion
        # tx=1mm, ty=0, tz=0, rx=0.01 rad (~0.5mm), ry=0, rz=0
        # FD = 1 + 0 + 0 + 0.5 + 0 + 0 = 1.5
        fd = quality_check.calculate_fd([1.0, 0, 0, 0.01, 0, 0])
        self.assertAlmostEqual(fd, 1.5, places=1)
    
    def test_compute_subject_fd(self):
        """Test computing FD for a subject."""
        fd_series, total_vol, high_motion_count = quality_check.compute_subject_fd(self.motion_json)
        
        # We have 10 volumes, so 9 FD values (differences)
        self.assertEqual(len(fd_series), 9)
        self.assertEqual(total_vol, 9)
        
        # With small motions, high motion count should be 0 (threshold 0.5mm)
        self.assertEqual(high_motion_count, 0)
    
    def test_compute_subject_fd_missing_file(self):
        """Test computing FD for missing file."""
        fd_series, total_vol, high_motion_count = quality_check.compute_subject_fd(Path("/nonexistent.json"))
        self.assertEqual(len(fd_series), 0)
        self.assertEqual(total_vol, 0)
        self.assertEqual(high_motion_count, 0)
    
    def test_find_motion_jsons(self):
        """Test finding motion JSON files."""
        # Create another motion file
        other_motion = self.data_dir / "sub-02" / "func" / "sub-02_task-rest_bold_motion.json"
        other_motion.parent.mkdir(parents=True)
        with open(other_motion, 'w') as f:
            json.dump(self.motion_data, f)
        
        found_files = quality_check.find_motion_jsons(self.data_dir)
        self.assertEqual(len(found_files), 2)
    
    def test_run_quality_check_includes_all(self):
        """Test quality check when all subjects pass."""
        # Create a subject with very low motion
        subject_dir = self.data_dir / "sub-02" / "func"
        subject_dir.mkdir(parents=True)
        motion_json = subject_dir / "sub-02_task-rest_bold_motion.json"
        
        # Very low motion
        low_motion_data = {
            "trans_x": [0.0, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
            "trans_y": [0.0, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
            "trans_z": [0.0, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
            "rot_x": [0.0, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001],
            "rot_y": [0.0, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001],
            "rot_z": [0.0, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001]
        }
        
        with open(motion_json, 'w') as f:
            json.dump(low_motion_data, f)
        
        # Create a manifest directory
        output_dir = self.temp_dir / "manifests"
        output_dir.mkdir()
        
        # We need at least 20 subjects to pass the check, so we'll mock the count
        # For this test, we'll just verify the logic works for a small set
        # and trust the sample size check for the full integration test
        
        # Since we only have 2 subjects, the check will fail the n>=20 requirement
        # So we test the logic by mocking the sample size check
        with unittest.mock.patch.object(quality_check, 'MIN_SAMPLE_SIZE', 1):
            manifest = quality_check.run_quality_check(self.data_dir, output_dir)
            
            self.assertEqual(manifest["total_subjects"], 2)
            self.assertEqual(manifest["included_subjects"], 2)
            self.assertEqual(manifest["excluded_subjects"], 0)
            
            # Verify manifest file was created
            manifest_path = output_dir / "exclusion_manifest.json"
            self.assertTrue(manifest_path.exists())
    
    def test_run_quality_check_excludes_high_motion(self):
        """Test quality check excludes high motion subjects."""
        # Create a subject with high motion
        subject_dir = self.data_dir / "sub-03" / "func"
        subject_dir.mkdir(parents=True)
        motion_json = subject_dir / "sub-03_task-rest_bold_motion.json"
        
        # High motion: >10% volumes above 0.5mm
        # 100 volumes, 15 high motion
        high_motion_data = {
            "trans_x": [0.0] * 100,
            "trans_y": [0.0] * 100,
            "trans_z": [0.0] * 100,
            "rot_x": [0.0] * 100,
            "rot_y": [0.0] * 100,
            "rot_z": [0.0] * 100
        }
        
        # Inject high motion at specific indices
        high_motion_indices = [10, 20, 30, 40, 50, 60, 70, 80, 90, 91, 92, 93, 94, 95, 96]
        for idx in high_motion_indices:
            if idx > 0:
                high_motion_data["trans_x"][idx] = 0.6  # > 0.5mm
        
        with open(motion_json, 'w') as f:
            json.dump(high_motion_data, f)
        
        # Create another low motion subject to ensure we have enough for the check
        subject_dir2 = self.data_dir / "sub-04" / "func"
        subject_dir2.mkdir(parents=True)
        motion_json2 = subject_dir2 / "sub-04_task-rest_bold_motion.json"
        
        low_motion_data = {
            "trans_x": [0.0] * 100,
            "trans_y": [0.0] * 100,
            "trans_z": [0.0] * 100,
            "rot_x": [0.0] * 100,
            "rot_y": [0.0] * 100,
            "rot_z": [0.0] * 100
        }
        with open(motion_json2, 'w') as f:
            json.dump(low_motion_data, f)
        
        # Create enough low-motion subjects to pass the n>=20 check
        # We'll create 19 more
        for i in range(5, 25):
            sub_dir = self.data_dir / f"sub-{i:02d}" / "func"
            sub_dir.mkdir(parents=True)
            sub_json = sub_dir / f"sub-{i:02d}_task-rest_bold_motion.json"
            with open(sub_json, 'w') as f:
                json.dump(low_motion_data, f)
        
        output_dir = self.temp_dir / "manifests"
        output_dir.mkdir()
        
        manifest = quality_check.run_quality_check(self.data_dir, output_dir)
        
        self.assertEqual(manifest["total_subjects"], 24) # 1 high + 23 low
        self.assertEqual(manifest["excluded_subjects"], 1)
        self.assertEqual(manifest["included_subjects"], 23)
        self.assertIn("sub-03", manifest["excluded_list"])
        self.assertNotIn("sub-03", manifest["included_list"])
    
    def test_run_quality_check_fails_low_sample(self):
        """Test quality check fails if sample size < 20."""
        # Only create 5 subjects, all low motion
        for i in range(1, 6):
            subject_dir = self.data_dir / f"sub-{i:02d}" / "func"
            subject_dir.mkdir(parents=True)
            motion_json = subject_dir / f"sub-{i:02d}_task-rest_bold_motion.json"
            
            low_motion_data = {
                "trans_x": [0.0] * 10,
                "trans_y": [0.0] * 10,
                "trans_z": [0.0] * 10,
                "rot_x": [0.0] * 10,
                "rot_y": [0.0] * 10,
                "rot_z": [0.0] * 10
            }
            with open(motion_json, 'w') as f:
                json.dump(low_motion_data, f)
        
        output_dir = self.temp_dir / "manifests"
        output_dir.mkdir()
        
        with self.assertRaises(ValueError) as context:
            quality_check.run_quality_check(self.data_dir, output_dir)
        
        self.assertIn("below the minimum required threshold", str(context.exception))
        self.assertIn("20", str(context.exception))

if __name__ == "__main__":
    unittest.main()