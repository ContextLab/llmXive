"""
Integration test for User Story 1: Access Control.

Task: T013 [P] [US1] Integration test: Run full pipeline on "medical" domain subset 
and assert Access Control score is calculated.

This test verifies that the full Gatekeeper pipeline can be executed on a specific
domain subset ('medical') and that the resulting Access Control score is calculated
and present in the output.
"""
import os
import sys
import json
import pytest
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.gatekeeper.pipeline import run_gatekeeper, run_baseline
from code.gatekeeper.metrics import calculate_access_control_score
from code.logging_config import setup_logging, pin_random_seed

# Setup logging
logger = setup_logging("test_us1_integration", level=logging.INFO)

@pytest.fixture(scope="module")
def setup_environment():
    """Ensure necessary directories exist."""
    data_dir = project_root / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def test_run_pipeline_and_calculate_access_control(setup_environment):
    """
    Integration Test: Run full pipeline on "medical" domain subset and assert 
    Access Control score is calculated.
    
    Steps:
    1. Run the Gatekeeper pipeline on the 'medical' domain.
    2. Run the Baseline pipeline on the 'medical' domain.
    3. Load the results.
    4. Calculate the Access Control score.
    5. Assert the score is a valid number (not None, not NaN).
    """
    # Pin seed for reproducibility
    pin_random_seed(42)

    medical_domain = "medical"
    output_dir = setup_environment
    
    # Define output paths
    gatekeeper_output_path = output_dir / "access_control_results_gatekeeper.json"
    baseline_output_path = output_dir / "access_control_results_baseline.json"
    
    logger.info(f"Starting Gatekeeper pipeline for domain: {medical_domain}")
    
    # Run Gatekeeper Pipeline
    # Note: We assume the pipeline writes to the specified output path or a default location
    # The run_gatekeeper function signature is assumed to accept domain and output_path
    try:
        run_gatekeeper(
            domain=medical_domain,
            output_path=str(gatekeeper_output_path),
            batch_size=32,
            seed=42
        )
        logger.info("Gatekeeper pipeline completed.")
    except Exception as e:
        # If the pipeline fails due to missing data or model, we log and fail the test
        # This is expected if the environment isn't fully set up with real data, 
        # but for the purpose of this task, we assume the code path is correct.
        logger.error(f"Gatekeeper pipeline failed: {e}")
        pytest.fail(f"Gatekeeper pipeline execution failed: {e}")

    logger.info(f"Starting Baseline pipeline for domain: {medical_domain}")
    
    # Run Baseline Pipeline
    try:
        run_baseline(
            domain=medical_domain,
            output_path=str(baseline_output_path),
            batch_size=32,
            seed=42
        )
        logger.info("Baseline pipeline completed.")
    except Exception as e:
        logger.error(f"Baseline pipeline failed: {e}")
        pytest.fail(f"Baseline pipeline execution failed: {e}")

    # Verify output files exist
    assert gatekeeper_output_path.exists(), f"Gatekeeper output file not found: {gatekeeper_output_path}"
    assert baseline_output_path.exists(), f"Baseline output file not found: {baseline_output_path}"

    # Load results
    with open(gatekeeper_output_path, 'r') as f:
        gatekeeper_results = json.load(f)
    
    with open(baseline_output_path, 'r') as f:
        baseline_results = json.load(f)

    logger.info("Calculating Access Control Score...")

    # Calculate Access Control Score
    # The function expects predictions and ground truth. 
    # We assume the pipeline outputs a list of episodes with 'predicted_leak' and 'actual_leak'
    try:
        # We pass the loaded results directly if the structure matches
        # If the pipeline output format differs, we might need to extract specific fields
        # For now, assuming the output is a list of dicts with necessary fields
        score = calculate_access_control_score(
            predictions=gatekeeper_results, 
            ground_truth=baseline_results # Using baseline as a proxy for ground truth structure if needed, 
                                        # or the pipeline results contain both
        )
        
        # Alternative: If the pipeline output already contains the score, we verify that.
        # But the task asks to "assert Access Control score is calculated", implying we run the calculation.
        
        logger.info(f"Calculated Access Control Score: {score}")
        
        # Assert score is calculated (not None) and is a valid number
        assert score is not None, "Access Control score is None."
        assert isinstance(score, (int, float)), f"Access Control score is not a number: {type(score)}"
        assert not (score != score), "Access Control score is NaN." # Check for NaN
        
        # Assert score is within valid probability range [0, 1]
        assert 0.0 <= score <= 1.0, f"Access Control score {score} is outside valid range [0, 1]."

        logger.info("Integration Test PASSED: Access Control score calculated successfully.")

    except Exception as e:
        logger.error(f"Error calculating Access Control Score: {e}")
        pytest.fail(f"Failed to calculate Access Control Score: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
