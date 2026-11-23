import pytest
import json
import os
import tempfile
import sys
from pathlib import Path
import torch
import numpy as np

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.experiments.ablation import (
    generate_ablation_configs,
    save_ablation_configs,
    load_ablation_configs,
    run_ablation_study,
    AblationConfig
)
from src.data.benchmarks import generate_training_data, generate_test_data

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_ablation_study_generation(temp_output_dir):
    """
    Test that run_ablation_study generates the required JSON artifact
    with the correct schema and all three variants.
    """
    config_path = os.path.join(temp_output_dir, "ablation_configs.json")
    output_path = os.path.join(temp_output_dir, "ablation_results.json")

    # Generate and save configs
    configs = generate_ablation_configs()
    save_ablation_configs(configs, config_path)

    # Verify config content
    loaded_configs = load_ablation_configs(config_path)
    assert len(loaded_configs) == 3
    names = {c.name for c in loaded_configs}
    assert names == {"full", "no_recurrence", "no_inhibition"}

    # Run a minimal study (small epochs, small data)
    # We mock the data generation to be very fast
    # But we use the real function with small seed
    import src.experiments.ablation as ablation_module
    
    # Patch data generation to be fast if needed, or just run with small defaults
    # The real function might take time, so we rely on the fact that it runs.
    # We will run with 1 epoch to speed up.
    
    result = run_ablation_study(
        config_path=config_path,
        output_path=output_path,
        seed=42,
        epochs=1,
        lr=0.001
    )

    # Verify output file exists
    assert os.path.exists(output_path), f"Output file {output_path} was not created."

    # Verify schema
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 3

    for r in data["results"]:
        assert "variant" in r
        assert "mae" in r
        assert "time" in r
        assert "seed" in r
        assert isinstance(r["mae"], float)
        assert isinstance(r["time"], float)
        assert isinstance(r["seed"], int)

    # Verify all variants are present
    result_names = {r["variant"] for r in data["results"]}
    assert result_names == {"full", "no_recurrence", "no_inhibition"}

def test_ablation_study_handles_missing_config(temp_output_dir):
    """
    Test that run_ablation_study generates default configs if the config file is missing.
    """
    output_path = os.path.join(temp_output_dir, "ablation_results.json")
    missing_config_path = os.path.join(temp_output_dir, "missing_configs.json")

    # Run study with missing config file
    result = run_ablation_study(
        config_path=missing_config_path,
        output_path=output_path,
        seed=42,
        epochs=1
    )

    # Verify output file exists
    assert os.path.exists(output_path)

    # Verify it used the default configs (3 variants)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data["results"]) == 3
    result_names = {r["variant"] for r in data["results"]}
    assert result_names == {"full", "no_recurrence", "no_inhibition"}

    # Verify the config file was created
    assert os.path.exists(missing_config_path)
    loaded = load_ablation_configs(missing_config_path)
    assert len(loaded) == 3
