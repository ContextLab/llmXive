import os
import sys
import json
import pytest
from pathlib import Path

# Ensure code directory is in path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.run_evaluation import main as run_evaluation_main
from gatekeeper.metrics import calculate_access_control_score, load_predictions_and_ground_truth

@pytest.mark.integration
def test_us1_medical_domain():
    """
    Integration test: Run full pipeline on "medical" domain subset and assert Access Control score is calculated.
    
    This test executes the full evaluation pipeline for the 'medical' domain,
    then verifies that:
    1. The output file data/processed/access_control_results.json exists.
    2. The file contains valid JSON with the expected schema.
    3. The calculated Access Control score is > 0.0 (indicating the metric was computed).
    """
    # Ensure output directory exists
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Construct arguments for the evaluation pipeline
    # We target the 'medical' domain as specified in the task
    test_args = [
        "run_evaluation.py",
        "--domains", "medical",
        "--skip-stats",  # Skip heavy stats for this integration check
        "--output-dir", str(output_dir)
    ]
    
    # Mock sys.argv to simulate CLI execution
    original_argv = sys.argv
    try:
        sys.argv = test_args
        
        # Run the evaluation pipeline
        # This will trigger T016 (Gatekeeper), T017a/b (Baselines), and T018 (Metrics)
        run_evaluation_main()
        
        # Verify the expected output file exists
        results_file = output_dir / "access_control_results.json"
        assert results_file.exists(), f"Output file {results_file} was not created by the pipeline."
        
        # Load and validate the results
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        assert isinstance(results, list), "Results should be a list of episode results."
        assert len(results) > 0, "Results list is empty; no episodes were processed."
        
        # Check for the presence of the 'score' field in at least one entry
        # and assert that the score is > 0.0 as per the task requirement
        scores = [entry.get('score') for entry in results if 'score' in entry]
        
        assert len(scores) > 0, "No 'score' field found in results."
        
        # The task requires asserting score > 0.0. 
        # In a real scenario, we expect some leakage (score > 0) or perfect blocking (score = 0).
        # However, the metric calculation itself must have run. 
        # We assert that the calculation happened and produced a valid numeric result.
        # If the metric is "unauthorized exposure rate", a score of 0.0 is possible (perfect security),
        # but the task specifically asks to assert score > 0.0. 
        # Assuming the medical domain has some leakage in the test data or the metric is defined 
        # such that a non-zero value is expected for the 'medical' subset.
        # If the dataset is perfect, this assertion might fail, but we follow the task instruction.
        # Note: If the dataset has 0 leakage, the score is 0. The task says "assert score > 0.0".
        # We will check if ANY score is > 0. If all are 0, the test fails as per instruction.
        
        max_score = max(scores)
        assert max_score > 0.0, f"Access Control score is 0.0 (or all 0.0). Expected > 0.0 for medical domain. Scores: {scores}"
        
    finally:
        sys.argv = original_argv