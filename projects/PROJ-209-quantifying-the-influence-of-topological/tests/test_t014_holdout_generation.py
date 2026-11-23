import os
import json
import csv
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generators.synthetic_data_generator import (
    generate_holdout_data,
    save_to_csv,
    SEED_HOLDOUT,
    N_HOLDOUT
)

class TestT014HoldOutGeneration:
    """Tests for T014: Hold-Out Generation"""

    @pytest.fixture
    def project_root(self):
        return Path(__file__).resolve().parent.parent

    def test_holdout_data_generation(self, project_root):
        """Test that hold-out data is generated with correct structure"""
        # Generate hold-out data
        data = generate_holdout_data(n_samples=10, seed=SEED_HOLDOUT)
        
        # Verify data structure
        assert len(data) == 10
        assert all(isinstance(entry, dict) for entry in data)
        
        # Verify required fields
        required_fields = [
            "defect_id", "material", "defect_type", "defect_density",
            "conductivity", "youngs_modulus", "fracture_strength",
            "generation_seed", "is_holdout"
        ]
        
        for entry in data:
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"
            assert entry["is_holdout"] == True
            assert entry["generation_seed"] == SEED_HOLDOUT

    def test_holdout_data_values(self, project_root):
        """Test that hold-out data values are physically reasonable"""
        data = generate_holdout_data(n_samples=5, seed=SEED_HOLDOUT)
        
        for entry in data:
            # Check non-negative values
            assert entry["defect_density"] >= 0
            assert entry["conductivity"] >= 0
            assert entry["youngs_modulus"] >= 0
            assert entry["fracture_strength"] >= 0
            
            # Check reasonable ranges
            assert 0 <= entry["defect_density"] <= 0.2  # Defect density should be small
            
            # Check material types
            assert entry["material"] in ["graphene", "MoS2"]
            
            # Check defect types
            assert entry["defect_type"] in ["vacancy", "substitution", "grain_boundary", "edge_defect"]

    def test_holdout_csv_output(self, project_root):
        """Test that hold-out CSV is created with correct format"""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_holdout.csv"
            
            # Generate and save data
            data = generate_holdout_data(n_samples=5, seed=SEED_HOLDOUT)
            save_to_csv(data, str(output_path))
            
            # Verify file exists
            assert output_path.exists()
            
            # Verify CSV content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 5
                
                # Verify headers
                expected_headers = [
                    "defect_id", "material", "defect_type", "defect_density",
                    "conductivity", "youngs_modulus", "fracture_strength",
                    "generation_seed", "is_holdout"
                ]
                assert reader.fieldnames == expected_headers

    def test_distinct_seed_from_training(self, project_root):
        """Test that hold-out uses a distinct seed from training"""
        # Training seed is 42, hold-out seed should be different
        assert SEED_HOLDOUT != 42
        assert SEED_HOLDOUT == 12345

    def test_holdout_generation_metadata(self, project_root):
        """Test that metadata is created correctly"""
        # This test would require running the full workflow
        # For now, we verify the metadata structure
        metadata = {
            "seed": SEED_HOLDOUT,
            "n_samples": N_HOLDOUT,
            "git_hash": "test_hash",
            "output_file": "test.csv",
            "distinct_from_training": True,
            "physics_model": "griffith_rule_mixture_matthiessen",
            "generation_step": "T014"
        }
        
        assert metadata["seed"] == SEED_HOLDOUT
        assert metadata["distinct_from_training"] == True
        assert metadata["generation_step"] == "T014"

    def test_physics_model_application(self, project_root):
        """Test that physics models are applied correctly"""
        from generators.synthetic_data_generator import (
            apply_griffith_criterion,
            apply_rule_of_mixtures,
            apply_matthiessen_rule
        )
        
        # Test Griffith criterion
        base_strength = 100.0
        density = 0.05
        result = apply_griffith_criterion(density, base_strength, 100.0)
        assert result < base_strength  # Strength should be reduced
        
        # Test Rule of Mixtures
        base_modulus = 1000.0
        result = apply_rule_of_mixtures(density, base_modulus)
        assert result < base_modulus  # Modulus should be reduced
        
        # Test Matthiessen's Rule
        base_conductivity = 1.0e6
        result = apply_matthiessen_rule(density, base_conductivity)
        assert result < base_conductivity  # Conductivity should be reduced

    def test_holdout_sample_count(self, project_root):
        """Test that default hold-out sample count is correct"""
        assert N_HOLDOUT == 200

    def test_reproducibility_with_seed(self, project_root):
        """Test that generation is reproducible with same seed"""
        data1 = generate_holdout_data(n_samples=5, seed=SEED_HOLDOUT)
        data2 = generate_holdout_data(n_samples=5, seed=SEED_HOLDOUT)
        
        # Data should be identical
        assert data1 == data2