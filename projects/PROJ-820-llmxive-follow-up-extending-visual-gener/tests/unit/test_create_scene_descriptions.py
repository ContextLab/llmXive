"""
Unit tests for code/utils/create_scene_descriptions.py
Tests the fallback generation logic and CSV writing.
"""
import csv
import os
import sys
import tempfile
from pathlib import Path
import unittest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.create_scene_descriptions import generate_fallback_scenes, write_csv

class TestSceneDescriptionGeneration(unittest.TestCase):

    def test_generate_fallback_scenes_count(self):
        """Test that the correct number of scenes are generated."""
        scenes = generate_fallback_scenes(n=50, seed=123)
        self.assertEqual(len(scenes), 50)

    def test_generate_fallback_scenes_deterministic(self):
        """Test that generation is deterministic with the same seed."""
        scenes1 = generate_fallback_scenes(n=10, seed=42)
        scenes2 = generate_fallback_scenes(n=10, seed=42)
        scenes3 = generate_fallback_scenes(n=10, seed=43)

        # Same seed should produce identical results
        self.assertEqual(scenes1, scenes2)
        # Different seed should produce different results (highly likely)
        self.assertNotEqual(scenes1, scenes3)

    def test_generate_fallback_scenes_structure(self):
        """Test that generated scenes have the correct keys."""
        scenes = generate_fallback_scenes(n=1, seed=42)
        scene = scenes[0]
        self.assertIn("scene_id", scene)
        self.assertIn("description", scene)
        self.assertIn("source", scene)
        self.assertIn("seed", scene)
        self.assertEqual(scene["source"], "fallback_synthetic")

    def test_write_csv(self):
        """Test that scenes are written to CSV correctly."""
        scenes = generate_fallback_scenes(n=5, seed=42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scenes.csv"
            write_csv(scenes, output_path)
            
            self.assertTrue(output_path.exists())
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 5)
            self.assertIn("scene_id", rows[0])
            self.assertIn("description", rows[0])

    def test_scene_id_format(self):
        """Test that scene IDs are formatted correctly (scene_XXX)."""
        scenes = generate_fallback_scenes(n=105, seed=42)
        for i, scene in enumerate(scenes):
            expected_id = f"scene_{i+1:03d}"
            self.assertEqual(scene["scene_id"], expected_id)

if __name__ == '__main__':
    unittest.main()