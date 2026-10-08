import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

from data.compute_metrics import run_compute_metrics_pipeline, compute_halo_metrics

class TestConvergenceStats:
    """Test convergence rate logging and stats aggregation for T026."""

    def setup_method(self):
        """Create temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "test_halos.parquet")
        self.output_path = os.path.join(self.temp_dir, "test_metrics.parquet")
        self.stats_path = os.path.join(self.temp_dir, "convergence_stats.json")

    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        if os.path.exists(self.stats_path):
            os.remove(self.stats_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_convergence_stats_file_created(self):
        """Test that convergence_stats.json is created after pipeline run."""
        # Create mock input data
        n_halos = 10
        data = {
            'particle_positions': [np.random.rand(100, 3).astype(np.float64) for _ in range(n_halos)],
            'particle_velocities': [np.random.rand(100, 3).astype(np.float64) for _ in range(n_halos)],
            'particle_masses': [np.ones(100) for _ in range(n_halos)]
        }
        
        # Convert to DataFrame (simplified for testing)
        # In reality, this would be more complex with proper serialization
        df = pd.DataFrame({
            'id': range(n_halos),
            'has_data': [True] * n_halos
        })
        df.to_parquet(self.input_path)
        
        # Run pipeline
        result = run_compute_metrics_pipeline(self.input_path, self.output_path)
        
        # Check that stats file was created
        assert os.path.exists(self.stats_path), "convergence_stats.json not created"
        
        # Verify content
        with open(self.stats_path, 'r') as f:
            stats = json.load(f)
        
        assert 'total_halos' in stats
        assert 'successful_fits' in stats
        assert 'failed_fits' in stats
        assert 'success_rate_percent' in stats
        assert 'failure_rate_percent' in stats
        assert 'message' in stats
        assert 'CONVERGENCE' in stats['message']

    def test_convergence_message_format(self):
        """Test that the logged message matches expected format."""
        # Create mock input data
        n_halos = 5
        df = pd.DataFrame({
            'id': range(n_halos),
            'has_data': [True] * n_halos
        })
        df.to_parquet(self.input_path)
        
        result = run_compute_metrics_pipeline(self.input_path, self.output_path)
        
        # Check message format
        message = result['message']
        assert message.startswith("CONVERGENCE:"), f"Message format incorrect: {message}"
        assert "success" in message, f"Message missing 'success': {message}"
        assert "failed fits" in message, f"Message missing 'failed fits': {message}"

    def test_stats_aggregation_accuracy(self):
        """Test that stats correctly aggregate successful and failed fits."""
        # Create mock input data with known success/fail rates
        # For this test, we'll assume all fits succeed (simplified)
        n_halos = 20
        df = pd.DataFrame({
            'id': range(n_halos),
            'has_data': [True] * n_halos
        })
        df.to_parquet(self.input_path)
        
        result = run_compute_metrics_pipeline(self.input_path, self.output_path)
        
        # Verify totals
        assert result['total_halos'] == n_halos
        assert result['successful_fits'] + result['failed_fits'] == n_halos
        
        # Verify rates
        expected_rate = (result['successful_fits'] / n_halos) * 100
        assert abs(result['success_rate_percent'] - expected_rate) < 0.01

    def test_empty_input_handling(self):
        """Test pipeline handles empty input gracefully."""
        # Create empty DataFrame
        df = pd.DataFrame()
        df.to_parquet(self.input_path)
        
        result = run_compute_metrics_pipeline(self.input_path, self.output_path)
        
        # Should handle empty input without crashing
        assert result['total_halos'] == 0
        assert result['successful_fits'] == 0
        assert result['failed_fits'] == 0
        assert result['success_rate_percent'] == 0.0
        assert result['failure_rate_percent'] == 0.0