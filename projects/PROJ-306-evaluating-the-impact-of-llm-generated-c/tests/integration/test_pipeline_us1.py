"""
Integration test for end-to-end generation and coverage on multiple tasks (User Story 1).

This test verifies the full pipeline:
1. Load a small subset of tasks from the catalog.
2. Generate code for each task using the configured LLM.
3. Run coverage analysis on the generated code.
4. Verify that coverage reports are generated and contain expected fields.

Note: This test uses a small batch (default 2 tasks) and a timeout to ensure
it runs within reasonable time limits during CI/CD.
"""
import os
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Add project root to path to import code modules
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

sys.path.insert(0, str(PROJECT_ROOT))

from config import get_model_chain, get_model_config, resolve_model
from dataset_loader import load_mbpp_dataset, load_humaneval_dataset, validate_and_create_catalog
from llm_generator import generate_code
from coverage_runner import run_coverage

# Configuration for the integration test
TEST_BATCH_SIZE = 2  # Small batch for CI/CD
TEST_TIMEOUT_SECONDS = 300  # 5 minutes timeout for the whole test

def _get_sample_tasks(num_tasks: int = 2) -> List[Dict[str, Any]]:
    """
    Load a small sample of tasks from the catalog for integration testing.
    Prioritizes MBPP tasks as they are generally simpler for quick generation.
    """
    catalog_path = DATA_DIR / "benchmarks" / "processed" / "catalog.json"
    
    if not catalog_path.exists():
        # If catalog doesn't exist, run the loader first (should be done by setup)
        # For robustness in CI, we try to run the loader if needed
        print(f"Catalog not found at {catalog_path}, attempting to generate...")
        # This assumes the main dataset loader script is available
        # In a real CI, we would ensure prerequisites are met
        raise FileNotFoundError(f"Catalog file not found at {catalog_path}. Please run dataset loading tasks first.")

    with open(catalog_path, 'r') as f:
        catalog = json.load(f)

    # Filter for tasks that have all required fields and are likely to succeed
    valid_tasks = [
        t for t in catalog 
        if all(k in t for k in ['task_id', 'prompt', 'human_solution', 'test_suite_path'])
    ]

    # Select a small sample
    sample = valid_tasks[:num_tasks]
    
    if len(sample) < num_tasks:
        pytest.skip(f"Only {len(sample)} valid tasks found in catalog, need {num_tasks}")

    return sample

def _run_coverage_for_task(task: Dict[str, Any], generated_code_path: Path) -> Dict[str, Any]:
    """
    Run coverage analysis for a single generated task.
    """
    task_id = task['task_id']
    test_suite_path = Path(task['test_suite_path'])

    if not test_suite_path.exists():
        pytest.skip(f"Test suite not found for {task_id}: {test_suite_path}")

    # Run coverage using the coverage_runner module
    # We need to capture the result without running the full main script
    try:
        result = run_coverage(
            task_id=task_id,
            generated_code_path=generated_code_path,
            test_suite_path=test_suite_path,
            output_dir=DATA_DIR / "coverage_reports"
        )
        return result
    except Exception as e:
        # Log the error but don't fail the test immediately if it's a known issue
        print(f"Coverage run failed for {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error_message": str(e)
        }

@pytest.mark.integration
def test_end_to_end_generation_and_coverage():
    """
    Integration test: Generate code for a small batch of tasks and verify coverage reports.
    """
    # Ensure directories exist
    (DATA_DIR / "coverage_reports").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "generated").mkdir(parents=True, exist_ok=True)

    # Get sample tasks
    tasks = _get_sample_tasks(TEST_BATCH_SIZE)
    print(f"Running integration test on {len(tasks)} tasks: {[t['task_id'] for t in tasks]}")

    results = []
    start_time = time.time()

    for i, task in enumerate(tasks):
        # Check timeout
        if time.time() - start_time > TEST_TIMEOUT_SECONDS:
            pytest.fail("Integration test timed out")

        task_id = task['task_id']
        print(f"\n--- Processing Task {i+1}/{len(tasks)}: {task_id} ---")

        try:
            # 1. Generate Code
            print(f"  Generating code for {task_id}...")
            generated_path = generate_code(
                task_id=task_id,
                prompt=task['prompt'],
                output_dir=DATA_DIR / "generated"
            )

            if not generated_path or not generated_path.exists():
                results.append({
                    "task_id": task_id,
                    "status": "failed",
                    "error_message": "Code generation failed - no output file created"
                })
                continue

            print(f"  Code generated at: {generated_path}")

            # 2. Run Coverage
            print(f"  Running coverage for {task_id}...")
            coverage_result = _run_coverage_for_task(task, generated_path)
            results.append(coverage_result)

            # 3. Verify Output
            if coverage_result.get("status") == "success":
                report_path = DATA_DIR / "coverage_reports" / f"{task_id}.json"
                assert report_path.exists(), f"Coverage report not found for {task_id}"
                
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                
                assert "line_coverage" in report_data, f"Missing line_coverage in report for {task_id}"
                print(f"  Coverage Report: Line={report_data['line_coverage']}%, Branch={report_data.get('branch_coverage', 'N/A')}%")
            else:
                print(f"  Coverage failed for {task_id}: {coverage_result.get('error_message', 'Unknown error')}")

        except Exception as e:
            print(f"  Error processing {task_id}: {e}")
            results.append({
                "task_id": task_id,
                "status": "failed",
                "error_message": str(e)
            })

    # Assertions
    print("\n--- Test Summary ---")
    success_count = sum(1 for r in results if r.get("status") == "success")
    total_count = len(results)
    
    print(f"Total tasks: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")

    # We expect at least one success for the test to pass (unless all tasks are inherently problematic)
    # In a real CI, we might want 100% success, but for integration testing with LLMs,
    # we allow some failure rate as long as the pipeline runs correctly.
    assert success_count > 0, f"No tasks completed successfully. Results: {results}"
    
    # Verify that at least one coverage report was created
    reports = list((DATA_DIR / "coverage_reports").glob("*.json"))
    assert len(reports) > 0, "No coverage reports were generated"

if __name__ == "__main__":
    # Allow running directly for debugging
    pytest.main([__file__, "-v", "-s"])
