"""
Unit tests for synthetic data generator.
"""
import pytest
import os
import json
import h5py
import numpy as np
from pathlib import Path
import tempfile
import shutil

from data_generator import generate_synthetic_trajectory, main


class TestDataGenerator:
    """Test suite for synthetic trajectory generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir) / "test_trajectory.h5"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_generate_trajectory_creates_file(self):
        """Test that generate_synthetic_trajectory creates an HDF5 file."""
        metadata = generate_synthetic_trajectory(
            n_particles=100,
            n_steps=50,
            output_path=self.output_path
        )
        
        assert self.output_path.exists(), "HDF5 file was not created"
        assert metadata['trajectory_file'] == str(self.output_path)
    
    def test_generate_trajectory_metadata(self):
        """Test that metadata contains expected fields."""
        metadata = generate_synthetic_trajectory(
            n_particles=100,
            n_steps=50,
            strain_rate=1e-5,
            temperature=300.0,
            seed=42,
            output_path=self.output_path
        )
        
        assert metadata['n_particles'] == 100
        assert metadata['n_steps'] == 50
        assert metadata['strain_rate'] == 1e-5
        assert metadata['temperature'] == 300.0
        assert metadata['seed'] == 42
        assert 'label' in metadata
        assert metadata['label'] in ['brittle', 'ductile']
    
    def test_hdf5_structure(self):
        """Test that the HDF5 file has the correct structure."""
        metadata = generate_synthetic_trajectory(
            n_particles=100,
            n_steps=50,
            output_path=self.output_path
        )
        
        with h5py.File(self.output_path, 'r') as f:
            # Check attributes
            assert f.attrs['n_particles'] == 100
            assert f.attrs['n_steps'] == 50
            assert f.attrs['label'] in ['brittle', 'ductile']
            
            # Check datasets
            assert 'steps' in f
            assert 'positions' in f
            assert 'velocities' in f
            assert 'stress' in f
            assert 'box' in f
            
            # Check shapes
            assert f['steps'].shape == (50,)
            assert f['positions'].shape == (50, 100, 3)
            assert f['velocities'].shape == (50, 100, 3)
            assert f['stress'].shape == (50, 6)
            assert f['box'].shape == (3, 3)
    
    def test_label_assignment(self):
        """Test that labels are assigned based on parameters."""
        # Brittle case: high strain rate
        metadata_brittle = generate_synthetic_trajectory(
            n_particles=100,
            n_steps=50,
            strain_rate=1e-4,  # High strain rate
            temperature=300.0,
            output_path=self.output_path
        )
        assert metadata_brittle['label'] == 'brittle'
        
        # Ductile case: low strain rate, high temperature
        metadata_ductile = generate_synthetic_trajectory(
            n_particles=100,
            n_steps=50,
            strain_rate=1e-5,
            temperature=400.0,  # High temperature
            output_path=self.output_path
        )
        assert metadata_ductile['label'] == 'ductile'
    
    def test_stress_tensor_shape(self):
        """Test that stress tensor has correct shape (6 components)."""
        metadata = generate_synthetic_trajectory(
            n_particles=100,
            n_steps=50,
            output_path=self.output_path
        )
        
        with h5py.File(self.output_path, 'r') as f:
            stress = f['stress'][:]
            assert stress.shape == (50, 6)
            # Check for Voigt notation: xx, yy, zz, xy, xz, yz
    
    def test_reproducibility(self):
        """Test that same seed produces same results."""
        path1 = Path(self.temp_dir) / "test1.h5"
        path2 = Path(self.temp_dir) / "test2.h5"
        
        generate_synthetic_trajectory(
            n_particles=100,
            n_steps=50,
            seed=123,
            output_path=path1
        )
        
        generate_synthetic_trajectory(
            n_particles=100,
            n_steps=50,
            seed=123,
            output_path=path2
        )
        
        with h5py.File(path1, 'r') as f1, h5py.File(path2, 'r') as f2:
            assert np.array_equal(f1['positions'][:], f2['positions'][:])
            assert np.array_equal(f1['velocities'][:], f2['velocities'][:])
            assert np.array_equal(f1['stress'][:], f2['stress'][:])
    
    def test_main_function_creates_files(self):
        """Test that main() creates expected output files."""
        # Create a temporary directory for testing
        test_dir = Path(self.temp_dir) / "test_main"
        test_dir.mkdir(exist_ok=True)
        
        # Temporarily override the output path
        original_cwd = Path.cwd()
        os.chdir(test_dir)
        
        try:
            main()
            
            # Check that files were created
            raw_dir = test_dir / "data" / "raw"
            assert raw_dir.exists()
            assert (raw_dir / "metadata.json").exists()
            
            # Check for trajectory files
            h5_files = list(raw_dir.glob("synthetic_trajectory_*.h5"))
            assert len(h5_files) > 0, "No trajectory files were created"
            
            # Check metadata content
            with open(raw_dir / "metadata.json", 'r') as f:
                metadata = json.load(f)
                assert 'dataset_info' in metadata
                assert 'trajectories' in metadata
                assert len(metadata['trajectories']) > 0
        finally:
            os.chdir(original_cwd)
    
    def test_particle_count_validation(self):
        """Test that particle count is reasonable."""
        metadata = generate_synthetic_trajectory(
            n_particles=50,  # Small for testing
            n_steps=10,
            output_path=self.output_path
        )
        
        with h5py.File(self.output_path, 'r') as f:
            assert f.attrs['n_particles'] == 50
            assert f['positions'].shape[1] == 50