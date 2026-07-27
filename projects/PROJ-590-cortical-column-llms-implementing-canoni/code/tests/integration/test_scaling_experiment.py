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
    """Test scaling configuration generation."""

    def test_create_scaling_configs_generates_three_variants(self):
        """Verify that 1x, 2x, and 4x variants are created."""
        configs = create_scaling_configs(base_hidden_dim=64, base_neurons=128)
        
        assert len(configs) == 3, "Should generate exactly 3 variants"
        
        # Check variant names
        names = [c.variant_name for c in configs]
        assert "1x" in names, "1x variant should exist"
        assert "2x" in names, "2x variant should exist"
        assert "4x" in names, "4x variant should exist"

    def test_scaling_factors_are_correct(self):
        """Verify scale factors are 1.0, 2.0, 4.0."""
        configs = create_scaling_configs()
        factors = [c.scale_factor for c in configs]
        
        assert factors == [1.0, 2.0, 4.0], "Scale factors should be [1.0, 2.0, 4.0]"

    def test_dimensions_scale_deterministically(self):
        """Verify hidden_dim and neurons_per_layer scale correctly."""
        configs = create_scaling_configs(base_hidden_dim=64, base_neurons=128)
        
        # 1x: 64, 128
        assert configs[0].hidden_dim == 64
        assert configs[0].neurons_per_layer == 128
        
        # 2x: 128, 256
        assert configs[1].hidden_dim == 128
        assert configs[1].neurons_per_layer == 256
        
        # 4x: 256, 512
        assert configs[2].hidden_dim == 256
        assert configs[2].neurons_per_layer == 512


class TestScalingModelCreation:
    """Test model creation from scaling configs."""

    def test_create_model_from_config_returns_hybrid_network(self):
        """Verify model creation returns correct type."""
        config = create_scaling_configs()[0]
        model = create_model_from_config(config)
        
        assert isinstance(model, HybridNetwork), "Should return HybridNetwork instance"

    def test_model_parameters_scale_with_config(self):
        """Verify parameter count increases with scaling."""
        configs = create_scaling_configs()
        
        params = []
        for config in configs:
            model = create_model_from_config(config)
            param_count = sum(p.numel() for p in model.parameters())
            params.append(param_count)
        
        # Parameters should increase with scale
        assert params[0] < params[1] < params[2], \
            "Parameter count should increase: 1x < 2x < 4x"


class TestScalingVariantTraining:
    """Test training of individual scaling variants."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_train_scaling_variant_completes(self, temp_output_dir):
        """Verify training completes without error for 1x variant."""
        configs = create_scaling_configs()
        config_1x = configs[0]
        
        result = train_scaling_variant(
            config=config_1x,
            train_epochs=2,  # Minimal epochs for speed
            batch_size=32,
            learning_rate=1e-3
        )
        
        assert result.variant_name == "1x"
        assert result.train_mae >= 0.0
        assert result.test_mae >= 0.0
        assert result.training_time_seconds > 0
        assert result.num_parameters > 0

    def test_train_scaling_variant_returns_valid_result(self, temp_output_dir):
        """Verify result structure matches ScalingResult schema."""
        configs = create_scaling_configs()
        config = configs[0]
        
        result = train_scaling_variant(
            config=config,
            train_epochs=2,
            batch_size=32
        )
        
        # Check all required fields
        assert hasattr(result, 'variant_name')
        assert hasattr(result, 'scale_factor')
        assert hasattr(result, 'num_parameters')
        assert hasattr(result, 'train_mae')
        assert hasattr(result, 'test_mae')
        assert hasattr(result, 'training_time_seconds')
        assert hasattr(result, 'config')
        
        # Convert to dict and verify keys
        result_dict = result.to_dict()
        required_keys = ['variant_name', 'scale_factor', 'num_parameters',
                       'train_mae', 'test_mae', 'training_time_seconds', 'config']
        for key in required_keys:
            assert key in result_dict, f"Missing key: {key}"


class TestScalingResults:
    """Test scaling study execution and result persistence."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_run_scaling_study_saves_json(self, temp_output_dir):
        """Verify scaling study saves results to JSON file."""
        output_path = os.path.join(temp_output_dir, "scaling_results.json")
        
        # Run study with minimal epochs
        results = run_scaling_study(
            output_path=output_path,
            base_hidden_dim=64,
            base_neurons=128,
            train_epochs=2,
            batch_size=32
        )
        
        # Verify file exists
        assert os.path.exists(output_path), "Results file should exist"
        
        # Verify JSON is valid
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Results should be a list"
        assert len(data) == 3, "Should have 3 variants"

    def test_run_scaling_study_results_match_schema(self, temp_output_dir):
        """Verify saved results match expected schema."""
        output_path = os.path.join(temp_output_dir, "scaling_results.json")
        
        results = run_scaling_study(
            output_path=output_path,
            train_epochs=2,
            batch_size=32
        )
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Check each result has required fields
        required_fields = ['variant_name', 'scale_factor', 'num_parameters',
                         'train_mae', 'test_mae', 'training_time_seconds', 'config']
        
        for result in data:
            for field in required_fields:
                assert field in result, f"Missing field: {field}"
        
        # Verify variants are present
        variant_names = [r['variant_name'] for r in data]
        assert "1x" in variant_names
        assert "2x" in variant_names
        assert "4x" in variant_names

    def test_scaling_trend_is_observed(self, temp_output_dir):
        """Verify that scaling shows expected trend (more params, different MAE)."""
        output_path = os.path.join(temp_output_dir, "scaling_results.json")
        
        results = run_scaling_study(
            output_path=output_path,
            train_epochs=2,
            batch_size=32
        )
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Sort by scale factor
        data_sorted = sorted(data, key=lambda x: x['scale_factor'])
        
        # Verify parameter count increases
        params = [r['num_parameters'] for r in data_sorted]
        assert params[0] < params[1] < params[2], \
            "Parameter count should increase with scale"

    def test_deterministic_seeding(self, temp_output_dir):
        """Verify that same seed produces consistent results."""
        output_path_1 = os.path.join(temp_output_dir, "scaling_results_1.json")
        output_path_2 = os.path.join(temp_output_dir, "scaling_results_2.json")
        
        # Run twice with same config
        run_scaling_study(
            output_path=output_path_1,
            train_epochs=2,
            batch_size=32
        )
        
        run_scaling_study(
            output_path=output_path_2,
            train_epochs=2,
            batch_size=32
        )
        
        with open(output_path_1, 'r') as f:
            data_1 = json.load(f)
        
        with open(output_path_2, 'r') as f:
            data_2 = json.load(f)
        
        # Results should be identical due to deterministic seeding
        for r1, r2 in zip(data_1, data_2):
            assert r1['train_mae'] == r2['train_mae'], \
                "Train MAE should be deterministic"
            assert r1['test_mae'] == r2['test_mae'], \
                "Test MAE should be deterministic"
