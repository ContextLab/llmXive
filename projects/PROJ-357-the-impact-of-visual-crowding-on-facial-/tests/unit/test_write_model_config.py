"""
Unit tests for T037: write_model_config.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.write_model_config import generate_model_config

@pytest.fixture
def sample_results_data():
    return {
        "convergence_status": "converged",
        "model_type": "glmm",
        "fixed_effects": {
            "spatial_frequency_energy": {"coef": -0.5, "p_value": 0.03},
            "local_contrast_variance": {"coef": 0.2, "p_value": 0.15}
        },
        "random_effects_structure": {"participant_id": 1, "stimulus_id": 1},
        "fdr_applied": True,
        "fdr_threshold": 0.05,
        "sample_size": 1000,
        "n_observations": 5000,
        "n_stimuli": 500,
        "n_participants": 10
    }

def test_generate_model_config_creates_file(sample_results_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        results_path = tmpdir_path / "regression_results.json"
        output_path = tmpdir_path / "model_config.yaml"

        # Write sample results
        with open(results_path, 'w') as f:
            json.dump(sample_results_data, f)

        # Run generation
        config = generate_model_config(results_path, output_path)

        # Assertions
        assert output_path.exists(), "Output file was not created"
        
        # Verify YAML content
        with open(output_path, 'r') as f:
            loaded_config = yaml.safe_load(f)

        assert "hyperparameters" in loaded_config
        assert "model_diagnostics" in loaded_config
        assert "project_id" in loaded_config
        assert loaded_config["project_id"] == "PROJ-357-the-impact-of-visual-crowding-on-facial-"
        
        # Check specific values
        assert loaded_config["model_diagnostics"]["convergence_status"] == "converged"
        assert loaded_config["model_diagnostics"]["n_participants"] == 10
        assert "random_seed" in loaded_config["hyperparameters"]

def test_generate_model_config_missing_results():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        results_path = tmpdir_path / "nonexistent.json"
        output_path = tmpdir_path / "model_config.yaml"

        with pytest.raises(FileNotFoundError):
            generate_model_config(results_path, output_path)
