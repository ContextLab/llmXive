import pytest
import json
import os
import tempfile
import sys
from pathlib import Path
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.ablation import generate_ablation_configs, run_ablation_study, AblationConfig

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_ablation_study_generation(temp_output_dir):
    """
    Test that run_ablation_study generates the required output file
    with the correct schema.
    """
    configs_path = os.path.join(temp_output_dir, "ablation_configs.json")
    output_path = os.path.join(temp_output_dir, "ablation_results.json")

    # Generate configs first
    generate_ablation_configs(configs_path)
    assert os.path.exists(configs_path), "Config file not generated"

    # Run study
    # Note: This might take a few seconds. 
    # We assume the training logic is fast enough for unit/integration testing.
    try:
        results = run_ablation_study(configs_path, output_path)
    except Exception as e:
        pytest.fail(f"run_ablation_study failed: {e}")

    # Verify output file exists
    assert os.path.exists(output_path), "Output file not generated"

    # Verify schema
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "results" in data, "Missing 'results' key"
    assert isinstance(data["results"], list), "'results' must be a list"
    assert len(data["results"]) == 3, "Expected 3 variants"

    required_keys = {"variant", "mae", "time", "seed"}
    for item in data["results"]:
        assert set(item.keys()) == required_keys, f"Item missing keys: {item.keys()}"
        assert isinstance(item["variant"], str)
        assert isinstance(item["mae"], float)
        assert isinstance(item["time"], float)
        assert isinstance(item["seed"], int)

def test_ablation_study_handles_missing_config(temp_output_dir):
    """
    Test that run_ablation_study raises an error if config file is missing.
    """
    output_path = os.path.join(temp_output_dir, "ablation_results.json")
    missing_config = os.path.join(temp_output_dir, "missing.json")

    with pytest.raises(FileNotFoundError):
        run_ablation_study(missing_config, output_path)