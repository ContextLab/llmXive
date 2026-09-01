import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import os

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from data_ingestion import sample_holdout_known, load_hmao_dataset

def test_sample_holdout_known():
    """
    Test that sample_holdout_known correctly samples compositions
    that are not in the training set.
    """
    # Mock data
    aflow_raw_data = [
        {'composition': 'A B C D E', 'energy': -1.0},
        {'composition': 'F G H I J', 'energy': -2.0},
        {'composition': 'K L M N O', 'energy': -3.0},
        {'composition': 'P Q R S T', 'energy': -4.0},
        {'composition': 'U V W X Y', 'energy': -5.0},
    ]
    train_index = {'a b c d e', 'f g h i j'}  # lowercase, stripped
    n_samples = 2
    seed = 42

    sampled = sample_holdout_known(aflow_raw_data, train_index, n_samples, seed)

    # Check that we got the correct number of samples
    assert len(sampled) == n_samples

    # Check that none of the sampled compositions are in the training set
    for row in sampled:
        assert row['composition'].strip().lower() not in train_index

def test_load_hmao_dataset_fails_loudly():
    """
    Test that load_hmao_dataset raises an exception when the dataset fetch fails.
    """
    with patch('datasets.load_dataset') as mock_load_dataset:
        mock_load_dataset.side_effect = ConnectionError("Failed to load dataset")
        
        with pytest.raises(ConnectionError):
            load_hmao_dataset(streaming=True)
