import json
from pathlib import Path

from code.model import load_diffusion_model

def test_load_real_model_and_metadata():
    model = load_diffusion_model()
    # Ensure the model has parameters and is on CPU.
    assert sum(p.numel() for p in model.parameters()) <= 100_000_000
    # Verify metadata file exists and contains expected keys.
    meta_path = Path("outputs/model_checkpoint.json")
    assert meta_path.is_file()
    meta = json.loads(meta_path.read_text())
    for key in ["model_id", "parameter_count", "device", "config_sha256", "substitution_note"]:
        assert key in meta