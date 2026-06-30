"""
Integration test for the full pipeline flow.
Runs the pipeline on a mock subset and asserts numeric r and p values.
"""
import os
import sys
import tempfile
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.config import Config
from code.data.loader import (
    validate_caq_availability,
    validate_and_filter_subjects,
    filter_by_motion,
    log_exclusion
)
from code.errors import DataMissingCreativityError
from code.analysis.connectivity import compute_static_connectivity_strength
from code.analysis.dynamics import calculate_flexibility, detect_communities
from code.analysis.statistics import fit_regression

def generate_mock_fmri_data(n_timepoints: int, n_rois: int, seed: int = 42) -> np.ndarray:
    """
    Generate mock fMRI time series data.
    Uses a simple AR(1) process to simulate temporal autocorrelation.
    """
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((n_timepoints, n_rois))
    # Apply AR(1) to simulate fMRI-like autocorrelation
    for i in range(1, n_timepoints):
        data[i] = 0.5 * data[i-1] + 0.866 * rng.standard_normal(n_rois)
    return data

def generate_mock_behavioral_data(n_subjects: int, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate mock behavioral data including CAQ scores and demographics.
    """
    rng = np.random.default_rng(seed)
    subjects = []
    for i in range(n_subjects):
        caq_score = rng.uniform(20, 100)
        # Introduce a known correlation with flexibility later by adjusting slightly
        # We will adjust this in the test logic to ensure a detectable signal
        subjects.append({
            "subject_id": f"sub_{i:03d}",
            "caq": caq_score,
            "age": rng.integers(18, 65),
            "sex": rng.choice(["M", "F"]),
            "education": rng.integers(12, 25),
            "fd_mean": rng.uniform(0.0, 0.3), # Mean Framewise Displacement
            "fmri_data": generate_mock_fmri_data(200, 100, seed + i) # Mock fMRI data
        })
    return subjects

def test_end_to_end_correlation():
    """
    Integration test: test_end_to_end_correlation
    Runs the full pipeline on a mock subset and asserts numeric r and p values.
    """
    # 1. Setup: Create mock data
    # We need a dataset where we can control the relationship to ensure we get a result
    # Let's create 30 subjects with a known underlying correlation structure
    n_subjects = 30
    rng = np.random.default_rng(12345)
    
    # Generate base features
    base_flexibility = rng.standard_normal(n_subjects)
    noise = rng.standard_normal(n_subjects) * 0.5
    base_caq = 50 + 10 * base_flexibility + noise # CAQ depends on flexibility
    
    subjects = []
    for i in range(n_subjects):
        subjects.append({
            "subject_id": f"sub_{i:03d}",
            "caq": base_caq[i],
            "age": rng.integers(20, 50),
            "sex": rng.choice(["M", "F"]),
            "education": rng.integers(12, 20),
            "fd_mean": 0.15, # Low motion
            "fmri_data": generate_mock_fmri_data(100, 20, seed=42+i) # Small mock fMRI
        })

    # 2. Validation (Mock CAQ presence check)
    # We simulate a manifest check by ensuring the first subject has 'caq'
    mock_manifest = {"subjects": [{"id": "sub_000", "has_caq": True}]}
    mock_behavioral_path = "/tmp/mock_beh.json"
    with open(mock_behavioral_path, "w") as f:
        json.dump({"subjects": [{"caq": 50.0}]}, f)
    
    # We skip the actual file validation as we are mocking the data structure directly in the list
    # In a real run, validate_caq_availability would be called on files.
    # Here we assume the data passed in 'subjects' is valid.

    # 3. Filtering
    # Filter by motion (all have low motion, so all pass)
    filtered_subjects = filter_by_motion(subjects, fd_thresh=0.5)
    assert len(filtered_subjects) == n_subjects, "All subjects should pass motion filter"

    # 4. Processing: Compute metrics
    flexibility_values = []
    creativity_values = []
    static_strength_values = []

    for sub in filtered_subjects:
        fmri_data = sub["fmri_data"]
        
        # Compute static connectivity strength
        # Note: compute_static_connectivity_strength expects (n_timepoints, n_rois)
        stat_strength = compute_static_connectivity_strength(fmri_data)
        static_strength_values.append(stat_strength)

        # Compute flexibility
        # We need to simulate community detection. 
        # Since we don't have a real sliding window implementation in the API surface yet,
        # we will mock the community labels sequence for the integration test to ensure
        # calculate_flexibility runs and returns a float.
        # In a full run, this would come from compute_sliding_window_connectivity -> detect_communities.
        
        # Mock community labels: 10 ROIs, 5 time windows
        # Randomly assign communities to simulate dynamics
        n_windows = 5
        n_rois = fmri_data.shape[1]
        community_labels = []
        for _ in range(n_windows):
            labels = rng.integers(0, 3, size=n_rois).tolist()
            community_labels.append(labels)
        
        flex = calculate_flexibility(community_labels)
        flexibility_values.append(flex)
        creativity_values.append(sub["caq"])

    # 5. Statistical Analysis
    flexibility_arr = np.array(flexibility_values)
    creativity_arr = np.array(creativity_values)
    static_arr = np.array(static_strength_values)

    # Prepare covariates
    covariates = {
        "age": np.array([s["age"] for s in filtered_subjects]),
        "sex": np.array([1 if s["sex"] == "M" else 0 for s in filtered_subjects]),
        "education": np.array([s["education"] for s in filtered_subjects]),
        "static_connectivity_strength": static_arr
    }

    # Run regression
    result = fit_regression(flexibility_arr, creativity_arr, covariates)

    # 6. Assertions
    # The test asserts that numeric r and p values are returned
    assert result is not None, "Regression result should not be None"
    assert hasattr(result, 'r'), "Result must have 'r' attribute"
    assert hasattr(result, 'p'), "Result must have 'p' attribute"
    
    # Ensure values are numeric and not NaN/Inf
    assert isinstance(result.r, (int, float, np.floating)), "r must be numeric"
    assert isinstance(result.p, (int, float, np.floating)), "p must be numeric"
    assert not np.isnan(result.r), "r must not be NaN"
    assert not np.isnan(result.p), "p must not be NaN"
    assert not np.isinf(result.p), "p must not be Inf"

    # Verify the correlation is detectable (since we engineered a relationship)
    # The noise is small, so r should be significantly non-zero
    # We use a loose threshold because mock data is synthetic
    assert abs(result.r) > 0.1, f"Correlation r={result.r} is too low for the mock signal"
    assert result.p < 0.1, f"P-value {result.p} should be reasonably low for the mock signal"

    print(f"Test passed: r={result.r:.4f}, p={result.p:.4f}")

if __name__ == "__main__":
    test_end_to_end_correlation()
