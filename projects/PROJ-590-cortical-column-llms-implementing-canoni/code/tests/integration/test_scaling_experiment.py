"""
Integration tests for the scaling experiment (T026).

Tests verify:
1. Scaling configs are generated correctly (1x, 2x, 4x)
2. Models can be created from configs
3. Training completes without errors
4. Results JSON is generated with correct schema
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
    count_parameters,
    train_scaling_variant,
    run_scaling_study
)


class TestScalingConfigs:
    """Test scaling configuration generation."""

    def test_create_scaling_configs_defaults(self):
        """Test that default configs generate 1x, 2x, 4x variants."""
        configs = create_scaling_configs()
        
        assert len(configs) == 3
        
        # Check scale factors
        scale_factors = [c.scale_factor for c in configs]
        assert 1.0 in scale_factors
        assert 2.0 in scale_factors
        assert 4.0 in scale_factors
        
        # Check base config values
        base_config = [c for c in configs if c.scale_factor == 1.0][0]
        assert base_config.hidden_dim == 64
        assert base_config.neurons_per_layer == 128
        assert base_config.num_columns == 1

    def test_create_scaling_configs_custom(self):
        """Test that custom base config is applied correctly."""
        custom_base = {
            "hidden_dim": 32,
            "neurons_per_layer": 64,
            "num_columns": 2,
            "num_layers": 2,
            "epochs": 5,
            "batch_size": 16,
            "learning_rate": 0.0005,
            "dropout": 0.2,
            "seed": 123
        }
        
        configs = create_scaling_configs(custom_base)
        
        assert len(configs) == 3
        
        # Check 2x variant
        config_2x = [c for c in configs if c.scale_factor == 2.0][0]
        assert config_2x.hidden_dim == 64  # 32 * 2
        assert config_2x.neurons_per_layer == 128  # 64 * 2
        assert config_2x.num_columns == 4  # 2 * 2

class TestScalingModelCreation:
    """Test model creation from scaling configs."""

    def test_create_model_from_config(self):
        """Test that a model can be created from a scaling config."""
        config = ScalingConfig(
            name="test_1x",
            scale_factor=1.0,
            hidden_dim=64,
            neurons_per_layer=128,
            num_columns=1,
            num_layers=3
        )
        
        model = create_model_from_config(config)
        
        assert model is not None
        assert isinstance(model, torch.nn.Module)
        
        # Check parameter count is positive
        params = count_parameters(model)
        assert params > 0

    def test_model_parameter_scaling(self):
        """Test that parameter count scales approximately with config."""
        config_1x = ScalingConfig(
            name="test_1x",
            scale_factor=1.0,
            hidden_dim=64,
            neurons_per_layer=128,
            num_columns=1,
            num_layers=3
        )
        
        config_2x = ScalingConfig(
            name="test_2x",
            scale_factor=2.0,
            hidden_dim=128,
            neurons_per_layer=256,
            num_columns=2,
            num_layers=3
        )
        
        model_1x = create_model_from_config(config_1x)
        model_2x = create_model_from_config(config_2x)
        
        params_1x = count_parameters(model_1x)
        params_2x = count_parameters(model_2x)
        
        # 2x config should have significantly more parameters
        # Exact ratio depends on architecture, but should be > 2x
        assert params_2x > params_1x
        assert params_2x / params_1x > 2.0


class TestScalingVariantTraining:
    """Test training of individual scaling variants."""

    def test_train_scaling_variant(self):
        """Test that a single variant can be trained."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScalingConfig(
                name="test_1x",
                scale_factor=1.0,
                hidden_dim=64,
                neurons_per_layer=128,
                num_columns=1,
                num_layers=3,
                epochs=2,  # Minimal epochs for testing
                batch_size=16,
                learning_rate=0.001,
                dropout=0.1,
                seed=42
            )
            
            result = train_scaling_variant(config, output_dir=tmpdir)
            
            assert result is not None
            assert isinstance(result, ScalingResult)
            assert result.name == "test_1x"
            assert result.num_params > 0
            assert result.train_mae >= 0
            assert result.test_mae >= 0
            assert result.training_time > 0

    def test_train_scaling_variant_reproducibility(self):
        """Test that training is reproducible with same seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScalingConfig(
                name="test_repro",
                scale_factor=1.0,
                hidden_dim=64,
                neurons_per_layer=128,
                num_columns=1,
                num_layers=3,
                epochs=2,
                batch_size=16,
                learning_rate=0.001,
                dropout=0.1,
                seed=42
            )
            
            result1 = train_scaling_variant(config, output_dir=tmpdir)
            
            # Reset seed and run again
            torch.manual_seed(42)
            result2 = train_scaling_variant(config, output_dir=tmpdir)
            
            # Results should be identical
            assert result1.train_mae == result2.train_mae
            assert result1.test_mae == result2.test_mae


class TestScalingResults:
    """Test scaling study execution and result generation."""

    def test_run_scaling_study(self):
        """Test that the full scaling study runs and generates results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "scaling_results.json")
            
            # Run with minimal epochs for testing
            base_config = {
                "hidden_dim": 64,
                "neurons_per_layer": 128,
                "num_columns": 1,
                "num_layers": 3,
                "epochs": 2,
                "batch_size": 16,
                "learning_rate": 0.001,
                "dropout": 0.1,
                "seed": 42
            }
            
            results = run_scaling_study(base_config=base_config, output_path=output_path)
            
            # Check results
            assert len(results) == 3
            
            # Check output file exists and has correct schema
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "variants" in data
            assert len(data["variants"]) == 3
            
            # Check schema for each variant
            for variant in data["variants"]:
                assert "columns" in variant
                assert "params" in variant
                assert "mae" in variant
                assert "time" in variant
                
                # Check types
                assert isinstance(variant["columns"], str)
                assert isinstance(variant["params"], int)
                assert isinstance(variant["mae"], float)
                assert isinstance(variant["time"], float)

    def test_scaling_results_schema(self):
        """Test that results match the required schema from T026."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "scaling_results.json")
            
            base_config = {
                "hidden_dim": 64,
                "neurons_per_layer": 128,
                "num_columns": 1,
                "num_layers": 3,
                "epochs": 2,
                "batch_size": 16,
                "learning_rate": 0.001,
                "dropout": 0.1,
                "seed": 42
            }
            
            run_scaling_study(base_config=base_config, output_path=output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Required schema: {"variants": [{"columns": str, "params": int, "mae": float, "time": float}]}
            assert isinstance(data, dict)
            assert "variants" in data
            assert isinstance(data["variants"], list)
            
            for variant in data["variants"]:
                assert isinstance(variant, dict)
                assert "columns" in variant
                assert "params" in variant
                assert "mae" in variant
                assert "time" in variant
              
                # Type checks
                assert isinstance(variant["columns"], str)
                assert isinstance(variant["params"], int)
                assert isinstance(variant["mae"], float)
                assert isinstance(variant["time"], float)
                
                # Value constraints
                assert variant["params"] > 0
                assert variant["mae"] >= 0
                assert variant["time"] > 0

    def test_scaling_study_variants(self):
        """Test that all three variants (1x, 2x, 4x) are included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "scaling_results.json")
            
            base_config = {
                "hidden_dim": 64,
                "neurons_per_layer": 128,
                "num_columns": 1,
                "num_layers": 3,
                "epochs": 2,
                "batch_size": 16,
                "learning_rate": 0.001,
                "dropout": 0.1,
                "seed": 42
            }
            
            run_scaling_study(base_config=base_config, output_path=output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            variant_names = [v["columns"] for v in data["variants"]]
            
            assert "scale_1x" in variant_names
            assert "scale_2x" in variant_names
            assert "scale_4x" in variant_names