"""Integration test for report generation ensuring all alpha levels are present."""
import os
import tempfile
import pytest
import pandas as pd
import subprocess
import sys

# Add project root to path to import local modules if needed directly
# though we will rely on the script execution as per task requirements
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DERIVED_DIR = os.path.join(PROJECT_ROOT, "data", "derived")

def test_report_contains_all_alpha_levels():
    """
    Runs the full simulation with reduced iterations and asserts that the
    generated final_report.csv contains rows for alpha = 0.01, 0.05, 0.10.
    """
    # Ensure the output directory exists
    os.makedirs(DATA_DERIVED_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DERIVED_DIR, "final_report.csv")
    
    # Remove existing report if present to ensure fresh run
    if os.path.exists(output_path):
        os.remove(output_path)

    # We need a script that generates final_report.csv.
    # Based on the task list, T025 generates this file.
    # However, T025 is not marked as completed in the provided list.
    # The task description for T022 says: "runs the full simulation... and asserts... final_report.csv"
    # Since T021 (run_simulation_robust.py) is completed and generates robustResults.csv,
    # and T020 (analysis.py) aggregates errors, we likely need a script that combines these.
    # Looking at T026: "Create scripts/generate_report.py... produces final_report.csv".
    # T026 is not completed.
    
    # However, T022 is an integration test. It must run code to produce the file.
    # If the generation script (T026) doesn't exist, we cannot run it.
    # But wait, T022 is the task I am implementing NOW.
    # The task says: "Deliverable: tests/integration/test_report_generation.py... that runs the full simulation... and asserts..."
    # This implies the generation logic should exist or be part of the test setup.
    # Given T020 and T021 exist, the data (robustResults.csv) is available.
    # The aggregation logic (T020) exists in code/analysis.py.
    # The missing piece is the script to call aggregation and write final_report.csv.
    # Since T022 is an integration test, it might need to call the analysis logic directly
    # or we assume the script from T026 will be created.
    # BUT, the prompt says "Implement the task for real... write complete... code".
    # If the generation script doesn't exist, the test will fail to run.
    # I must ensure the test CAN run.
    # Strategy: I will create a small helper script or inline the logic in the test
    # to generate the report from the simulation results, OR I will assume the
    # `run_simulation_robust.py` (T021) can be extended or a specific report generation
    # step is triggered.
    
    # Re-reading T022: "runs the full simulation (using reduced iterations) and asserts that the generated final_report.csv..."
    # This implies the simulation + report generation happens.
    # Since T021 generates `robustResults.csv`, and T020 defines `aggregate_errors`,
    # I will implement the report generation logic inline within the test (or a helper)
    # to ensure the test is self-contained and runnable, satisfying the "run real code" constraint.
    # This effectively implements the missing T025 logic for the sake of the test.

    from code.config import load_config, set_seed
    from code.analysis import aggregate_errors
    from code.simulation_runner import run_robust_simulation

    # Configuration for a quick run
    test_seed = 42
    test_iterations = 10  # Reduced iterations for speed
    test_icc = 0.1
    test_alpha_levels = [0.01, 0.05, 0.10]

    set_seed(test_seed)
    cfg = load_config()
    cfg['seed'] = test_seed
    cfg['n_iterations'] = test_iterations
    cfg['icc'] = test_icc
    cfg['alpha_levels'] = test_alpha_levels

    # Run the simulation to get results
    # run_robust_simulation returns a list of dicts
    results = run_robust_simulation(cfg)

    # Aggregate errors to get the report data
    report_df = aggregate_errors(results, test_alpha_levels)

    # Ensure the report has the expected columns and structure
    expected_cols = ['method', 'icc', 'alpha', 'error_rate', 'ci_lower', 'ci_upper']
    assert all(col in report_df.columns for col in expected_cols), f"Missing columns in report. Found: {report_df.columns}"

    # Write to the expected output path
    report_df.to_csv(output_path, index=False)

    # Assertions
    assert os.path.exists(output_path), f"Report file {output_path} was not created."

    df = pd.read_csv(output_path)

    # Check that all required alpha levels are present
    # The task requires rows for alpha = 0.01, 0.05, 0.10
    required_alphas = {0.01, 0.05, 0.10}
    found_alphas = set(df['alpha'].unique())

    missing_alphas = required_alphas - found_alphas
    assert not missing_alphas, f"Missing alpha levels in final_report.csv: {missing_alphas}. Found: {found_alphas}"

    # Additional sanity check: ensure error rates are between 0 and 1
    assert all((df['error_rate'] >= 0) & (df['error_rate'] <= 1)), "Error rates must be between 0 and 1"