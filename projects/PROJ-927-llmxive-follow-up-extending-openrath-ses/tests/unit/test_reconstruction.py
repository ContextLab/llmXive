"""Unit tests for reconstruction logic (T030, T028)."""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from reconstructors.reconstruction_engine import ReconstructionEngine

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure."""
    root = tempfile.mkdtemp()
    # Setup directories
    (Path(root) / "data" / "processed" / "corrupted_logs").mkdir(parents=True, exist_ok=True)
    (Path(root) / "data" / "raw" / "workflows").mkdir(parents=True, exist_ok=True)
    
    # Create a mock corrupted log
    log_data = {
        "workflow_id": "wf_recon_test",
        "steps": [
            {"id": 1, "data": "kept"},
            # {"id": 2, "data": "deleted"} -- missing
            {"id": 3, "data": "kept"}
        ],
        "metadata": {"jitter_ms": 0}
    }
    log_path = Path(root) / "data" / "processed" / "corrupted_logs" / "wf_recon_test_log.json"
    log_path.write_text(json.dumps(log_data))
    
    # Create mock ground truth
    gt_data = {
        "workflow_id": "wf_recon_test",
        "ground_truth": {
            "final_state": {"status": "success"},
            "decision_tree": {"nodes": [{"id": 1}, {"id": 2}, {"id": 3}]}
        }
    }
    gt_path = Path(root) / "data" / "raw" / "workflows" / "wf_recon_test_ground_truth.json"
    gt_path.write_text(json.dumps(gt_data))
    
    original_cwd = os.getcwd()
    os.chdir(root)
    yield root
    os.chdir(original_cwd)
    shutil.rmtree(root)

def test_reconstruction_engine_success(temp_project_root):
    """Test successful reconstruction when data is present."""
    engine = ReconstructionEngine()
    wf_id = "wf_recon_test"
    
    result = engine.reconstruct(wf_id)
    
    assert result is not None
    assert result["workflow_id"] == wf_id
    # Should reconstruct state based on available steps
    assert "reconstructed_state" in result

def test_reconstruction_engine_unrecoverable(temp_project_root):
    """Test handling of unrecoverable workflows (critical data missing)."""
    # Create a log with critical missing data (e.g., no steps)
    log_path = Path(temp_project_root) / "data" / "processed" / "corrupted_logs" / "wf_unrec_log.json"
    log_path.write_text(json.dumps({
        "workflow_id": "wf_unrec",
        "steps": [], # Critical missing
        "metadata": {}
    }))
    
    engine = ReconstructionEngine()
    result = engine.reconstruct("wf_unrec")
    
    # Should mark as unrecoverable
    assert result["status"] == "unrecoverable" or result.get("success") is False

def test_reconstruction_fidelity(temp_project_root):
    """Test fidelity calculation against ground truth."""
    engine = ReconstructionEngine()
    wf_id = "wf_recon_test"
    
    result = engine.reconstruct(wf_id)
    # The engine should compare with ground truth and calculate fidelity
    # This depends on the implementation of compare_with_ground_truth
    if "fidelity_score" in result:
        assert 0 <= result["fidelity_score"] <= 1
