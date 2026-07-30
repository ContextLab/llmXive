import pytest
import json
import os
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path if not already
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.experiments.ablation import (
    generate_ablation_configs,
    save_ablation_configs,
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
    Test that run_ablation_study generates the expected output file
    and schema.
    """
    config_path = os.path.join(temp_output_dir, "ablation_configs.json")
    output_path = os.path.join(temp_output_dir, "ablation_results.json")

    # Generate and save configs
    configs = generate_ablation_configs()
    save_ablation_configs(configs, config_path)

    # Verify config file exists and has correct structure
    assert os.path.exists(config_path)
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    assert "variants" in config_data
    assert len(config_data["variants"]) == 4
    
    variant_names = {v["name"] for v in config_data["variants"]}
    expected_names = {"full", "no_recurrence", "no_inhibition", "no_homeostasis"}
    assert variant_names == expected_names

    # Mock the training functions to avoid actual training during unit test
    # We patch run_training and calculate_mae to return deterministic values
    with patch('src.experiments.ablation.run_training') as mock_run_training, \
         patch('src.experiments.ablation.calculate_mae') as mock_calc_mae, \
         patch('src.experiments.ablation.create_ablated_hybrid_network') as mock_create_model:
        
        mock_run_training.return_value = {"mae": 0.05}
        mock_calc_mae.return_value = 0.05
        mock_create_model.return_value = MagicMock()

        # Run the study
        results = run_ablation_study(
            base_model_config={"hidden_dim": 32},
            config_path=config_path,
            output_path=output_path
        )

        # Verify output file exists
        assert os.path.exists(output_path)

        # Verify output schema
        with open(output_path, 'r') as f:
            result_data = json.load(f)

        assert "results" in result_data
        assert len(result_data["results"]) == 4

        for res in result_data["results"]:
            assert "variant" in res
            assert "mae" in res
            assert "time" in res
            assert isinstance(res["mae"], float)
            assert isinstance(res["time"], float)

        # Verify all expected variants are present
        result_names = {r["variant"] for r in result_data["results"]}
        assert result_names == expected_names

def test_ablation_study_handles_missing_config(temp_output_dir):
    """
    Test that run_ablation_study generates configs if the file is missing.
    """
    output_path = os.path.join(temp_output_dir, "ablation_results.json")

    with patch('src.experiments.ablation.run_training') as mock_run_training, \
         patch('src.experiments.ablation.calculate_mae') as mock_calc_mae, \
         patch('src.experiments.ablation.create_ablated_hybrid_network') as mock_create_model:
        
        mock_run_training.return_value = {"mae": 0.05}
        mock_calc_mae.return_value = 0.05
        mock_create_model.return_value = MagicMock()

        # Run study without config file existing
        results = run_ablation_study(
            base_model_config={"hidden_dim": 32},
            config_path=os.path.join(temp_output_dir, "nonexistent.json"),
            output_path=output_path
        )

        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            result_data = json.load(f)
        
        assert len(result_data["results"]) == 4