"""
Integration test for the execution pipeline on a subset of 3 languages (C++, Java, Python).

This test verifies that the execution pipeline can successfully:
1. Load a subset of tasks for C++, Java, and Python.
2. Execute the pipeline logic for these tasks (mocking external LLM/sandbox calls for speed).
3. Produce a valid execution log structure containing Pass@k metrics.

Note: To keep this integration test runnable in CI without external dependencies,
we mock the heavy-lifting of `runner` and `sandbox` while exercising the orchestration
logic in `execute_pipeline` and the aggregation logic in `aggregators`.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, get_results_path, set_config
from execute_pipeline import ExecutionTask, run_pipeline, setup_logging
from execution.aggregators import compute_pass_k_for_task, aggregate_pass_k_by_group

# Constants for the test subset
TEST_LANGUAGES = ["cpp", "java", "python"]
TEST_TEMPERATURES = [0.2]  # Use one temperature for speed
TEST_RUNS = 2  # Small number of runs for integration speed
TEST_MODEL = "test-model-v1"

def test_execution_pipeline_integration():
    """
    Integration test: Run the pipeline on a subset of 3 languages and verify
    the structure of the generated execution_log.json.
    """
    # Setup temporary directory for this test run
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Override config paths to use temporary directory
        # We assume get_config returns a mutable object or we can set specific paths
        # Since we can't easily mutate the global config singleton without side effects in a real run,
        # we will mock the path getters for this test scope.
        
        original_results_path = get_results_path()
        
        # Patch config getters to point to our temp dir
        def mock_get_results_path():
            return tmp_path / "results" / "artifacts"
        
        # Create the directory structure
        (tmp_path / "results" / "artifacts").mkdir(parents=True, exist_ok=True)

        # Mock the dataset loading to return a small, deterministic subset of tasks
        # We simulate tasks for the 3 target languages
        mock_tasks = []
        for i, lang in enumerate(TEST_LANGUAGES):
            for j in range(2):  # 2 tasks per language
                mock_tasks.append({
                    "task_id": f"test_task_{lang}_{j}",
                    "language": lang,
                    "problem_statement": f"Mock problem for {lang} {j}",
                    "canonical_solution": f"print('solution {j}')",
                    "test_cases": [{"input": "", "output": "1"}]
                })

        # Mock the runner to return deterministic results
        def mock_run_single_inference(task, model, temp, seed):
            # Simulate a pass for the first run, fail for the second to test Pass@k logic
            # In a real scenario, this would call the LLM and sandbox
            return {
                "passed": (seed % 2 == 0), # Alternate pass/fail based on seed
                "duration_ms": 100 + seed,
                "tokens_used": 50
            }

        # Mock the sandbox execution if needed, but run_pipeline might handle it internally
        # We patch the specific execution function in execute_pipeline if it calls runner directly
        
        try:
            with patch('execute_pipeline.load_dataset_tasks', return_value=mock_tasks):
                with patch('execute_pipeline.run_single_inference', side_effect=mock_run_single_inference):
                    with patch('config.get_results_path', side_effect=mock_get_results_path):
                        with patch('config.get_models', return_value=[TEST_MODEL]):
                            with patch('config.get_temperatures', return_value=TEST_TEMPERATURES):
                                with patch('config.get_seed', return_value=42):
                                    # Run the pipeline
                                    # Note: We pass a subset of languages to the pipeline logic if supported,
                                    # or we rely on the mock dataset to only contain those languages.
                                    # The mock dataset above only contains our test languages.
                                    
                                    run_pipeline(
                                        languages=TEST_LANGUAGES,
                                        models=[TEST_MODEL],
                                        temperatures=TEST_TEMPERATURES,
                                        runs_per_task=TEST_RUNS,
                                        seed=42
                                    )
                                    
                                    # Verify output file exists
                                    output_file = tmp_path / "results" / "artifacts" / "execution_log.json"
                                    assert output_file.exists(), f"Execution log not created at {output_file}"
                                    
                                    # Load and validate content
                                    with open(output_file, 'r') as f:
                                        log_data = json.load(f)
                                    
                                    # Validate structure
                                    assert "results" in log_data, "Missing 'results' key in execution log"
                                    assert "summary" in log_data, "Missing 'summary' key in execution log"
                                    
                                    # Check that we have results for all 3 languages
                                    results = log_data["results"]
                                    found_languages = set()
                                    for entry in results:
                                        found_languages.add(entry.get("language"))
                                    
                                    assert TEST_LANGUAGES[0] in found_languages, f"Missing C++ results"
                                    assert TEST_LANGUAGES[1] in found_languages, f"Missing Java results"
                                    assert TEST_LANGUAGES[2] in found_languages, f"Missing Python results"
                                    
                                    # Check Pass@k presence
                                    for entry in results:
                                        assert "pass_at_1" in entry, f"Missing pass_at_1 for {entry['task_id']}"
                                        assert "pass_at_k" in entry, f"Missing pass_at_k for {entry['task_id']}"
                                    
                                    # Validate summary statistics
                                    summary = log_data["summary"]
                                    assert "total_tasks" in summary
                                    assert "total_tasks" == len(mock_tasks) # Should match our mock count
                                    
            print("Integration test passed: Pipeline executed and generated valid execution log.")

        finally:
            # Restore original config if necessary (though temp dir cleanup handles files)
            pass

if __name__ == "__main__":
    setup_logging()
    test_execution_pipeline_integration()
    print("SUCCESS: T016 Integration Test completed.")