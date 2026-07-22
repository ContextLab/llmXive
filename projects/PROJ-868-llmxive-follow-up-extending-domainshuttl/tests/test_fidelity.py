"""
Tests for T020: Full Fidelity Curve Scoring.
"""

import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from src.analysis.fidelity import (
    run_fidelity_curve_scoring,
    _extract_frames,
    _compute_clip_similarity,
    _run_generation_with_timeout,
    OUTPUT_FILE
)


class TestFidelityCurveScoring:
    """Test the full fidelity curve scoring pipeline."""

    @pytest.fixture
    def mock_subject_ids(self):
        return ["subject_001", "subject_002"]

    @pytest.fixture
    def mock_dimensions(self):
        return [16, 32]

    @pytest.fixture
    def mock_styles(self):
        return ['Anime', 'Sketch']

    @patch('src.analysis.fidelity._load_clip_model')
    @patch('src.analysis.fidelity._run_generation_with_timeout')
    @patch('src.analysis.fidelity._extract_frames')
    @patch('src.analysis.fidelity._compute_clip_similarity')
    @patch('pandas.read_csv')
    def test_run_fidelity_curve_scoring(
        self,
        mock_read_csv,
        mock_compute_similarity,
        mock_extract_frames,
        mock_run_gen,
        mock_load_clip,
        mock_subject_ids,
        mock_dimensions,
        mock_styles
    ):
        """Test that run_fidelity_curve_scoring produces expected output structure."""
        # Setup mocks
        mock_read_csv.return_value = MagicMock(__iter__=lambda self: iter([
            {"subject_id": "subject_001", "complexity_score": 0.5},
            {"subject_id": "subject_002", "complexity_score": 0.7}
        ]))
        mock_read_csv.return_value.__getitem__ = lambda self, key: [
            "subject_001", "subject_002"
        ] if key == "subject_id" else [0.5, 0.7]
        mock_read_csv.return_value.tolist = lambda: ["subject_001", "subject_002"]

        mock_load_clip.return_value = (MagicMock(), MagicMock())

        # Mock video paths
        mock_video_path = MagicMock()
        mock_video_path.exists.return_value = True
        mock_run_gen.return_value = mock_video_path

        # Mock frames
        mock_frames = [MagicMock()] * 5
        mock_extract_frames.return_value = mock_frames

        # Mock similarity score
        mock_compute_similarity.return_value = 0.85

        # Run the function
        results = run_fidelity_curve_scoring(
            subject_ids=mock_subject_ids,
            dimensions=mock_dimensions,
            styles=mock_styles,
            timeout_per_sample=60
        )

        # Verify structure
        assert "subject_001" in results
        assert "subject_002" in results
        for dim in mock_dimensions:
            assert str(dim) in results["subject_001"]
            for style in mock_styles:
                assert style in results["subject_001"][str(dim)]
                # Should be a float or None
                assert isinstance(results["subject_001"][str(dim)][style], (float, type(None)))

        # Verify file was written
        output_path = Path(OUTPUT_FILE)
        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        assert saved_results == results

    def test_extract_frames_empty_video(self):
        """Test frame extraction handles empty videos gracefully."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            # Write some dummy bytes to simulate a file
            tmp.write(b'\x00' * 100)
            tmp_path = Path(tmp.name)

        with pytest.raises(ValueError, match="Video has 0 frames"):
            _extract_frames(tmp_path, num_frames=5)

        # Clean up
        os.unlink(tmp_path)

    @patch('src.analysis.fidelity.with_timeout')
    def test_run_generation_with_timeout_success(self, mock_with_timeout):
        """Test timeout wrapper returns video path on success."""
        mock_video_path = MagicMock()
        mock_with_timeout.return_value = mock_video_path

        result = _run_generation_with_timeout("subj_001", 16, "Anime", timeout_seconds=60)

        assert result == mock_video_path
        mock_with_timeout.assert_called_once()

    @patch('src.analysis.fidelity.with_timeout')
    def test_run_generation_with_timeout_failure(self, mock_with_timeout):
        """Test timeout wrapper returns None on timeout/error."""
        mock_with_timeout.side_effect = Exception("Timeout")

        result = _run_generation_with_timeout("subj_001", 16, "Anime", timeout_seconds=60)

        assert result is None

@pytest.fixture
def sample_frames():
    """Create dummy PIL Images for testing."""
    from PIL import Image
    return [Image.new('RGB', (100, 100), color='red') for _ in range(5)]

@patch('src.analysis.fidelity.clip.load')
def test_compute_clip_similarity(mock_clip_load, sample_frames):
    """Test CLIP similarity computation."""
    # Mock model and preprocess
    mock_model = MagicMock()
    mock_model.encode_image.return_value = torch.randn(5, 512)
    mock_preprocess = MagicMock()
    mock_preprocess.return_value = torch.randn(3, 224, 224)

    mock_clip_load.return_value = (mock_model, mock_preprocess)

    # We need to mock the device handling
    with patch('torch.stack') as mock_stack, \
         patch('torch.no_grad') as mock_no_grad:

        mock_stack.return_value = torch.randn(5, 3, 224, 224)
        mock_no_grad.return_value.__enter__ = MagicMock()
        mock_no_grad.return_value.__exit__ = MagicMock()

        # Mock the encode_image chain
        mock_features = torch.randn(5, 512)
        mock_model.encode_image.return_value = mock_features

        # Mock normalization and similarity
        with patch('torch.nn.functional.normalize') as mock_norm, \
             patch('torch.matmul') as mock_matmul:

            mock_norm.return_value = mock_features
            mock_matmul.return_value = torch.tensor([[0.85]])

            score = _compute_clip_similarity(
                mock_model, mock_preprocess, sample_frames, sample_frames, "cpu"
            )

            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])