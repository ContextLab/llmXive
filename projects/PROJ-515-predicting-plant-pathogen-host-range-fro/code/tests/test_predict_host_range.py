import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We assume the module is importable as src.cli.predict_host_range
# Adjust import path if necessary based on project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.cli.predict_host_range import parse_args, load_reference_hosts, run_prediction, main

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_fasta(temp_data_dir):
    fasta_path = temp_data_dir / "sample.fa"
    with open(fasta_path, 'w') as f:
        f.write(">test_pathogen\nATCGATCGATCG\n")
    return str(fasta_path)

@pytest.fixture
def sample_model(temp_data_dir):
    # Create a dummy model file (pickle)
    import pickle
    model_path = temp_data_dir / "model.pkl"
    # Mock a logistic regression model with predict_proba
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.1, 0.9]]) # 90% probability
    mock_model.feature_names_in_ = ['effector_count', 'sm_clusters', 'gc_content', 'kmer_1', 'kmer_2']
    with open(model_path, 'wb') as f:
        pickle.dump(mock_model, f)
    return model_path

@pytest.fixture
def sample_interactions(temp_data_dir):
    # Create a dummy interactions CSV
    interactions_path = temp_data_dir / "interactions_merged.csv"
    data = {
        'pathogen_id': ['P1', 'P1', 'P2'],
        'host_species': ['H1', 'H2', 'H1'],
        'label': [1, 0, 1]
    }
    df = pd.DataFrame(data)
    df.to_csv(interactions_path, index=False)
    return interactions_path

def test_parse_args():
    with patch('sys.argv', ['prog', '--genome', 'test.fa', '--seed', '123']):
        args = parse_args()
        assert args.genome == 'test.fa'
        assert args.seed == 123

def test_load_reference_hosts(sample_interactions):
    # Mock config to point to sample_interactions parent
    config = {'paths': {'raw_data': str(sample_interactions.parent)}}
    hosts = load_reference_hosts(config)
    assert set(hosts) == {'H1', 'H2'}

@patch('src.cli.predict_host_range.extract_single_genome_features')
@patch('src.cli.predict_host_range.load_model')
def test_run_prediction(mock_load_model, mock_extract, sample_fasta, sample_model, sample_interactions):
    # Setup mocks
    mock_extract.return_value = {
        'effector_count': 1,
        'sm_clusters': 0,
        'gc_content': 0.5,
        'kmer_profile': {'ATCG': 1},
        'pfam_counts': {'PF0001': 1}
    }
    
    mock_model_instance = MagicMock()
    mock_model_instance.predict_proba.return_value = np.array([[0.8]])
    mock_load_model.return_value = mock_model_instance
    
    config = {'paths': {'raw_data': str(sample_interactions.parent)}}
    reference_hosts = ['H1', 'H2']
    
    predictions, breadth = run_prediction(sample_fasta, sample_model, reference_hosts, config)
    
    assert len(predictions) == 2
    assert predictions['H1'] == 0.8
    assert predictions['H2'] == 0.8
    assert breadth == 0.8

@patch('src.cli.predict_host_range.extract_single_genome_features')
@patch('src.cli.predict_host_range.load_model')
def test_run_prediction_zero_feature(mock_load_model, mock_extract, sample_fasta, sample_model, sample_interactions):
    # Simulate Zero-Feature Pathogen
    mock_extract.return_value = {
        'effector_count': 0,
        'sm_clusters': 0,
        'gc_content': 0,
        'kmer_profile': {}, # Empty
        'pfam_counts': {}
    }
    
    config = {'paths': {'raw_data': str(sample_interactions.parent)}}
    reference_hosts = ['H1', 'H2']
    
    predictions, breadth = run_prediction(sample_fasta, sample_model, reference_hosts, config)
    
    # Should assign baseline probability (calculated from interactions: 2 pos / 3 total = 0.666)
    expected_baseline = 2/3
    assert abs(predictions['H1'] - expected_baseline) < 0.001
    assert abs(predictions['H2'] - expected_baseline) < 0.001
    assert abs(breadth - expected_baseline) < 0.001

def test_main_execution(temp_data_dir, sample_fasta, sample_model, sample_interactions):
    # Mock sys.argv
    args = [
        'prog', 
        '--genome', sample_fasta, 
        '--model', str(sample_model),
        '--output-dir', str(temp_data_dir),
        '--seed', '42'
    ]
    
    # Mock the interactions path in config to point to our temp file
    # This is tricky because config is global. We patch the get_default_config or the load logic.
    # For this test, we assume the environment is set up correctly or we patch the specific function.
    
    with patch('sys.argv', args):
        with patch('src.cli.predict_host_range.load_reference_hosts') as mock_load_hosts:
            mock_load_hosts.return_value = ['H1', 'H2']
            with patch('src.cli.predict_host_range.extract_single_genome_features') as mock_extract:
                mock_extract.return_value = {
                    'effector_count': 1, 'sm_clusters': 0, 'gc_content': 0.5,
                    'kmer_profile': {'ATCG': 1}, 'pfam_counts': {'PF0001': 1}
                }
                with patch('src.cli.predict_host_range.load_model') as mock_load_model:
                    mock_model = MagicMock()
                    mock_model.predict_proba.return_value = np.array([[0.9]])
                    mock_load_model.return_value = mock_model
                    
                    main()
                    
                    # Check outputs
                    pred_csv = temp_data_dir / "prediction.csv"
                    breadth_json = temp_data_dir / "host_range_breadth.json"
                    
                    assert pred_csv.exists()
                    assert breadth_json.exists()
                    
                    df = pd.read_csv(pred_csv)
                    assert 'host_species' in df.columns
                    assert 'probability' in df.columns
                    assert len(df) == 2