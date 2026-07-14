"""
Integration test for centrality metric calculation (T020).

Verifies that the centrality module correctly processes connectivity matrices
and produces valid CSV output with expected columns.
"""

import os
import tempfile
import shutil
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
import pytest

# Import the module under test
# Note: In a real run, ensure code/ is in sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.centrality import (
    compute_centrality_metrics,
    run_centrality_analysis,
    get_subject_list_from_directory,
    process_subject
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    base_path = Path(temp_dir)

    # Create directory structure
    (base_path / "processed" / "connectivity").mkdir(parents=True)
    (base_path / "processed" / "centrality").mkdir(parents=True)

    yield base_path

    # Cleanup
    shutil.rmtree(temp_dir)


def create_test_connectivity_matrix(n_nodes=10, seed=42):
    """
    Create a synthetic but realistic connectivity matrix for testing.
    """
    np.random.seed(seed)
    # Create a random symmetric matrix with positive values
    matrix = np.random.rand(n_nodes, n_nodes)
    matrix = (matrix + matrix.T) / 2  # Symmetrize
    np.fill_diagonal(matrix, 0)  # Zero diagonal
    return matrix


def test_compute_centrality_metrics():
    """Test that centrality metrics are computed correctly for a known graph."""
    # Create a simple star graph matrix manually
    # Node 0 is connected to all others (1-4), others only connected to 0
    n = 5
    matrix = np.zeros((n, n))
    for i in range(1, n):
        matrix[0, i] = 1.0
        matrix[i, 0] = 1.0

    metrics = compute_centrality_metrics(matrix)

    # Check keys exist
    assert 'degree' in metrics
    assert 'betweenness' in metrics
    assert 'eigenvector' in metrics

    # Check shapes
    assert metrics['degree'].shape == (n,)
    assert metrics['betweenness'].shape == (n,)
    assert metrics['eigenvector'].shape == (n,)

    # In a star graph, center node (0) should have highest degree and betweenness
    assert metrics['degree'][0] > metrics['degree'][1]
    assert metrics['betweenness'][0] > metrics['betweenness'][1]
    assert metrics['eigenvector'][0] > metrics['eigenvector'][1]


def test_run_centrality_analysis_integration(temp_data_dir):
    """
    End-to-end test: create matrices, run analysis, verify CSV output.
    """
    connectivity_dir = temp_data_dir / "processed" / "connectivity"
    centrality_dir = temp_data_dir / "processed" / "centrality"

    # Create 3 test subjects
    subject_ids = ["sub-001", "sub-002", "sub-003"]
    for sub_id in subject_ids:
        matrix = create_test_connectivity_matrix(n_nodes=90, seed=hash(sub_id))
        np.save(connectivity_dir / f"{sub_id}_matrix.npy", matrix)

    # Run analysis
    output_file = run_centrality_analysis(
        subject_ids=subject_ids,
        data_dir=temp_data_dir,
        output_dir=centrality_dir
    )

    # Verify output file exists
    assert os.path.exists(output_file)

    # Verify content
    df = pd.read_csv(output_file)

    # Check required columns
    assert 'subject_id' in df.columns
    # Check for at least one metric column (e.g., degree_node_0)
    assert any('degree_node' in col for col in df.columns)
    assert any('betweenness_node' in col for col in df.columns)
    assert any('eigenvector_node' in col for col in df.columns)

    # Check row count
    assert len(df) == len(subject_ids)

    # Check subject IDs match
    assert set(df['subject_id'].tolist()) == set(subject_ids)


def test_process_subject_missing_matrix(temp_data_dir):
    """Test handling of missing connectivity matrix."""
    result = process_subject("sub-missing", temp_data_dir)
    assert result is None