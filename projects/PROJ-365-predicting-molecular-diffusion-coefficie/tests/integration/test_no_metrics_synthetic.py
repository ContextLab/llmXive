import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil

import pytest

from utils.config import get_project_root

@pytest.fixture
def synthetic_project_root(tmp_path):
    """
    Create a temporary project structure with synthetic data flag set.
    """
    # Copy the structure or create necessary files
    # We need:
    # 1. data/data_source_flag.json -> {"source": "synthetic"}
    # 2. data/processed/featurized.jsonl (dummy)
    # 3. code/training/evaluate.py (the one we just wrote)
    
    # Since we are running tests in the context of the project, 
    # we assume the code exists. We just need to set up the data state.
    
    root = tmp_path / "project"
    root.mkdir()
    
    # Create directories
    (root / "data").mkdir()
    (root / "data" / "processed").mkdir()
    (root / "artifacts" / "reports").mkdir(parents=True)
    
    # Create synthetic flag
    flag_file = root / "data" / "data_source_flag.json"
    with open(flag_file, 'w') as f:
        json.dump({"source": "synthetic"}, f)
    
    # Create dummy featurized data
    featurized_file = root / "data" / "processed" / "featurized.jsonl"
    with open(featurized_file, 'w') as f:
        # Dummy row with required fields
        f.write(json.dumps({
            "smiles": "CCO",
            "diffusion_coefficient": 1.0,
            "predicted_diffusion": 1.1
        }) + "\n")
    
    # Create a temporary config to point to this root?
    # The evaluate.py uses get_project_root(). 
    # We need to override the project root for this test.
    # Since we can't easily patch get_project_root without modifying utils.config,
    # we will run the script with an environment variable or modify the test to 
    # temporarily patch the function.
    
    # Better approach: Patch the function in the module being tested.
    return root

def test_synthetic_data_suppression(synthetic_project_root, monkeypatch):
    """
    Test that evaluate.py exits with non-zero status and prints suppression message
    when data_source_flag.json indicates 'synthetic'.
    """
    # Patch get_project_root to return our temp directory
    from utils import config
    original_get_project_root = config.get_project_root
    
    def mock_get_project_root():
        return synthetic_project_root
    
    monkeypatch.setattr(config, "get_project_root", mock_get_project_root)
    
    # Import the main function from evaluate (after patching)
    # We need to reload the module to pick up the patch, or just call the function logic
    # Since we patched the config, we can import evaluate and call main()
    from training.evaluate import main
    
    # Run main
    exit_code = main()
    
    # Assertions
    assert exit_code == 1, f"Expected exit code 1 for synthetic data, got {exit_code}"
    
    # Check that evaluation.json was NOT created
    report_path = synthetic_project_root / "artifacts" / "reports" / "evaluation.json"
    assert not report_path.exists(), "evaluation.json should NOT be created for synthetic data"

def test_real_data_metrics_generated(synthetic_project_root, monkeypatch, capsys):
    """
    Test that evaluate.py creates evaluation.json when data_source_flag is 'real'.
    """
    # Update flag to real
    flag_file = synthetic_project_root / "data" / "data_source_flag.json"
    with open(flag_file, 'w') as f:
        json.dump({"source": "real"}, f)
    
    # Patch get_project_root
    from utils import config
    def mock_get_project_root():
        return synthetic_project_root
    monkeypatch.setattr(config, "get_project_root", mock_get_project_root)
    
    # Import and run
    from training.evaluate import main
    exit_code = main()
    
    # Assertions
    assert exit_code == 0, f"Expected exit code 0 for real data, got {exit_code}"
    
    # Check that evaluation.json WAS created
    report_path = synthetic_project_root / "artifacts" / "reports" / "evaluation.json"
    assert report_path.exists(), "evaluation.json should be created for real data"
    
    # Check content
    with open(report_path) as f:
        report = json.load(f)
    
    assert "pearson_r" in report
    assert "rmse" in report
    assert "hypothesis_status" in report
    assert report["hypothesis_status"] in ["positive", "null", "inconclusive"]

def test_missing_flag_behavior(synthetic_project_root, monkeypatch):
    """
    Test behavior when data_source_flag.json is missing.
    Based on implementation, it should warn and attempt to run (treat as real/unknown).
    """
    # Remove flag
    flag_file = synthetic_project_root / "data" / "data_source_flag.json"
    if flag_file.exists():
        flag_file.unlink()
    
    # Patch
    from utils import config
    def mock_get_project_root():
        return synthetic_project_root
    monkeypatch.setattr(config, "get_project_root", mock_get_project_root)
    
    from training.evaluate import main
    # Should run (exit 0) or fail with data error?
    # Our implementation: if source is None, it proceeds (with warning).
    # So it should try to compute metrics and succeed (exit 0).
    exit_code = main()
    assert exit_code == 0, "Should proceed if flag is missing (assuming real)"
    
    report_path = synthetic_project_root / "artifacts" / "reports" / "evaluation.json"
    assert report_path.exists(), "Should create report if flag is missing"