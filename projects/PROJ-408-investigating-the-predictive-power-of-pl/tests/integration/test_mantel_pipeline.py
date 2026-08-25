"""
Integration test for full pipeline run on a diverse set of species.
Task: T011 [US1]
Input: data/raw/test_species_10.txt
Output: data/processed/test_tree.newick
Assertion: p-value < 0.05 (or < 0.1 for small sample)
"""
import os
import sys
import json
import subprocess
from pathlib import Path
import pytest

# Ensure code/ is in path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config, load_config
from entities import DistanceMatrix

# Constants
SPECIES_LIST_PATH = "data/raw/test_species_10.txt"
TREE_OUTPUT_PATH = "data/processed/test_tree.newick"
METADATA_OUTPUT_PATH = "data/processed/mantel_results.json"
EXPECTED_P_VALUE_THRESHOLD = 0.10  # Relaxed for small sample (n=10)

def _run_pipeline(species_file: str) -> None:
    """
    Executes the main pipeline script.
    In a real CI/CD, this would be a subprocess call to `python code/main.py`.
    For this integration test, we assume the pipeline is invoked via a script
    that sets up the environment and runs the logic.
    """
    config = load_config()
    
    # Simulate the pipeline execution steps that T013-T019 would perform
    # Since T013-T019 are not fully implemented yet (they are future tasks),
    # this test validates the *integration logic* by checking if the pipeline
    # *would* run or by running a mock of the critical path if the real
    # dependencies are missing.
    
    # However, per instructions: "Implement the task for real... never a stub".
    # Since T013 (Data Loader) and T015 (Phylo Pipeline) are NOT implemented yet,
    # we cannot run the *real* end-to-end fetch and tree build without stubbing.
    # BUT, the instruction also says: "If the task is too large to implement as a 
    # single coherent unit, return verdict: atomize".
    #
    # CRITICAL REALIZATION: T011 is an Integration Test. It depends on T013, T014, T015, T016, T017, T018, T019.
    # Those tasks are marked [ ] (not done). 
    # We cannot run a real integration test if the pipeline code doesn't exist.
    #
    # Strategy: We implement the TEST FRAMEWORK and the EXPECTATION. 
    # We will create a script `run_integration_test.py` that:
    # 1. Checks if the input file exists.
    # 2. Attempts to run the pipeline (which will fail if code is missing).
    # 3. If the pipeline code IS present (future state), it runs it.
    # 4. Validates the output.
    #
    # Since we are implementing T011 NOW, and the pipeline code (T013-T019) is NOT there,
    # we must provide the *test harness* that will work once the pipeline is done.
    # We will also provide a *minimal mock pipeline* in the test artifact itself 
    # ONLY IF the real pipeline is missing, to satisfy "real runnable code" 
    # BUT the constraints say "NEVER fabricate".
    #
    # Correct Approach for T011 in a sequence where dependencies are missing:
    # Write the test that *calls* the real pipeline. If the pipeline is missing,
    # the test fails (which is correct).
    # However, the prompt says "Implement the task for real... write real, runnable research code".
    # If I write a test that just `assert False` because dependencies are missing, it's not "runnable research code".
    #
    # Let's look at the "Execution Failed" rule. If I try to run the real pipeline and it fails, I must fix it.
    # But I can't fix T013-T019 here because I'm only doing T011.
    #
    # Alternative Interpretation: T011 is the *definition* of the integration test.
    # The "implementation" is the test code itself. The test code should be runnable.
    # It will attempt to run the pipeline. If the pipeline is missing, it raises an error.
    # This is a valid state.
    #
    # HOWEVER, to make it "runnable" and "produce real output" as per constraints:
    # We will write a script that:
    # 1. Reads the species list.
    # 2. Checks if `code/main.py` exists and has the necessary functions.
    # 3. If so, runs it.
    # 4. If not, it raises a clear ImportError indicating which component is missing.
    #
    # To satisfy "produce real output" and "assert p-value", we need the pipeline.
    # Since the pipeline is not done, we cannot produce the *real* tree or p-value.
    #
    # WAIT: The prompt says "If the task is too large... return verdict: atomize".
    # But T011 is a test task. It is small. It just depends on others.
    # Maybe I should implement the test such that it *generates* the expected output structure
    # if the pipeline is missing? No, "NEVER fabricate".
    #
    # Let's re-read: "Implement the task for real... If the task asks for an analysis, write the code that performs it".
    # The task asks for an "Integration test". The code that performs an integration test is the test script.
    # The test script runs the pipeline.
    #
    # Since T013-T019 are not implemented, running the pipeline will fail.
    # This is expected. The test *is* the verification that the pipeline works.
    # If the pipeline doesn't exist, the test fails.
    #
    # BUT, the constraint "Produce real outputs, not demos" applies to the *artifacts*.
    # If I write a test that fails because dependencies are missing, I haven't produced the output file `test_tree.newick`.
    #
    # Solution: I will implement the test script. I will also implement a `run_pipeline_mock` 
    # that is ONLY used if the real pipeline is not found, BUT this violates "NEVER fabricate".
    #
    # Let's look at the "VERIFIED REAL DATA SOURCE" rule.
    # "If the messages contain a VERIFIED REAL DATA SOURCE... write the loader to use THAT".
    # There is no such block here.
    #
    # Conclusion: I must implement the test. The test will attempt to run the real pipeline.
    # If the pipeline is missing, the test fails. This is the correct behavior for a test task
    # when dependencies are incomplete.
    #
    # However, to make the code "runnable" and "complete", I will write the test to:
    # 1. Verify input file exists.
    # 2. Try to import and run the pipeline from `code/main.py`.
    # 3. If `code/main.py` is missing or incomplete, raise a clear error.
    # 4. If it runs, verify the output and the p-value.
    #
    # Since I cannot run the real pipeline (T013-T019 missing), I will write the test
    # to be ready for when they are implemented.
    #
    # To satisfy "produce real output" for the *test run* (even if it fails):
    # The test will fail with a clear message.
    #
    # Wait, maybe I can implement a minimal version of the pipeline *inside* the test
    # to demonstrate the logic? No, "NEVER fabricate".
    #
    # Okay, I will write the test. It will fail if dependencies are missing.
    # This is the only honest implementation.
    #
    # BUT, the prompt says "Implement the task for real... write complete, correct, executable code".
    # If I write code that fails because of missing dependencies, is it "correct"?
    # Yes, if the dependencies are supposed to be there.
    # But they are not.
    #
    # Let's try to implement a *minimal* pipeline in the test file itself?
    # No, that's duplicating work for T013-T019.
    #
    # Let's assume the user expects the test to *pass* if the pipeline is implemented.
    # Since the pipeline is NOT implemented, the test *should* fail.
    #
    # I will write the test to:
    # 1. Check for `code/main.py`.
    # 2. If present, run it.
    # 3. If not, raise `ImportError: Pipeline implementation (T013-T019) is missing`.
    #
    # This is the correct implementation of T011 given the current state.
    pass

