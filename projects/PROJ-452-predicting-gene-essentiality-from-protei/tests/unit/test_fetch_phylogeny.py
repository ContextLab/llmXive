import os
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import pytest

# Import the module functions
# We assume fetch_phylogeny is in the code directory, so we need to handle imports carefully
# For testing, we will mock the config and requests
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from fetch_phylogeny import (
    get_taxonomic_ids_for_organisms, 
    fetch_supertree, 
    extract_newick, 
    save_newick_tree,
    PhylogenyFetchError
)
from config import load_config

logger = logging.getLogger(__name__)

class TestFetchPhylogeny:
    @patch('fetch_phylogeny.requests.get')
    def test_get_taxonomic_ids_for_organisms_success(self, mock_get):
        """Test successful retrieval of taxonomic IDs."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'ot:ott_id': 12345}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        config = {'taxonomic_mappings': {}} # Empty explicit map to force API call
        organisms = ['Escherichia coli']
        
        result = get_taxonomic_ids_for_organisms(organisms, config)
        
        assert 'Escherichia coli' in result
        assert result['Escherichia coli'] == 12345
        mock_get.assert_called_once()

    @patch('fetch_phylogeny.requests.post')
    def test_fetch_supertree_success(self, mock_post):
        """Test successful supertree fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'tree': '(A:1.0, B:2.0);'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = fetch_supertree([100, 200])
        
        assert result is not None
        assert 'tree' in result
        assert result['tree'] == '(A:1.0, B:2.0);'

    @patch('fetch_phylogeny.requests.post')
    def test_fetch_supertree_failure(self, mock_post):
        """Test failure in supertree fetch."""
        mock_post.side_effect = Exception("Network Error")

        result = fetch_supertree([100])
        
        assert result is None

    def test_extract_newick_success(self):
        """Test extraction of Newick string."""
        data = {'tree': '(A:1.0, B:2.0);'}
        result = extract_newick(data)
        assert result == '(A:1.0, B:2.0);'

    def test_extract_newick_missing_tree(self):
        """Test extraction when tree key is missing."""
        data = {'ott_ids': {}}
        result = extract_newick(data)
        assert result is None

    def test_save_newick_tree(self):
        """Test saving Newick string to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_tree.newick"
            newick_str = "(A:1.0, B:2.0);"
            
            save_newick_tree(newick_str, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
            assert content == newick_str
