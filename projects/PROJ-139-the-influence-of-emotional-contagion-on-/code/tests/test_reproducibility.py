import os
import json
import pytest
import hashlib
from pathlib import Path
import sys

# Add parent to path for imports if running from tests directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.verify_reproducibility import (
    compute_file_sha256,
    load_recorded_checksums,
    verify_artifacts,
    generate_report
)
from config.settings import get_config

def test_reproducibility_full_pipeline():
    """
    Test T028: Verify reproducibility by re-running pipeline and matching checksums.
    
    This test:
    1. Loads the recorded checksums from the previous run (state/...yaml).
    2. Computes the current SHA-256 hashes of the critical artifacts.
    3. Verifies that the current hashes match the recorded ones.
    4. Generates a report to state/reproducibility_report.json.
    """
    config = get_config()
    state_dir = config.paths.state
    
    # Path to the recorded checksums from T027
    recorded_checksums_path = state_dir / "projects" / "PROJ-139-the-influence-of-emotional-contagion-on-.yaml"
    
    if not recorded_checksums_path.exists():
        pytest.fail(f"Recorded checksums file not found at {recorded_checksums_path}. "
                    "Run T027 first to record checksums before running T028.")
    
    # Load recorded checksums
    recorded = load_recorded_checksums(recorded_checksums_path)
    
    if not recorded:
        pytest.fail("Recorded checksums file is empty or invalid.")
    
    # Verify artifacts
    # This function returns a dict: {path: {"expected": str, "current": str, "match": bool}}
    results = verify_artifacts(recorded)
    
    # Check if all matches are True
    all_matched = all(r["match"] for r in results.values())
    
    # Generate the report to disk as required by the task
    report_content = generate_report(results)
    report_path = state_dir / "reproducibility_report.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_content, f, indent=2)
    
    # Assert that the verification passed
    assert all_matched, (
        f"Reproducibility check failed. Mismatched artifacts:\n"
        f"{json.dumps({k: v for k, v in results.items() if not v['match']}, indent=2)}"
    )

def test_report_generation():
    """
    Verify that the reproducibility report was actually written to disk.
    """
    config = get_config()
    report_path = config.paths.state / "reproducibility_report.json"
    assert report_path.exists(), "Reproducibility report was not generated."
    
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert "timestamp" in data
    assert "verification_results" in data
    assert "status" in data
    assert data["status"] == "passed"
