"""
Unit tests for src/models/vae_loader.py.
Tests Task 0.2: Model Availability & Fallback Validation logic.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

# We mock torch/transformers to avoid heavy dependencies during unit tests
# The actual logic of availability checking is tested via the mocked return values.

@pytest.fixture
def mock_torch():
    mock = MagicMock()
    mock.__version__ = "2.0.0"
    return mock

@pytest.fixture
def mock_transformers():
    mock_config = MagicMock()
    mock_config.architectures = ["Qwen2VLForConditionalGeneration"]
    mock_config.model_type = "qwen2_vl"
    
    mock_model = MagicMock()
    mock_model.from_pretrained.return_value = MagicMock()
    
    return {
        "AutoConfig": MagicMock(from_pretrained=MagicMock(return_value=mock_config)),
        "AutoModel": mock_model
    }

def test_check_model_availability_success(mock_torch, mock_transformers):
    """Test that a successful model check returns expected structure."""
    with patch.dict(sys.modules, {
        "torch": mock_torch,
        "transformers": mock_transformers
    }):
        from models.vae_loader import check_model_availability
        
        result = check_model_availability("some/model/id")
        
        assert result["model_id"] == "some/model/id"
        assert result["exists"] is True
        assert result["cpu_feasible"] is True
        assert result["reason"] == "Config found"

def test_check_model_availability_failure(mock_torch, mock_transformers):
    """Test that a failed model check returns expected structure."""
    # Force the config loader to raise an exception
    mock_transformers["AutoConfig"].from_pretrained.side_effect = Exception("Model not found")
    
    with patch.dict(sys.modules, {
        "torch": mock_torch,
        "transformers": mock_transformers
    }):
        # Need to re-import to pick up the new side_effect if module caching is an issue,
        # but in this simple setup, the function uses the patched global.
        # However, to be safe, we reload or ensure the patch is active.
        from models import vae_loader
        # Re-patch inside the function if needed, but here we assume the mock is global.
        # Actually, the function uses AutoConfig from the module scope.
        # We need to ensure the function sees the patched version.
        vae_loader.AutoConfig = mock_transformers["AutoConfig"]
        
        result = vae_loader.check_model_availability("nonexistent/model")
        
        assert result["model_id"] == "nonexistent/model"
        assert result["exists"] is False
        assert result["cpu_feasible"] is False
        assert "Model not found" in result["reason"]

def test_trigger_fallback_protocol(mock_torch, mock_transformers):
    """Test that the fallback protocol selects a valid candidate."""
    # Mock the first candidate to fail, second to succeed
    call_count = 0
    
    def mock_check(model_id):
        nonlocal call_count
        call_count += 1
        if "sdxl" in model_id:
            return {"model_id": model_id, "exists": True, "cpu_feasible": True}
        return {"model_id": model_id, "exists": False, "cpu_feasible": False}
    
    with patch.dict(sys.modules, {
        "torch": mock_torch,
        "transformers": mock_transformers
    }):
        from models import vae_loader
        vae_loader.check_model_availability = mock_check
        
        fallback = vae_loader.trigger_fallback_protocol()
        
        assert fallback is not None
        assert "sdxl" in fallback

def test_trigger_fallback_protocol_no_candidates(mock_torch, mock_transformers):
    """Test fallback returns None if no candidates are found."""
    def mock_check(model_id):
        return {"model_id": model_id, "exists": False, "cpu_feasible": False}
    
    with patch.dict(sys.modules, {
        "torch": mock_torch,
        "transformers": mock_transformers
    }):
        from models import vae_loader
        vae_loader.check_model_availability = mock_check
        
        fallback = vae_loader.trigger_fallback_protocol()
        
        assert fallback is None

def test_run_availability_check_output(mock_torch, mock_transformers):
    """Test that run_availability_check writes the correct JSON file."""
    # Mock the check to return success immediately
    def mock_check(model_id):
        return {"model_id": model_id, "exists": True, "cpu_feasible": True}
    
    with patch.dict(sys.modules, {
        "torch": mock_torch,
        "transformers": mock_transformers
    }):
        from models import vae_loader
        vae_loader.check_model_availability = mock_check
        
        # Ensure output dir exists
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "model_availability.json"
        
        # Run the function
        result = vae_loader.run_availability_check()
        
        # Verify file exists
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "PASS"
        assert data["fallback_model_id"] == vae_loader.TARGET_MODEL_ID
        
        # Cleanup
        output_file.unlink()
