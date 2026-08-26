"""
Unit tests for conformer generation module.
"""
import pytest
import pickle
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

from code.data.conformer_gen import generate_conformers, save_conformers

# Valid SMILES strings for testing
VALID_SMILES = [
    "CCO",  # Ethanol
    "CC(=O)O",  # Acetic acid
    "c1ccccc1",  # Benzene
    "CC1CCCCC1",  # Methylcyclohexane
]

INVALID_SMILES = [
    "invalid_smiles",
    "",
    "C((",  # Malformed
]

class TestConformerGeneration:
    """Tests for the generate_conformers function."""

    def test_generate_conformers_valid_smiles(self):
        """Test that conformers are generated for valid SMILES."""
        result = generate_conformers(VALID_SMILES, num_conformers=10, energy_window=5.0)
        
        assert 'conformers' in result
        assert 'lowest_energy_conformer_id' in result
        assert 'success_rate' in result
        assert 'failed_smiles' in result
        
        # Check that we got some conformers
        assert len(result['conformers']) > 0
        assert result['success_rate'] > 0
        assert result['total_success'] > 0

    def test_generate_conformers_invalid_smiles(self):
        """Test that invalid SMILES are handled gracefully."""
        mixed_smiles = VALID_SMILES + INVALID_SMILES
        result = generate_conformers(mixed_smiles, num_conformers=5, energy_window=5.0)
        
        # Should have some failures
        assert len(result['failed_smiles']) > 0
        # Should have some successes
        assert result['total_success'] > 0
        
        # Check that failed SMILES are in the failed list
        for invalid in INVALID_SMILES:
            assert invalid in result['failed_smiles']

    def test_generate_conformers_energy_filtering(self):
        """Test that conformers are filtered by energy window."""
        result = generate_conformers(VALID_SMILES[:2], num_conformers=20, energy_window=2.0)
        
        # Check that all conformers are within the energy window
        lowest_energies = {}
        for conf in result['conformers']:
            smiles = conf['smiles']
            energy = conf['energy']
            
            if smiles not in lowest_energies:
                lowest_energies[smiles] = energy
            else:
                # Should be within window of lowest
                assert energy - lowest_energies[smiles] <= 2.0, \
                    f"Conformer energy {energy} is outside window of lowest {lowest_energies[smiles]}"

    def test_generate_conformers_structure(self):
        """Test that conformer data has the expected structure."""
        result = generate_conformers(VALID_SMILES[:1], num_conformers=5, energy_window=10.0)
        
        for conf in result['conformers']:
            assert 'smiles' in conf
            assert 'conformer_id' in conf
            assert 'energy' in conf
            assert 'coords' in conf
            assert 'num_atoms' in conf
            
            # Check coords structure
            assert isinstance(conf['coords'], list)
            assert len(conf['coords']) == conf['num_atoms']
            for coord in conf['coords']:
                assert len(coord) == 3  # x, y, z

    def test_generate_conformers_lowest_energy_tracking(self):
        """Test that lowest energy conformers are correctly tracked."""
        result = generate_conformers(VALID_SMILES, num_conformers=10, energy_window=10.0)
        
        for smiles, lowest_info in result['lowest_energy_conformer_id'].items():
            assert 'conformer_id' in lowest_info
            assert 'energy' in lowest_info
            
            # Verify this is indeed the lowest for this SMILES
            confs_for_smiles = [c for c in result['conformers'] if c['smiles'] == smiles]
            min_energy = min(c['energy'] for c in confs_for_smiles)
            assert abs(lowest_info['energy'] - min_energy) < 1e-6

class TestSaveConformers:
    """Tests for the save_conformers function."""

    def test_save_and_load_conformers(self):
        """Test that conformers can be saved and loaded correctly."""
        result = generate_conformers(VALID_SMILES[:2], num_conformers=5, energy_window=5.0)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_conformers.pkl'
            save_conformers(result, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Load and verify content
            with open(output_path, 'rb') as f:
                loaded = pickle.load(f)
            
            assert 'conformers' in loaded
            assert len(loaded['conformers']) == len(result['conformers'])
            assert loaded['success_rate'] == result['success_rate']

    def test_save_conformers_empty_list(self):
        """Test saving conformers for an empty list."""
        result = generate_conformers([], num_conformers=5, energy_window=5.0)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'empty_conformers.pkl'
            save_conformers(result, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'rb') as f:
                loaded = pickle.load(f)
            
            assert len(loaded['conformers']) == 0
            assert loaded['success_rate'] == 0.0

class TestConformerIntegration:
    """Integration tests for conformer generation workflow."""

    def test_full_workflow(self):
        """Test the full workflow from SMILES to saved conformers."""
        # Generate conformers
        result = generate_conformers(VALID_SMILES, num_conformers=10, energy_window=5.0)
        
        # Verify intermediate results
        assert result['total_processed'] == len(VALID_SMILES)
        assert result['total_success'] == len(VALID_SMILES)  # All should succeed
        assert len(result['failed_smiles']) == 0
        
        # Save to file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'integration_test.pkl'
            save_conformers(result, output_path)
            
            # Verify file size is reasonable (not empty)
            assert output_path.stat().st_size > 100

    def test_large_smiles_list(self):
        """Test with a larger list of SMILES."""
        # Create a list of 10 identical SMILES to test batching
        large_list = VALID_SMILES * 2  # 8 molecules
        
        result = generate_conformers(large_list, num_conformers=5, energy_window=5.0)
        
        assert result['total_processed'] == 8
        assert result['total_success'] == 8
        assert len(result['conformers']) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])