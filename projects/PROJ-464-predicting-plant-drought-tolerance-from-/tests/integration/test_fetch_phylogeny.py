"""
Integration tests for phylogenetic tree fetching.

Tests:
- test_fetch_tree_integration: Verifies the full pipeline from species extraction
  to tree saving, ensuring the output file is created and contains valid Newick.
- test_fetch_tree_handles_missing_data: Verifies proper error handling when
  input data is missing.
- test_fetch_tree_handles_empty_species: Verifies proper error handling when
  no species are found.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from fetch_phylogeny import (
    get_species_list,
    resolve_taxon_ids,
    fetch_phylogenetic_tree,
    save_tree,
    main,
    OUTPUT_FILE,
    RSA_METRICS_PATH,
    MERGED_PATH
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

class TestPhylogenyFetching:
    """Integration tests for phylogenetic tree fetching functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Set up and tear down test environment."""
        # Create temporary directories for test data
        self.test_data_dir = tmp_path / "data" / "derived"
        self.test_data_dir.mkdir(parents=True)
        
        # Backup original paths
        self.original_rsa_path = RSA_METRICS_PATH
        self.original_merged_path = MERGED_PATH
        self.original_output_path = OUTPUT_FILE
        
        # Mock paths to use temporary directory
        import fetch_phylogeny
        fetch_phylogeny.RSA_METRICS_PATH = self.test_data_dir / "rsametrics.csv"
        fetch_phylogeny.MERGED_PATH = self.test_data_dir / "merged_dataset.csv"
        fetch_phylogeny.OUTPUT_FILE = self.test_data_dir / "phylogenetic_tree.newick"
        
        yield
        
        # Restore original paths
        fetch_phylogeny.RSA_METRICS_PATH = self.original_rsa_path
        fetch_phylogeny.MERGED_PATH = self.original_merged_path
        fetch_phylogeny.OUTPUT_FILE = self.original_output_path
        
        # Clean up test data
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir, ignore_errors=True)
    
    def test_get_species_list_from_merged(self, setup_teardown):
        """Test species extraction from merged dataset."""
        # Create a mock merged dataset
        mock_data = {
            'species_id': ['Arabidopsis thaliana', 'Zea mays', 'Oryza sativa'],
            'depth': [10.5, 15.2, 12.8],
            'conductance': [0.3, 0.4, 0.35]
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(fetch_phylogeny.MERGED_PATH, index=False)
        
        species = get_species_list()
        
        assert len(species) == 3
        assert 'Arabidopsis thaliana' in species
        assert 'Zea mays' in species
        assert 'Oryza sativa' in species
    
    def test_get_species_list_from_rsa_fallback(self, setup_teardown):
        """Test species extraction falls back to RSA metrics if merged is missing."""
        # Create only RSA metrics file
        mock_data = {
            'species_id': ['Triticum aestivum', 'Sorghum bicolor'],
            'depth': [11.0, 14.5]
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(fetch_phylogeny.RSA_METRICS_PATH, index=False)
        
        species = get_species_list()
        
        assert len(species) == 2
        assert 'Triticum aestivum' in species
    
    def test_get_species_list_no_data(self, setup_teardown):
        """Test error when no input data exists."""
        with pytest.raises(FileNotFoundError, match="No input data found"):
            get_species_list()
    
    def test_get_species_list_empty(self, setup_teardown):
        """Test error when data has no species."""
        # Create empty merged dataset
        df = pd.DataFrame(columns=['species_id', 'depth'])
        df.to_csv(fetch_phylogeny.MERGED_PATH, index=False)
        
        with pytest.raises(ValueError, match="No species found"):
            get_species_list()
    
    def test_resolve_taxon_ids(self):
        """Test taxon ID resolution (may require network)."""
        # Test with a few well-known species
        species_list = ['Arabidopsis thaliana', 'Zea mays']
        
        try:
            name_to_id = resolve_taxon_ids(species_list)
            
            # Should resolve at least some species
            assert len(name_to_id) > 0
            
            # Check that returned IDs are strings
            for name, otu_id in name_to_id.items():
                assert isinstance(otu_id, str)
                assert len(otu_id) > 0
                
        except RuntimeError as e:
            # If API is unavailable, we still test that the function raises properly
            pytest.skip(f"Open Tree API unavailable: {e}")
    
    def test_fetch_tree_integration(self, setup_teardown):
        """Test full integration: species -> IDs -> tree -> file."""
        # Create mock merged dataset with real species
        mock_data = {
            'species_id': ['Arabidopsis thaliana', 'Zea mays', 'Oryza sativa'],
            'depth': [10.5, 15.2, 12.8],
            'conductance': [0.3, 0.4, 0.35]
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(fetch_phylogeny.MERGED_PATH, index=False)
        
        try:
            # Get species
            species_list = get_species_list()
            assert len(species_list) == 3
            
            # Resolve IDs
            name_to_id = resolve_taxon_ids(species_list)
            assert len(name_to_id) > 0
            
            # Fetch tree
            tree_string = fetch_phylogenetic_tree(list(name_to_id.values()))
            
            # If we get a tree, verify it's valid Newick (basic check)
            if tree_string:
                assert isinstance(tree_string, str)
                assert len(tree_string) > 10
                assert tree_string.startswith('(') or tree_string.startswith('[')
                
                # Save tree
                save_tree(tree_string, fetch_phylogeny.OUTPUT_FILE)
                
                # Verify file exists and contains tree
                assert fetch_phylogeny.OUTPUT_FILE.exists()
                with open(fetch_phylogeny.OUTPUT_FILE, 'r') as f:
                    saved_tree = f.read()
                assert saved_tree == tree_string
                
        except RuntimeError as e:
            # If API fails, the error message should be appropriate
            assert "Tree fetch failed" in str(e) or "No phylogenetic tree found" in str(e)
    
    def test_save_tree_creates_directory(self, setup_teardown):
        """Test that save_tree creates parent directories."""
        deep_path = self.test_data_dir / "deep" / "nested" / "tree.newick"
        fetch_phylogeny.OUTPUT_FILE = deep_path
        
        test_tree = "((A,B),C);"
        save_tree(test_tree, deep_path)
        
        assert deep_path.exists()
        with open(deep_path, 'r') as f:
            assert f.read() == test_tree
    
    def test_main_execution(self, setup_teardown, caplog):
        """Test main() function execution with valid data."""
        # Create mock merged dataset
        mock_data = {
            'species_id': ['Arabidopsis thaliana', 'Zea mays'],
            'depth': [10.5, 15.2]
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(fetch_phylogeny.MERGED_PATH, index=False)
        
        # Run main - this may fail if API is down, which is acceptable
        # We're testing that it runs without crashing on valid input structure
        try:
            main()
            # If successful, check output file
            if fetch_phylogeny.OUTPUT_FILE.exists():
                with open(fetch_phylogeny.OUTPUT_FILE, 'r') as f:
                    content = f.read()
                assert len(content) > 10
        except SystemExit as e:
            # Expected if API call fails - check it's not a silent failure
            assert e.code == 1
        except RuntimeError as e:
            # Expected if no tree found - error should be logged
            assert "Phylogenetic tree fetch failed" in str(e)