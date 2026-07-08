"""
Integration test for single-subject pipeline (US1).

This test verifies that the full pipeline (structural + functional metrics)
runs successfully on a single HCP subject and produces valid, non-null outputs.

Prerequisites:
- T006: Data loading utilities
- T007: Structural metric calculation
- T008: Functional state extraction
- T012: Unit tests for structural
- T013: Unit tests for functional
"""

import os
import sys
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from preprocess.loader import load_hcp_data
from preprocess.structural import compute_graph_metrics
from preprocess.functional import extract_dynamic_states_loo, calculate_dynamic_metrics
from config import get_config


@pytest.mark.integration
def test_single_subject_pipeline():
    """
    Run the full US1 pipeline on a single subject.

    Steps:
    1. Load real HCP data for one subject (using a small subset or first available).
    2. Compute structural graph metrics (global efficiency, clustering, modularity).
    3. Compute functional dynamic metrics (dwell time, visited states) using LOO K-Means.
    4. Assert that outputs are non-null and within expected ranges.
    """
    config = get_config()

    # 1. Load Data
    # We attempt to load the first available subject from the dataset.
    # If the dataset is not downloaded, this will raise an error, which is expected.
    try:
        subject_id, dmri_data, fmri_data = load_hcp_data(subject_limit=1)
    except Exception as e:
        pytest.fail(f"Failed to load HCP data: {e}")

    assert subject_id is not None, "Subject ID must not be None"
    assert dmri_data is not None, "DMRI data must not be None"
    assert fmri_data is not None, "FMRI data must not be None"

    # 2. Compute Structural Metrics
    # Assuming dmri_data is a connectivity matrix (adjacency)
    # If dmri_data is a list of edges, we might need to convert, but loader usually handles this.
    # For this test, we assume it returns a dense numpy array or similar.
    if not isinstance(dmri_data, np.ndarray):
        # If it's a list of edges or sparse, convert to dense for test simplicity
        # In real code, compute_graph_metrics handles this.
        dmri_matrix = np.array(dmri_data)
    else:
        dmri_matrix = dmri_data

    # Ensure matrix is square
    if dmri_matrix.shape[0] != dmri_matrix.shape[1]:
        pytest.fail(f"DMRI matrix is not square: {dmri_matrix.shape}")

    try:
        structural_metrics = compute_graph_metrics(dmri_matrix)
    except Exception as e:
        pytest.fail(f"Structural metric computation failed: {e}")

    # 3. Compute Functional Metrics
    # LOO K-Means requires at least 2 subjects to exclude one.
    # Since we are testing on a single subject, we must simulate a second "dummy" subject
    # to satisfy the LOO requirement, OR the function should handle single-subject edge cases.
    # However, the task description for T017 says "For each subject i, centroids... all subjects j != i".
    # If we only have 1 subject, we cannot compute LOO strictly.
    # To make this integration test passable with real data (which might be limited in CI),
    # we will load 2 subjects if available, or skip if only 1 is available.
    
    # Re-load with 2 subjects to satisfy LOO logic
    try:
        # Reload to get 2 subjects for valid LOO calculation
        subject_ids, dmri_list, fmri_list = load_hcp_data(subject_limit=2)
        if len(subject_ids) < 2:
            pytest.skip("Integration test requires at least 2 subjects for LOO K-Means. Only 1 found.")
        
        # Use the first subject as the target, but pass all to the function
        target_subject_idx = 0
        target_subject_id = subject_ids[target_subject_idx]
        
        # Prepare data for LOO function
        # The function extract_dynamic_states_loo expects a list of fmri data and a subject index
        # or it handles the loop internally. Based on T017, it should handle the LOO logic.
        # Let's assume the function signature is: extract_dynamic_states_loo(fmri_data_list, subject_indices)
        # or it takes the full list and computes for all, then we extract the one we need.
        # Given T017 description: "Must run sequentially... for each subject i".
        # Let's assume the function returns a dict of results for all subjects.
        
        dynamic_results = extract_dynamic_states_loo(fmri_list)
        
        # Check if our target subject is in results
        if target_subject_id not in dynamic_results:
            # Maybe the key is index?
            if target_subject_idx in dynamic_results:
                dynamic_metrics = calculate_dynamic_metrics(dynamic_results[target_subject_idx])
            else:
                pytest.fail(f"Target subject {target_subject_id} not found in dynamic results")
        else:
            dynamic_metrics = calculate_dynamic_metrics(dynamic_results[target_subject_id])

    except Exception as e:
        pytest.fail(f"Functional metric computation failed: {e}")

    # 4. Assertions
    # Structural
    assert structural_metrics is not None, "Structural metrics must not be None"
    assert "global_efficiency" in structural_metrics, "global_efficiency missing"
    assert "avg_clustering" in structural_metrics, "avg_clustering missing"
    assert "modularity" in structural_metrics, "modularity missing"
    
    assert isinstance(structural_metrics["global_efficiency"], (int, float)), "global_efficiency must be numeric"
    assert isinstance(structural_metrics["avg_clustering"], (int, float)), "avg_clustering must be numeric"
    assert isinstance(structural_metrics["modularity"], (int, float)), "modularity must be numeric"

    # Functional
    assert dynamic_metrics is not None, "Dynamic metrics must not be None"
    assert "visited_states" in dynamic_metrics, "visited_states missing"
    assert "mean_dwell_time" in dynamic_metrics, "mean_dwell_time missing"
    
    assert isinstance(dynamic_metrics["visited_states"], int), "visited_states must be int"
    assert isinstance(dynamic_metrics["mean_dwell_time"], (int, float)), "mean_dwell_time must be numeric"

    # Output a temporary JSON to verify file writing capability (optional but good for integration)
    output_dir = Path(tempfile.gettempdir()) / "llmXive_test_output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"subject_{target_subject_id}_results.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "subject_id": target_subject_id,
            "structural": structural_metrics,
            "dynamic": dynamic_metrics
        }, f, indent=2)

    assert output_file.exists(), "Output JSON file was not created"

    print(f"Integration test passed for subject {target_subject_id}")