import os
import subprocess
import sys
import yaml

def test_main_produces_statistical_summary(tmp_path, monkeypatch):
    """
    Runs the main orchestrator in pilot mode for a tiny seed range and verifies
    that `results/statistical_summary.json` is created.
    """
    # Use a small seed range to keep the test fast
    seeds = [1, 2]
    config_path = os.path.join(tmp_path, "config", "seeds.yaml")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(seeds, f)

    # Patch the project paths used by the orchestrator to the temporary directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    monkeypatch.setenv("PYTHONPATH", project_root)

    # Invoke the orchestrator
    result = subprocess.run(
        [sys.executable, "code/main.py", "--mode", "pilot", "--seeds", "1..2"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Main script failed: {result.stderr}"

    # Verify that the statistical summary exists
    summary_path = os.path.join(project_root, "results", "statistical_summary.json")
    assert os.path.isfile(summary_path), "statistical_summary.json was not created"

    # Basic sanity check on the JSON content
    with open(summary_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "text_mean" in content and "baseline_mean" in content, "Summary JSON missing expected keys"