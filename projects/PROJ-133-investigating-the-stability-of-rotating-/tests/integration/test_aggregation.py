"""
Integration test for the full aggregation pipeline (T027).

This test verifies that the entire pipeline from raw simulation snapshots
to aggregated statistical results (Two-Way ANOVA) executes correctly.

It depends on:
- code/simulation/runner.py (to generate mock data if needed, or real data if present)
- code/analysis/pipeline.py (to process snapshots)
- code/statistics/aggregators.py (to aggregate and run ANOVA)

Since this is an integration test, it simulates a small batch run to ensure
the data flows correctly through all stages.
"""

import os
import sys
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from simulation.runner import run_single_simulation, GPEParameters
from analysis.pipeline import process_single_snapshot, aggregate_results
from statistics.aggregators import run_two_way_anova, calculate_aggregated_metrics
from utils.logger import configure_logging, get_logger
from utils.seed_manager import set_global_seed

# Configure logging for the test
configure_logging(level="INFO", log_file="tests/logs/test_aggregation.log")
logger = get_logger(__name__)

# Test configuration
TEST_OUTPUT_DIR = Path("data/processed/test_aggregation")
TEST_AGGREGATED_DIR = Path("data/aggregated/test_aggregation")
TEST_PARAMS = [
    {"omega": 0.5, "eps_dd": 0.5, "N": 10000, "grid_size": 32},  # Small grid for speed
    {"omega": 0.6, "eps_dd": 0.5, "N": 10000, "grid_size": 32},
    {"omega": 0.5, "eps_dd": 0.8, "N": 10000, "grid_size": 32},
]

def _ensure_test_dirs():
    """Create necessary test directories."""
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEST_AGGREGATED_DIR.mkdir(parents=True, exist_ok=True)
    Path("tests/logs").mkdir(parents=True, exist_ok=True)

def _generate_mock_snapshots():
    """
    Generate minimal mock simulation snapshots to test the pipeline.
    In a real CI environment, this would run the actual GPE solver for a few steps.
    For speed, we generate synthetic data that matches the expected schema.
    """
    logger.info("Generating mock simulation snapshots for integration test...")
    set_global_seed(42)
    
    for i, params in enumerate(TEST_PARAMS):
        omega = params["omega"]
        eps_dd = params["eps_dd"]
        N = params["N"]
        grid_size = params["grid_size"]
        
        # Create a simple density profile (Gaussian-like)
        x = np.linspace(-10, 10, grid_size)
        y = np.linspace(-10, 10, grid_size)
        X, Y = np.meshgrid(x, y)
        R2 = X**2 + Y**2
        density = np.exp(-R2 / 2.0) * N
        
        # Add some phase structure (vortices) based on parameters
        phase = np.zeros_like(density)
        if omega > 0.55:
            # Simulate a vortex at the center
            theta = np.arctan2(Y, X)
            phase = theta
        
        # Save as .npy files
        snap_dir = TEST_OUTPUT_DIR / f"run_{i:03d}"
        snap_dir.mkdir(parents=True, exist_ok=True)
        
        np.save(snap_dir / "density.npy", density)
        np.save(snap_dir / "phase.npy", phase)
        
        # Save metadata
        meta = {
            "omega": omega,
            "eps_dd": eps_dd,
            "N": N,
            "grid_size": grid_size,
            "status": "success"
        }
        np.save(snap_dir / "metadata.npy", meta)
        
        logger.info(f"Generated mock snapshot: {snap_dir}")

def _run_full_pipeline():
    """Execute the full aggregation pipeline."""
    logger.info("Starting full aggregation pipeline...")
    
    # 1. Process individual snapshots
    all_metrics = []
    for i in range(len(TEST_PARAMS)):
        snap_dir = TEST_OUTPUT_DIR / f"run_{i:03d}"
        params = TEST_PARAMS[i]
        
        # Run analysis on this snapshot
        metrics = process_single_snapshot(
            density_path=snap_dir / "density.npy",
            phase_path=snap_dir / "phase.npy",
            metadata=params
        )
        
        if metrics:
            all_metrics.append(metrics)
            logger.info(f"Processed snapshot {i}: Vortex Density = {metrics.vortex_density:.4f}")
        
        if not all_metrics:
            raise RuntimeError("Analysis pipeline failed to produce metrics.")
    
    # 2. Aggregate results
    if not all_metrics:
        raise RuntimeError("No metrics to aggregate.")
    
    aggregated = aggregate_results(all_metrics)
    logger.info(f"Aggregated {len(all_metrics)} runs into {len(aggregated)} groups.")
    
    # 3. Run Two-Way ANOVA
    # We need to structure data for ANOVA: factors are omega, eps_dd; response is stability metric
    # For this test, we use vortex_density as the response
    anova_results = run_two_way_anova(
        data=aggregated,
        factor1="omega",
        factor2="eps_dd",
        response="vortex_density"
    )
    
    logger.info(f"ANOVA Results: Omega p-value={anova_results['omega_p']:.4f}, "
                f"Eps_dd p-value={anova_results['eps_dd_p']:.4f}, "
                f"Interaction p-value={anova_results['interaction_p']:.4f}")
    
    # 4. Save aggregated results
    output_path = TEST_AGGREGATED_DIR / "aggregation_results.json"
    aggregated.to_json(output_path, orient="records", indent=2)
    logger.info(f"Saved aggregated results to {output_path}")
    
    return anova_results, aggregated

def test_full_aggregation_pipeline():
    """
    Integration test: test_full_aggregation_pipeline.
    
    Verifies that:
    1. Mock data can be generated (or real data loaded).
    2. The analysis pipeline processes snapshots without error.
    3. Aggregation groups results correctly.
    4. Two-Way ANOVA runs and produces p-values.
    5. Results are saved to the expected output file.
    """
    _ensure_test_dirs()
    
    # Generate mock data for the test
    _generate_mock_snapshots()
    
    # Run the pipeline
    anova_results, aggregated_df = _run_full_pipeline()
    
    # Assertions
    assert anova_results is not None, "ANOVA results should not be None"
    assert "omega_p" in anova_results, "ANOVA results missing omega_p"
    assert "eps_dd_p" in anova_results, "ANOVA results missing eps_dd_p"
    assert "interaction_p" in anova_results, "ANOVA results missing interaction_p"
    
    # Check that p-values are floats
    assert isinstance(anova_results["omega_p"], (int, float)), "omega_p must be numeric"
    assert isinstance(anova_results["eps_dd_p"], (int, float)), "eps_dd_p must be numeric"
    assert isinstance(anova_results["interaction_p"], (int, float)), "interaction_p must be numeric"
    
    # Check aggregated dataframe
    assert len(aggregated_df) > 0, "Aggregated dataframe should not be empty"
    assert "vortex_density" in aggregated_df.columns, "Aggregated dataframe missing vortex_density"
    
    # Check output file exists
    output_path = TEST_AGGREGATED_DIR / "aggregation_results.json"
    assert output_path.exists(), f"Output file {output_path} was not created"
    
    logger.info("Integration test PASSED: Full aggregation pipeline executed successfully.")

if __name__ == "__main__":
    test_full_aggregation_pipeline()
    print("Integration test completed successfully.")
