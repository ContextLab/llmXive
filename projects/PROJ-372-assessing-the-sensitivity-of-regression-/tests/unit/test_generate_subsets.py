"""
Unit tests for T047: Subset Generation.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.generate_subsets import generate_subset_indices, main

class TestGenerateSubsetIndices:
    def test_generate_subset_basic(self):
        """Test basic generation of a subset."""
        n_total = 100
        n_subset = 10
        seed_offset = 0
        
        indices = generate_subset_indices(n_total, n_subset, seed_offset)
        
        assert len(indices) == n_subset
        assert all(0 <= i < n_total for i in indices)
        assert len(set(indices)) == n_subset  # No duplicates
        assert indices == sorted(indices)  # Sorted

    def test_generate_subset_unique_across_offsets(self):
        """Test that different seed offsets produce different subsets."""
        n_total = 100
        n_subset = 10
        
        indices1 = generate_subset_indices(n_total, n_subset, seed_offset=0)
        indices2 = generate_subset_indices(n_total, n_subset, seed_offset=1)
        
        # They should not be identical
        assert indices1 != indices2

    def test_generate_subset_exceeds_total(self):
        """Test that requesting more items than available raises an error."""
        with pytest.raises(ValueError):
            generate_subset_indices(10, 20, 0)

    def test_generate_subset_equal_to_total(self):
        """Test that requesting all items returns all items."""
        n_total = 10
        indices = generate_subset_indices(n_total, n_total, 0)
        assert indices == list(range(n_total))

class TestMainFunction:
    def test_main_requires_profile(self):
        """Test that main() fails if profile is missing."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir) / "artifacts" / "stability"
            profiles_dir = Path(tmpdir) / "artifacts" / "profiles"
            profiles_dir.mkdir(parents=True)
            
            # Override global constants in the module
            import code.generate_subsets as gs
            original_output_dir = gs.OUTPUT_DIR
            original_project_root = gs.PROJECT_ROOT
            original_dataset_name = gs.DATASET_NAME
            
            try:
                gs.OUTPUT_DIR = artifacts_dir
                gs.PROJECT_ROOT = Path(tmpdir)
                gs.DATASET_NAME = "nonexistent"
                
                # This should raise FileNotFoundError
                with pytest.raises(FileNotFoundError):
                    gs.main()
            finally:
                # Restore original values
                gs.OUTPUT_DIR = original_output_dir
                gs.PROJECT_ROOT = original_project_root
                gs.DATASET_NAME = original_dataset_name

    def test_main_generates_files(self):
        """Test that main() generates the expected output files when profile exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir) / "artifacts" / "stability"
            profiles_dir = Path(tmpdir) / "artifacts" / "profiles"
            profiles_dir.mkdir(parents=True)
            
            # Create a mock profile
            profile_data = {"n_observations": 1000}
            profile_path = profiles_dir / "auto_profile.json"
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f)
            
            # Create a mock config file to satisfy load_config
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, 'w') as f:
                f.write("sample_tiers:\n  - 10\n  - 25\n")
            
            import code.generate_subsets as gs
            original_output_dir = gs.OUTPUT_DIR
            original_project_root = gs.PROJECT_ROOT
            original_dataset_name = gs.DATASET_NAME
            original_config_path = gs.PROJECT_ROOT / "config.yaml" # Mocking config loading path logic if needed
            
            try:
                gs.OUTPUT_DIR = artifacts_dir
                gs.PROJECT_ROOT = Path(tmpdir)
                gs.DATASET_NAME = "auto"
                
                # Mock load_config and load_sample_tiers to avoid file dependency issues in test
                # We patch them directly in the module
                def mock_load_config():
                    return {"sample_tiers": [10, 25]}
                
                def mock_load_sample_tiers(cfg):
                    return cfg.get("sample_tiers", [10, 25])
                
                gs.load_config = mock_load_config
                gs.load_sample_tiers = mock_load_sample_tiers
                
                # Run main
                gs.main()
                
                # Check that files were created
                assert (artifacts_dir / "subsets_tier_10pct.json").exists()
                assert (artifacts_dir / "subsets_tier_25pct.json").exists()
                assert (artifacts_dir / "subsets_summary.json").exists()
                assert (artifacts_dir / "subsets_checkpoint.json").exists()
                
                # Verify content of one file
                with open(artifacts_dir / "subsets_tier_10pct.json", 'r') as f:
                    data = json.load(f)
                    assert isinstance(data, list)
                    # N=200 subsets per tier
                    assert len(data) == 200 
                    # Each subset should have 10% of 1000 = 100 items
                    assert len(data[0]) == 100
                    
            finally:
                gs.OUTPUT_DIR = original_output_dir
                gs.PROJECT_ROOT = original_project_root
                gs.DATASET_NAME = original_dataset_name
                gs.load_config = gs.load_config # Restore if needed, though function reassignment is local
                gs.load_sample_tiers = gs.load_sample_tiers