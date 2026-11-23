"""
Unit tests for the downsampler module.
"""

import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.downsampler import (
    DownsamplingError,
    VideoClip,
    extract_4s_clips,
    downsample_frames,
    process_stream_for_clips
)


class TestVideoClip(unittest.TestCase):
    """Tests for VideoClip class."""

    def test_create_valid_clip(self):
        """Test creating a valid VideoClip."""
        frames = [np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
                 for _ in range(100)]
        metadata = {'id': 'test_001', 'class': 'running'}

        clip = VideoClip(
            frames=frames,
            metadata=metadata,
            timestamp_start=0.0,
            timestamp_end=4.0
        )

        self.assertEqual(clip.num_frames, 100)
        self.assertEqual(clip.duration, 4.0)
        self.assertEqual(clip.metadata['id'], 'test_001')
        self.assertEqual(len(clip.frames), 100)

    def test_create_clip_with_empty_frames(self):
        """Test that creating a clip with empty frames raises an error."""
        with self.assertRaises(DownsamplingError):
            VideoClip(
                frames=[],
                metadata={'id': 'test'},
                timestamp_start=0.0,
                timestamp_end=4.0
            )

    def test_create_clip_with_inconsistent_frame_shapes(self):
        """Test that inconsistent frame shapes raise an error."""
        frames = [
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8),
            np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        ]

        with self.assertRaises(DownsamplingError):
            VideoClip(
                frames=frames,
                metadata={'id': 'test'},
                timestamp_start=0.0,
                timestamp_end=4.0
            )

    def test_to_tensor(self):
        """Test converting VideoClip to tensor."""
        frames = [np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
                 for _ in range(10)]
        clip = VideoClip(
            frames=frames,
            metadata={'id': 'test'},
            timestamp_start=0.0,
            timestamp_end=4.0
        )

        tensor = clip.to_tensor()

        self.assertEqual(tensor.shape, (10, 224, 224, 3))
        self.assertTrue(0 <= tensor.min() <= 1)
        self.assertTrue(0 <= tensor.max() <= 1)

    def test_repr(self):
        """Test string representation of VideoClip."""
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(10)]
        clip = VideoClip(
            frames=frames,
            metadata={'id': 'test_001'},
            timestamp_start=0.0,
            timestamp_end=4.0
        )

        repr_str = repr(clip)
        self.assertIn('VideoClip', repr_str)
        self.assertIn('test_001', repr_str)


class TestExtract4sClips(unittest.TestCase):
    """Tests for extract_4s_clips function."""

    def test_extract_clips_from_long_video(self):
        """Test extracting 4-second clips from a long video."""
        fps = 30.0
        duration = 16.0  # 16 seconds
        num_frames = int(duration * fps)  # 480 frames
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(num_frames)]

        clips = extract_4s_clips(frames, fps=fps, target_duration=4.0)

        # Should get 4 non-overlapping 4-second clips (16s / 4s = 4)
        self.assertEqual(len(clips), 4)
        for clip in clips:
            self.assertEqual(len(clip), int(4.0 * fps))  # 120 frames per clip

    def test_extract_clips_from_short_video(self):
        """Test that short videos raise an error."""
        fps = 30.0
        # 2 seconds of video (60 frames)
        num_frames = int(2.0 * fps)
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(num_frames)]

        with self.assertRaises(DownsamplingError):
            extract_4s_clips(frames, fps=fps, target_duration=4.0)

    def test_extract_clips_empty_frames(self):
        """Test that empty frame list raises an error."""
        with self.assertRaises(DownsamplingError):
            extract_4s_clips([], fps=30.0, target_duration=4.0)

    def test_extract_clips_invalid_fps(self):
        """Test that invalid FPS raises an error."""
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(100)]

        with self.assertRaises(DownsamplingError):
            extract_4s_clips(frames, fps=0.0, target_duration=4.0)

        with self.assertRaises(DownsamplingError):
            extract_4s_clips(frames, fps=-1.0, target_duration=4.0)

    def test_extract_clips_invalid_duration(self):
        """Test that invalid duration raises an error."""
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(100)]

        with self.assertRaises(DownsamplingError):
            extract_4s_clips(frames, fps=30.0, target_duration=0.0)

        with self.assertRaises(DownsamplingError):
            extract_4s_clips(frames, fps=30.0, target_duration=-1.0)


