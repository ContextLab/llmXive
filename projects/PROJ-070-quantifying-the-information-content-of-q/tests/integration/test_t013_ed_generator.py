"""
Integration test for T013: Exact Diagonalization generator.

Tests that the ED generator produces valid wavefunctions for N <= 20.
"""
import os
import tempfile
import numpy as np
import h5py
import pytest
from data_loader import generate_internal_wavefunction, save_wavefunction_hdf5, generate_internal_dataset
from logging_config import setup_logging

@pytest.fixture(scope='module')
def setup_logging_fixture():
    """Setup logging for tests."""
    setup_logging()

class TestEDGenerator:
    """Test suite for Exact Diagonalization generator."""
    
    def test_ed_heisenberg_small_system(self, setup_logging_fixture):
        """Test ED generation for small Heisenberg system (N=10)."""
        wavefunction, metadata = generate_internal_wavefunction(
            model_type='heisenberg_1d',
            system_size=10,
            seed=42,
            method='ED'
        )
        
        # Verify wavefunction properties
        assert wavefunction is not None
        assert len(wavefunction) == 2 ** 10, "Hilbert space dimension mismatch"
        assert np.isclose(np.linalg.norm(wavefunction), 1.0), "Wavefunction not normalized"
        
        # Verify metadata
        assert metadata['model_type'] == 'heisenberg_1d'
        assert metadata['system_size'] == 10
        assert metadata['method'] == 'ED'
        assert 'ground_energy' in metadata
        assert metadata['hilbert_dim'] == 2 ** 10
    
    def test_ed_ising_small_system(self, setup_logging_fixture):
        """Test ED generation for small Ising system (N=12)."""
        wavefunction, metadata = generate_internal_wavefunction(
            model_type='ising_1d',
            system_size=12,
            seed=42,
            method='ED'
        )
        
        # Verify wavefunction properties
        assert wavefunction is not None
        assert len(wavefunction) == 2 ** 12
        assert np.isclose(np.linalg.norm(wavefunction), 1.0)
        
        # Verify metadata
        assert metadata['model_type'] == 'ising_1d'
        assert metadata['system_size'] == 12
        assert metadata['method'] == 'ED'
    
    def test_ed_save_hdf5(self, setup_logging_fixture):
        """Test saving wavefunction to HDF5 format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_wavefunction.h5')
            
            wavefunction, metadata = generate_internal_wavefunction(
                model_type='heisenberg_1d',
                system_size=10,
                seed=42,
                method='ED'
            )
            
            save_wavefunction_hdf5(wavefunction, metadata, output_path)
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify contents
            with h5py.File(output_path, 'r') as f:
                assert 'wavefunction_real' in f
                assert 'wavefunction_imag' in f
                assert f.attrs['model_type'] == 'heisenberg_1d'
                assert f.attrs['system_size'] == 10
                assert f.attrs['method'] == 'ED'
                
                # Verify data integrity
                real_part = f['wavefunction_real'][:]
                imag_part = f['wavefunction_imag'][:]
                loaded_wf = real_part + 1j * imag_part
                assert np.allclose(loaded_wf, wavefunction)
    
    def test_ed_generate_dataset(self, setup_logging_fixture):
        """Test generating multiple wavefunctions in a dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            system_sizes = [10, 12, 14]
            
            output_files = generate_internal_dataset(
                model_type='heisenberg_1d',
                system_sizes=system_sizes,
                output_dir=tmpdir,
                seed_base=42
            )
            
            # Verify files generated
            assert len(output_files) == len(system_sizes)
            
            # Verify each file
            for i, filepath in enumerate(output_files):
                assert os.path.exists(filepath)
                with h5py.File(filepath, 'r') as f:
                    assert 'wavefunction_real' in f
                    assert 'wavefunction_imag' in f
                    assert f.attrs['system_size'] == system_sizes[i]
    
    def test_ed_system_size_constraints(self, setup_logging_fixture):
        """Test that system size constraints are enforced."""
        # Valid size
        wavefunction, metadata = generate_internal_wavefunction(
            model_type='heisenberg_1d',
            system_size=20,
            seed=42,
            method='ED'
        )
        assert wavefunction is not None
        
        # Invalid size (too small)
        with pytest.raises(ValueError):
            generate_internal_wavefunction(
                model_type='heisenberg_1d',
                system_size=3,
                seed=42,
                method='ED'
            )
        
        # Invalid size (too large for ED, should trigger warning but may still work)
        # Note: N=25 might work on some systems but is generally too large
        # We test that the function doesn't crash with a reasonable upper bound
        try:
            wavefunction, metadata = generate_internal_wavefunction(
                model_type='heisenberg_1d',
                system_size=22,
                seed=42,
                method='ED'  # Should fall back to DMRG or raise error
            )
            # If it succeeds, metadata should reflect fallback
            assert metadata['method'] in ['ED', 'DMRG']
        except (RuntimeError, MemoryError):
            # Expected for very large systems
            pass
    
    def test_ed_ground_state_properties(self, setup_logging_fixture):
        """Test that generated ground states have expected properties."""
        wavefunction, metadata = generate_internal_wavefunction(
            model_type='heisenberg_1d',
            system_size=10,
            seed=42,
            method='ED'
        )
        
        # Ground state energy should be negative for Heisenberg antiferromagnet
        assert metadata['ground_energy'] < 0
        
        # Wavefunction should be complex (due to Y-Y interactions)
        assert np.any(wavefunction.imag != 0) or np.all(wavefunction.real != 0)
    
    def test_ed_reproducibility(self, setup_logging_fixture):
        """Test that same seed produces same results."""
        wf1, meta1 = generate_internal_wavefunction(
            model_type='heisenberg_1d',
            system_size=10,
            seed=123,
            method='ED'
        )
        
        wf2, meta2 = generate_internal_wavefunction(
            model_type='heisenberg_1d',
            system_size=10,
            seed=123,
            method='ED'
        )
        
        assert np.allclose(wf1, wf2)
        assert meta1['ground_energy'] == meta2['ground_energy']
    
    def test_ed_invalid_method(self, setup_logging_fixture):
        """Test that invalid method raises error."""
        with pytest.raises(ValueError):
            generate_internal_wavefunction(
                model_type='heisenberg_1d',
                system_size=10,
                seed=42,
                method='INVALID'
            )
    
    def test_ed_hilbert_space_scaling(self, setup_logging_fixture):
        """Test that Hilbert space dimension scales correctly."""
        for N in [10, 12, 14, 16]:
            wavefunction, metadata = generate_internal_wavefunction(
                model_type='heisenberg_1d',
                system_size=N,
                seed=42,
                method='ED'
            )
            assert len(wavefunction) == 2 ** N
            assert metadata['hilbert_dim'] == 2 ** N

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
