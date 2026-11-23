"""
Unit tests for survey logic randomization and mock survey execution.
This file implements T011 (stratified randomization) and T020a (mock survey logic).
"""
import pytest
import sys
from pathlib import Path
import json
import random

# Add code directory to path for imports
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

# Import the functions to be tested
try:
    from survey_logic import stratified_randomize, run_mock_survey, load_explanations
except ImportError:
    # If the module or function doesn't exist, we define stubs that will fail
    # to ensure the test fails as expected before implementation.
    def stratified_randomize(snippets, seed=42):
        raise NotImplementedError("stratified_randomize is not implemented yet.")

    def run_mock_survey(n_participants, snippets, explanations_path):
        raise NotImplementedError("run_mock_survey is not implemented yet.")

    def load_explanations(path):
        raise NotImplementedError("load_explanations is not implemented yet.")


def test_stratified_randomization():
    """
    Test that stratified randomization assigns snippets evenly to three conditions
    (Code Only, Code+LLM, Code+Docstring) using seed=42.
    
    Asserts: len(condition_A) == len(condition_B) == len(condition_C)
    """
    # Create a mock list of snippets with complexity labels for stratification
    # We need a number of snippets divisible by 3 to ensure perfect balance
    mock_snippets = [
        {"id": f"snippet_{i}", "complexity": "low" if i % 3 == 0 else ("medium" if i % 3 == 1 else "high")}
        for i in range(30)
    ]
    
    # Run the randomization
    result = stratified_randomize(mock_snippets, seed=42)
    
    # Extract the lists for each condition
    condition_A = result.get("condition_A", [])
    condition_B = result.get("condition_B", [])
    condition_C = result.get("condition_C", [])
    
    # Assert that the lengths are equal (stratified randomization should balance the groups)
    # With 30 snippets and 3 conditions, each should have exactly 10
    assert len(condition_A) == len(condition_B), \
        f"Condition A ({len(condition_A)}) and Condition B ({len(condition_B)}) have different lengths"
    assert len(condition_B) == len(condition_C), \
        f"Condition B ({len(condition_B)}) and Condition C ({len(condition_C)}) have different lengths"
    
    # Assert total count matches input
    total_assigned = len(condition_A) + len(condition_B) + len(condition_C)
    assert total_assigned == len(mock_snippets), \
        f"Total assigned ({total_assigned}) does not match input count ({len(mock_snippets)})"
    
    # Optional: Verify that the seed produces deterministic results
    result_again = stratified_randomize(mock_snippets, seed=42)
    assert result == result_again, "Randomization is not deterministic with the same seed"


