import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from select_convergence_targets import load_network_metrics, select_representative_graphs, save_convergence_targets

@pytest.fixture
def sample_networks_csv(tmp_path):
    """Create a temporary CSV file with sample network data."""
    csv_path = tmp_path / "networks.csv"
    data = {
        'id': ['graph_0001', 'graph_0002', 'graph_0003', 'graph_0004', 'graph_0005',
               'graph_0006', 'graph_0007', 'graph_0008', 'graph_0009', 'graph_0010'],
        'class': ['random', 'random', 'scale_free', 'scale_free', 'small_world',
                  'small_world', 'lattice', 'lattice', 'star', 'star'],
        'average_degree': [4.0, 4.2, 3.8, 3.9, 5.0, 5.1, 6.0, 6.0, 2.0, 2.0],
        'clustering_coefficient': [0.1, 0.12, 0.3, 0.28, 0.4, 0.42, 0.6, 0.6, 0.0, 0.0],
        'average_path_length': [3.5, 3.4, 4.1, 4.0, 2.8, 2.7, 3.0, 3.0, 1.5, 1.5]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def empty_csv(tmp_path):
    """Create an empty CSV file with headers only."""
    csv_path = tmp_path / "empty_networks.csv"
    pd.DataFrame(columns=['id', 'class', 'average_degree', 'clustering_coefficient', 'average_path_length']).to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def missing_col_csv(tmp_path):
    """Create a CSV file missing a required column."""
    csv_path = tmp_path / "missing_col_networks.csv"
    data = {
        'id': ['graph_0001'],
        'class': ['random'],
        'average_degree': [4.0],
        'clustering_coefficient': [0.1]
        # missing 'average_path_length'
    }
    pd.DataFrame(data).to_csv(csv_path, index=False)
    return str(csv_path)

def test_load_network_metrics_valid(sample_networks_csv):
    """Test loading a valid CSV file."""
    df = load_network_metrics(sample_networks_csv)
    assert len(df) == 10
    assert 'id' in df.columns
    assert 'class' in df.columns
    assert 'average_degree' in df.columns

def test_load_network_metrics_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_network_metrics("nonexistent/path.csv")

def test_load_network_metrics_missing_columns(missing_col_csv):
    """Test that ValueError is raised for missing columns."""
    with pytest.raises(ValueError):
        load_network_metrics(missing_col_csv)

def test_load_network_metrics_empty(empty_csv):
    """Test loading an empty CSV (headers only)."""
    df = load_network_metrics(empty_csv)
    assert len(df) == 0

def test_select_representative_graphs(sample_networks_csv):
    """Test selection of representative graphs."""
    df = load_network_metrics(sample_networks_csv)
    selected_ids = select_representative_graphs(df)
    
    # Should select one per class (5 classes)
    assert len(selected_ids) == 5
    
    # Check uniqueness
    assert len(set(selected_ids)) == 5
    
    # Check that all classes are represented
    classes_in_df = df['class'].unique()
    assert len(selected_ids) == len(classes_in_df)

def test_select_representative_graphs_ties(sample_networks_csv):
    """Test tie-breaking by lowest ID."""
    # The test data has ties for 'lattice' (6.0, 6.0) and 'star' (2.0, 2.0)
    df = load_network_metrics(sample_networks_csv)
    selected_ids = select_representative_graphs(df)
    
    # For 'lattice', graph_0007 and graph_0008 both have avg_degree 6.0
    # graph_0007 should be selected (lower ID)
    # For 'star', graph_0009 and graph_0010 both have avg_degree 2.0
    # graph_0009 should be selected (lower ID)
    assert 'graph_0007' in selected_ids
    assert 'graph_0009' in selected_ids

def test_select_representative_graphs_empty(empty_csv):
    """Test selection on empty DataFrame."""
    df = load_network_metrics(empty_csv)
    selected_ids = select_representative_graphs(df)
    assert selected_ids == []

def test_save_convergence_targets(tmp_path):
    """Test saving convergence targets to JSON."""
    selected_ids = ['graph_0001', 'graph_0003', 'graph_0005']
    output_path = str(tmp_path / "targets.json")
    
    save_convergence_targets(selected_ids, output_path)
    
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['count'] == 3
    assert data['convergence_targets'] == selected_ids
    assert 'description' in data

def test_full_pipeline(sample_networks_csv, tmp_path):
    """Test the full pipeline from loading to saving."""
    output_path = str(tmp_path / "convergence_targets.json")
    
    df = load_network_metrics(sample_networks_csv)
    selected_ids = select_representative_graphs(df)
    save_convergence_targets(selected_ids, output_path)
    
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data['convergence_targets']) == 5
    assert data['count'] == 5