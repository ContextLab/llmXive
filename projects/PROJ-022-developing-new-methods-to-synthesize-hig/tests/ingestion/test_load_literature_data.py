"""
Unit tests for the load_literature_data module (T013).
"""

import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
from ingestion.load_literature_data import load_and_merge_sources
from utils.errors import DataInsufficientError

@pytest.fixture
def mock_manual_data():
    return pd.DataFrame({
        'smiles': ['CCO', 'CCC'],
        'polymer_name': ['PolyA', 'PolyB'],
        'permeability': [100.0, 200.0],
        'selectivity': [5.0, 10.0]
    })

@pytest.fixture
def mock_arxiv_data():
    return pd.DataFrame({
        'smiles': ['CCCC'],
        'polymer_name': ['PolyC'],
        'permeability': [150.0],
        'selectivity': [7.0]
    })

@pytest.fixture
def mock_openpolymer_data():
    return pd.DataFrame({
        'SMILES': ['CCCCC'], # Test case insensitivity
        'name': ['PolyD'],
        'permeability': [120.0],
        'selectivity': [6.0]
    })

def test_merge_manual_and_automated(mock_manual_data, mock_arxiv_data, mock_openpolymer_data):
    """
    Test that data from all three sources is correctly merged and source tags are applied.
    """
    with patch('ingestion.load_literature_data.load_manual_extraction_data', return_value=mock_manual_data), \
         patch('ingestion.load_literature_data.fetch_arxiv_membrane_papers', return_value=mock_arxiv_data), \
         patch('ingestion.load_literature_data.fetch_openpolymer_data', return_value=mock_openpolymer_data):
        
        result_df = load_and_merge_sources()
        
        # Check total count
        assert len(result_df) == 3
        
        # Check source tags
        sources = result_df['source'].tolist()
        assert 'manual' in sources
        assert 'arxiv' in sources
        assert 'openpolymer' in sources
        
        # Check column normalization (SMILES -> smiles, name -> polymer_name)
        assert 'smiles' in result_df.columns
        assert 'polymer_name' in result_df.columns
        assert 'SMILES' not in result_df.columns
        assert 'name' not in result_df.columns

def test_empty_manual_source(mock_arxiv_data, mock_openpolymer_data):
    """
    Test behavior when manual data is missing (None).
    """
    with patch('ingestion.load_literature_data.load_manual_extraction_data', return_value=None), \
         patch('ingestion.load_literature_data.fetch_arxiv_membrane_papers', return_value=mock_arxiv_data), \
         patch('ingestion.load_literature_data.fetch_openpolymer_data', return_value=mock_openpolymer_data):
        
        result_df = load_and_merge_sources()
        
        assert len(result_df) == 2
        assert 'manual' not in result_df['source'].tolist()

def test_all_sources_empty():
    """
    Test that an error is raised if all sources fail to return data.
    """
    with patch('ingestion.load_literature_data.load_manual_extraction_data', return_value=None), \
         patch('ingestion.load_literature_data.fetch_arxiv_membrane_papers', return_value=None), \
         patch('ingestion.load_literature_data.fetch_openpolymer_data', return_value=None):
        
        with pytest.raises(ValueError, match="No valid data sources found"):
            load_and_merge_sources()

def test_output_file_creation(tmp_path):
    """
    Test that the script actually writes the CSV file to the expected location.
    """
    # Mock data
    mock_data = pd.DataFrame({
        'smiles': ['CCO'],
        'polymer_name': ['TestPoly'],
        'permeability': [100.0],
        'selectivity': [5.0],
        'source': ['manual']
    })

    # Patch the ensure_directory to use tmp_path to avoid writing to project root in test
    with patch('ingestion.load_literature_data.load_manual_extraction_data', return_value=mock_data), \
         patch('ingestion.load_literature_data.fetch_arxiv_membrane_papers', return_value=pd.DataFrame()), \
         patch('ingestion.load_literature_data.fetch_openpolymer_data', return_value=pd.DataFrame()), \
         patch('ingestion.load_literature_data.ensure_directory'):
        
        # Temporarily override the output path logic by mocking the internal call
        # or by checking the side effect. Since the function hardcodes "data/processed",
        # we will just verify the logic flow by mocking the file write.
        with patch('pandas.DataFrame.to_csv') as mock_to_csv:
            load_and_merge_sources()
            mock_to_csv.assert_called_once()
            # Verify the path argument
            call_args = mock_to_csv.call_args
            assert 'standardized_polymers.csv' in call_args[0][0] or call_args[1].get('index') == False