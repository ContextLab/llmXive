"""
Integration tests for scaling experiments.

Verifies that scaling configurations are created correctly
and that the training pipeline works for scaled models.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
import torch

from src.experiments.scaling import (
    create_scaling_configs,
    ScalingConfig,
    ScalingResult,
    create_model_from_config,
    train_scaling_variant
)
from src.models.hybrid_network import HybridNetwork

class TestScalingConfigs:
    """Tests for scaling configuration generation."""
    
    def test_create_scaling_configs_returns_three_variants(self):
        """Verify that 1x, 2x, 4x configurations are created."""
        configs = create_scaling_configs()
        
        assert len(configs) == 3, "Should create exactly 3 scaling configurations"
        
        multipliers = [c.multiplier for c in configs]
        assert 1.0 in multipliers, "Should include 1x configuration"
        assert 2.0 in multipliers, "Should include 2x configuration"
        assert 4.0 in multipliers, "Should include 4x configuration"
    
    def test_base_configuration_correct(self):
        """Verify base (1x) configuration has correct parameters."""
        configs = create_scaling_configs()
        base_config = next(c for c in configs if c.multiplier == 1.0)
        
        assert base_config.column_count == 1
        assert base_config.hidden_dim == 64
        assert base_config.neurons_per_layer == 128
    
    def test_scaled_configurations_deterministic(self):
        """Verify that 2x and 4x configurations scale deterministically."""
        configs = create_scaling_configs()
        
        config_2x = next(c for c in configs if c.multiplier == 2.0)
        config_4x = next(c for c in configs if c.multiplier == 4.0)
        
        # 2x should be exactly double base
        assert config_2x.column_count == 2
        assert config_2x.hidden_dim == 128
        assert config_2x.neurons_per_layer == 256
        
        # 4x should be exactly quadruple base
        assert config_4x.column_count == 4
        assert config_4x.hidden_dim == 256
        assert config_4x.neurons_per_layer == 512
    
    def test_config_serialization(self):
        """Verify configs can be serialized to JSON."""
        configs = create_scaling_configs()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            data = [c.__dict__ for c in configs]
            json.dump(data, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert len(loaded) == 3
            assert loaded[0]['multiplier'] == 1.0
        finally:
            os.unlink(temp_path)

class TestScalingModelCreation:
    """Tests for model creation from scaling configs."""
    
    def test_create_model_from_config_1x(self):
        """Verify 1x config creates valid model."""
        config = ScalingConfig(
            multiplier=1.0,
            column_count=1,
            hidden_dim=64,
            neurons_per_layer=128
        )
        
        model = create_model_from_config(config)
        assert isinstance(model, HybridNetwork)
        assert model is not None
    
    def test_create_model_from_config_2x(self):
        """Verify 2x config creates valid model."""
        config = ScalingConfig(
            multiplier=2.0,
            column_count=2,
            hidden_dim=128,
            neurons_per_layer=256
        )
        
        model = create_model_from_config(config)
        assert isinstance(model, HybridNetwork)
        assert model is not None
    
    def test_model_parameter_count_scales(self):
        """Verify parameter count increases with scaling."""
        config_1x = ScalingConfig(
            multiplier=1.0,
            column_count=1,
            hidden_dim=64,
            neurons_per_layer=128
        )
        config_2x = ScalingConfig(
            multiplier=2.0,
            column_count=2,
            hidden_dim=128,
            neurons_per_layer=256
        )
        
        model_1x = create_model_from_config(config_1x)
        model_2x = create_model_from_config(config_2x)
        
        params_1x = sum(p.numel() for p in model_1x.parameters())
        params_2x = sum(p.numel() for p in model_2x.parameters())
        
        # 2x should have significantly more parameters
        assert params_2x > params_1x, "2x model should have more parameters than 1x"
    
    def test_model_forward_pass(self):
        """Verify scaled models can perform forward pass."""
        config = ScalingConfig(
            multiplier=1.0,
            column_count=1,
            hidden_dim=64,
            neurons_per_layer=128
        )
        
        model = create_model_from_config(config)
        model.eval()
        
        # Create dummy input
        batch_size = 4
        seq_len = 10
        input_dim = 64
        
        x = torch.randn(batch_size, seq_len, input_dim)
        
        with torch.no_grad():
            output = model(x)
        
        assert output is not None
        assert output.shape[0] == batch_size

class TestScalingVariantTraining:
    """Tests for training individual scaling variants."""
    
    @pytest.mark.timeout(120)  # 2 minute timeout for training test
    def test_train_scaling_variant_1x(self):
        """Test training a 1x variant (quick test with few epochs)."""
        config = ScalingConfig(
            multiplier=1.0,
            column_count=1,
            hidden_dim=64,
            neurons_per_layer=128,
            num_epochs=2,  # Minimal epochs for test
            batch_size=8
        )
        
        result = train_scaling_variant(config)
        
        assert isinstance(result, ScalingResult)
        assert result.multiplier == 1.0
        assert result.column_count == 1
        assert result.train_mae is not None
        assert result.test_mae is not None
        assert result.total_parameters > 0
        assert result.training_time_seconds > 0

class TestScalingResults:
    """Tests for scaling result handling."""
    
    def test_scaling_result_to_dict(self):
        """Verify ScalingResult can be converted to dict."""
        result = ScalingResult(
            multiplier=1.0,
            column_count=1,
            total_parameters=1000,
            train_mae=0.05,
            test_mae=0.06,
            training_time_seconds=10.0,
            peak_memory_mb=100.0
        )
        
        data = result.to_dict()
        
        assert data['multiplier'] == 1.0
        assert data['train_mae'] == 0.05
        assert data['test_mae'] == 0.06
        assert data['total_parameters'] == 1000
    
    def test_scaling_result_json_serialization(self):
        """Verify ScalingResult can be serialized to JSON."""
        result = ScalingResult(
            multiplier=2.0,
            column_count=2,
            total_parameters=5000,
            train_mae=0.04,
            test_mae=0.05,
            training_time_seconds=20.0,
            peak_memory_mb=200.0
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(result.to_dict(), f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded['multiplier'] == 2.0
            assert loaded['train_mae'] == 0.04
        finally:
            os.unlink(temp_path)