def test_mock_survey_logic():
    """
    Test the mock survey runner logic.
    
    Asserts:
    1. Condition assignment is valid (A, B, or C).
    2. Latency is recorded and > 30000ms (30s).
    3. Output structure matches expected CSV columns.
    4. N participants are generated.
    """
    # Create mock data
    mock_snippets = [
        {"id": f"snippet_{i}", "code": f"def func_{i}(): pass", "complexity": "low"}
        for i in range(10)
    ]
    
    # Create a temporary mock explanations file (simulating T014 output)
    # In a real run, this would be data/intermediate/explanations.json
    mock_explanations = []
    for s in mock_snippets:
        mock_explanations.append({
            "snippet_id": s["id"],
            "code": s["code"],
            "complexity": s["complexity"],
            "explanation": f"Explanation for {s['id']}",
            "token_count": 10,
            "model_used": "TinyLlama",
            "status": "success"
        })
    
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        exp_path = os.path.join(tmpdir, "explanations.json")
        with open(exp_path, "w") as f:
            json.dump(mock_explanations, f)
        
        # Run the mock survey
        output_path = os.path.join(tmpdir, "mock_responses.csv")
        
        # We need to patch the random latency generation to ensure it's > 30s
        # The actual implementation in code/02_survey_logic.py should handle this.
        # Here we assume the function works and check the output.
        
        # Since we can't easily patch the internal random call in the imported module
        # without modifying the module, we will run the function and check the result.
        # If the implementation is correct, it will generate N=10 rows.
        
        try:
            # Call the function. We pass the mock data paths.
            # Note: run_mock_survey typically writes to a specific path or returns data.
            # Based on T020b description, it outputs to data/intermediate/mock_responses.csv.
            # We will call it with a custom output path if the API allows, or check the default.
            # Assuming the API allows an output_path argument or we verify the default.
            # Let's assume the signature is run_mock_survey(n, snippets, exp_path, output_path)
            # or it writes to a default. The task description says "Output data/intermediate/mock_responses.csv".
            # We will implement the test to verify the logic by calling the function.
            
            # To strictly test the logic without file system side effects in the test,
            # we might need the function to return the data, or we read the file it creates.
            # Let's assume it creates the file.
            
            # We need to import the actual implementation to run it.
            # If the implementation is not done, this will raise NotImplementedError.
            from survey_logic import run_mock_survey
            
            # We need to ensure the function uses the temp directory for output if possible,
            # or we check the default location. For this test, we assume the function
            # can be directed to write to the temp dir or we check the default.
            # Since the task T020a is a unit test, we focus on the logic.
            # We will call the function with the temp dir as the base or check the result.
            
            # Let's assume the function signature is:
            # run_mock_survey(n_participants, snippets, explanations_path, output_path=None)
            # If output_path is None, it defaults to data/intermediate/mock_responses.csv.
            # We will pass the temp dir path.
            
            # However, the function might not accept output_path.
            # Let's try to call it with the required args and see.
            # If it fails, we adjust.
            
            # For now, let's assume the function is implemented to accept an output path.
            # If not, we would need to modify the test or the function.
            # Given the task is to write the test that fails because logic is not implemented,
            # we assume the function signature is flexible or we test the side effect.
            
            # Let's assume the function writes to a default path. We will check that path.
            # But since we are in a temp dir, we need to make sure the function writes there.
            # This is tricky without knowing the exact implementation.
            
            # Alternative: We mock the random module to ensure latency > 30s.
            # But that's complex.
            
            # Let's assume the function is implemented and we just run it.
            # We will create a mock file for explanations and pass it.
            
            # We'll assume the function writes to the path specified in the task:
            # data/intermediate/mock_responses.csv.
            # But we are in a temp dir. So we need to adjust.
            
            # Let's assume the function takes an output_path argument.
            # If not, we might need to skip the file check and just check the logic.
            
            # For the purpose of this test, we will assume the function is implemented
            # and we can call it with the temp dir.
            
            # We'll call the function and check the output file.
            # If the function doesn't exist or is not implemented, it will raise an error.
            
            # Let's assume the function signature is:
            # run_mock_survey(n_participants, snippets, explanations_path, output_path)
            
            # We'll call it with the temp dir path.
            run_mock_survey(10, mock_snippets, exp_path, output_path)
            
            # Now check the output file
            assert os.path.exists(output_path), "Output file was not created."
            
            # Read the file
            import csv
            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Assert N=10 participants
            assert len(rows) == 10, f"Expected 10 rows, got {len(rows)}"
            
            # Assert columns exist
            expected_columns = {"participant_id", "condition", "snippet_id", "answer", "latency_ms", "timestamp"}
            assert set(rows[0].keys()) == expected_columns, f"Columns mismatch: {rows[0].keys()} vs {expected_columns}"
            
            # Assert condition is valid
            for row in rows:
                assert row["condition"] in ["A", "B", "C"], f"Invalid condition: {row['condition']}"
                
                # Assert latency > 30000ms
                latency = int(row["latency_ms"])
                assert latency > 30000, f"Latency {latency} is not > 30000ms"
                
                # Assert answer is bool (0 or 1 in CSV)
                assert row["answer"] in ["0", "1"], f"Invalid answer: {row['answer']}"
                
                # Assert participant_id is unique (or at least present)
                assert row["participant_id"] is not None and row["participant_id"] != "", "participant_id is missing"
                
        except NotImplementedError:
            # This is expected if the function is not implemented yet.
            # The test should fail in this case.
            pytest.fail("run_mock_survey is not implemented yet.")
        except Exception as e:
            # If there's another error, re-raise it
            pytest.fail(f"Error running mock survey: {e}")