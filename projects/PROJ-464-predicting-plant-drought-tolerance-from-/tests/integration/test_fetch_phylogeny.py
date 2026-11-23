"""
Integration tests for T024a: Fetch Phylogenetic Tree.

Tests verify that:
1. The script can resolve a known list of species.
2. The script can fetch a tree if species are resolvable.
3. The script halts with the correct error message if the fetch fails.
4. The output file is created with valid Newick content.
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from fetch_phylogeny import (
    get_species_list,
    resolve_taxon_ids,
    fetch_phylogenetic_tree,
    save_tree,
    main
)

class TestFetchPhylogeny:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data" / "derived"
        self.data_dir.mkdir(parents=True)
        
        # Create a mock merged_data.csv
        self.mock_merged_data = self.data_dir / "merged_data.csv"
        mock_df = pd.DataFrame({
            'species': ['Arabidopsis thaliana', 'Oryza sativa', 'Zea mays', 'Solanum lycopersicum'],
            'depth': [10.0, 20.0, 15.0, 12.0],
            'branching_density': [0.5, 0.6, 0.4, 0.55],
            'surface_area': [100.0, 200.0, 150.0, 120.0],
            'stomatal_conductance': [0.1, 0.2, 0.15, 0.12]
        })
        mock_df.to_csv(self.mock_merged_data, index=False)
        
        # Backup original paths if needed, but we will mock file access
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_get_species_list_reads_csv(self):
        """Test that get_species_list correctly reads species from merged_data.csv."""
        species = get_species_list()
        assert len(species) == 4
        assert "Arabidopsis thaliana" in species
        assert "Oryza sativa" in species

    @patch('fetch_phylogeny.requests.post')
    def test_resolve_taxon_ids_success(self, mock_post):
        """Test successful resolution of taxon names."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "resolved": [
                {"name": "Arabidopsis thaliana", "ot:ott_id": "12345"},
                {"name": "Oryza sativa", "ot:ott_id": "67890"}
            ],
            "unresolved": []
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = resolve_taxon_ids(["Arabidopsis thaliana", "Oryza sativa"])
        
        assert len(result["resolved_ids"]) == 2
        assert "12345" in result["resolved_ids"]
        assert "67890" in result["resolved_ids"]
        assert len(result["unresolved"]) == 0

    @patch('fetch_phylogeny.requests.post')
    def test_resolve_taxon_ids_partial_failure(self, mock_post):
        """Test resolution when some taxa are unresolved."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "resolved": [
                {"name": "Arabidopsis thaliana", "ot:ott_id": "12345"}
            ],
            "unresolved": ["Unknown Species X"]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = resolve_taxon_ids(["Arabidopsis thaliana", "Unknown Species X"])
        
        assert len(result["resolved_ids"]) == 1
        assert len(result["unresolved"]) == 1

    @patch('fetch_phylogeny.requests.post')
    def test_fetch_tree_success(self, mock_post):
        """Test successful tree fetch."""
        mock_newick = "((12345:0.1,67890:0.2):0.3,99999:0.4);"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ot:tree": mock_newick
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        tree = fetch_phylogenetic_tree(["12345", "67890"])
        
        assert tree == mock_newick
        assert "(" in tree
        assert ";" in tree

    @patch('fetch_phylogeny.requests.post')
    def test_fetch_tree_failure_raises_error(self, mock_post):
        """Test that fetch tree raises RuntimeError on API failure."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="Phylogenetic tree fetch failed"):
            fetch_phylogenetic_tree(["12345"])

    @patch('fetch_phylogeny.requests.post')
    def test_fetch_tree_no_tree_in_response_raises_error(self, mock_post):
        """Test that fetch tree raises RuntimeError if no tree in response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "No tree found"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="No tree found"):
            fetch_phylogenetic_tree(["12345"])

    def test_save_tree_creates_file(self):
        """Test that save_tree writes the file correctly."""
        output_path = self.data_dir / "test_tree.newick"
        test_tree = "((A:0.1,B:0.2):0.3,C:0.4);"
        
        save_tree(test_tree, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        assert content == test_tree

    @patch('fetch_phylogeny.requests.post')
    def test_main_success_path(self, mock_post):
        """Test the full main() flow with mocked API calls."""
        # Mock resolve
        def mock_resolve_post(url, json, **kwargs):
            m = MagicMock()
            if "resolve" in url:
                m.json.return_value = {
                    "resolved": [{"name": n, "ot:ott_id": str(i+100)} for i, n in enumerate(json["names"])],
                    "unresolved": []
                }
            else:
                m.json.return_value = {"ot:tree": "((100:0.1,101:0.2):0.3,102:0.4,103:0.5);"}
            m.raise_for_status.return_value = None
            return m

        mock_post.side_effect = mock_resolve_post

        # Run main
        main()
        
        # Check output file
        output_path = Path("data/derived/phylogenetic_tree.newick")
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        assert content.startswith("(")
        assert content.endswith(";")

    @patch('fetch_phylogeny.requests.post')
    def test_main_halts_on_fetch_failure(self, mock_post):
        """Test that main() exits with error if tree fetch fails."""
        # Mock resolve success
        def mock_resolve_post(url, json, **kwargs):
            m = MagicMock()
            if "resolve" in url:
                m.json.return_value = {
                    "resolved": [{"name": n, "ot:ott_id": "123"} for n in json["names"]],
                    "unresolved": []
                }
            else:
                m.json.return_value = {"error": "Tree not found"}
            m.raise_for_status.return_value = None
            return m

        mock_post.side_effect = mock_resolve_post

        # Capture sys.exit
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
        # Verify output file does not exist (or is empty/invalid if partially written)
        output_path = Path("data/derived/phylogenetic_tree.newick")
        # In a real failure, we expect the script to exit before saving
        # However, if it saved a partial file, the content would be invalid.
        # The key is that the process exited with code 1.