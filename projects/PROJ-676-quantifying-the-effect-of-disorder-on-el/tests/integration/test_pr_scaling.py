import json
import os
import pytest
from pathlib import Path
from code.config import get_config

def test_scaling_fits_existence():
    """
    Integration test for finite-size scaling workflow.
    Asserts existence of data/processed/scaling_fits.json.
    """
    config = get_config()
    output_path = Path(config.DATA_DIR) / "processed" / "scaling_fits.json"
    
    assert output_path.exists(), f"scaling_fits.json not found at {output_path}"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "scaling_fits.json must be a list"
    assert len(data) > 0, "scaling_fits.json must contain at least one result"

def test_scaling_fits_structure():
    """
    Validates the structure of the scaling fits data.
    Ensures each entry contains required keys: disorder_width, xi, uncertainty, p_value.
    """
    config = get_config()
    output_path = Path(config.DATA_DIR) / "processed" / "scaling_fits.json"
    
    if not output_path.exists():
        pytest.skip("scaling_fits.json does not exist yet; run the pipeline first.")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    required_keys = {"disorder_width", "xi", "uncertainty", "p_value"}
    
    for i, entry in enumerate(data):
        assert isinstance(entry, dict), f"Entry {i} must be a dictionary"
        missing_keys = required_keys - set(entry.keys())
        assert not missing_keys, f"Entry {i} is missing required keys: {missing_keys}"
        
        # Validate numeric types
        assert isinstance(entry["disorder_width"], (int, float)), "disorder_width must be numeric"
        assert isinstance(entry["xi"], (int, float)), "xi must be numeric"
        assert isinstance(entry["uncertainty"], (int, float)), "uncertainty must be numeric"
        assert isinstance(entry["p_value"], (int, float)), "p_value must be numeric"

def test_scaling_fits_plot_exists():
    """
    Validates that the diagnostic plot for PR scaling exists.
    """
    config = get_config()
    plot_path = Path(config.DATA_DIR) / "processed" / "pr_scaling_plot.png"
    
    assert plot_path.exists(), f"pr_scaling_plot.png not found at {plot_path}"
    
    # Basic check that the file is not empty
    assert plot_path.stat().st_size > 0, "pr_scaling_plot.png is empty"

def test_residues_log_exists():
    """
    Validates that the residuals log exists as per T017b requirements.
    """
    config = get_config()
    log_path = Path(config.DATA_DIR) / "metadata" / "residuals.json"
    
    assert log_path.exists(), f"residuals.json not found at {log_path}"
    
    # Verify it's not empty
    assert log_path.stat().st_size > 0, "residuals.json is empty"

def test_bonferroni_results_exist():
    """
    Validates that the Bonferroni correction results exist as per T015 requirements.
    """
    config = get_config()
    output_path = Path(config.DATA_DIR) / "processed" / "bonferroni_results.json"
    
    assert output_path.exists(), f"bonferroni_results.json not found at {output_path}"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, dict), "bonferroni_results.json must be a dictionary"
    assert "corrected_alpha" in data, "bonferroni_results.json must contain 'corrected_alpha'"
    assert "results" in data, "bonferroni_results.json must contain 'results'"