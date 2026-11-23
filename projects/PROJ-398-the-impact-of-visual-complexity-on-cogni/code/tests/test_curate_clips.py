"""
Tests for the curate_clips module.

Verifies that:
- Clips are filtered correctly based on resolution and duration criteria
- Output CSV is generated with correct schema
- Manifest JSON is generated with correct provenance information
- Edge cases (no clips, all rejected, etc.) are handled properly
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import cv2
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.experiment.curate_clips import (
    curate_clips,
    get_video_info,
    meets_criteria,
    MIN_WIDTH,
    MIN_HEIGHT,
    MAX_DURATION_SECONDS
)


class TestCurateClips(unittest.TestCase):
    """Test suite for clip curation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.raw_dir = self.temp_dir / "raw_clips"
        self.raw_dir.mkdir()
        self.output_dir = self.temp_dir / "output"
        self.output_dir.mkdir()
        
        # Create test video files with mock data
        self._create_test_videos()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_videos(self):
        """Create mock video files for testing."""
        # Create a small test video that meets criteria
        test_video_path = self.raw_dir / "good_clip.mp4"
        self._create_mock_video(test_video_path, width=1280, height=720, duration=5.0)
        
        # Create a video that fails resolution (too small)
        small_video_path = self.raw_dir / "small_clip.mp4"
        self._create_mock_video(small_video_path, width=320, height=240, duration=5.0)
        
        # Create a video that fails duration (too long)
        long_video_path = self.raw_dir / "long_clip.mp4"
        self._create_mock_video(long_video_path, width=1280, height=720, duration=15.0)
        
        # Create a video that fails both
        bad_video_path = self.raw_dir / "bad_clip.mp4"
        self._create_mock_video(bad_video_path, width=320, height=240, duration=15.0)
        
        # Create a video at exactly the boundary (should pass)
        boundary_video_path = self.raw_dir / "boundary_clip.mp4"
        self._create_mock_video(boundary_video_path, width=640, height=360, duration=10.0)

    def _create_mock_video(self, path: Path, width: int, height: int, duration: float):
        """Create a mock video file using OpenCV."""
        fps = 30.0
        frame_count = int(duration * fps)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
        
        # Write a few frames
        for _ in range(min(10, frame_count)):
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            out.write(frame)
        
        out.release()

    def test_curated_clips_meet_criteria(self):
        """Test that curated clips meet the specified criteria."""
        output_csv = self.output_dir / "curated_clips.csv"
        manifest_output = self.output_dir / "curated_manifest.json"
        
        # Run curation
        result = curate_clips(
            raw_dir=self.raw_dir,
            output_csv=output_csv,
            manifest_output=manifest_output
        )
        
        # Verify results
        self.assertEqual(result['curated_count'], 2)  # good_clip and boundary_clip
        self.assertEqual(result['rejected_count'], 3)  # small, long, bad
        
        # Verify CSV exists and has correct content
        self.assertTrue(output_csv.exists())
        self.assertTrue(manifest_output.exists())
        
        # Read and verify CSV content
        import csv
        with open(output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        
        # Check that only qualifying clips are in the CSV
        filenames = [row['filename'] for row in rows]
        self.assertIn('good_clip.mp4', filenames)
        self.assertIn('boundary_clip.mp4', filenames)
        self.assertNotIn('small_clip.mp4', filenames)
        self.assertNotIn('long_clip.mp4', filenames)
        self.assertNotIn('bad_clip.mp4', filenames)
        
        # Verify manifest content
        with open(manifest_output, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        self.assertEqual(manifest['curated_count'], 2)
        self.assertEqual(manifest['rejected_count'], 3)
        self.assertEqual(manifest['filter_criteria']['min_width'], MIN_WIDTH)
        self.assertEqual(manifest['filter_criteria']['min_height'], MIN_HEIGHT)
        self.assertEqual(manifest['filter_criteria']['max_duration_seconds'], MAX_DURATION_SECONDS)

    def test_meets_criteria_function(self):
        """Test the meets_criteria function directly."""
        # Should pass
        self.assertTrue(meets_criteria({
            'width': 1280,
            'height': 720,
            'duration': 5.0
        }))
        
        # Should fail resolution
        self.assertFalse(meets_criteria({
            'width': 320,
            'height': 240,
            'duration': 5.0
        }))
        
        # Should fail duration
        self.assertFalse(meets_criteria({
            'width': 1280,
            'height': 720,
            'duration': 15.0
        }))
        
        # Should fail both
        self.assertFalse(meets_criteria({
            'width': 320,
            'height': 240,
            'duration': 15.0
        }))
        
        # Boundary case: exactly at limits
        self.assertTrue(meets_criteria({
            'width': 640,
            'height': 360,
            'duration': 10.0
        }))
        
        # Below boundary
        self.assertFalse(meets_criteria({
            'width': 639,
            'height': 360,
            'duration': 10.0
        }))
        
        self.assertFalse(meets_criteria({
            'width': 640,
            'height': 359,
            'duration': 10.0
        }))
        
        self.assertFalse(meets_criteria({
            'width': 640,
            'height': 360,
            'duration': 10.1
        }))

    def test_no_clips_directory(self):
        """Test behavior when no clips exist in directory."""
        empty_dir = self.temp_dir / "empty_clips"
        empty_dir.mkdir()
        
        output_csv = self.output_dir / "curated_clips_empty.csv"
        manifest_output = self.output_dir / "curated_manifest_empty.json"
        
        result = curate_clips(
            raw_dir=empty_dir,
            output_csv=output_csv,
            manifest_output=manifest_output
        )
        
        self.assertEqual(result['curated_count'], 0)
        self.assertEqual(result['rejected_count'], 0)
        self.assertTrue(output_csv.exists())
        self.assertTrue(manifest_output.exists())

    def test_csv_schema(self):
        """Test that output CSV has correct schema."""
        output_csv = self.output_dir / "curated_clips_schema.csv"
        manifest_output = self.output_dir / "curated_manifest_schema.json"
        
        curate_clips(
            raw_dir=self.raw_dir,
            output_csv=output_csv,
            manifest_output=manifest_output
        )
        
        import csv
        with open(output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        
        expected_fields = ['filename', 'width', 'height', 'duration', 'fps', 'frame_count']
        self.assertEqual(fieldnames, expected_fields)

    def test_manifest_provenance(self):
        """Test that manifest includes provenance information."""
        output_csv = self.output_dir / "curated_clips_prov.csv"
        manifest_output = self.output_dir / "curated_manifest_prov.json"
        
        curate_clips(
            raw_dir=self.raw_dir,
            output_csv=output_csv,
            manifest_output=manifest_output
        )
        
        with open(manifest_output, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Check that provenance fields exist
        self.assertIn('source_dataset', manifest)
        self.assertIn('source_version', manifest)
        self.assertIn('source_url', manifest)
        self.assertIn('filter_criteria', manifest)
        self.assertIn('statistics', manifest)
        
        # Check filter criteria
        criteria = manifest['filter_criteria']
        self.assertEqual(criteria['min_width'], MIN_WIDTH)
        self.assertEqual(criteria['min_height'], MIN_HEIGHT)
        self.assertEqual(criteria['max_duration_seconds'], MAX_DURATION_SECONDS)

    def test_get_video_info(self):
        """Test video info extraction."""
        test_video = self.raw_dir / "good_clip.mp4"
        
        info = get_video_info(test_video)
        
        self.assertIsNotNone(info)
        self.assertIn('width', info)
        self.assertIn('height', info)
        self.assertIn('duration', info)
        self.assertIn('fps', info)
        self.assertIn('frame_count', info)
        
        # Verify dimensions
        self.assertEqual(info['width'], 1280)
        self.assertEqual(info['height'], 720)

    def test_get_video_info_missing_file(self):
        """Test video info extraction for missing file."""
        missing_video = self.raw_dir / "nonexistent.mp4"
        
        info = get_video_info(missing_video)
        
        self.assertIsNone(info)

    def test_statistics_accuracy(self):
        """Test that statistics are calculated correctly."""
        output_csv = self.output_dir / "curated_clips_stats.csv"
        manifest_output = self.output_dir / "curated_manifest_stats.json"
        
        curate_clips(
            raw_dir=self.raw_dir,
            output_csv=output_csv,
            manifest_output=manifest_output
        )
        
        with open(manifest_output, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        stats = manifest['statistics']
        
        self.assertEqual(stats['total_processed'], 5)
        self.assertEqual(stats['curated_count'], 2)
        self.assertEqual(stats['rejected_count'], 3)
        self.assertEqual(stats['resolution_rejected'], 2)  # small and bad
        self.assertEqual(stats['duration_rejected'], 2)  # long and bad
        self.assertEqual(stats['both_rejected'], 1)  # bad