def test_integration_pipeline_run():
    """
    Integration test: Run full pipeline on test_species_10.txt.
    """
    species_path = PROJECT_ROOT / SPECIES_LIST_PATH
    tree_path = PROJECT_ROOT / TREE_OUTPUT_PATH
    metadata_path = PROJECT_ROOT / METADATA_OUTPUT_PATH

    # Ensure input exists
    if not species_path.exists():
        pytest.fail(f"Input file not found: {species_path}")

    # Attempt to run the pipeline
    # Since T013-T019 are not implemented, we expect this to fail or raise an error.
    # We will write the test to catch the specific error if the pipeline is missing.
    try:
        # Try to import the main pipeline logic
        # We assume code/main.py will have a function `run_full_pipeline(species_file)`
        # or similar.
        from main import run_full_pipeline
        
        # Run it
        result = run_full_pipeline(str(species_path))
        
        # Verify outputs
        assert tree_path.exists(), f"Output tree not found: {tree_path}"
        assert metadata_path.exists(), f"Output metadata not found: {metadata_path}"

        # Verify p-value
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        p_value = data.get('p_value')
        assert p_value is not None, "p-value missing from results"
        
        # Assertion: p-value < 0.05 (or < 0.1 for small sample)
        if p_value >= EXPECTED_P_VALUE_THRESHOLD:
            pytest.fail(f"Phylogenetic signal not significant: p-value={p_value:.4f} (threshold={EXPECTED_P_VALUE_THRESHOLD})")
            
    except ImportError as e:
        # This is expected if T013-T019 are not done
        pytest.fail(f"Pipeline implementation missing (T013-T019 not completed): {e}")
    except Exception as e:
        pytest.fail(f"Pipeline execution failed: {e}")

if __name__ == "__main__":
    test_integration_pipeline_run()
