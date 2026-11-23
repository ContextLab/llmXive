"""
Unit tests for the CV Pipeline.
"""
import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.filtering.cv_pipeline import (
    KalmanFilter1D, 
    TrajectoryExtractor, 
    run_cv_pipeline,
    DEFAULT_KALMAN_Q,
    DEFAULT_KALMAN_R
)

class TestKalmanFilter1D:
    def test_init(self):
        kf = KalmanFilter1D()
        assert kf.q == DEFAULT_KALMAN_Q
        assert kf.r == DEFAULT_KALMAN_R
        assert kf.x.shape == (2,)
        assert kf.P.shape == (2, 2)

    def test_update_single_point(self):
        kf = KalmanFilter1D()
        kf.update(10.0)
        state = kf.get_state()
        assert abs(state - 10.0) < 1.0 # Should be close to input

    def test_smooth_noisy_data(self):
        kf = KalmanFilter1D(q=0.01, r=1.0) # High measurement noise
        data = [10.0, 10.5, 9.5, 10.2, 9.8]
        for val in data:
            kf.update(val)
        state = kf.get_state()
        # Should be close to the mean
        assert 9.5 < state < 10.5

class TestTrajectoryExtractor:
    @pytest.fixture
    def mock_models(self):
        with patch('src.filtering.cv_pipeline.build_sam2') as mock_sam, \
             patch('src.filtering.cv_pipeline.SAM2ImagePredictor') as mock_pred, \
             patch('src.filtering.cv_pipeline.create_model') as mock_zoe:
            
            mock_sam.return_value = MagicMock()
            mock_pred.return_value = MagicMock()
            mock_zoe.return_value = MagicMock()
            mock_zoe.return_value.infer_pil.return_value = torch.ones((100, 100)) * 10.0
            
            yield mock_sam, mock_pred, mock_zoe

    def test_process_frame_with_mask(self, mock_models):
        # This test requires torch
        try:
            import torch
        except ImportError:
            pytest.skip("PyTorch not available")

        extractor = TrajectoryExtractor.__new__(TrajectoryExtractor)
        extractor.device = "cpu"
        extractor.sam2_model = MagicMock()
        extractor.sam2_predictor = MagicMock()
        extractor.zoe_model = MagicMock()
        extractor.zoe_model.infer_pil.return_value = torch.ones((100, 100)) * 10.0

        # Create a dummy frame
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, 40:60] = 255 # Center square

        result = extractor.process_frame(frame, mask)

        assert "mask" in result
        assert "centroid_2d" in result
        assert "depth_val" in result
        assert result["centroid_2d"] == (50, 50)
        assert result["depth_val"] == 10.0

    def test_extract_trajectory(self, mock_models):
        try:
            import torch
        except ImportError:
            pytest.skip("PyTorch not available")

        extractor = TrajectoryExtractor.__new__(TrajectoryExtractor)
        extractor.device = "cpu"
        extractor.sam2_model = MagicMock()
        extractor.sam2_predictor = MagicMock()
        extractor.zoe_model = MagicMock()
        extractor.zoe_model.infer_pil.return_value = torch.ones((100, 100)) * 10.0

        frames = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(5)]
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, 40:60] = 255

        trajectory = extractor.extract_trajectory(frames, mask)

        assert len(trajectory) == 5
        for point in trajectory:
            assert "frame_idx" in point
            assert "centroid_2d" in point
            assert "depth" in point

class TestRunCVPipeline:
    def test_run_cv_pipeline_integration(self):
        try:
            import torch
        except ImportError:
            pytest.skip("PyTorch not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            scene_config_path = Path(tmpdir) / "scene.json"
            output_path = Path(tmpdir) / "trajectory.json"

            # Mock video file creation (dummy)
            # In a real test, we would need a valid video file.
            # For unit test, we might mock cv2.VideoCapture
            # But let's test the logic flow with mocks.
            
            scene_config = {
                "objects": [
                    {"bbox": [40, 40, 20, 20], "mask": None} # Fallback to bbox
                ]
            }
            with open(scene_config_path, 'w') as f:
                json.dump(scene_config, f)

            # Mock cv2
            with patch('src.filtering.cv_pipeline.cv2.VideoCapture') as mock_cap, \
                 patch('src.filtering.cv_pipeline.TrajectoryExtractor') as MockExtractor:
                 
                 # Setup mock video
                 mock_cap_instance = MagicMock()
                 mock_cap_instance.read.side_effect = [
                     (True, np.zeros((100, 100, 3), dtype=np.uint8)),
                     (True, np.zeros((100, 100, 3), dtype=np.uint8)),
                     (False, None)
                 ]
                 mock_cap.return_value = mock_cap_instance

                 # Setup mock extractor
                 mock_extractor = MagicMock()
                 mock_extractor.extract_trajectory.return_value = [
                     {"frame_idx": 0, "centroid_2d": (50, 50), "depth": 10.0},
                     {"frame_idx": 1, "centroid_2d": (50, 50), "depth": 10.0}
                 ]
                 MockExtractor.return_value = mock_extractor

                 result = run_cv_pipeline(str(video_path), str(scene_config_path), str(output_path))

                 assert result["status"] == "success"
                 assert result["num_frames"] == 2
                 assert os.path.exists(output_path)

                 with open(output_path, 'r') as f:
                     saved_data = json.load(f)
                 assert saved_data["status"] == "success"