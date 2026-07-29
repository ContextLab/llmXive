import pytest
import json
import os
import tempfile
import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.experiments.ablation import (
    generate_ablation_configs, 
    save_ablation_configs, 
    run_ablation_study
)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    configs_dir = tmp_path / "configs"
    results_dir = tmp_path / "results"
    configs_dir.mkdir()
    results_dir.mkdir()
    return {
        "configs": str(configs_dir),
        "results": str(results_dir)
    }

def test_ablation_study_generation(temp_output_dir):
    """Test that run_ablation_study generates the correct output schema."""
    # 1. Generate and save configs
    configs = generate_ablation_configs()
    config_path = os.path.join(temp_output_dir["configs"], "ablation_configs.json")
    save_ablation_configs(configs, config_path)
    
    # 2. Run study with minimal epochs for speed
    results_path = os.path.join(temp_output_dir["results"], "ablation_results.json")
    
    # Run with very few epochs to ensure it finishes quickly in test
    result_data = run_ablation_study(
        config_path=config_path,
        output_path=results_path,
        epochs=2,  # Minimal epochs for testing
        hidden_dim=16, # Small model
        num_layers=2
    )
    
    # 3. Verify file exists
    assert os.path.exists(results_path), "Output file ablation_results.json was not created"
    
    # 4. Verify schema
    with open(results_path, 'r') as f:
        loaded_data = json.load(f)
    
    assert "results" in loaded_data, "Missing 'results' key in output"
    assert isinstance(loaded_data["results"], list), "'results' should be a list"
    assert len(loaded_data["results"]) == 4, "Should have 4 variant results"
    
    # 5. Verify each result entry schema
    required_keys = {"variant", "mae", "time"}
    for entry in loaded_data["results"]:
        assert all(k in entry for k in required_keys), f"Missing keys in entry: {entry}"
        assert isinstance(entry["variant"], str), "variant must be string"
        assert isinstance(entry["mae"], (int, float)), "mae must be numeric"
        assert isinstance(entry["time"], (int, float)), "time must be numeric"
    
    # 6. Verify all expected variants are present
    variants = {r["variant"] for r in loaded_data["results"]}
    expected_variants = {"full", "no_recurrence", "no_inhibition", "no_homeostasis"}
    assert variants == expected_variants, f"Missing variants. Found: {variants}, Expected: {expected_variants}"

def test_ablation_study_handles_missing_config(temp_output_dir):
    """Test that run_ablation_study fails loudly if config is missing."""
    results_path = os.path.join(temp_output_dir["results"], "ablation_results.json")
    non_existent_config = os.path.join(temp_output_dir["configs"], "missing.json")
    
    with pytest.raises(FileNotFoundError):
        run_ablation_study(config_path=non_existent_config, output_path=results_path)
