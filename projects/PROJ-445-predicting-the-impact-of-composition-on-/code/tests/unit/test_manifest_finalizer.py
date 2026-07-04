"""
Unit tests for manifest finalization (T033).
"""
import os
import sys
import tempfile
import json
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.manifest_finalizer import (
    get_lofo_model_hashes,
    record_shap_artifacts,
    update_manifest_with_shap_hashes,
    compute_file_hash
)

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directories
    artifacts_dir = tmp_path / "artifacts"
    state_dir = tmp_path / "state"
    data_dir = tmp_path / "data" / "models" / "lofo_models"
    
    artifacts_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    
    # Create a sample manifest
    manifest_path = state_dir / "manifest.json"
    initial_manifest = {
        "version": "1.0",
        "artifacts": []
    }
    with open(manifest_path, 'w') as f:
        json.dump(initial_manifest, f)
    
    # Create dummy LOFO models
    model1 = data_dir / "lofo_model_family1.pkl"
    model2 = data_dir / "lofo_model_family2.pkl"
    with open(model1, 'wb') as f:
        pickle.dump({"model": "family1"}, f)
    with open(model2, 'wb') as f:
        pickle.dump({"model": "family2"}, f)
    
    # Create dummy SHAP artifacts
    (artifacts_dir / "shap_report.md").write_text("# SHAP Report")
    (artifacts_dir / "performance_metrics.json").write_text('{"rmse": 1.0}')
    
    return tmp_path

def test_get_lofo_model_hashes(temp_project_root):
    """Test that LOFO model hashes are computed correctly."""
    # Patch PROJECT_ROOT
    with patch('src.utils.manifest_finalizer.PROJECT_ROOT', temp_project_root):
        hashes = get_lofo_model_hashes()
        
        assert len(hashes) == 2
        paths = [h['path'] for h in hashes]
        assert any('lofo_model_family1.pkl' in p for p in paths)
        assert any('lofo_model_family2.pkl' in p for p in paths)
        
        # Verify hash is a non-empty string
        for h in hashes:
            assert isinstance(h['hash'], str)
            assert len(h['hash']) > 0
            assert h['type'] == 'lofo_model'

def test_record_shap_artifacts(temp_project_root):
    """Test that SHAP artifacts are recorded correctly."""
    with patch('src.utils.manifest_finalizer.PROJECT_ROOT', temp_project_root):
        artifacts = record_shap_artifacts()
        
        assert len(artifacts) == 2
        paths = [a['path'] for a in artifacts]
        assert any('shap_report.md' in p for p in paths)
        assert any('performance_metrics.json' in p for p in paths)
        
        for a in artifacts:
            assert isinstance(a['hash'], str)
            assert len(a['hash']) > 0
            assert a['type'] == 'shap_report_or_data'

def test_update_manifest_with_shap_hashes(temp_project_root):
    """Test manifest update logic."""
    with patch('src.utils.manifest_finalizer.PROJECT_ROOT', temp_project_root):
        initial_manifest = {"version": "1.0", "artifacts": []}
        updated = update_manifest_with_shap_hashes(initial_manifest)
        
        assert "shap_artifacts" in updated
        assert "lofo_models" in updated["shap_artifacts"]
        assert "reports" in updated["shap_artifacts"]
        assert len(updated["shap_artifacts"]["lofo_models"]) == 2
        assert len(updated["shap_artifacts"]["reports"]) == 2
        assert "last_updated" in updated

def test_compute_file_hash(temp_project_root):
    """Test file hash computation."""
    test_file = temp_project_root / "artifacts" / "shap_report.md"
    file_hash = compute_file_hash(test_file)
    
    assert isinstance(file_hash, str)
    assert len(file_hash) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in file_hash)