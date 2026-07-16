import os
import json
import subprocess
import sys

def test_t021b_execution():
    """
    Integration test for T021b:
    1. Runs the repo_metrics_runner script.
    2. Verifies that data/raw/repo_selection_rubric.json exists.
    3. Verifies that data/raw/repo_metrics.json exists.
    4. Verifies that data/checksums.txt contains a checksum for the rubric file.
    5. Verifies that metrics are numeric.
    """
    # Run the script
    result = subprocess.run(
        [sys.executable, "code/repo_metrics_runner.py"],
        capture_output=True,
        text=True
    )
    
    # Check exit code
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check output files exist
    assert os.path.exists("data/raw/repo_selection_rubric.json"), "Rubric JSON missing"
    assert os.path.exists("data/raw/repo_metrics.json"), "Metrics JSON missing"
    assert os.path.exists("data/checksums.txt"), "Checksums file missing"
    
    # Load and verify rubric JSON
    with open("data/raw/repo_selection_rubric.json", "r") as f:
        rubric_data = json.load(f)
    
    assert isinstance(rubric_data, list), "Rubric data should be a list"
    assert len(rubric_data) > 0, "Rubric data should not be empty"
    
    for item in rubric_data:
        assert "repo" in item, "Missing 'repo' key"
        assert "rubric_score" in item, "Missing 'rubric_score' key"
        assert isinstance(item["rubric_score"], (int, float)), "rubric_score must be numeric"
        assert "passed" in item, "Missing 'passed' key"
        assert isinstance(item["passed"], bool), "passed must be boolean"
    
    # Load and verify metrics JSON
    with open("data/raw/repo_metrics.json", "r") as f:
        metrics_data = json.load(f)
    
    assert isinstance(metrics_data, list), "Metrics data should be a list"
    
    for item in metrics_data:
        assert "loc" in item, "Missing 'loc' key"
        assert "cyclomatic_complexity" in item, "Missing 'cyclomatic_complexity' key"
        assert isinstance(item["loc"], (int, float)), "loc must be numeric"
        assert isinstance(item["cyclomatic_complexity"], (int, float)), "CC must be numeric"
        assert "excluded" in item, "Missing 'excluded' key"
    
    # Verify checksum file contains rubric checksum
    with open("data/checksums.txt", "r") as f:
        checksum_content = f.read()
    
    assert "data/raw/repo_selection_rubric.json" in checksum_content, "Rubric checksum not recorded"
    
    print("All T021b verification checks passed.")

if __name__ == "__main__":
    test_t021b_execution()
