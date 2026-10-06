"""
Unit tests for the synthetic data generator (T006).
"""

import os
import json
import tempfile
import pytest
import numpy as np
import h5py
from pathlib import Path

from data_generator import (
    generate_synthetic_trajectory,
    save_trajectory_to_h5,
    save_metadata_json,
    _determine_label,
    _compute_box_dimensions,
    _apply_shear_deformation
)

class TestSyntheticDataGenerator:
    
    def test_generate_synthetic_trajectory_structure(self):
        """Test that generated trajectory has correct structure."""
        traj = generate_synthetic_trajectory(
            num_particles=100,
            num_timesteps=50,
            temperature=300.0,
            strain_rate=1e-7,
            seed=42
        )
        
        assert "particles" in traj
        assert "box_dimensions" in traj
        assert "stress_tensor" in traj
        assert "timesteps" in traj
        assert "label" in traj
        assert "metadata" in traj
        
        # Check shapes
        assert traj["particles"].shape == (50, 100, 3)
        assert traj["stress_tensor"].shape == (50, 3, 3)
        assert traj["timesteps"] == 50
        assert traj["label"] in ["brittle", "ductile"]
    
    def test_label_determination(self):
        """Test label determination logic."""
        # Brittle: high strain rate, low temperature
        assert _determine_label(1e-6, 300.0) == "brittle"
        assert _determine_label(5e-7, 250.0) == "brittle"
        
        # Ductile: low strain rate, high temperature
        assert _determine_label(1e-9, 500.0) == "ductile"
        assert _determine_label(5e-10, 600.0) == "ductile"
    
    def test_box_dimensions_calculation(self):
        """Test box dimension calculation."""
        Lx, Ly, Lz = _compute_box_dimensions(1000, 2.3)
        
        assert Lx > 0
        assert Ly > 0
        assert Lz > 0
        assert abs(Lx - Ly) < 1e-6  # Should be cubic
        assert abs(Lx - Lz) < 1e-6
    
    def test_shear_deformation(self):
        """Test shear deformation application."""
        coords = np.array([[0.0, 0.0, 0.0], [0.0, 10.0, 0.0]])
        prev_coords = coords.copy()
        
        new_coords = _apply_shear_deformation(coords, 100, 1e-7, 20.0, 20.0, 20.0)
        
        # At timestep 100, gamma = 1e-7 * 100 = 1e-5
        # x' = x + gamma * y
        # Particle at y=10 should have x shifted by 1e-5 * 10 = 1e-4
        expected_shift = 1e-4
        assert abs(new_coords[1, 0] - (coords[1, 0] + expected_shift)) < 1e-6
    
    def test_save_and_load_h5(self):
        """Test saving and loading trajectory to/from HDF5."""
        traj = generate_synthetic_trajectory(
            num_particles=50,
            num_timesteps=20,
            temperature=300.0,
            strain_rate=1e-7,
            seed=42
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_trajectory.h5")
            save_trajectory_to_h5(traj, filepath)
            
            # Verify file exists
            assert os.path.exists(filepath)
            
            # Load and verify
            with h5py.File(filepath, 'r') as f:
                loaded_particles = f['particles'][:]
                loaded_stress = f['stress_tensor'][:]
                loaded_label = f.attrs['label']
                
                assert np.allclose(loaded_particles, traj["particles"])
                assert np.allclose(loaded_stress, traj["stress_tensor"])
                assert loaded_label == traj["label"]
    
    def test_metadata_json_output(self):
        """Test metadata JSON generation."""
        trajectories = [
            generate_synthetic_trajectory(num_particles=50, num_timesteps=20, seed=42),
            generate_synthetic_trajectory(num_particles=50, num_timesteps=20, seed=43)
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override METADATA_PATH
            import data_generator
            original_path = data_generator.METADATA_PATH
            data_generator.METADATA_PATH = Path(tmpdir) / "metadata.json"
            
            try:
                save_metadata_json(trajectories)
                
                assert os.path.exists(data_generator.METADATA_PATH)
                
                with open(data_generator.METADATA_PATH, 'r') as f:
                    metadata = json.load(f)
                
                assert len(metadata) == 2
                assert "filename" in metadata[0]
                assert "label" in metadata[0]
                assert "num_particles" in metadata[0]
            finally:
                data_generator.METADATA_PATH = original_path
    
    def test_reproducibility(self):
        """Test that same seed produces same results."""
        traj1 = generate_synthetic_trajectory(seed=42)
        traj2 = generate_synthetic_trajectory(seed=42)
        
        assert np.allclose(traj1["particles"], traj2["particles"])
        assert np.allclose(traj1["stress_tensor"], traj2["stress_tensor"])
        assert traj1["label"] == traj2["label"]
    
    def test_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        traj1 = generate_synthetic_trajectory(seed=42)
        traj2 = generate_synthetic_trajectory(seed=43)
        
        # Should be different (with very high probability)
        assert not np.allclose(traj1["particles"], traj2["particles"])