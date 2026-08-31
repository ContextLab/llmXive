import pytest
import os
import json
import tempfile
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the functions to test
from src.cli.run_simulation import ensure_fallback_dataset, run_simulation_with_fallback
from src.data.loader import DataUnavailableError
from src.data.synthetic_fallback import generate_synthetic_fallback_dataset

class TestT015bFallbackLogic:
    """
    Tests for T015b: Fallback logic and Power-Limited flagging.
    
    Verifies that:
    1. DataUnavailableError triggers synthetic fallback
    2. Synthetic dataset is generated correctly
    3. Status log contains 'Power-Limited' flag
    """

    @patch('src.cli.run_simulation.load_real_dataset')
    @patch('src.cli.run_simulation.generate_synthetic_fallback_dataset')
    def test_fallback_triggered_on_data_unavailable(self, mock_gen_fallback, mock_load_real):
        """Test that fallback is triggered when real data is unavailable."""
        # Arrange
        mock_load_real.side_effect = DataUnavailableError("Real data not found")
        mock_gen_fallback.return_value = None
        
        output_path = tempfile.mktemp(suffix='.csv')
        
        # Act
        result = ensure_fallback_dataset("config.yaml", output_path)
        
        # Assert
        assert result is True, "Should return True when fallback is triggered"
        mock_load_real.assert_called_once_with("config.yaml")
        mock_gen_fallback.assert_called_once_with(output_path)

    @patch('src.cli.run_simulation.load_real_dataset')
    def test_no_fallback_when_data_available(self, mock_load_real):
        """Test that fallback is NOT triggered when real data is available."""
        # Arrange
        mock_load_real.return_value = None  # Success
        
        output_path = tempfile.mktemp(suffix='.csv')
        
        # Act
        result = ensure_fallback_dataset("config.yaml", output_path)
        
        # Assert
        assert result is False, "Should return False when data is available"
        mock_load_real.assert_called_once_with("config.yaml")

    def test_synthetic_fallback_generates_file(self):
        """Test that synthetic fallback actually creates a file."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fallback.csv")
            
            # Act
            df = generate_synthetic_fallback_dataset(output_path, num_steps=100)
            
            # Assert
            assert os.path.exists(output_path), "Fallback file should be created"
            assert df.shape[0] == 100, "Should generate correct number of steps"
            assert 'coherence' in df.columns, "Should have coherence column"
            assert 'diversity' in df.columns, "Should have diversity column"
            assert 'source' in df.columns, "Should have source column"
            assert (df['source'] == 'synthetic_fallback').all(), "Source should be marked"

    @patch('src.cli.run_simulation.load_real_dataset')
    @patch('src.cli.run_simulation.generate_synthetic_fallback_dataset')
    @patch('src.cli.run_simulation.run_simulation')
    def test_status_log_contains_power_limited_flag(self, mock_run_sim, mock_gen_fallback, mock_load_real):
        """Test that status log contains 'Power-Limited' flag when fallback is used."""
        # Arrange
        mock_load_real.side_effect = DataUnavailableError("Data missing")
        mock_gen_fallback.return_value = None
        mock_run_sim.return_value = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary config file
            config_path = os.path.join(tmpdir, "config.yaml")
            with open(config_path, 'w') as f:
                f.write("steps: 1000\n")
            
            status_log_path = os.path.join(tmpdir, "status.json")
            
            # Mock the write_status_log to capture the status
            captured_status = {}
            def mock_write_status(status, path):
                captured_status.update(status)
            
            # Patch the write function and ensure output dir
            with patch('src.cli.run_simulation.write_status_log', mock_write_status):
                with patch('src.cli.run_simulation.ensure_output_dir'):
                    # Create args object
                    args = MagicMock()
                    args.config = config_path
                    args.steps = 1000
                    args.seed = 42
                    args.timeout = None
                    
                    # Act
                    try:
                        run_simulation_with_fallback(args)
                    except Exception:
                        pass  # We expect it might fail if sim logic is incomplete, but status should be written
                    
                    # Assert
                    assert "flags" in captured_status, "Status should have flags"
                    assert "Power-Limited" in captured_status["flags"], "Should have Power-Limited flag"

    def test_fallback_dataset_structure(self):
        """Test that the fallback dataset has the correct structure for downstream processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fallback.csv")
            df = generate_synthetic_fallback_dataset(output_path, num_steps=50)
            
            # Check required columns for analysis
            required_cols = ['time_step', 'coherence', 'diversity', 'latency_ms', 'physics_violation']
            for col in required_cols:
                assert col in df.columns, f"Missing required column: {col}"
            
            # Check data types
            assert df['time_step'].dtype in [np.int64, np.int32], "time_step should be integer"
            assert df['coherence'].dtype in [np.float64, np.float32], "coherence should be float"
            assert df['diversity'].dtype in [np.float64, np.float32], "diversity should be float"
            assert df['latency_ms'].dtype in [np.float64, np.float32], "latency should be float"