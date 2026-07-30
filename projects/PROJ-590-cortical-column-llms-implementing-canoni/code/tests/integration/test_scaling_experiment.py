"""
Integration tests for scaling experiments.

These tests verify that the scaling study produces valid results
and that the output JSON schema is correct.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
import torch

from src.experiments.scaling import (
    create_scaling_configs,
    create_model_from_config,
    count_parameters,
    train_scaling_variant,
    run_scaling_study,
    ScalingConfig
)
from src.models.hybrid_network import HybridNetwork


class TestScalingConfigs:
    """Tests for scaling configuration generation."""

    def test_create_scaling_configs_returns_three_variants(self):
        """Verify that three scaling variants are created."""
        configs = create_scaling_configs()
        
        assert len(configs) == 3
        
        # Check variant names
        names = [c.name for c in configs]
        assert '1x_baseline' in names
        assert '2x_neurons' in names
        assert '4x_neurons' in names
    
    def test_scaling_configs_have_correct_neurons(self):
        """Verify neuron counts scale correctly."""
        configs = create_scaling_configs()
        
        base_neurons = configs[0].neurons_per_layer
        
        # 2x should have double
        assert configs[1].neurons_per_layer == base_neurons * 2
        
        # 4x should have quadruple
        assert configs[2].neurons_per_layer == base_neurons * 4
    
    def test_scaling_configs_have_correct_columns(self):
        """Verify column counts scale correctly."""
        configs = create_scaling_configs()
        
        assert configs[0].columns == 1
        assert configs[1].columns == 2
        assert configs[2].columns == 4


class TestScalingModelCreation:
    """Tests for model creation from scaling configs."""

    def test_create_model_from_config_returns_hybrid_network(self):
        """Verify model creation returns correct type."""
        config = ScalingConfig(
            name='test',
            columns=1,
            neurons_per_layer=64,
            hidden_dim=32,
            num_layers=2
        )
        
        model = create_model_from_config(config)
        
        assert isinstance(model, HybridNetwork)
    
    def test_model_parameters_scale_with_neurons(self):
        """Verify parameter count increases with neuron count."""
        config_small = ScalingConfig(
            name='small',
            columns=1,
            neurons_per_layer=32,
            hidden_dim=32,
            num_layers=2
        )
        
        config_large = ScalingConfig(
            name='large',
            columns=1,
            neurons_per_layer=64,
            hidden_dim=32,
            num_layers=2
        )
        
        model_small = create_model_from_config(config_small)
        model_large = create_model_from_config(config_large)
        
        params_small = count_parameters(model_small)
        params_large = count_parameters(model_large)
        
        assert params_large > params_small


class TestScalingVariantTraining:
    """Tests for training individual scaling variants."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_train_scaling_variant_produces_results(self, temp_output_dir):
        """Verify training produces valid results."""
        config = ScalingConfig(
            name='test_variant',
            columns=1,
            neurons_per_layer=32,
            hidden_dim=16,
            num_layers=2,
            epochs=2,  # Minimal epochs for speed
            batch_size=8,
            learning_rate=0.01,
            seed=42
        )
        
        result = train_scaling_variant(config)
        
        assert result.variant_name == 'test_variant'
        assert result.columns == 1
        assert result.neurons_per_layer == 32
        assert result.total_params > 0
        assert result.train_mae >= 0
        assert result.test_mae >= 0
        assert result.training_time > 0


class TestScalingResults:
    """Tests for scaling study output."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_run_scaling_study_creates_json(self, temp_output_dir):
        """Verify scaling study creates output JSON."""
        output_path = os.path.join(temp_output_dir, 'scaling_results.json')
        
        # Create minimal configs for speed
        configs = [
            ScalingConfig(
                name='1x_test',
                columns=1,
                neurons_per_layer=16,
                hidden_dim=8,
                num_layers=2,
                epochs=1,
                batch_size=4,
                learning_rate=0.01,
                seed=42
            )
        ]
        
        run_scaling_study(configs=configs, output_path=output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'variants' in data
        assert len(data['variants']) == 1
        
        variant = data['variants'][0]
        assert 'name' in variant
        assert 'columns' in variant
        assert 'params' in variant
        assert 'train_mae' in variant
        assert 'test_mae' in variant
        assert 'time' in variant
    
    def test_scaling_results_schema(self, temp_output_dir):
        """Verify scaling results match expected schema."""
        output_path = os.path.join(temp_output_dir, 'scaling_results.json')
        
        configs = [
            ScalingConfig(
                name='schema_test',
                columns=1,
                neurons_per_layer=16,
                hidden_dim=8,
                num_layers=2,
                epochs=1,
                batch_size=4,
                learning_rate=0.01,
                seed=42
            )
        ]
        
        run_scaling_study(configs=configs, output_path=output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Validate schema
        assert isinstance(data, dict)
        assert 'variants' in data
        assert isinstance(data['variants'], list)
        
        for variant in data['variants']:
            assert isinstance(variant['name'], str)
            assert isinstance(variant['columns'], int)
            assert isinstance(variant['params'], int)
            assert isinstance(variant['train_mae'], float)
            assert isinstance(variant['test_mae'], float)
            assert isinstance(variant['time'], float)