class TestDownsampleFrames(unittest.TestCase):
    """Tests for downsample_frames function."""

    def test_downsample_frames(self):
        """Test frame downsampling."""
        # Create 10 frames of 448x448
        frames = [np.random.randint(0, 255, (448, 448, 3), dtype=np.uint8)
                 for _ in range(10)]

        downsampled = downsample_frames(
            frames,
            target_size=(224, 224),
            frame_sampling_rate=1
        )

        self.assertEqual(len(downsampled), 10)
        self.assertEqual(downsampled[0].shape, (224, 224, 3))

    def test_downsample_with_frame_sampling(self):
        """Test downsampling with frame sampling."""
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(20)]

        downsampled = downsample_frames(
            frames,
            target_size=(224, 224),
            frame_sampling_rate=2  # Keep every 2nd frame
        )

        self.assertEqual(len(downsampled), 10)  # 20 / 2 = 10

    def test_downsample_empty_frames(self):
        """Test downsampling empty frame list."""
        downsampled = downsample_frames([], target_size=(224, 224))
        self.assertEqual(len(downsampled), 0)

    def test_downsample_invalid_target_size(self):
        """Test that invalid target size raises an error."""
        frames = [np.zeros((224, 224, 3), dtype=np.uint8)]

        with self.assertRaises(DownsamplingError):
            downsample_frames(frames, target_size=(0, 0))

        with self.assertRaises(DownsamplingError):
            downsample_frames(frames, target_size=(-1, -1))

    def test_downsample_invalid_sampling_rate(self):
        """Test that invalid sampling rate raises an error."""
        frames = [np.zeros((224, 224, 3), dtype=np.uint8)]

        with self.assertRaises(DownsamplingError):
            downsample_frames(frames, frame_sampling_rate=0)

        with self.assertRaises(DownsamplingError):
            downsample_frames(frames, frame_sampling_rate=-1)


class TestProcessStreamForClips(unittest.TestCase):
    """Tests for process_stream_for_clips function."""

    def test_process_stream_with_mock_data(self):
        """Test processing a mock streaming dataset."""
        # Create mock samples
        mock_samples = [
            {
                'id': 'test_001',
                'label': 'running',
                'video': [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(120)],
                'fps': 30.0
            },
            {
                'id': 'test_002',
                'label': 'walking',
                'video': [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(120)],
                'fps': 30.0
            }
        ]

        def mock_stream():
            for sample in mock_samples:
                yield sample

        clips = list(process_stream_for_clips(
            mock_stream(),
            target_size=(224, 224),
            frame_sampling_rate=1,
            target_duration=4.0,
            max_clips=5
        ))

        # Each 120-frame video at 30fps = 4 seconds, so 1 clip per sample
        self.assertEqual(len(clips), 2)
        self.assertEqual(clips[0].metadata['id'], 'test_001')
        self.assertEqual(clips[1].metadata['id'], 'test_002')

    def test_process_stream_max_clips(self):
        """Test that max_clips parameter limits output."""
        mock_samples = [
            {
                'id': f'test_{i:03d}',
                'label': 'class',
                'video': [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(120)],
                'fps': 30.0
            }
            for i in range(10)
        ]

        def mock_stream():
            for sample in mock_samples:
                yield sample

        clips = list(process_stream_for_clips(
            mock_stream(),
            target_size=(224, 224),
            max_clips=3
        ))

        self.assertEqual(len(clips), 3)

    def test_process_stream_short_videos_skipped(self):
        """Test that videos too short are skipped."""
        mock_samples = [
            {
                'id': 'short_001',
                'label': 'class',
                'video': [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(60)],  # 2 seconds
                'fps': 30.0
            },
            {
                'id': 'long_001',
                'label': 'class',
                'video': [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(120)],  # 4 seconds
                'fps': 30.0
            }
        ]

        def mock_stream():
            for sample in mock_samples:
                yield sample

        clips = list(process_stream_for_clips(
            mock_stream(),
            target_size=(224, 224),
            target_duration=4.0
        ))

        # Only the long video should produce a clip
        self.assertEqual(len(clips), 1)
        self.assertEqual(clips[0].metadata['id'], 'long_001')


if __name__ == '__main__':
    unittest.main()