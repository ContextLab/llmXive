"""
Unit tests for synthetic data generator (T011).

Tests that the synthetic generator produces valid compositions
with realistic descriptor ranges.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.synthetic import (
    generate_composition_from_system,
    generate_synthetic_phase,
    generate_synthetic_dataset,
    apply_descriptors_to_dataframe,
    save_synthetic_dataset
)
from features.descriptors import parse_composition

class TestCompositionGeneration:
    """Tests for composition generation functions."""
    
    def test_generate_composition_valid_format(self):
        """Test that generated compositions have valid chemical format."""
        system = ['Zr', 'Cu', 'Al']
        composition, fractions = generate_composition_from_system(system)
        
        # Check composition is not empty
        assert len(composition) > 0
        
        # Check all elements from system are in composition
        for elem in system:
            assert elem in composition
        
        # Check fractions sum to approximately 1
        assert abs(sum(fractions.values()) - 1.0) < 0.01
        
    def test_generate_composition_multiple_systems(self):
        """Test composition generation for various alloy systems."""
        systems = [
            ['Zr', 'Cu', 'Al'],
            ['Pd', 'Ni', 'P'],
            ['Mg', 'Cu', 'Y']
        ]
        
        for system in systems:
            composition, fractions = generate_composition_from_system(system)
            assert len(composition) > 0
            assert abs(sum(fractions.values()) - 1.0) < 0.01

class TestPhaseGeneration:
    """Tests for phase label generation."""
    
    def test_phase_is_valid_label(self):
        """Test that generated phases are valid labels."""
        composition, fractions = generate_composition_from_system(['Zr', 'Cu', 'Al'])
        phase = generate_synthetic_phase(composition, fractions)
        
        assert phase in ['amorphous', 'crystalline']
        
    def test_phase_distribution(self):
        """Test that phase distribution is reasonable."""
        phases = []
        for _ in range(100):
            composition, fractions = generate_composition_from_system(['Zr', 'Cu', 'Al'])
            phase = generate_synthetic_phase(composition, fractions)
            phases.append(phase)
        
        # Should have both phases represented
        assert 'amorphous' in phases
        assert 'crystalline' in phases

class TestDatasetGeneration:
    """Tests for full dataset generation."""
    
    def test_dataset_size(self):
        """Test that generated dataset meets minimum size requirement."""
        df = generate_synthetic_dataset(n_samples=1000)
        
        assert len(df) >= 1000, f"Expected >= 1000 samples, got {len(df)}"
        
    def test_dataset_columns(self):
        """Test that dataset has all required columns."""
        df = generate_synthetic_dataset(n_samples=100)
        
        required_columns = [
            'composition', 'phase', 'atomic_radius', 'electronegativity',
            'vec', 'size_mismatch', 'electronegativity_diff', 'mixing_enthalpy',
            'source'
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
            
    def test_descriptor_ranges(self):
        """Test that computed descriptors fall within physically reasonable ranges."""
        df = generate_synthetic_dataset(n_samples=100)
        
        # Atomic radius should be positive and reasonable (50-200 pm)
        assert df['atomic_radius'].min() > 0
        assert df['atomic_radius'].max() < 300
        
        # Electronegativity should be positive (Pauling scale)
        assert df['electronegativity'].min() > 0
        assert df['electronegativity'].max() < 4.0
        
        # VEC should be positive
        assert df['vec'].min() > 0
        
        # Size mismatch should be non-negative
        assert df['size_mismatch'].min() >= 0
        
        # Electronegativity difference should be non-negative
        assert df['electronegativity_diff'].min() >= 0
        
        # Mixing enthalpy can be negative or positive
        # (typical range for alloys is -50 to +50 kJ/mol)
        
    def test_composition_parsing(self):
        """Test that generated compositions can be parsed."""
        df = generate_synthetic_dataset(n_samples=50)
        
        for _, row in df.iterrows():
            try:
                parsed = parse_composition(row['composition'])
                assert len(parsed) > 0
            except Exception as e:
                pytest.fail(f"Failed to parse composition {row['composition']}: {e}")

class TestSaveSyntheticDataset:
    """Tests for saving synthetic datasets."""
    
    def test_save_creates_file(self, tmp_path):
        """Test that save function creates output file."""
        df = generate_synthetic_dataset(n_samples=10)
        
        output_path = str(tmp_path / 'test_synthetic.csv')
        saved_path = save_synthetic_dataset(df, output_path)
        
        assert os.path.exists(saved_path)
        
        # Verify file is readable
        loaded_df = pd.read_csv(saved_path)
        assert len(loaded_df) == len(df)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
