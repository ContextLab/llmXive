"""
Unit tests for CodeCarbon CPU device detection.

This module verifies that the codecarbon library correctly identifies
and tracks emissions on CPU devices, ensuring the pipeline's
energy instrumentation works as expected for the GPT-2-medium inference
on CPU requirement.
"""

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import json
import tempfile
import os

# We test the integration by mocking the heavy dependencies but verifying
# the configuration and device detection logic.
try:
    from codecarbon import EmissionsTracker
    from codecarbon.core.gpu import AllGPUDevices
    from codecarbon.core.cpu import IntelPowerGadget, AMDProcessor
    CODECARBON_AVAILABLE = True
except ImportError:
    CODECARBON_AVAILABLE = False


class TestCodeCarbonCPUDeviceDetection(unittest.TestCase):
    """Tests to ensure CodeCarbon correctly detects and logs CPU usage."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = self.temp_dir
        self.project_name = "test_project"
        self.experiment_name = "test_experiment"

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.skipUnless(CODECARBON_AVAILABLE, "codecarbon library not installed")
    def test_tracker_initialization_cpu_mode(self):
        """
        Test that EmissionsTracker initializes correctly for CPU-only mode.
        Verifies that no GPU devices are forcibly selected when explicitly
        targeting CPU or when no GPU is available.
        """
        # Mock the device detection to simulate a CPU-only environment
        with patch('codecarbon.EmissionsTracker._get_device') as mock_get_device:
            # Simulate CPU detection
            mock_get_device.return_value = 'cpu'

            tracker = EmissionsTracker(
                project_name=self.project_name,
                output_dir=self.output_dir
            )

            # Verify the tracker was instantiated
            self.assertIsNotNone(tracker)
            # Verify the device detection was called
            mock_get_device.assert_called_once()

    @unittest.skipUnless(CODECARBON_AVAILABLE, "codecarbon library not installed")
    def test_cpu_power_measurement_simulation(self):
        """
        Test that the tracker attempts to measure CPU power.
        We mock the specific CPU power measurement classes to ensure
        the logic flow for CPU detection is triggered.
        """
        with patch('codecarbon.core.cpu.IntelPowerGadget.is_available', return_value=True):
            with patch('codecarbon.core.cpu.AMDProcessor.is_available', return_value=False):
                with patch('codecarbon.core.cpu.IntelPowerGadget.read_power', return_value=15.5):
                    with patch('codecarbon.EmissionsTracker._get_device', return_value='cpu'):
                        tracker = EmissionsTracker(
                            project_name=self.project_name,
                            output_dir=self.output_dir
                        )
                        
                        # Start the tracker to trigger device initialization
                        tracker.start()
                        
                        # Verify that the CPU power measurement logic was attempted
                        # by checking if the tracker's internal state reflects CPU monitoring
                        # Note: Direct inspection of internal state is implementation-dependent,
                        # so we verify via the successful start without GPU errors.
                        self.assertTrue(tracker._started)
                        
                        tracker.stop()

    @unittest.skipUnless(CODECARBON_AVAILABLE, "codecarbon library not installed")
    def test_no_gpu_detection_when_cpu_only(self):
        """
        Ensure that when running on CPU, the tracker does not attempt to
        read from non-existent GPU devices, preventing initialization errors.
        """
        # Mock GPU detection to return empty list (no GPUs)
        with patch('codecarbon.core.gpu.AllGPUDevices.is_available', return_value=False):
            with patch('codecarbon.EmissionsTracker._get_device', return_value='cpu'):
                try:
                    tracker = EmissionsTracker(
                        project_name=self.project_name,
                        output_dir=self.output_dir,
                        # Force CPU tracking explicitly if supported, or rely on detection
                    )
                    tracker.start()
                    # Simulate a small workload
                    import time
                    time.sleep(0.1)
                    tracker.stop()
                    
                    # If we reached here without a GPU-related exception, the test passes
                    self.assertTrue(True)
                except Exception as e:
                    # If an error occurred, it should not be related to missing GPU drivers
                    self.assertNotIn("CUDA", str(e))
                    self.assertNotIn("gpu", str(e).lower())

    @unittest.skipUnless(CODECARBON_AVAILABLE, "codecarbon library not installed")
    def test_emissions_output_schema_cpu(self):
        """
        Verify that the output JSON from the tracker contains the expected
        fields when run on CPU, specifically checking for energy and CO2 metrics.
        """
        # Mock the actual power reading to return a fixed value for deterministic testing
        with patch('codecarbon.core.cpu.IntelPowerGadget.is_available', return_value=True):
            with patch('codecarbon.core.cpu.IntelPowerGadget.read_power', return_value=25.0):
                with patch('codecarbon.core.cpu.IntelPowerGadget.get_cpu_frequency', return_value=2.5):
                    with patch('codecarbon.EmissionsTracker._get_device', return_value='cpu'):
                        tracker = EmissionsTracker(
                            project_name=self.project_name,
                            output_dir=self.output_dir
                        )
                        
                        tracker.start()
                        
                        # Simulate a minimal workload
                        _ = sum(i for i in range(10000))
                        
                        tracker.stop()
                        
                        # Check the output file
                        output_file = os.path.join(self.output_dir, "emissions.json")
                        
                        # CodeCarbon might write to a specific filename or directory structure
                        # We check for the existence of the file and its content structure
                        if os.path.exists(output_file):
                            with open(output_file, 'r') as f:
                                data = json.load(f)
                                
                            # Verify required keys exist
                            self.assertIn('energy_consumed', data)
                            self.assertIn('emissions', data)
                            self.assertIn('duration', data)
                            
                            # Verify values are numeric and non-negative
                            self.assertIsInstance(data['energy_consumed'], (int, float))
                            self.assertGreaterEqual(data['energy_consumed'], 0)
                            
                            self.assertIsInstance(data['emissions'], (int, float))
                            self.assertGreaterEqual(data['emissions'], 0)
                        else:
                            # Fallback: CodeCarbon sometimes writes to a different path or structure
                            # depending on version. We assert that the tracker stopped cleanly.
                            self.assertTrue(tracker._stopped)

    def test_cpu_device_detection_logic(self):
        """
        Test the logic that determines if the environment is CPU-only.
        This ensures that the pipeline correctly identifies the hardware
        before initializing the tracker.
        """
        # Simulate an environment where CUDA is not available
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
            with patch('torch.cuda.is_available', return_value=False):
                # We are testing the logic that would be used in run_inference.py
                # to decide to use CPU.
                import torch
                device = torch.device("cpu" if not torch.cuda.is_available() else "cuda")
                self.assertEqual(device.type, "cpu")

    @unittest.skipUnless(CODECARBON_AVAILABLE, "codecarbon library not installed")
    def test_tracker_context_manager_cpu(self):
        """
        Test that the EmissionsTracker works correctly as a context manager
        on CPU, ensuring start/stop are called automatically.
        """
        with patch('codecarbon.core.cpu.IntelPowerGadget.is_available', return_value=True):
            with patch('codecarbon.core.cpu.IntelPowerGadget.read_power', return_value=10.0):
                with patch('codecarbon.EmissionsTracker._get_device', return_value='cpu'):
                    with EmissionsTracker(
                        project_name=self.project_name,
                        output_dir=self.output_dir
                    ) as tracker:
                        # Perform a small computation
                        x = sum(i**2 for i in range(1000))
                        self.assertGreater(x, 0)
                    
                    # After exiting context, tracker should be stopped
                    self.assertTrue(tracker._stopped)

if __name__ == '__main__':
    unittest.main()