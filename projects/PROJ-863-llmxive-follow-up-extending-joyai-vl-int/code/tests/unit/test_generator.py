"""
Unit tests for src.data_synthesis.generator
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from src.data_synthesis.generator import generate_activity_sequence, generate_video_stream, FRAME_RATE


class TestGenerateActivitySequence:
    def test_sequence_length(self):
        """Verify the generator produces the correct number of frames."""
        duration = 10  # seconds
        frames = list(generate_activity_sequence(duration, frame_rate=FRAME_RATE))
        expected_frames = duration * FRAME_RATE
        assert len(frames) == expected_frames
    
    def test_activity_distribution(self):
        """Verify activities are drawn from the valid set."""
        valid_activities = {'sitting', 'standing', 'walking', 'falling', 'lying_down'}
        frames = list(generate_activity_sequence(5, frame_rate=FRAME_RATE))
        for f in frames:
            assert f['activity'] in valid_activities
    
    def test_critical_labeling(self):
        """Verify 'falling' activity is marked as critical."""
        frames = list(generate_activity_sequence(100, frame_rate=FRAME_RATE, seed=42))
        critical_frames = [f for f in frames if f['is_critical']]
        for f in critical_frames:
            assert f['activity'] == 'falling'
        # Verify non-falling frames are not critical
        non_critical_frames = [f for f in frames if not f['is_critical']]
        for f in non_critical_frames:
            assert f['activity'] != 'falling'
    
    def test_deterministic_seed(self):
        """Verify same seed produces same sequence."""
        seq1 = list(generate_activity_sequence(10, frame_rate=FRAME_RATE, seed=123))
        seq2 = list(generate_activity_sequence(10, frame_rate=FRAME_RATE, seed=123))
        seq3 = list(generate_activity_sequence(10, frame_rate=FRAME_RATE, seed=456))
        
        assert seq1 == seq2
        assert seq1 != seq3


class TestGenerateVideoStream:
    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @patch('src.data_synthesis.generator.get_handoff_manager')
    @patch('src.data_synthesis.generator.get_logger')
    def test_writes_to_disk(self, mock_logger, mock_handoff_mgr, temp_output_dir):
        """Verify the generator writes JSONL files to disk."""
        mock_handoff_instance = MagicMock()
        mock_handoff_mgr.return_value = mock_handoff_instance
        
        duration = 2  # seconds (small for test)
        generate_video_stream(
            duration_seconds=duration,
            output_dir=temp_output_dir,
            chunk_duration=duration, # Force 1 chunk
            seed=42
        )

        # Check files exist
        files = list(temp_output_dir.glob("chunk_*.jsonl"))
        assert len(files) == 1
        
        # Verify content is valid JSONL
        with open(files[0]) as f:
            lines = f.readlines()
        assert len(lines) == duration * FRAME_RATE
        for line in lines:
            data = json.loads(line)
            assert "frame_index" in data
            assert "activity" in data

    @patch('src.data_synthesis.generator.get_handoff_manager')
    def test_manifest_entries_returned(self, mock_handoff_mgr, temp_output_dir):
        """Verify the function returns manifest entries."""
        mock_handoff_instance = MagicMock()
        mock_handoff_mgr.return_value = mock_handoff_instance

        duration = 2
        manifest = generate_video_stream(
            duration_seconds=duration,
            output_dir=temp_output_dir,
            chunk_duration=duration,
            seed=42
        )

        assert isinstance(manifest, list)
        assert len(manifest) >= 1
        assert "chunk_id" in manifest[0]
        assert "file_path" in manifest[0]
        assert "frame_count" in manifest[0]

    @patch('src.data_synthesis.generator.get_handoff_manager')
    def test_ci_mode_subset(self, mock_handoff_mgr, temp_output_dir):
        """Verify CI mode limits duration."""
        mock_handoff_instance = MagicMock()
        mock_handoff_mgr.return_value = mock_handoff_instance

        # Request 100 hours, but CI mode should cap it
        duration = 360000 # 100 hours
        manifest = generate_video_stream(
            duration_seconds=duration,
            output_dir=temp_output_dir,
            chunk_duration=60, # Small chunks for speed
            seed=42,
            is_ci_mode=True
        )

        total_frames = sum(e["frame_count"] for e in manifest)
        # Should be capped at ~1 hour (3600 seconds)
        assert total_frames <= (3600 * FRAME_RATE) + 100 # Allow small margin for chunking
        # Should be significantly less than requested 100 hours
        assert total_frames < (360000 * FRAME_RATE)

    @patch('src.data_synthesis.generator.log_no_vlm_call')
    @patch('src.data_synthesis.generator.get_handoff_manager')
    def test_logs_no_vlm_call(self, mock_handoff_mgr, mock_log_no_vlm, temp_output_dir):
        """Verify the generator logs that no VLM was used."""
        mock_handoff_instance = MagicMock()
        mock_handoff_mgr.return_value = mock_handoff_instance

        generate_video_stream(
            duration_seconds=1,
            output_dir=temp_output_dir,
            seed=42
        )

        mock_log_no_vlm.assert_called()