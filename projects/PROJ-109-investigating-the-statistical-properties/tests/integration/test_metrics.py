"""
Integration tests for the full metric computation pipeline (US2).

This test verifies the end-to-end flow:
1. Loads pre-processed halo data (from T014 output).
2. Runs the metric computation pipeline (T022, T023, T024).
3. Validates output schema and physical ranges.
4. Ensures artifacts are written to disk.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest
import numpy as np
import pandas as pd
import h5py

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.data.compute_metrics import run_compute_metrics_pipeline
from code.data.preprocess import run_preprocessing_pipeline
from code.data.synthetic_generator import generate_synthetic_halos
from code.config import BOX_SIZE, MIN_PARTICLES_THRESHOLD
from code.utils.logging import get_logger

logger = get_logger(__name__)

# Constants for test generation
TEST_HALO_COUNT = 10
TEST_PARTICLES_PER_HALO = 500  # Must be >= 300 to pass filter
TEST_MASS_MIN = 1e10
TEST_MASS_MAX = 1e13

class TestFullMetricPipeline:
    """Integration test for the full metric computation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_data_path = os.path.join(self.temp_dir, "raw_halos.h5")
        self.filtered_data_path = os.path.join(self.temp_dir, "filtered_halos.parquet")
        self.metrics_output_path = os.path.join(self.temp_dir, "halo_metrics.parquet")
        self.metrics_json_path = os.path.join(self.temp_dir, "metrics_stats.json")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.raw_data_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.filtered_data_path), exist_ok=True)
        
        yield
        
        # Teardown: clean up temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _generate_test_halo_data(self, path: str):
        """
        Generates a minimal HDF5 file with synthetic halo data for testing.
        This mimics the output of T012 (download) or T007B (synthetic fallback).
        """
        logger.info(f"Generating test halo data at {path}")
        
        with h5py.File(path, 'w') as f:
            # Create groups for different data types
            f.attrs['simulation'] = 'TestSim'
            f.attrs['box_size'] = BOX_SIZE
            
            # Generate data
            n_halos = TEST_HALO_COUNT
            n_particles = TEST_PARTICLES_PER_HALO
            
            # Halo IDs
            halo_ids = np.arange(n_halos)
            f.create_dataset('halo_id', data=halo_ids)
            
            # Masses (log-uniform distribution)
            masses = np.logspace(np.log10(TEST_MASS_MIN), np.log10(TEST_MASS_MAX), n_halos)
            f.create_dataset('mass', data=masses)
            
            # Positions (random within box)
            positions = np.random.uniform(0, BOX_SIZE, size=(n_halos, 3))
            f.create_dataset('position', data=positions)
            
            # Velocities (random, small magnitude)
            velocities = np.random.normal(0, 10, size=(n_halos, 3))
            f.create_dataset('velocity', data=velocities)
            
            # Particle counts (ensure >= 300)
            particle_counts = np.full(n_halos, n_particles, dtype=np.int32)
            f.create_dataset('particle_count', data=particle_counts)
            
            # Create a separate group for particle-level data needed for metrics
            # We will store a flattened array of positions for all particles
            total_particles = n_halos * n_particles
            all_particle_positions = np.random.uniform(0, BOX_SIZE, size=(total_particles, 3))
            all_particle_masses = np.random.uniform(0.5, 1.5, size=total_particles) # Relative masses
            
            # Store as chunks to simulate real structure
            for i in range(n_halos):
                start_idx = i * n_particles
                end_idx = (i + 1) * n_particles
                group = f.create_group(f'halo_{i}')
                group.create_dataset('positions', data=all_particle_positions[start_idx:end_idx])
                group.create_dataset('masses', data=all_particle_masses[start_idx:end_idx])
                group.attrs['particle_count'] = n_particles
                group.attrs['halo_id'] = i

    def test_full_metric_pipeline(self):
        """
        Runs the full pipeline:
        1. Generate synthetic raw data (simulating T012/T007B).
        2. Run preprocessing (T013/T014) to filter and save.
        3. Run metric computation (T022/T023/T024) on filtered data.
        4. Validate outputs exist and contain expected columns/ranges.
        """
        logger.info("Starting full metric pipeline integration test")

        # Step 1: Generate raw test data
        self._generate_test_halo_data(self.raw_data_path)
        assert os.path.exists(self.raw_data_path), "Raw data generation failed"

        # Step 2: Run Preprocessing Pipeline (T013, T014, T015)
        # We manually invoke the logic to ensure the filtered file is created
        # Since run_preprocessing_pipeline might expect specific CLI args or state,
        # we implement the core logic here to ensure the test is self-contained.
        
        logger.info("Running preprocessing step...")
        with h5py.File(self.raw_data_path, 'r') as f_in:
            # Load data
            halo_ids = f_in['halo_id'][:]
            masses = f_in['mass'][:]
            positions = f_in['position'][:]
            velocities = f_in['velocity'][:]
            particle_counts = f_in['particle_count'][:]
            
            # Filter: particle_count >= 300
            mask = particle_counts >= MIN_PARTICLES_THRESHOLD
            filtered_ids = halo_ids[mask]
            filtered_masses = masses[mask]
            filtered_positions = positions[mask]
            filtered_velocities = velocities[mask]
            filtered_particle_counts = particle_counts[mask]
            
            # Create DataFrame
            df = pd.DataFrame({
                'halo_id': filtered_ids,
                'mass': filtered_masses,
                'position_x': filtered_positions[:, 0],
                'position_y': filtered_positions[:, 1],
                'position_z': filtered_positions[:, 2],
                'velocity_x': filtered_velocities[:, 0],
                'velocity_y': filtered_velocities[:, 1],
                'velocity_z': filtered_velocities[:, 2],
                'particle_count': filtered_particle_counts
            })
            
            # Validate schema (simplified check for T015)
            required_cols = ['mass', 'position_x', 'position_y', 'position_z', 
                             'velocity_x', 'velocity_y', 'velocity_z', 'particle_count']
            assert all(col in df.columns for col in required_cols), "Schema validation failed"
            
            # Write parquet (T014)
            df.to_parquet(self.filtered_data_path, compression='snappy')
        
        assert os.path.exists(self.filtered_data_path), "Preprocessing output not created"
        logger.info(f"Preprocessing complete. Filtered {len(df)} halos.")

        # Step 3: Run Metric Computation Pipeline (T021 Target)
        # We need to prepare the input for compute_metrics. 
        # The compute_metrics pipeline expects to read from the filtered parquet or raw h5.
        # For this test, we will call the pipeline function directly.
        # Note: The actual implementation of run_compute_metrics_pipeline needs to handle
        # reading particle data from the raw file or a derived structure.
        # We assume the pipeline reads the raw file to get particle positions for metrics.
        
        logger.info("Running metric computation pipeline...")
        
        # Prepare arguments for the pipeline
        # The pipeline should take the raw data path to access particle positions
        # and the filtered data path to know which halos to process.
        pipeline_args = {
            'input_raw_path': self.raw_data_path,
            'input_filtered_path': self.filtered_data_path,
            'output_metrics_path': self.metrics_output_path,
            'output_stats_path': self.metrics_json_path,
            'box_size': BOX_SIZE
        }
        
        # Execute
        try:
            run_compute_metrics_pipeline(**pipeline_args)
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise

        # Step 4: Validate Outputs
        
        # 4a. Check metrics parquet exists
        assert os.path.exists(self.metrics_output_path), "Metrics output file not created"
        
        # 4b. Check metrics stats JSON exists
        assert os.path.exists(self.metrics_json_path), "Metrics stats JSON not created"
        
        # 4c. Load and validate metrics DataFrame
        metrics_df = pd.read_parquet(self.metrics_output_path)
        
        required_metric_cols = ['halo_id', 'shape_s', 'spin_lambda', 'concentration_c', 'energy_total']
        for col in required_metric_cols:
            assert col in metrics_df.columns, f"Missing metric column: {col}"
        
        # 4d. Validate physical ranges (T025)
        # Shape s: [0, 1]
        assert metrics_df['shape_s'].between(0, 1).all(), "Shape parameter out of range [0, 1]"
        
        # Spin lambda: [0, 1] (typically small, but bounded)
        assert metrics_df['spin_lambda'].between(0, 1).all(), "Spin parameter out of range [0, 1]"
        
        # Concentration c: > 0
        assert (metrics_df['concentration_c'] > 0).all(), "Concentration parameter must be positive"
        
        # Energy: typically negative for bound systems
        # (Allow small positive due to numerical noise or unbound particles in test)
        # Just check it's numeric and not NaN
        assert not metrics_df['energy_total'].isna().any(), "Energy values contain NaN"
        
        # 4e. Validate JSON stats
        with open(self.metrics_json_path, 'r') as f:
            stats = json.load(f)
        
        assert 'total_halos_processed' in stats, "Missing total_halos_processed in stats"
        assert 'failed_fits' in stats, "Missing failed_fits in stats"
        assert 'convergence_rate' in stats, "Missing convergence_rate in stats"
        
        assert stats['total_halos_processed'] == len(metrics_df), "Stats count mismatch"
        
        logger.info("Full metric pipeline integration test PASSED")

    def test_metric_pipeline_with_empty_filter(self):
        """
        Test behavior when filtering results in 0 halos.
        Ensures the pipeline handles empty inputs gracefully without crashing.
        """
        logger.info("Testing pipeline with empty filtered set...")
        
        # Create a raw file with halos < 300 particles
        with h5py.File(self.raw_data_path, 'w') as f:
            f.create_dataset('halo_id', data=[1, 2])
            f.create_dataset('mass', data=[1e10, 1e10])
            f.create_dataset('position', data=[[0,0,0], [1,1,1]])
            f.create_dataset('velocity', data=[[0,0,0], [0,0,0]])
            f.create_dataset('particle_count', data=[50, 100]) # All below threshold
            # No particle groups needed since we expect no processing

        # Run preprocessing logic to create empty parquet
        df = pd.DataFrame({
            'halo_id': [], 'mass': [], 'position_x': [], 'position_y': [], 'position_z': [],
            'velocity_x': [], 'velocity_y': [], 'velocity_z': [], 'particle_count': []
        })
        df.to_parquet(self.filtered_data_path, compression='snappy')
        
        # Run pipeline
        pipeline_args = {
            'input_raw_path': self.raw_data_path,
            'input_filtered_path': self.filtered_data_path,
            'output_metrics_path': self.metrics_output_path,
            'output_stats_path': self.metrics_json_path,
            'box_size': BOX_SIZE
        }
        
        # Should not raise error
        run_compute_metrics_pipeline(**pipeline_args)
        
        # Verify output exists and is empty
        assert os.path.exists(self.metrics_output_path)
        metrics_df = pd.read_parquet(self.metrics_output_path)
        assert len(metrics_df) == 0, "Expected empty metrics dataframe"
        
        logger.info("Empty filter test PASSED")