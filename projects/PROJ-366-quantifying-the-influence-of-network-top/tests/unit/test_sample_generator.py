"""
Unit tests for sample_generator.py.

Tests:
1. Verify that generate_samples creates the correct number of files.
2. Verify that generated files have >= min_atoms.
3. Verify file format (XYZ).
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from ase.io import read
from ingest.sample_generator import generate_samples, create_initial_crystal

class TestSampleGenerator:
    
    def test_create_initial_crystal_size(self):
        """Test that create_initial_crystal creates a structure with >= target atoms."""
        atoms = create_initial_crystal(1000)
        assert len(atoms) >= 1000, f"Expected >= 1000 atoms, got {len(atoms)}"
        
    @pytest.mark.integration
    def test_generate_samples_creates_files(self):
        """
        Integration test: Run generate_samples and verify files are created.
        Note: This requires LAMMPS and Si.sw to be present.
        """
        # Skip if LAMMPS is not available
        if not shutil.which('lammps'):
            pytest.skip("LAMMPS executable not found in PATH. Skipping integration test.")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            n_samples = 2
            min_atoms = 1000
            
            # We cannot easily mock the LAMMPS subprocess in a way that generates 
            # valid XYZ files without a real simulation, so we skip the full run 
            # in a pure unit test environment if LAMMPS is missing.
            # However, if LAMMPS is present, we run it.
            
            files = generate_samples(n_samples=n_samples, min_atoms=min_atoms, output_dir=tmpdir)
            
            assert len(files) == n_samples
            
            for f in files:
                assert os.path.exists(f)
                atoms = read(f)
                assert len(atoms) >= min_atoms
                # Check if it's a valid XYZ (read should succeed)
                assert atoms is not None
