"""Tests for ``code/model.py``."""

import json
from pathlib import Path

import torch

from code.model import load_diffusion_model

def test_load_diffusion_model_returns_module_and_forward():
    """The loader must return a torch.nn.Module that runs on CPU."""
    model = load_diffusion_model()
    assert isinstance(model, torch.nn.Module)

    # Dummy input – small tensor to keep runtime < 2 s.
    dummy = torch.randn(2, 5)
    out = model(dummy)

    # Identity mapping: output should equal input.
    assert torch.allclose(out, dummy)

    # Verify that the metadata JSON was written.
    meta_path = Path("outputs/model_checkpoint.json")
    assert meta_path.is_file()

    meta = json.loads(meta_path.read_text())
    assert "model_id" in meta and "checkpoint_path" in meta
    # The checkpoint path should point to an existing file.
    assert Path(meta["checkpoint_path"]).is_file()
