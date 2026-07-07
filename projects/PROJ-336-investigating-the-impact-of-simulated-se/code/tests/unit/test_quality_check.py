import unittest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.quality_check import load_motion_json, calculate_fd, compute_subject_fd, run_quality_check, save_manifest
from src.config import FD_THRESHOLD, HIGH_MOTION_PERCENTAGE_THRESHOLD, MIN_SAMPLE_SIZE

class TestQualityCheck(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.subject_dir = self.temp_dir / "sub-01"
        self.subject_dir.mkdir()
        
        # Create mock motion data
        self.motion_data = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # First volume
            [0.1, 0.1, 0.1, 0.001, 0.001, 0.001],  # Small motion
            [0.5, 0.5, 0.5, 0.01, 0.01, 0.01],  # High motion (FD > 0.5)
            [0.1, 0.1, 0.1, 0.001, 0.001, 0.001],  # Small motion
        ]
        
        self.motion_json_path = self.subject_dir / "sub-01_task-rest_run-01_desc-motions.json"
        with open(self.motion_json_path, 'w') as f:
            json.dump({"repetitions": self.motion_data}, f)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_motion_json(self):
        data = load_motion_json(self.motion_json_path)
        self.assertIn("repetitions", data)
        self.assertEqual(len(data["repetitions"]), len(self.motion_data))
    
    def test_calculate_fd(self):
        # Test with known motion parameters
        motion = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        fd = calculate_fd(motion)
        self.assertEqual(fd, 0.0)
        
        # Test with small motion
        motion = [0.1, 0.1, 0.1, 0.001, 0.001, 0.001]
        fd = calculate_fd(motion)
        # FD should be > 0.3 (trans) + small rotation
        self.assertGreater(fd, 0.3)
        
        # Test with high motion
        motion = [0.5, 0.5, 0.5, 0.01, 0.01, 0.01]
        fd = calculate_fd(motion)
        # FD should be > 1.5 (trans) + rotation
        self.assertGreater(fd, 1.5)
    
    def test_compute_subject_fd(self):
        mean_fd, n_high, n_total = compute_subject_fd(self.motion_json_path)
        
        self.assertEqual(n_total, 4)
        # First volume has no previous, so we calculate for 3 transitions
        # Volume 1->2: low motion
        # Volume 2->3: high motion (0.4 diff in trans + rotation)
        # Volume 3->4: low motion
        self.assertEqual(n_high, 1)  # Only one high motion transition
        self.assertGreater(mean_fd, 0)
    
    def test_run_quality_check_with_valid_data(self):
        # Create a valid subject
        valid_subject_dir = self.temp_dir / "sub-02"
        valid_subject_dir.mkdir()
        
        valid_motion_data = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.1, 0.1, 0.1, 0.001, 0.001, 0.001],
            [0.1, 0.1, 0.1, 0.001, 0.001, 0.001],
            [0.1, 0.1, 0.1, 0.001, 0.001, 0.001],
        ]
        
        with open(valid_subject_dir / "sub-02_task-rest_run-01_desc-motions.json", 'w') as f:
            json.dump({"repetitions": valid_motion_data}, f)
        
        # Create enough subjects to meet minimum sample size
        for i in range(20, 25):
            sub_dir = self.temp_dir / f"sub-{i:02d}"
            sub_dir.mkdir()
            sub_motion_data = [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.1, 0.1, 0.1, 0.001, 0.001, 0.001],
            ]
            with open(sub_dir / f"sub-{i:02d}_task-rest_run-01_desc-motions.json", 'w') as f:
                json.dump({"repetitions": sub_motion_data}, f)
        
        manifest = run_quality_check(self.temp_dir)
        
        self.assertGreater(len(manifest["included"]), 0)
        self.assertIn("sub-01", [s["subject_id"] for s in manifest["excluded"]])
        self.assertIn("sub-02", [s["subject_id"] for s in manifest["included"]])
    
    def test_run_quality_check_high_motion_exclusion(self):
        # Create a subject with high motion
        high_motion_subject = self.temp_dir / "sub-high"
        high_motion_subject.mkdir()
        
        high_motion_data = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.5, 0.5, 0.5, 0.01, 0.01, 0.01],  # High motion
            [0.5, 0.5, 0.5, 0.01, 0.01, 0.01],  # High motion
            [0.5, 0.5, 0.5, 0.01, 0.01, 0.01],  # High motion
        ]
        
        with open(high_motion_subject / "sub-high_task-rest_run-01_desc-motions.json", 'w') as f:
            json.dump({"repetitions": high_motion_data}, f)
        
        # Create enough valid subjects
        for i in range(20, 25):
            sub_dir = self.temp_dir / f"sub-{i:02d}"
            sub_dir.mkdir()
            sub_motion_data = [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.1, 0.1, 0.1, 0.001, 0.001, 0.001],
            ]
            with open(sub_dir / f"sub-{i:02d}_task-rest_run-01_desc-motions.json", 'w') as f:
                json.dump({"repetitions": sub_motion_data}, f)
        
        manifest = run_quality_check(self.temp_dir)
        
        self.assertTrue(any(s["subject_id"] == "sub-high" for s in manifest["excluded"]))
        self.assertTrue(any(s["reason"] == "high_motion" for s in manifest["excluded"]))
    
    def test_run_quality_check_minimum_sample_size_error(self):
        # Create only 5 valid subjects (below MIN_SAMPLE_SIZE)
        for i in range(1, 6):
            sub_dir = self.temp_dir / f"sub-{i:02d}"
            sub_dir.mkdir()
            sub_motion_data = [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.1, 0.1, 0.1, 0.001, 0.001, 0.001],
            ]
            with open(sub_dir / f"sub-{i:02d}_task-rest_run-01_desc-motions.json", 'w') as f:
                json.dump({"repetitions": sub_motion_data}, f)
        
        with self.assertRaises(ValueError) as context:
            run_quality_check(self.temp_dir)
        
        self.assertIn("below minimum threshold", str(context.exception))
    
    def test_save_manifest(self):
        manifest = {
            "included": [{"subject_id": "sub-01"}],
            "excluded": [{"subject_id": "sub-02", "reason": "high_motion"}],
            "total_subjects": 2,
            "high_motion_excluded": 1,
            "missing_data_excluded": 0
        }
        
        output_path = self.temp_dir / "test_manifest.json"
        save_manifest(manifest, output_path)
        
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            loaded_manifest = json.load(f)
        
        self.assertEqual(loaded_manifest, manifest)

if __name__ == "__main__":
    unittest.main()