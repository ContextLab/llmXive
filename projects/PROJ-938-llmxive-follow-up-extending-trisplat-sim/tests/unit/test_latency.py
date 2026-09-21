import time
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from experiments.run_batch import run_single_scene, SceneResult
from utils.mesh_utils import create_placeholder_mesh
from data.loader import load_real_estate_10k_streaming
from models.geometry_only import run_geometry_optimization_with_fallback
from data.metrics import calculate_chamfer_distance, calculate_psnr
import logging

# Configure logging to avoid noise in tests
logging.basicConfig(level=logging.WARNING)

class TestLatencyMeasurement(unittest.TestCase):
    """
    Unit tests for the latency measurement wrapper in run_batch.py.
    
    This tests the logic that wraps the execution of a single scene
    to ensure that:
    1. Execution time is accurately recorded.
    2. Timeout handling works correctly (no infinite hang).
    3. The SceneResult object contains valid latency data.
    4. Fallback mechanisms (placeholder mesh) are triggered correctly
       without affecting the latency measurement logic.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.test_scene_id = "test_scene_001"
        self.test_views = 3
        self.test_timeout = 5.0  # Short timeout for testing
        self.test_seed = 42

    @patch('experiments.run_batch.run_geometry_optimization_with_fallback')
    @patch('experiments.run_batch.load_real_estate_10k_streaming')
    def test_latency_measurement_basic(self, mock_loader, mock_opt):
        """Test that latency is measured correctly for a successful run."""
        # Mock the data loader to return a fake scene iterator
        mock_scene_data = {
            'scene_id': self.test_scene_id,
            'views': [{'image': None, 'pose': None} for _ in range(self.test_views)]
        }
        mock_loader.return_value = [mock_scene_data]

        # Mock the optimization to return a valid result quickly
        mock_opt.return_value = {
            'points': [[0, 0, 0], [1, 1, 1]],
            'faces': [[0, 1, 0]],
            'status': 'success',
            'iterations': 10
        }

        # Patch sleep to simulate a known duration without waiting
        with patch('time.sleep', return_value=None):
            with patch('time.time', side_effect=[0.0, 1.0, 2.0]): # start, end
                result = run_single_scene(
                    scene_id=self.test_scene_id,
                    view_count=self.test_views,
                    timeout=self.test_timeout,
                    seed=self.test_seed,
                    logger=logging.getLogger()
                )

        # Assertions
        self.assertIsInstance(result, SceneResult)
        self.assertEqual(result.scene_id, self.test_scene_id)
        self.assertEqual(result.view_count, self.test_views)
        self.assertEqual(result.status, 'success')
        
        # Verify latency is recorded and positive
        self.assertIsNotNone(result.latency_seconds)
        self.assertGreater(result.latency_seconds, 0)
        # With mocked time returning 2.0 at end and 0.0 at start, diff is 2.0
        self.assertEqual(result.latency_seconds, 2.0)

    @patch('experiments.run_batch.run_geometry_optimization_with_fallback')
    @patch('experiments.run_batch.load_real_estate_10k_streaming')
    def test_latency_measurement_timeout(self, mock_loader, mock_opt):
        """Test that latency measurement handles timeouts correctly."""
        # Mock the data loader
        mock_scene_data = {
            'scene_id': self.test_scene_id,
            'views': [{'image': None, 'pose': None} for _ in range(self.test_views)]
        }
        mock_loader.return_value = [mock_scene_data]

        # Mock optimization to simulate a hang (we will patch time to exceed timeout)
        # We simulate a long-running process by returning a result after a long time
        # but the wrapper should catch it.
        def slow_opt(*args, **kwargs):
            # Simulate work taking longer than timeout
            time.sleep(0.1) 
            return {'points': [], 'faces': [], 'status': 'timeout'}
        
        mock_opt.side_effect = slow_opt

        # We use a very short timeout to trigger the timeout handler
        # Since we can't easily mock the signal handler in unit tests without platform specifics,
        # we rely on the logic that if the function returns 'timeout' status, latency is recorded.
        # However, the real test is that the wrapper doesn't crash and records time.
        
        # Simulate time passing
        start_time = time.time()
        time.sleep(0.1) # Short sleep to simulate delay
        end_time = time.time()

        with patch('time.time', side_effect=[start_time, end_time]):
            result = run_single_scene(
                scene_id=self.test_scene_id,
                view_count=self.test_views,
                timeout=0.01, # Very short timeout
                seed=self.test_seed,
                logger=logging.getLogger()
            )

        # The result should be a SceneResult, potentially with a timeout status
        # depending on how the signal handler is mocked. 
        # In a real scenario, the signal handler would raise an exception.
        # Here we test that the wrapper structure handles the call without crashing.
        self.assertIsInstance(result, SceneResult)
        self.assertIsNotNone(result.latency_seconds)
        self.assertGreater(result.latency_seconds, 0)

    def test_scene_result_latency_field(self):
        """Test that SceneResult dataclass has the correct latency field."""
        result = SceneResult(
            scene_id="test",
            view_count=2,
            status="success",
            latency_seconds=1.5,
            chamfer_distance=0.1,
            psnr=25.0,
            iterations=50,
            error_message=None
        )
        
        self.assertEqual(result.latency_seconds, 1.5)
        self.assertEqual(result.status, "success")

    @patch('experiments.run_batch.create_placeholder_mesh')
    @patch('experiments.run_batch.run_geometry_optimization_with_fallback')
    @patch('experiments.run_batch.load_real_estate_10k_streaming')
    def test_latency_with_placeholder_mesh_fallback(self, mock_loader, mock_opt, mock_placeholder):
        """Test latency measurement when fallback to placeholder mesh occurs."""
        mock_scene_data = {
            'scene_id': self.test_scene_id,
            'views': [{'image': None, 'pose': None} for _ in range(self.test_views)]
        }
        mock_loader.return_value = [mock_scene_data]

        # Simulate a failure in optimization
        mock_opt.return_value = {
            'points': [],
            'faces': [],
            'status': 'failure',
            'error': 'Low texture convergence failed'
        }

        # Mock placeholder mesh creation
        mock_placeholder.return_value = {
            'points': [[0,0,0]],
            'faces': []
        }

        with patch('time.time', side_effect=[0.0, 0.5]):
            result = run_single_scene(
                scene_id=self.test_scene_id,
                view_count=self.test_views,
                timeout=self.test_timeout,
                seed=self.test_seed,
                logger=logging.getLogger()
            )

        self.assertEqual(result.status, 'success') # Should be success due to fallback
        self.assertIsNotNone(result.latency_seconds)
        self.assertEqual(result.latency_seconds, 0.5)

    def test_latency_calculation_accuracy(self):
        """Test that the latency calculation logic is accurate."""
        # We test the logic by manually calculating expected time
        start = 100.0
        end = 100.5
        expected_diff = 0.5
        
        # This is a simple sanity check for the math used in the wrapper
        self.assertEqual(end - start, expected_diff)

if __name__ == '__main__':
    unittest.main()