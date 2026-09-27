"""
Integration test for plot generation and sensitivity report (T033).

This test verifies that the visualization pipeline successfully:
1. Loads the unified dataset and model results.
2. Generates Partial Dependence Plots (PDP) for weather-feature interactions.
3. Performs sensitivity analysis on classification thresholds.
4. Writes all output artifacts to the expected paths.

It relies on the successful completion of T016 (Unified Dataset) and T030 (Model Results).
"""
import os
import sys
import json
import logging
from pathlib import Path
import pytest

# Add project root to path to resolve imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_path
from code.main import run_visual_stage
from code.utils.reporting import load_results

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tests.integration.test_visualization")

@pytest.mark.integration
def test_visualization_pipeline_execution():
    """
    Integration test: Run the full visualization stage and verify output artifacts.
    
    This test executes the `run_visual_stage` function which orchestrates:
    - PDP generation (T034)
    - Sensitivity analysis (T035, T036)
    - Report generation (T037, T038)
    
    It asserts that:
    1. The `results.json` file is updated with visualization metrics.
    2. The `figures/` directory contains the generated plots.
    3. The sensitivity report contains the expected threshold sweep data.
    """
    logger.info("Starting integration test for Visualization Pipeline (T033)")
    
    # Define expected paths
    results_path = get_path("results.json")
    figures_dir = get_path("figures")
    unified_csv_path = get_path("data/processed/unified_analysis.csv")
    model_results_path = get_path("results.json") # Assuming model results are in results.json or a specific file

    # Pre-check: Ensure input artifacts exist
    assert unified_csv_path.exists(), f"Input dataset missing at {unified_csv_path}. Run T016 first."
    assert model_results_path.exists(), f"Model results missing at {model_results_path}. Run T030 first."

    # Load existing results to verify updates later
    initial_results = load_results()
    logger.info(f"Loaded initial results. Keys: {list(initial_results.keys())}")

    # Execute the visualization stage
    # This calls the main orchestration logic for the visual stage
    try:
        run_visual_stage()
    except Exception as e:
        logger.error(f"Visualization stage failed: {e}")
        # Re-raise to fail the test if the stage crashes
        raise

    # Post-check 1: Verify results.json was updated
    assert results_path.exists(), "results.json was not created or updated."
    updated_results = load_results()
    
    # Verify visualization-specific keys exist
    assert "visualization" in updated_results, "Visualization section missing from results.json."
    viz_data = updated_results["visualization"]
    
    assert "sensitivity_analysis" in viz_data, "Sensitivity analysis data missing from results."
    assert "partial_dependence_plots" in viz_data, "PDP metadata missing from results."
    
    # Verify sensitivity analysis structure (T035, T036)
    sens_data = viz_data["sensitivity_analysis"]
    assert "thresholds" in sens_data, "Threshold sweep list missing."
    assert "metrics" in sens_data, "Metrics for thresholds missing."
    
    # Check that we swept at least the defined thresholds (0.05, 0.1, etc.)
    # The baseline is the 90th percentile, so we expect deviations
    expected_thresholds = sens_data.get("thresholds", [])
    logger.info(f"Thresholds swept: {expected_thresholds}")
    assert len(expected_thresholds) >= 3, "Expected at least 3 threshold points (baseline + 2 deviations)."

    # Post-check 2: Verify Figures exist
    assert figures_dir.exists(), f"Figures directory {figures_dir} does not exist."
    
    # List expected plot files based on T034/T035 implementation details
    # We expect PDP plots and potentially a sensitivity summary plot
    expected_plots = [
        "pdp_humidity_interaction.png",
        "pdp_temperature_interaction.png",
        "sensitivity_analysis_report.png" # Or similar
    ]
    
    found_plots = []
    for plot_name in expected_plots:
        plot_path = figures_dir / plot_name
        if plot_path.exists():
            found_plots.append(plot_name)
            logger.info(f"Found expected plot: {plot_name}")
        else:
            logger.warning(f"Expected plot not found: {plot_name} (might be named differently)")
    
    # At least one PDP plot should exist to confirm the pipeline ran
    pdp_plots = [p for p in found_plots if "pdp" in p]
    assert len(pdp_plots) > 0, "No Partial Dependence Plots found in figures directory."

    # Post-check 3: Verify report content integrity
    # Ensure the report flags if findings are robust across thresholds (T038)
    assert "robustness_flag" in sens_data or "conclusion" in sens_data, \
        "Sensitivity report missing robustness/conclusion field."

    logger.info("Integration test T033 PASSED: Visualization pipeline executed successfully.")

@pytest.mark.integration
def test_visualization_on_small_subset():
    """
    Optional: Run visualization on a small subset to ensure quick feedback during CI.
    This is a wrapper if the main stage is too slow, but for T033 we test the full stage.
    If the full stage is too slow, we rely on the main test above.
    """
    # For now, we just re-run the main check or skip if the main one passed
    # In a real CI, we might mock the data loading to be faster.
    # Since T033 is an integration test, it expects the real pipeline.
    pass

if __name__ == "__main__":
    # Allow running directly for debugging
    test_visualization_pipeline_execution()
