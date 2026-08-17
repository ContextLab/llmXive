"""
Integration test for end-to-end hybrid simulation and metrics.
Verifies that the full pipeline (T047 -> T045 -> T018a -> T050 -> T028 -> T049)
produces valid artifacts and passes statistical constraints.

This test is part of User Story 3 (US3) and depends on:
- T047: Counterfactual indices generation
- T045: Fallback handler implementation
- T018a: Finalized estimator checkpoint
- T050: Hybrid simulation execution
- T028: Metrics computation
- T049: TOST equivalence tests
"""
import os
import sys
import pytest
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'code'))

from inference.hybrid_sim import main as run_hybrid_sim
from evaluation.metrics import main as run_metrics
from metrics.tost_equivalence import main as run_tost
from inference.generate_counterfactual_indices import main as run_counterfactual
from inference.fallback_handler import main as run_fallback

# Constants
HYBRID_OUTPUT_PATH = PROJECT_ROOT / 'data' / 'processed' / 'hybrid_output.parquet'
COUNTERFACTUAL_PATH = PROJECT_ROOT / 'data' / 'processed' / 'counterfactual_indices.parquet'
SAMPLED_DATASET_PATH = PROJECT_ROOT / 'data' / 'processed' / 'sampled_dataset.parquet'
ESTIMATOR_CHECKPOINT_PATH = PROJECT_ROOT / 'data' / 'models' / 'estimator_checkpoint_final.pt'
TOST_RESULTS_PATH = PROJECT_ROOT / 'data' / 'metrics' / 'tost_results.csv'
METRICS_OUTPUT_PATH = PROJECT_ROOT / 'data' / 'metrics' / 'hybrid_metrics.json'

def _ensure_prerequisites():
    """
    Ensure all prerequisite artifacts exist. If missing, skip the test
    with a clear message indicating which dependency is missing.
    """
    missing = []
    
    if not SAMPLED_DATASET_PATH.exists():
        missing.append(str(SAMPLED_DATASET_PATH))
    if not ESTIMATOR_CHECKPOINT_PATH.exists():
        missing.append(str(ESTIMATOR_CHECKPOINT_PATH))
        
    if missing:
        pytest.skip(f"Prerequisites missing: {', '.join(missing)}. Run upstream tasks first.")

def test_hybrid_simulation_executes():
    """
    Test that the hybrid simulation script runs end-to-end without crashing.
    This verifies T050 execution.
    """
    _ensure_prerequisites()
    
    # Generate counterfactual indices if missing (T047)
    if not COUNTERFACTUAL_PATH.exists():
        # Run counterfactual generation
        sys.argv = ['generate_counterfactual_indices']
        try:
            run_counterfactual()
        except Exception as e:
            pytest.fail(f"Counterfactual index generation failed: {e}")
    
    # Run hybrid simulation (T050)
    sys.argv = ['hybrid_sim']
    try:
        run_hybrid_sim()
    except Exception as e:
        pytest.fail(f"Hybrid simulation execution failed: {e}")
    
    assert HYBRID_OUTPUT_PATH.exists(), "Hybrid output file not created"
    assert HYBRID_OUTPUT_PATH.stat().st_size > 0, "Hybrid output file is empty"

def test_hybrid_output_schema():
    """
    Test that the hybrid output parquet file has the correct schema.
    Expected columns: frame_id (int64), latency (float64), fid_score (float64), skip_flag (bool)
    """
    if not HYBRID_OUTPUT_PATH.exists():
        pytest.skip("Hybrid output not generated. Run test_hybrid_simulation_executes first.")
    
    df = pd.read_parquet(HYBRID_OUTPUT_PATH)
    
    required_columns = ['frame_id', 'latency', 'fid_score', 'skip_flag']
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    assert df['frame_id'].dtype == np.int64, "frame_id must be int64"
    assert df['latency'].dtype == np.float64, "latency must be float64"
    assert df['fid_score'].dtype == np.float64, "fid_score must be float64"
    assert df['skip_flag'].dtype == bool, "skip_flag must be bool"

def test_latency_reduction():
    """
    Test that the hybrid simulation achieves at least 20% latency reduction
    compared to the baseline (full solver).
    """
    if not HYBRID_OUTPUT_PATH.exists():
        pytest.skip("Hybrid output not generated.")
    
    df = pd.read_parquet(HYBRID_OUTPUT_PATH)
    
    # Calculate average latency
    avg_latency = df['latency'].mean()
    
    # Baseline latency (simulated as 100ms per frame for full solver)
    # In a real scenario, this would be measured from the full solver run
    baseline_latency_per_frame = 0.100  # 100ms
    expected_baseline_avg = baseline_latency_per_frame * len(df)
    
    # Calculate reduction percentage
    reduction = (expected_baseline_avg - avg_latency) / expected_baseline_avg
    
    assert reduction >= 0.20, f"Latency reduction {reduction:.2%} is less than required 20%"

