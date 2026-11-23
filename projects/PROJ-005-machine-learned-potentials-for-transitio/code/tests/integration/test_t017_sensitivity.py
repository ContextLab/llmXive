import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.data.sensitivity_analysis import (
    calculate_graph_metrics_for_cutoff,
    run_sensitivity_analysis,
    select_optimal_cutoff,
    run_cutoff_selection_and_graph_generation
)
from src.utils.config import load_config, get_project_root

@pytest.fixture
def sample_data_dir(tmp_path):
    """Create a temporary directory with sample data for testing."""
    data_dir = tmp_path / "code"
    (data_dir / "data" / "processed").mkdir(parents=True)
    (data_dir / "data" / "results").mkdir(parents=True)
    
    # Create a mock intermediate graphs file
    # Simulate a few transition states with positions
    sample_positions = [
        np.array([[0.0, 0.0, 0.0], [1.5, 0.0, 0.0], [0.0, 1.5, 0.0]]), # 3 atoms
        np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]) # 4 atoms
    ]
    
    df = pd.DataFrame({
        "sample_id": ["TS1", "TS2"],
        "positions": sample_positions,
        "energy_dft": [10.0, 12.0],
        "barrier_height": [5.0, 6.0],
        "metal_center": ["Pd", "Ni"],
        "ligand_class": ["Group 13", "Conventional"]
    })
    
    output_path = data_dir / "data" / "processed" / "graphs_intermediate.parquet"
    df.to_parquet(output_path)
    
    return data_dir

def test_calculate_graph_metrics_for_cutoff(sample_data_dir):
    """Test metric calculation for a specific cutoff."""
    df = pd.read_parquet(sample_data_dir / "data" / "processed" / "graphs_intermediate.parquet")
    positions = df['positions'].values[0] # Take first sample
    
    metrics = calculate_graph_metrics_for_cutoff(df.iloc[[0]], 2.0, None, positions)
    
    assert metrics['cutoff'] == 2.0
    assert metrics['samples_processed'] == 1
    assert 'total_edges' in metrics
    assert 'avg_degree' in metrics
    assert 'graph_density' in metrics
    assert metrics['avg_edge_feature_cv'] >= 0.0

def test_select_optimal_cutoff():
    """Test optimal cutoff selection logic."""
    results = [
        {"cutoff": 2.5, "avg_edge_feature_cv": 0.5},
        {"cutoff": 3.0, "avg_edge_feature_cv": 0.3},
        {"cutoff": 3.5, "avg_edge_feature_cv": 0.4}
    ]
    
    import logging
    logger = logging.getLogger(__name__)
    
    best_cutoff, justification = select_optimal_cutoff(results, logger)
    
    assert best_cutoff == 3.0
    assert "3.0" in justification

def test_run_cutoff_selection_and_graph_generation(sample_data_dir):
    """Integration test for the full T017 workflow."""
    config = load_config()
    
    # Run the main function
    run_cutoff_selection_and_graph_generation(sample_data_dir, config)
    
    # Verify outputs
    raw_output = sample_data_dir / "data" / "results" / "cutoff_sensitivity_raw.json"
    summary_output = sample_data_dir / "data" / "results" / "cutoff_sensitivity.json"
    graphs_output = sample_data_dir / "data" / "processed" / "graphs.parquet"
    
    assert raw_output.exists(), "Raw sensitivity results file not created."
    assert summary_output.exists(), "Sensitivity summary file not created."
    assert graphs_output.exists(), "Final graphs parquet file not created."
    
    # Verify content of raw results
    with open(raw_output, 'r') as f:
        raw_data = json.load(f)
    assert len(raw_data) > 0, "Raw results are empty."
    assert 'cutoff' in raw_data[0], "Missing cutoff in raw results."
    
    # Verify content of summary
    with open(summary_output, 'r') as f:
        summary_data = json.load(f)
    assert any('optimal_cutoff' in item for item in summary_data), "Missing optimal cutoff in summary."
    
    # Verify graphs parquet
    final_df = pd.read_parquet(graphs_output)
    assert 'is_outlier' in final_df.columns, "Missing is_outlier column in final graphs."
    assert 'coordination_number' in final_df.columns, "Missing coordination_number column in final graphs."
    assert len(final_df) > 0, "Final graphs dataframe is empty."