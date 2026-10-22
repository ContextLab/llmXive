import json
from pathlib import Path

def test_thin_training_output_exists():
    """Verify that the thin‑training script creates a valid JSON file."""
    result_path = Path(
        "data/results/fixed_baselines/rho0.5_seed42.json"
    )
    assert result_path.is_file(), f"{result_path} does not exist"

    # Load and perform a very light sanity‑check on the JSON structure.
    with result_path.open() as f:
        data = json.load(f)

    # Required top‑level keys (a subset of the schema)
    for key in ["rho_teacher", "seed", "loss_trajectory", "final_accuracy", "final_f1", "metadata"]:
        assert key in data, f"Missing key {key} in result JSON"

    # Basic type checks
    assert isinstance(data["loss_trajectory"], list)
    assert isinstance(data["final_accuracy"], float)
    assert isinstance(data["final_f1"], float)
    assert isinstance(data["metadata"], dict)