"""
Integration test for replicate statistics (T020).

This test verifies that the system correctly calculates mean lifetime,
standard deviation, and confidence intervals for n >= 3 replicates per solvent.
It depends on the kinetic fit module (T021) and synthetic data generation (T015).
"""

import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.seeds import set_seed
from config import get_processed_data_path, get_raw_data_path, ensure_directories
from data.generate_synthetic import generate_synthetic_traces
from analysis.kinetic_fit import calculate_replicate_statistics, process_traces_for_replicates

# Configure logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestReplicateAnalysis:
    """Integration tests for replicate statistical analysis."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and clean up after."""
        # Set seed for reproducibility
        set_seed(42)

        # Create temporary directories for test data
        self.test_dir = tempfile.mkdtemp(prefix="test_replicate_")
        self.raw_dir = Path(self.test_dir) / "raw"
        self.processed_dir = Path(self.test_dir) / "processed"
        self.raw_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)

        # Mock config paths by temporarily patching
        self.original_raw_path = None
        self.original_processed_path = None

        # We will use direct path arguments instead of config patching for robustness
        logger.info(f"Test environment created at: {self.test_dir}")

        yield

        # Cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            logger.info(f"Test environment cleaned up: {self.test_dir}")

    def _generate_test_traces(self, solvent: str, n_replicates: int, base_lifetime: float, noise_level: float = 0.05):
        """Generate synthetic traces for a specific solvent with known lifetime."""
        traces = []
        for i in range(n_replicates):
            # Generate decay curve with known parameters
            t = np.linspace(0, 10, 100)
            # Add small random variation to lifetime for realism
            actual_lifetime = base_lifetime * (1 + np.random.normal(0, noise_level))
            intensity = np.exp(-t / actual_lifetime)
            # Add noise
            noise = np.random.normal(0, 0.02, size=intensity.shape)
            intensity_noisy = intensity + noise
            intensity_noisy = np.clip(intensity_noisy, 0, None)

            traces.append({
                'time': t,
                'intensity': intensity_noisy,
                'solvent': solvent,
                'replicate_id': i,
                'true_lifetime': actual_lifetime
            })
        return traces

    def test_replicate_statistics_calculation(self):
        """Test that mean, std, and CI are calculated correctly for replicates."""
        # Generate test data: 3 replicates for Acetonitrile (lifetime ~2.5 ns)
        solvent = "Acetonitrile"
        n_replicates = 3
        true_lifetime = 2.5
        noise_level = 0.05

        traces = self._generate_test_traces(solvent, n_replicates, true_lifetime, noise_level)

        # Convert to DataFrame
        df_list = []
        for trace in traces:
            for t, i in zip(trace['time'], trace['intensity']):
                df_list.append({
                    'time': t,
                    'intensity': i,
                    'solvent': solvent,
                    'replicate_id': trace['replicate_id']
                })

        df = pd.DataFrame(df_list)

        # Process traces to extract lifetimes
        # Note: This calls the kinetic_fit module which performs the exponential fitting
        lifetimes = process_traces_for_replicates(df, solvent)

        # Verify we got the expected number of lifetimes
        assert len(lifetimes) == n_replicates, f"Expected {n_replicates} lifetimes, got {len(lifetimes)}"

        # Calculate statistics
        stats = calculate_replicate_statistics(lifetimes)

        # Verify statistics structure
        assert 'mean' in stats, "Missing 'mean' in statistics"
        assert 'std' in stats, "Missing 'std' in statistics"
        assert 'ci_lower' in stats, "Missing 'ci_lower' in statistics"
        assert 'ci_upper' in stats, "Missing 'ci_upper' in statistics"
        assert 'n' in stats, "Missing 'n' in statistics"

        # Verify statistical properties
        assert stats['n'] == n_replicates
        assert stats['mean'] > 0, "Mean lifetime should be positive"
        assert stats['std'] >= 0, "Std deviation should be non-negative"
        assert stats['ci_lower'] < stats['mean'], "CI lower should be less than mean"
        assert stats['ci_upper'] > stats['mean'], "CI upper should be greater than mean"

        # Verify the mean is close to the true lifetime (within noise bounds)
        expected_range = (true_lifetime * 0.9, true_lifetime * 1.1)
        assert expected_range[0] <= stats['mean'] <= expected_range[1], \
            f"Mean lifetime {stats['mean']} outside expected range {expected_range}"

        logger.info(f"Replicate statistics for {solvent}: mean={stats['mean']:.4f}, std={stats['std']:.4f}, "
                    f"CI=[{stats['ci_lower']:.4f}, {stats['ci_upper']:.4f}]")

    def test_multiple_solvents_replicate_analysis(self):
        """Test replicate analysis across multiple solvents."""
        solvents_config = [
            ("Hexane", 1.8, 0.04),
            ("Ethyl Acetate", 2.2, 0.05),
            ("Acetonitrile", 2.5, 0.05)
        ]

        all_results = {}

        for solvent, base_lifetime, noise in solvents_config:
            traces = self._generate_test_traces(solvent, 3, base_lifetime, noise)

            df_list = []
            for trace in traces:
                for t, i in zip(trace['time'], trace['intensity']):
                    df_list.append({
                        'time': t,
                        'intensity': i,
                        'solvent': solvent,
                        'replicate_id': trace['replicate_id']
                    })

            df = pd.DataFrame(df_list)
            lifetimes = process_traces_for_replicates(df, solvent)
            stats = calculate_replicate_statistics(lifetimes)
            all_results[solvent] = stats

            logger.info(f"Processed {solvent}: mean={stats['mean']:.4f} ns")

        # Verify all solvents were processed
        assert len(all_results) == len(solvents_config), "Not all solvents were processed"

        # Verify each solvent has valid statistics
        for solvent, stats in all_results.items():
            assert stats['mean'] > 0, f"Invalid mean for {solvent}"
            assert stats['std'] >= 0, f"Invalid std for {solvent}"
            assert stats['ci_lower'] < stats['ci_upper'], f"Invalid CI for {solvent}"

    def test_insufficient_replicates_handling(self):
        """Test behavior when n < 3 replicates are provided."""
        # Generate only 2 replicates
        traces = self._generate_test_traces("TestSolvent", 2, 2.0, 0.05)

        df_list = []
        for trace in traces:
            for t, i in zip(trace['time'], trace['intensity']):
                df_list.append({
                    'time': t,
                    'intensity': i,
                    'solvent': "TestSolvent",
                    'replicate_id': trace['replicate_id']
                })

        df = pd.DataFrame(df_list)
        lifetimes = process_traces_for_replicates(df, "TestSolvent")

        # Should still calculate statistics but with warning
        stats = calculate_replicate_statistics(lifetimes)

        assert stats['n'] == 2
        # CI calculation with n=2 is less reliable but should still return values
        assert 'ci_lower' in stats
        assert 'ci_upper' in stats

    def test_replicate_output_file_generation(self):
        """Test that replicate statistics are written to output file."""
        # Generate test data
        solvent = "Acetonitrile"
        traces = self._generate_test_traces(solvent, 3, 2.5, 0.05)

        df_list = []
        for trace in traces:
            for t, i in zip(trace['time'], trace['intensity']):
                df_list.append({
                    'time': t,
                    'intensity': i,
                    'solvent': solvent,
                    'replicate_id': trace['replicate_id']
                })

        df = pd.DataFrame(df_list)
        lifetimes = process_traces_for_replicates(df, solvent)
        stats = calculate_replicate_statistics(lifetimes)

        # Write to output file
        output_path = Path(self.test_dir) / "replicate_stats.json"
        with open(output_path, 'w') as f:
            json.dump({solvent: stats}, f, indent=2)

        # Verify file exists and contains valid data
        assert output_path.exists(), "Output file not created"

        with open(output_path, 'r') as f:
            loaded_data = json.load(f)

        assert solvent in loaded_data
        assert loaded_data[solvent]['mean'] == stats['mean']
        assert loaded_data[solvent]['n'] == 3

        logger.info(f"Replicate stats written to {output_path}")

    def test_outlier_detection_in_replicates(self):
        """Test that outliers are detected in replicate sets."""
        # Generate 4 replicates, one with significantly different lifetime
        traces = self._generate_test_traces("OutlierTest", 4, 2.5, 0.02)

        # Manually inject an outlier
        outlier_idx = 3
        traces[outlier_idx]['intensity'] = np.exp(-traces[outlier_idx]['time'] / 5.0) + np.random.normal(0, 0.02, len(traces[outlier_idx]['time']))
        traces[outlier_idx]['true_lifetime'] = 5.0  # Significantly different

        df_list = []
        for trace in traces:
            for t, i in zip(trace['time'], trace['intensity']):
                df_list.append({
                    'time': t,
                    'intensity': i,
                    'solvent': "OutlierTest",
                    'replicate_id': trace['replicate_id']
                })

        df = pd.DataFrame(df_list)
        lifetimes = process_traces_for_replicates(df, "OutlierTest")

        # Calculate statistics with outlier detection
        stats = calculate_replicate_statistics(lifetimes, detect_outliers=True)

        # Verify outlier flag is present
        assert 'outliers' in stats or 'outlier_indices' in stats, "Outlier detection should return outlier info"

        logger.info(f"Outlier test stats: {stats}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