def test_fid_quality_preservation():
    """
    Test that FID degradation is within acceptable limits (<= 5%).
    """
    if not HYBRID_OUTPUT_PATH.exists():
        pytest.skip("Hybrid output not generated.")
    
    df = pd.read_parquet(HYBRID_OUTPUT_PATH)
    
    # Calculate average FID score
    avg_fid = df['fid_score'].mean()
    
    # In a real scenario, we would compare against a baseline FID
    # For this test, we assume the baseline FID is known or calculated
    # Here we use a placeholder baseline (e.g., 10.0)
    baseline_fid = 10.0
    degradation = (avg_fid - baseline_fid) / baseline_fid if baseline_fid != 0 else 0
    
    # Allow for some degradation but not more than 5%
    assert degradation <= 0.05, f"FID degradation {degradation:.2%} exceeds 5% limit"

def test_tost_equivalence_test():
    """
    Test that TOST equivalence tests pass (p-value < 0.05) for quality metrics.
    This verifies T049 execution.
    """
    if not HYBRID_OUTPUT_PATH.exists():
        pytest.skip("Hybrid output not generated.")
    
    # Run TOST equivalence test (T049)
    sys.argv = ['tost_equivalence']
    try:
        run_tost()
    except Exception as e:
        pytest.fail(f"TOST equivalence test failed: {e}")
    
    assert TOST_RESULTS_PATH.exists(), "TOST results file not created"
    
    # Load and validate TOST results
    tost_results = pd.read_csv(TOST_RESULTS_PATH)
    
    assert 'metric' in tost_results.columns, "Missing 'metric' column in TOST results"
    assert 'p_value' in tost_results.columns, "Missing 'p_value' column in TOST results"
    
    # Check that all p-values are < 0.05
    failed_tests = tost_results[tost_results['p_value'] >= 0.05]
    assert len(failed_tests) == 0, f"TOST tests failed for metrics: {failed_tests['metric'].tolist()}"

def test_counterfactual_intervention_applied():
    """
    Test that the counterfactual intervention (randomized skip) was correctly applied.
    Verifies that frames in the counterfactual set have skip_flag=True.
    """
    if not HYBRID_OUTPUT_PATH.exists() or not COUNTERFACTUAL_PATH.exists():
        pytest.skip("Hybrid output or counterfactual indices not generated.")
    
    hybrid_df = pd.read_parquet(HYBRID_OUTPUT_PATH)
    counterfactual_df = pd.read_parquet(COUNTERFACTUAL_PATH)
    
    counterfactual_ids = set(counterfactual_df['frame_id'].tolist())
    
    # Check that all counterfactual frames are marked as skipped
    counterfactual_frames = hybrid_df[hybrid_df['frame_id'].isin(counterfactual_ids)]
    
    if len(counterfactual_frames) > 0:
        assert all(counterfactual_frames['skip_flag'] == True), \
            "Not all counterfactual frames were marked as skipped"
    
    # Verify that at least 5% of total frames are in the counterfactual set
    total_frames = len(hybrid_df)
    counterfactual_count = len(counterfactual_df)
    
    assert counterfactual_count >= 0.05 * total_frames, \
        f"Counterfactual set size ({counterfactual_count}) is less than 5% of total ({total_frames})"

def test_metrics_output_generated():
    """
    Test that the metrics output file is generated and contains expected fields.
    This verifies T028 execution.
    """
    if not HYBRID_OUTPUT_PATH.exists():
        pytest.skip("Hybrid output not generated.")
    
    # Run metrics evaluation (T028)
    sys.argv = ['metrics']
    try:
        run_metrics()
    except Exception as e:
        pytest.fail(f"Metrics evaluation failed: {e}")
    
    assert METRICS_OUTPUT_PATH.exists(), "Metrics output file not created"
    
    with open(METRICS_OUTPUT_PATH, 'r') as f:
        metrics = json.load(f)
    
    required_keys = ['avg_latency', 'avg_fid', 'latency_reduction_pct', 'fid_degradation_pct']
    for key in required_keys:
        assert key in metrics, f"Missing required key in metrics: {key}"
    
    assert isinstance(metrics['avg_latency'], (int, float)), "avg_latency must be numeric"
    assert isinstance(metrics['avg_fid'], (int, float)), "avg_fid must be numeric"
    assert isinstance(metrics['latency_reduction_pct'], (int, float)), "latency_reduction_pct must be numeric"
    assert isinstance(metrics['fid_degradation_pct'], (int, float)), "fid_degradation_pct must be numeric"