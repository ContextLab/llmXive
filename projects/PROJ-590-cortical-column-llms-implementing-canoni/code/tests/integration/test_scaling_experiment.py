"""
Integration tests for the scaling experiment (T027).
Verifies that scaling configurations are generated correctly,
models are created, and results are saved to the expected path.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
import torch

from src.experiments.scaling import (
    ScalingConfig,
    ScalingResult,
    create_scaling_configs,
    create_model_from_config,
    train_scaling_variant,
    run_scaling_study
)
from src.models.hybrid_network import HybridNetwork


class TestScalingConfigs:
    """Tests for scaling configuration generation."""

    def test_create_scaling_configs_returns_three_variants(self):
        """Verify that create_scaling_configs returns 1x, 2x, and 4x variants."""
        configs = create_scaling_configs()
        
        assert len(configs) == 3
        
        names = [c.name for c in configs]
        assert "1x" in names
        assert "2x" in names
        assert "4x" in names

    def test_scaling_configs_have_correct_neurons_scaling(self):
        """Verify that neurons_per_layer scales correctly (1x, 2x, 4x)."""
        base_neurons = 128
        configs = create_scaling_configs(base_config={'hidden_dim': 64, 'neurons_per_layer': base_neurons})
        
        neurons = {c.name: c.neurons_per_layer for c in configs}
        
        assert neurons["1x"] == base_neurons
        assert neurons["2x"] == base_neurons * 2
        assert neurons["4x"] == base_neurons * 4

    def test_scaling_configs_have_correct_column_counts(self):
        """Verify that column counts match the variant name."""
        configs = create_scaling_configs()
        
        for config in configs:
            expected_columns = int(config.name.replace("x", ""))
            assert config.columns == expected_columns


class TestScalingModelCreation:
    """Tests for model creation from scaling configs."""

    def test_create_model_from_config_returns_hybrid_network(self):
        """Verify that create_model_from_config returns a HybridNetwork instance."""
        config = ScalingConfig(
            name="1x",
            columns=1,
            hidden_dim=64,
            neurons_per_layer=128,
            num_layers=4
        )
        
        model = create_model_from_config(config)
        
        assert isinstance(model, HybridNetwork)

    def test_model_parameter_count_increases_with_scaling(self):
        """Verify that larger variants have more parameters."""
        configs = create_scaling_configs()
        
        param_counts = {}
        for config in configs:
            model = create_model_from_config(config)
            param_counts[config.name] = sum(p.numel() for p in model.parameters())
        
        # 4x should have more params than 2x, which should have more than 1x
        assert param_counts["4x"] > param_counts["2x"] > param_counts["1x"]


class TestScalingVariantTraining:
    """Tests for training individual scaling variants."""

    def test_train_scaling_variant_returns_scaling_result(self):
        """Verify that train_scaling_variant returns a ScalingResult object."""
        config = ScalingConfig(
            name="1x",
            columns=1,
            hidden_dim=64,
            neurons_per_layer=128,
            num_layers=4
        )
        
        result = train_scaling_variant(config, train_epochs=2, batch_size=16)
        
        assert isinstance(result, ScalingResult)
        assert result.columns == "1x"
        assert result.params > 0
        assert result.mae >= 0
        assert result.time > 0

    def test_train_scaling_variant_with_different_variants(self):
        """Verify training works for all scaling variants."""
        configs = create_scaling_configs()
        
        for config in configs:
            result = train_scaling_variant(config, train_epochs=2, batch_size=16)
            
            assert result.columns == config.name
            assert result.params > 0
            assert result.mae >= 0
            assert result.time > 0


class TestScalingResults:
    """Tests for scaling results output and validation."""

    def test_run_scaling_study_creates_output_file(self):
        """Verify that run_scaling_study creates the expected output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "scaling_results.json")
            
            results = run_scaling_study(
                output_path=output_path,
                train_epochs=2,
                batch_size=16
            )
            
            assert os.path.exists(output_path)
            
            # Verify file is valid JSON
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert "variants" in loaded
            assert len(loaded["variants"]) == 3

    def test_scaling_results_schema(self):
        """Verify the schema of scaling results matches requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "scaling_results.json")
            
            results = run_scaling_study(
                output_path=output_path,
                train_epochs=2,
                batch_size=16
            )
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            # Verify top-level structure
            assert isinstance(loaded, dict)
            assert "variants" in loaded
            assert isinstance(loaded["variants"], list)
            assert len(loaded["variants"]) == 3
            
            # Verify each variant has required fields
            required_fields = ["columns", "params", "mae", "time"]
            for variant in loaded["variants"]:
                for field_name in required_fields:
                    assert field_name in variant, f"Missing field '{field_name}' in variant {variant.get('columns')}"
                
                # Verify types
                assert isinstance(variant["columns"], str)
                assert isinstance(variant["params"], int)
                assert isinstance(variant["mae"], float)
                assert isinstance(variant["time"], float)

    def test_scaling_results_file_at_default_path(self):
        """Verify that run_scaling_study can write to the default path."""
        # Use a temporary directory to avoid cluttering the repo
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "results", "scaling_results.json")
            
            results = run_scaling_study(
                output_path=output_path,
                train_epochs=2,
                batch_size=16
            )
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert len(loaded["variants"]) == 3

    def test_scaling_results_contain_all_variants(self):
        """Verify that all three variants (1x, 2x, 4x) are present in results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "scaling_results.json")
            
            run_scaling_study(
                output_path=output_path,
                train_epochs=2,
                batch_size=16
            )
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            variant_names = [v["columns"] for v in loaded["variants"]]
            
            assert "1x" in variant_names
            assert "2x" in variant_names
            assert "4x" in variant_names
