"""
Unit tests for T040: Motion labels (optical flow) logic.

Tests that motion_labels.py correctly computes optical flow magnitude.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import numpy as np

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.stats.motion_labels import compute_optical_flow_magnitude, generate_motion_labels


class TestOpticalFlowComputation:
    """Tests for optical flow magnitude computation."""

    @patch('src.stats.motion_labels.cv2.calcOpticalFlowFarneback')
    def test_compute_optical_flow_magnitude_returns_positive_value(self, mock_calc_flow):
        """Test that optical flow computation returns a positive magnitude."""
        # Mock flow to return a simple flow field
        mock_flow = np.array([
            [[1.0, 0.0], [0.0, 1.0]],
            [[1.0, 0.0], [0.0, 1.0]]
        ], dtype=np.float32)
        
        mock_calc_flow.return_value = mock_flow
        
        # Create mock frames
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
        
        magnitude = compute_optical_flow_magnitude(frame1, frame2)
        
        assert isinstance(magnitude, (int, float))
        assert magnitude >= 0
        mock_calc_flow.assert_called_once()

    @patch('src.stats.motion_labels.cv2.calcOpticalFlowFarneback')
    def test_compute_optical_flow_magnitude_handles_zero_flow(self, mock_calc_flow):
        """Test computation when there is no motion."""
        # Mock zero flow
        mock_flow = np.zeros((100, 100, 2), dtype=np.float32)
        mock_calc_flow.return_value = mock_flow
        
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
        
        magnitude = compute_optical_flow_magnitude(frame1, frame2)
        
        assert magnitude == 0.0


class TestMotionLabelGeneration:
    """Tests for motion label generation."""

    def test_generate_motion_labels_classifies_high_motion(self):
        """Test that high optical flow is classified as 'High' motion."""
        threshold = 0.05
        high_magnitude = 0.15
        
        label = generate_motion_labels(high_magnitude, threshold)
        
        assert label == 'High'

    def test_generate_motion_labels_classifies_low_motion(self):
        """Test that low optical flow is classified as 'Low' motion."""
        threshold = 0.05
        low_magnitude = 0.02
        
        label = generate_motion_labels(low_magnitude, threshold)
        
        assert label == 'Low'

    def test_generate_motion_labels_classifies_boundary_case(self):
        """Test classification at the exact threshold."""
        threshold = 0.05
        boundary_magnitude = 0.05
        
        label = generate_motion_labels(boundary_magnitude, threshold)
        
        # Should be classified as 'High' when equal to threshold
        assert label == 'High'

    def test_generate_motion_labels_handles_edge_cases(self):
        """Test edge cases like negative or very large values."""
        threshold = 0.05
        
        # Negative magnitude (shouldn't happen but test robustness)
        label_neg = generate_motion_labels(-0.01, threshold)
        assert label_neg == 'Low'
        
        # Very large magnitude
        label_large = generate_motion_labels(100.0, threshold)
        assert label_large == 'High'
