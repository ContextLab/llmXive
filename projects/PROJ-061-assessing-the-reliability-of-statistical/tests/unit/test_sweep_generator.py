"""
Unit tests for the sweep generator logic (T021b).

Verifies that configuration generation and iteration logic works correctly
before integration with the main pipeline.
"""
import pytest
import json
from pathlib import Path
import tempfile

# Import the module under test
from code.sweep_generator import (
    get_sweep_configs,
    run_sweep_for_violation,
    generate_all_sweep_configs,
    save_sweep_configs
)
from code.config import VIOLATION_SWEEP_CONFIG

class TestSweepConfigGeneration:
    """Tests for configuration retrieval and generation."""

    def test_get_sweep_configs_heavy_tailed(self):
        """Verify heavy-tailed sweep returns correct df values."""
        configs = get_sweep_configs("heavy_tailed")
        
        assert len(configs) == len(VIOLATION_SWEEP_CONFIG["heavy_tailed"]["values"])
        
        expected_values = VIOLATION_SWEEP_CONFIG["heavy_tailed"]["values"]
        for i, cfg in enumerate(configs):
            assert cfg["violation_type"] == "heavy_tailed"
            assert cfg["parameter_name"] == "df"
            assert cfg["parameter_value"] == expected_values[i]

    def test_get_sweep_configs_ar1(self):
        """Verify AR(1) sweep returns correct rho values."""
        configs = get_sweep_configs("ar1_autocorrelation")
        
        assert len(configs) == len(VIOLATION_SWEEP_CONFIG["ar1_autocorrelation"]["values"])
        
        expected_values = VIOLATION_SWEEP_CONFIG["ar1_autocorrelation"]["values"]
        for i, cfg in enumerate(configs):
            assert cfg["violation_type"] == "ar1_autocorrelation"
            assert cfg["parameter_name"] == "rho"
            assert cfg["parameter_value"] == expected_values[i]

    def test_get_sweep_configs_heterogeneity(self):
        """Verify effect size heterogeneity includes fixed parameters."""
        configs = get_sweep_configs("effect_size_heterogeneity")
        
        # Check that fixed parameters are included in each config
        for cfg in configs:
            assert cfg["violation_type"] == "effect_size_heterogeneity"
            assert cfg["parameter_name"] == "mixing_ratio"
            assert "fixed_separation" in cfg
            assert cfg["fixed_separation"] == 1.5
            assert "fixed_ratio" in cfg
            assert cfg["fixed_ratio"] == 0.2

    def test_invalid_violation_type_raises_error(self):
        """Verify that an unknown violation type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown violation type"):
            get_sweep_configs("invalid_type")

    def test_generate_all_sweep_configs(self):
        """Verify total count of all sweep configurations."""
        all_configs = generate_all_sweep_configs()
        
        expected_count = sum(
            len(VIOLATION_SWEEP_CONFIG[vt]["values"]) 
            for vt in VIOLATION_SWEEP_CONFIG
        )
        assert len(all_configs) == expected_count

class TestSweepIterator:
    """Tests for the generator-based sweep iteration."""

    def test_run_sweep_for_violation_generator(self):
        """Verify the sweep generator yields correct number of configs."""
        count = 0
        for cfg in run_sweep_for_violation("ar1_autocorrelation"):
            count += 1
            assert isinstance(cfg, dict)
            assert "violation_type" in cfg
            assert "parameter_value" in cfg
        
        expected = len(VIOLATION_SWEEP_CONFIG["ar1_autocorrelation"]["values"])
        assert count == expected

class TestSweepPersistence:
    """Tests for saving sweep configurations."""

    def test_save_sweep_configs_creates_file(self):
        """Verify that save_sweep_configs creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sweep.json"
            save_sweep_configs(str(output_path))
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list)
            assert len(data) > 0
            assert "violation_type" in data[0]
            assert "parameter_value" in data[0]

    def test_save_sweep_configs_content(self):
        """Verify the saved JSON contains expected violation types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sweep.json"
            save_sweep_configs(str(output_path))
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            violation_types = {cfg["violation_type"] for cfg in data}
            assert "heavy_tailed" in violation_types
            assert "ar1_autocorrelation" in violation_types
            assert "effect_size_heterogeneity" in violation_types
