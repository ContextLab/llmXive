"""
Unit tests for the mock Guava dataset generator (T013b).

These tests verify that the synthetic data generation produces:
1. Valid image files
2. Correctly structured annotations JSON
3. Consistent checksums
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data.generate_mock_guava import (
    generate_synthetic_frame,
    create_bounding_box,
    generate_mock_dataset
)

class TestMockDatasetGeneration(TestCase):
    
    def test_generate_synthetic_frame_shape(self):
        """Test that generated frame has correct dimensions."""
        width, height = 640, 480
        frame = generate_synthetic_frame(width, height, seed=42)
        
        self.assertEqual(frame.shape[0], height)
        self.assertEqual(frame.shape[1], width)
        self.assertEqual(frame.dtype, 'uint8')
        
    def test_generate_synthetic_frame_values(self):
        """Test that generated frame values are in valid range."""
        frame = generate_synthetic_frame(100, 100, seed=123)
        
        self.assertGreaterEqual(frame.min(), 0)
        self.assertLessEqual(frame.max(), 255)
        
    def test_create_bounding_box_structure(self):
        """Test that bounding box dictionary has correct structure."""
        bbox = create_bounding_box(10, 20, 30, 40, class_id=1)
        
        self.assertIn("class_id", bbox)
        self.assertIn("bbox", bbox)
        self.assertIn("confidence", bbox)
        self.assertIn("is_visible", bbox)
        
        self.assertEqual(bbox["class_id"], 1)
        self.assertEqual(bbox["bbox"], [10, 20, 40, 60])
        self.assertEqual(bbox["confidence"], 1.0)
        self.assertTrue(bbox["is_visible"])
        
    def test_generate_mock_dataset_files_created(self):
        """Test that all expected files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = generate_mock_dataset(output_dir, num_trajectories=1, frames_per_trajectory=2)
            
            # Check annotations file
            annotations_path = output_dir / "ground_truth_annotations.json"
            self.assertTrue(annotations_path.exists())
            
            # Check checksums file
            checksums_path = output_dir / "frame_checksums.json"
            self.assertTrue(checksums_path.exists())
            
            # Check frames directory
            frames_dir = output_dir / "frames"
            self.assertTrue(frames_dir.exists())
            
            # Check frame files exist
            frame_files = list(frames_dir.glob("*.png"))
            self.assertEqual(len(frame_files), 2)
            
    def test_generate_mock_dataset_annotations_valid(self):
        """Test that annotations JSON has valid structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_mock_dataset(output_dir, num_trajectories=1, frames_per_trajectory=2)
            
            annotations_path = output_dir / "ground_truth_annotations.json"
            with open(annotations_path, 'r') as f:
                data = json.load(f)
                
            self.assertIn("dataset_version", data)
            self.assertIn("annotations", data)
            self.assertIn("total_trajectories", data)
            self.assertEqual(data["total_trajectories"], 1)
            
            # Check annotation structure
            self.assertEqual(len(data["annotations"]), 2)
            
            for annotation in data["annotations"]:
                self.assertIn("trajectory_id", annotation)
                self.assertIn("frame_index", annotation)
                self.assertIn("frame_path", annotation)
                self.assertIn("objects", annotation)
                
    def test_generate_mock_dataset_checksums_match(self):
        """Test that generated checksums match actual file hashes."""
        import hashlib
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_mock_dataset(output_dir, num_trajectories=1, frames_per_trajectory=2)
            
            frames_dir = output_dir / "frames"
            checksums_path = output_dir / "frame_checksums.json"
            
            with open(checksums_path, 'r') as f:
                stored_checksums = json.load(f)
                
            for filename, stored_hash in stored_checksums.items():
                file_path = frames_dir / filename
                with open(file_path, 'rb') as f:
                    actual_hash = hashlib.sha256(f.read()).hexdigest()
                
                self.assertEqual(stored_hash, actual_hash, f"Checksum mismatch for {filename}")
                
    def test_generate_mock_dataset_deterministic(self):
        """Test that generation is deterministic with same seed."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                output_dir1 = Path(tmpdir1)
                output_dir2 = Path(tmpdir2)
                
                generate_mock_dataset(output_dir1, num_trajectories=1, frames_per_trajectory=2)
                generate_mock_dataset(output_dir2, num_trajectories=1, frames_per_trajectory=2)
                
                # Compare checksums
                with open(output_dir1 / "frame_checksums.json", 'r') as f1:
                    checksums1 = json.load(f1)
                with open(output_dir2 / "frame_checksums.json", 'r') as f2:
                    checksums2 = json.load(f2)
                    
                self.assertEqual(checksums1, checksums2)
                
    def test_generate_mock_dataset_empty_trajectories(self):
        """Test generation with zero trajectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = generate_mock_dataset(output_dir, num_trajectories=0, frames_per_trajectory=0)
            
            annotations_path = output_dir / "ground_truth_annotations.json"
            with open(annotations_path, 'r') as f:
                data = json.load(f)
                
            self.assertEqual(data["total_trajectories"], 0)
            self.assertEqual(len(data["annotations"]), 0)
            
    def test_generate_mock_dataset_large_trajectory(self):
        """Test generation with a larger number of frames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = generate_mock_dataset(output_dir, num_trajectories=1, frames_per_trajectory=50)
            
            frames_dir = output_dir / "frames"
            frame_files = list(frames_dir.glob("*.png"))
            
            self.assertEqual(len(frame_files), 50)
            
            annotations_path = output_dir / "ground_truth_annotations.json"
            with open(annotations_path, 'r') as f:
                data = json.load(f)
                
            self.assertEqual(len(data["annotations"]), 50)