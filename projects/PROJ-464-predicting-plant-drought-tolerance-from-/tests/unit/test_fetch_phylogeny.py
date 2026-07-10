import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd

# Add project root to path if needed (usually handled by pytest config)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.fetch_phylogeny import (
    get_species_list_from_data,
    fetch_otolith_id,
    fetch_phylogenetic_tree,
    main
)

class TestGetSpeciesListFromData:
    def test_loads_species_from_merged_data(self, tmp_path):
        # Create a mock merged_data.csv
        data_dir = tmp_path / "data" / "derived"
        data_dir.mkdir(parents=True)
        csv_path = data_dir / "merged_data.csv"
        
        df = pd.DataFrame({
            'species_id': ['Arabidopsis_thaliana', 'Zea_mays', 'Solanum_lycopersicum'],
            'conductance': [0.1, 0.2, 0.3]
        })
        df.to_csv(csv_path, index=False)
        
        # Mock the Path existence check and reading
        with patch('code.fetch_phylogeny.Path.exists', return_value=True):
            with patch('code.fetch_phylogeny.pd.read_csv', return_value=df):
                species = get_species_list_from_data()
        
        assert len(species) == 3
        assert 'Arabidopsis_thaliana' in species

    def test_handles_missing_file(self, tmp_path):
        with patch('code.fetch_phylogeny.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                get_species_list_from_data()

class TestFetchOttId:
    @patch('code.fetch_phylogeny.requests.post')
    def test_returns_ott_id_on_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'otolith_id': '12345'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        ott_id = fetch_otolith_id("Test_Species")
        
        assert ott_id == "12345"
        mock_post.assert_called_once()

    @patch('code.fetch_phylogeny.requests.post')
    def test_returns_none_on_missing_id(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {} # No ott_id key
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        ott_id = fetch_otolith_id("Test_Species")
        
        assert ott_id is None

    @patch('code.fetch_phylogeny.requests.post')
    def test_returns_none_on_network_error(self, mock_post):
        mock_post.side_effect = Exception("Network Error")
        
        ott_id = fetch_otolith_id("Test_Species")
        
        assert ott_id is None

class TestFetchPhylogeneticTree:
    @patch('code.fetch_phylogeny.requests.post')
    def test_writes_newick_file_on_success(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.json.return_value = {'newick': '(A:1.0, B:1.0);'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        output_path = tmp_path / "test_tree.newick"
        
        success = fetch_phylogenetic_tree(['123', '456'], output_path)
        
        assert success is True
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        assert content == '(A:1.0, B:1.0);'

    @patch('code.fetch_phylogeny.requests.post')
    def test_returns_false_on_missing_newick_key(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.json.return_value = {'error': 'Tree not found'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        output_path = tmp_path / "test_tree.newick"
        
        success = fetch_phylogenetic_tree(['123'], output_path)
        
        assert success is False
        assert not output_path.exists()

    def test_returns_false_on_empty_ott_ids(self, tmp_path):
        output_path = tmp_path / "test_tree.newick"
        success = fetch_phylogenetic_tree([], output_path)
        assert success is False

class TestMain:
    @patch('code.fetch_phylogeny.get_species_list_from_data')
    @patch('code.fetch_phylogeny.fetch_otolith_id')
    @patch('code.fetch_phylogeny.fetch_phylogenetic_tree')
    @patch('code.fetch_phylogeny.ensure_directories')
    def test_main_success(
        self, mock_ensure, mock_fetch_tree, mock_fetch_ott, mock_get_species, tmp_path
    ):
        # Setup mocks
        mock_get_species.return_value = ['Species_A']
        mock_fetch_ott.return_value = '123'
        mock_fetch_tree.return_value = True
        
        # Create a dummy config file to satisfy ensure_directories if needed
        (tmp_path / "config.py").touch()
        
        # Change CWD to tmp_path to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Mock sys.exit to prevent actual exit
            with patch('code.fetch_phylogeny.sys.exit') as mock_exit:
                main()
            
            # Verify calls
            mock_get_species.assert_called_once()
            mock_fetch_ott.assert_called_once_with('Species_A')
            mock_fetch_tree.assert_called_once()
            mock_exit.assert_not_called() # Should not exit on success
        finally:
            os.chdir(original_cwd)

    @patch('code.fetch_phylogeny.get_species_list_from_data')
    @patch('code.fetch_phylogeny.fetch_otolith_id')
    @patch('code.fetch_phylogeny.fetch_phylogenetic_tree')
    @patch('code.fetch_phylogeny.ensure_directories')
    def test_main_halts_on_no_ott_ids(
        self, mock_ensure, mock_fetch_tree, mock_fetch_ott, mock_get_species, tmp_path
    ):
        mock_get_species.return_value = ['Species_A']
        mock_fetch_ott.return_value = None # No OTT ID found
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            with patch('code.fetch_phylogeny.sys.exit') as mock_exit:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                # Verify exit code is 1 (failure)
                assert exc_info.value.code == 1
                # Verify critical error logic was triggered
                assert mock_exit.called
        finally:
            os.chdir(original_cwd)
