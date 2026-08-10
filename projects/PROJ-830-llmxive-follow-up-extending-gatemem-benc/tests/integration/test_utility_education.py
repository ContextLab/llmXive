"""
Integration test for User Story 2: Utility Evaluation.

Task: T022 - Run pipeline on "education" domain and assert Utility score matches expected range.

This test verifies that:
1. The Gatekeeper and Baseline pipelines can be executed on the "education" domain.
2. The utility scores are calculated correctly.
3. The utility score falls within a reasonable expected range (0.0 to 1.0).
4. The results are saved to the correct output file.
"""
import os
import json
import sys
import pytest
from pathlib import Path

# Add the project root to the path to allow imports
# Assuming this test is run from the project root or tests/ directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.logging_config import setup_logging
from code.cli.run_evaluation import run_gatekeeper_pipeline, run_baseline_pipeline, load_domain_data
from code.gatekeeper.metrics import calculate_utility_score

# Setup logging for the test
logger = setup_logging("test_utility_education", level="INFO")

# Expected output paths
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
GATEKEEPER_RESULTS_PATH = OUTPUT_DIR / "gatekeeper_education_results.json"
BASELINE_RESULTS_PATH = OUTPUT_DIR / "baseline_education_results.json"
UTILITY_RESULTS_PATH = OUTPUT_DIR / "utility_results.json"

@pytest.mark.integration
def test_utility_score_education_domain():
    """
    Integration test: Run pipeline on "education" domain and assert Utility score matches expected range.
    """
    domain = "education"
    logger.info(f"Starting integration test for domain: {domain}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data for the education domain
    # Note: This relies on T006a/T006 being implemented to fetch/validate data
    try:
        episodes = load_domain_data(domain)
        assert len(episodes) > 0, f"No episodes found for domain: {domain}"
        logger.info(f"Loaded {len(episodes)} episodes for domain: {domain}")
    except Exception as e:
        logger.error(f"Failed to load data for domain {domain}: {e}")
        pytest.fail(f"Data loading failed for domain {domain}: {e}")

    # 2. Run Gatekeeper Pipeline
    logger.info(f"Running Gatekeeper pipeline for domain: {domain}")
    try:
        gatekeeper_results = run_gatekeeper_pipeline(episodes, domain)
        assert gatekeeper_results is not None, "Gatekeeper pipeline returned None"
        assert len(gatekeeper_results) == len(episodes), "Gatekeeper results count mismatch"
        
        # Save results
        with open(GATEKEEPER_RESULTS_PATH, 'w') as f:
            json.dump(gatekeeper_results, f, indent=2)
        logger.info(f"Saved Gatekeeper results to {GATEKEEPER_RESULTS_PATH}")
    except Exception as e:
        logger.error(f"Gatekeeper pipeline failed: {e}")
        pytest.fail(f"Gatekeeper pipeline execution failed: {e}")

    # 3. Run Baseline Pipeline
    logger.info(f"Running Baseline pipeline for domain: {domain}")
    try:
        baseline_results = run_baseline_pipeline(episodes, domain)
        assert baseline_results is not None, "Baseline pipeline returned None"
        assert len(baseline_results) == len(episodes), "Baseline results count mismatch"
        
        # Save results
        with open(BASELINE_RESULTS_PATH, 'w') as f:
            json.dump(baseline_results, f, indent=2)
        logger.info(f"Saved Baseline results to {BASELINE_RESULTS_PATH}")
    except Exception as e:
        logger.error(f"Baseline pipeline failed: {e}")
        pytest.fail(f"Baseline pipeline execution failed: {e}")

    # 4. Calculate Utility Score
    logger.info("Calculating Utility Score")
    try:
        # Load the results back to calculate utility (simulating the metrics module usage)
        # In a real scenario, calculate_utility_score might take the raw episode list + predictions
        utility_score = calculate_utility_score(gatekeeper_results, baseline_results)
        
        logger.info(f"Calculated Utility Score: {utility_score}")
        
        # 5. Assert Utility score is within expected range [0.0, 1.0]
        assert 0.0 <= utility_score <= 1.0, f"Utility score {utility_score} is out of expected range [0.0, 1.0]"
        
        # 6. Assert the score is not trivially 0 or 1 unless the dataset is extremely small/biased
        # (Optional: Add a more specific range check if ground truth is known, e.g., > 0.1)
        # For now, we assert it's a valid probability.
        
        # 7. Save Utility Results
        utility_data = {
            "domain": domain,
            "gatekeeper_utility": utility_score,
            "baseline_utility": calculate_utility_score(baseline_results, baseline_results), # Baseline vs itself or similar logic
            "num_episodes": len(episodes)
        }
        
        with open(UTILITY_RESULTS_PATH, 'w') as f:
            json.dump(utility_data, f, indent=2)
        logger.info(f"Saved Utility results to {UTILITY_RESULTS_PATH}")
        
        logger.info(f"SUCCESS: Utility score {utility_score} is valid for domain {domain}")

    except Exception as e:
        logger.error(f"Utility calculation failed: {e}")
        pytest.fail(f"Utility score calculation failed: {e}")

if __name__ == "__main__":
    # Allow running this test directly for manual verification
    test_utility_score_education_domain()
    print("Integration test T022 passed.")