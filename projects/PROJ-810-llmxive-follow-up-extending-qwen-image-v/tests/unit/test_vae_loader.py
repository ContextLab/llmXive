"""
Unit tests for src/models/vae_loader.py.
Tests Task T016: CPU fallback logic validation.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

# We mock torch/transformers to avoid heavy dependencies during unit tests
# The actual logic of CPU fallback is tested via the mocked return values.

@pytest.fixture
def mock_torch_cpu_false():
    """Mock torch where CUDA is not available."""
    mock = MagicMock()
    mock.__version__ = "2.0.0"
    mock.cuda.is_available.return_value = False
    mock.no_grad = MagicMock()
    # Mock device context
    mock.device = MagicMock()
    mock.device.return_value = MagicMock()
    return mock

@pytest.fixture
def mock_torch_cpu_true():
    """Mock torch where CUDA is available but we force CPU."""
    mock = MagicMock()
    mock.__version__ = "2.0.0"
    mock.cuda.is_available.return_value = True
    mock.no_grad = MagicMock()
    mock.device = MagicMock()
    mock.device.return_value = MagicMock()
    return mock

@pytest.fixture
def mock_transformers():
    mock_config = MagicMock()
    mock_config.architectures = ["Qwen2VLForConditionalGeneration"]
    mock_config.model_type = "qwen2_vl"
    
    mock_model = MagicMock()
    mock_model.from_pretrained.return_value = MagicMock()
    mock_model.to.return_value = mock_model  # Chainable to()
    
    return {
        "AutoConfig": MagicMock(from_pretrained=MagicMock(return_value=mock_config)),
        "AutoModel": mock_model,
        "Qwen2VLForConditionalGeneration": mock_model
    }

def test_load_vae_cpu_when_cuda_unavailable(mock_torch_cpu_false, mock_transformers):
    """Test that load_vae_cpu works correctly when CUDA is not available."""
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_false,
        "transformers": mock_transformers
    }):
        from models.vae_loader import load_vae_cpu
        
        result = load_vae_cpu("some/model/id")
        
        assert result is not None
        assert "model" in result
        assert result["device"] == "cpu"
        # Verify to('cpu') was called
        result["model"].to.assert_called_with("cpu")

def test_load_vae_cpu_forces_cpu_when_cuda_available(mock_torch_cpu_true, mock_transformers):
    """Test that load_vae_cpu forces CPU even when CUDA is available."""
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_true,
        "transformers": mock_transformers
    }):
        from models.vae_loader import load_vae_cpu
        
        result = load_vae_cpu("some/model/id")
        
        assert result is not None
        assert result["device"] == "cpu"
        # Verify to('cpu') was called despite CUDA availability
        result["model"].to.assert_called_with("cpu")

def test_load_vae_cpu_no_grad_context(mock_torch_cpu_false, mock_transformers):
    """Test that load_vae_cpu uses torch.no_grad() context."""
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_false,
        "transformers": mock_transformers
    }):
        from models.vae_loader import load_vae_cpu
        
        # Mock no_grad as a context manager
        mock_torch_cpu_false.no_grad.return_value.__enter__ = MagicMock(return_value=None)
        mock_torch_cpu_false.no_grad.return_value.__exit__ = MagicMock(return_value=False)
        
        result = load_vae_cpu("some/model/id")
        
        assert result is not None
        # Verify no_grad was used
        mock_torch_cpu_false.no_grad.assert_called()

def test_load_vae_cpu_memory_error_handling(mock_torch_cpu_false, mock_transformers):
    """Test that load_vae_cpu handles memory errors appropriately."""
    mock_model = MagicMock()
    mock_model.from_pretrained.side_effect = RuntimeError("CUDA out of memory")
    
    mock_transformers["AutoModel"] = mock_model
    
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_false,
        "transformers": mock_transformers
    }):
        from models.vae_loader import load_vae_cpu
        
        # Should raise an error if it can't load even on CPU
        with pytest.raises(RuntimeError, match="CUDA out of memory"):
            load_vae_cpu("some/model/id")

def test_check_cpu_feasibility_success(mock_torch_cpu_false, mock_transformers):
    """Test check_cpu_feasibility returns True when CPU is viable."""
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_false,
        "transformers": mock_transformers
    }):
        from models.vae_loader import check_cpu_feasibility
        
        result = check_cpu_feasibility("some/model/id")
        
        assert result["feasible"] is True
        assert result["device"] == "cpu"

def test_check_cpu_feasibility_failure(mock_torch_cpu_false, mock_transformers):
    """Test check_cpu_feasibility returns False when model is too large."""
    mock_config = MagicMock()
    mock_config.from_pretrained.side_effect = RuntimeError("Model too large for CPU memory")
    
    mock_transformers["AutoConfig"] = MagicMock(from_pretrained=MagicMock(side_effect=mock_config.from_pretrained.side_effect))
    
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_false,
        "transformers": mock_transformers
    }):
        from models.vae_loader import check_cpu_feasibility
        
        result = check_cpu_feasibility("huge/model/id")
        
        assert result["feasible"] is False
        assert "too large" in result["reason"].lower() or "error" in result["reason"].lower()

def test_trigger_model_substitution_protocol(mock_torch_cpu_false, mock_transformers):
    """Test that model substitution protocol selects a smaller candidate."""
    call_count = 0
    
    def mock_check(model_id):
        nonlocal call_count
        call_count += 1
        if "tiny" in model_id:
            return {"feasible": True, "device": "cpu"}
        return {"feasible": False, "reason": "Memory error"}
    
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_false,
        "transformers": mock_transformers
    }):
        from models import vae_loader
        vae_loader.check_cpu_feasibility = mock_check
        
        fallback = vae_loader.trigger_model_substitution_protocol()
        
        assert fallback is not None
        assert "tiny" in fallback

def test_trigger_model_substitution_protocol_no_fallback(mock_torch_cpu_false, mock_transformers):
    """Test that model substitution returns None if no candidates work."""
    def mock_check(model_id):
        return {"feasible": False, "reason": "Memory error"}
    
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_false,
        "transformers": mock_transformers
    }):
        from models import vae_loader
        vae_loader.check_cpu_feasibility = mock_check
        
        fallback = vae_loader.trigger_model_substitution_protocol()
        
        assert fallback is None

def test_run_model_availability_check_output(mock_torch_cpu_false, mock_transformers):
    """Test that run_model_availability_check writes the correct JSON file."""
    def mock_check(model_id):
        return {"model_id": model_id, "exists": True, "cpu_feasible": True}
    
    with patch.dict(sys.modules, {
        "torch": mock_torch_cpu_false,
        "transformers": mock_transformers
    }):
        from models import vae_loader
        vae_loader.check_model_availability = mock_check
        
        # Ensure output dir exists
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "model_availability.json"
        
        # Run the function
        result = vae_loader.run_model_availability_check()
        
        # Verify file exists
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "PASS"
        assert data["fallback_model_id"] == vae_loader.TARGET_MODEL_ID
        
        # Cleanup
        output_file.unlink()