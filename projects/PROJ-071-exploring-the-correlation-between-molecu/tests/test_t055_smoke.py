"""
Test for T055: Full Pipeline Smoke Test.
Executes the pipeline end-to-end and verifies the existence and non-empty status of required artifacts.
"""
import os
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Project root relative to test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

REQUIRED_ARTIFACTS = [
    "data/processed/merged_drugs.csv",
    "data/processed/analysis_results.json",
    "results_report.md",
    "reproducibility_log.json",
]

def test_pipeline_execution():
    """
    Executes code/run_pipeline.py and verifies that all required output files
    are created and are non-empty.
    """
    pipeline_script = CODE_DIR / "run_pipeline.py"
    
    # Ensure the script exists
    assert pipeline_script.exists(), f"Pipeline script not found at {pipeline_script}"

    # Run the pipeline
    # We run it in the project root to ensure relative paths work correctly
    result = subprocess.run(
        [sys.executable, str(pipeline_script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    # Log output for debugging if it fails
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    
    # The test passes if the script runs successfully (returncode 0)
    # OR if it fails specifically due to Data Availability Gate (which is a valid outcome for the smoke test
    # if the real data is insufficient, though we expect success with the real dataset).
    # However, the task definition says: "Success Criteria: ... are all created and non-empty."
    # If the gate fails, some files (like analysis_results) might be skipped or contain 'Skipped' status.
    # Per T052, if the gate fails, the analysis results should reflect that, but the report must exist.
    # We will assert that the script ran and the files exist.
    
    # Check if any critical error occurred that prevented file creation entirely
    # (e.g., import errors, missing dependencies).
    if result.returncode != 0:
        # If it failed, check if it's a known data insufficiency exit (handled gracefully)
        # or a hard crash. For a smoke test, we primarily care that the code runs.
        # But strictly, T055 expects the files to be created.
        # If the gate failed, T034 generates data_insufficiency_report.md, not results_report.md.
        # The task description lists 'results_report.md' as a success criteria.
        # We will assume the real data is sufficient for this smoke test to pass the specific criteria.
        # If the gate fails, this test technically fails the specific criteria of T055 as written,
        # but the pipeline logic is correct.
        # Given the constraint "Real data only", if the real data is insufficient, we cannot fake it.
        # We proceed to check file existence.
        pass

    # Verify artifacts exist and are non-empty
    missing_files = []
    empty_files = []

    for artifact_rel_path in REQUIRED_ARTIFACTS:
        full_path = PROJECT_ROOT / artifact_rel_path
        
        if not full_path.exists():
            missing_files.append(artifact_rel_path)
            continue

        # Check file size
        if full_path.stat().st_size == 0:
            empty_files.append(artifact_rel_path)

    # Assert no missing or empty files
    assert len(missing_files) == 0, f"Missing required artifacts: {missing_files}"
    assert len(empty_files) == 0, f"Empty required artifacts: {empty_files}"

    # Additional check: Ensure analysis_results.json is not just a "Skipped" placeholder if gate passed
    # (This is a soft check; T052 handles the hard failure logic in the pipeline itself)
    analysis_path = PROJECT_ROOT / "data/processed/analysis_results.json"
    if analysis_path.exists():
        with open(analysis_path, 'r') as f:
            try:
                data = json.load(f)
                # If the gate passed, we expect actual results. If it failed, we expect a specific structure.
                # We don't assert specific values here to avoid brittle tests, but we ensure it's valid JSON.
            except json.JSONDecodeError:
                pytest.fail("analysis_results.json is not valid JSON")

    # If we are here, the pipeline ran and produced the required files.
    # If the pipeline exited with an error code due to Data Gate, the files might still exist 
    # (e.g., data_insufficiency_report.md), but the specific list in T055 requires results_report.md.
    # We assume the real data supports the full run for this smoke test.
    assert result.returncode == 0, f"Pipeline execution failed with code {result.returncode}. See logs above."