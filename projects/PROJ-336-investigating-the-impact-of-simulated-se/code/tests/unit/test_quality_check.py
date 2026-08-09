import unittest
import json
import tempfile
from pathlib import Path
import sys
import os
import numpy as np

# Add code to path if not already
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.quality_check import (
    load_motion_json,
    calculate_fd,
    compute_subject_fd,
    run_quality_check,
    save_manifest,
    FD_THRESHOLD_MM,
    MAX_HIGH_MOTION_PCT,
    MIN_SAMPLE_SIZE
)


class TestQualityCheck(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_root = Path(self.temp_dir.name)
        
        # Create mock subject directories
        self.sub1_dir = self.data_root / "sub-01" / "func"
        self.sub1_dir.mkdir(parents=True)
        
        self.sub2_dir = self.data_root / "sub-02" / "func"
        self.sub2_dir.mkdir(parents=True)
        
        self.sub3_dir = self.data_root / "sub-03" / "func"
        self.sub3_dir.mkdir(parents=True)
        
        # Mock motion data for sub-01 (low motion)
        self.motion_data_low = {
            "trans_x": [0.0, 0.1, 0.1, 0.1, 0.1],
            "trans_y": [0.0, 0.1, 0.1, 0.1, 0.1],
            "trans_z": [0.0, 0.1, 0.1, 0.1, 0.1],
            "rot_x": [0.0, 0.01, 0.01, 0.01, 0.01],
            "rot_y": [0.0, 0.01, 0.01, 0.01, 0.01],
            "rot_z": [0.0, 0.01, 0.01, 0.01, 0.01],
            "total_volume_count": 5
        }
        
        # Mock motion data for sub-02 (high motion)
        self.motion_data_high = {
            "trans_x": [0.0, 1.0, 1.0, 1.0, 1.0],
            "trans_y": [0.0, 1.0, 1.0, 1.0, 1.0],
            "trans_z": [0.0, 1.0, 1.0, 1.0, 1.0],
            "rot_x": [0.0, 0.5, 0.5, 0.5, 0.5],
            "rot_y": [0.0, 0.5, 0.5, 0.5, 0.5],
            "rot_z": [0.0, 0.5, 0.5, 0.5, 0.5],
            "total_volume_count": 5
        }
        
        # Mock motion data for sub-03 (low motion)
        self.motion_data_low_2 = {
            "trans_x": [0.0, 0.1, 0.1, 0.1, 0.1],
            "trans_y": [0.0, 0.1, 0.1, 0.1, 0.1],
            "trans_z": [0.0, 0.1, 0.1, 0.1, 0.1],
            "rot_x": [0.0, 0.01, 0.01, 0.01, 0.01],
            "rot_y": [0.0, 0.01, 0.01, 0.01, 0.01],
            "rot_z": [0.0, 0.01, 0.01, 0.01, 0.01],
            "total_volume_count": 5
        }
        
        # Write JSON files
        self.json1 = self.sub1_dir / "sub-01_task-rest_bold.json"
        with open(self.json1, 'w') as f:
            json.dump(self.motion_data_low, f)
            
        self.json2 = self.sub2_dir / "sub-02_task-rest_bold.json"
        with open(self.json2, 'w') as f:
            json.dump(self.motion_data_high, f)
            
        self.json3 = self.sub3_dir / "sub-03_task-rest_bold.json"
        with open(self.json3, 'w') as f:
            json.dump(self.motion_data_low_2, f)
            
        self.manifest_path = self.data_root / "exclusion_manifest.json"

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_motion_json(self):
        """Test loading a motion JSON file."""
        data = load_motion_json(self.json1)
        self.assertIn('trans_x', data)
        self.assertEqual(len(data['trans_x']), 5)

    def test_load_motion_json_not_found(self):
        """Test loading a non-existent JSON file raises error."""
        with self.assertRaises(FileNotFoundError):
            load_motion_json(Path("non_existent.json"))

    def test_calculate_fd(self):
        """Test FD calculation logic."""
        # Create motion data with known differences
        motion = {
            "trans_x": [0.0, 0.5, 0.0],
            "trans_y": [0.0, 0.0, 0.0],
            "trans_z": [0.0, 0.0, 0.0],
            "rot_x": [0.0, 0.0, 0.0],
            "rot_y": [0.0, 0.0, 0.0],
            "rot_z": [0.0, 0.0, 0.0]
        }
        
        fd = calculate_fd(motion)
        
        # Expected: |0.5 - 0| = 0.5 for trans_x
        # rest are 0
        # FD = 0.5
        self.assertEqual(len(fd), 2)
        self.assertAlmostEqual(fd[0], 0.5, places=4)
        self.assertAlmostEqual(fd[1], 0.5, places=4)

    def test_calculate_fd_missing_keys(self):
        """Test FD calculation with missing keys raises error."""
        motion = {"trans_x": [0.0, 0.1]}
        with self.assertRaises(ValueError):
            calculate_fd(motion)

    def test_compute_subject_fd(self):
        """Test computing FD for a subject."""
        fd_values, total_vols = compute_subject_fd([self.json1])
        self.assertEqual(total_vols, 5)
        self.assertEqual(len(fd_values), 4) # N-1

    def test_run_quality_check_exclusion_logic(self):
        """Test that high motion subjects are excluded."""
        # We have 3 subjects: sub-01 (low), sub-02 (high), sub-03 (low)
        # Expected: sub-02 excluded, sub-01 and sub-03 included
        manifest = run_quality_check(self.data_root, self.manifest_path)
        
        self.assertEqual(manifest['included_count'], 2)
        self.assertEqual(manifest['excluded_count'], 1)
        self.assertIn('sub-02', manifest['exclusion_reasons'])
        self.assertNotIn('sub-01', manifest['exclusion_reasons'])
        self.assertNotIn('sub-03', manifest['exclusion_reasons'])
        
        # Verify manifest file exists
        self.assertTrue(self.manifest_path.exists())

    def test_run_quality_check_sample_size_threshold(self):
        """Test that execution halts if sample size < 20."""
        # Create a temporary directory with only 2 low-motion subjects
        temp_dir = tempfile.TemporaryDirectory()
        try:
            small_root = Path(temp_dir.name)
            
            for i in range(2):
                sub_dir = small_root / f"sub-{i+1:02d}" / "func"
                sub_dir.mkdir(parents=True)
                json_file = sub_dir / f"sub-{i+1:02d}_task-rest_bold.json"
                with open(json_file, 'w') as f:
                    json.dump(self.motion_data_low, f)
            
            manifest_path = small_root / "exclusion_manifest.json"
            
            # This should succeed because 2 >= 20 is False, but we only have 2 subjects
            # Wait, the threshold is 20. With only 2 subjects, it should fail.
            with self.assertRaises(ValueError) as context:
                run_quality_check(small_root, manifest_path)
                
            self.assertIn("below minimum threshold", str(context.exception))
            
        finally:
            temp_dir.cleanup()

    def test_save_manifest(self):
        """Test saving the exclusion manifest."""
        data = {
            "total_subjects": 3,
            "included": [{"subject_id": "sub-01"}],
            "excluded": [],
            "exclusion_reasons": {},
            "sample_size": 1
        }
        save_manifest(data, self.manifest_path)
        
        self.assertTrue(self.manifest_path.exists())
        with open(self.manifest_path, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data['sample_size'], 1)


if __name__ == '__main__':
    unittest.main()
