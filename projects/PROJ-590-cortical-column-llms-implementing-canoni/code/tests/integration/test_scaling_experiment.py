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
    save_scaling_results,
    ScalingConfig,
    ScalingResult
)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

class TestScalingConfigs:
    """Test scaling configuration generation."""
    
    def test_create_scaling_configs_returns_three_variants(self):
        """Should generate 1x, 2x, and 4x variants."""
        configs = create_scaling_configs()
        assert len(configs) == 3
        
        names = [c.name for c in configs]
        assert "1x" in names
        assert "2x" in names
        assert "4x" in names
    
    def test_scaling_configs_have_correct_scaling_factors(self):
        """Verify neurons_per_layer scales correctly."""
        configs = create_scaling_configs()
        
        base_neurons = configs[0].neurons_per_layer
        assert configs[0].neurons_per_layer == base_neurons
        assert configs[1].neurons_per_layer == base_neurons * 2
        assert configs[2].neurons_per_layer == base_neurons * 4
    
    def test_scaling_configs_have_correct_column_counts(self):
        """Verify num_columns scales correctly."""
        configs = create_scaling_configs()
        
        assert configs[0].num_columns == 1
        assert configs[1].num_columns == 2
        assert configs[2].num_columns == 4

class TestScalingModelCreation:
    """Test model creation from scaling configurations."""
    
    def test_create_model_from_config_1x(self):
        """Should create valid model for 1x config."""
        config = ScalingConfig(
            name="1x",
            hidden_dim=64,
            neurons_per_layer=128,
            num_columns=1,
            seed=42
        )
        model = create_model_from_config(config)
        assert model is not None
        assert isinstance(model, torch.nn.Module)
    
    def test_create_model_from_config_2x(self):
        """Should create valid model for 2x config."""
        config = ScalingConfig(
            name="2x",
            hidden_dim=128,
            neurons_per_layer=256,
            num_columns=2,
            seed=42
        )
        model = create_model_from_config(config)
        assert model is not None
        assert isinstance(model, torch.nn.Module)
    
    def test_parameter_count_increases_with_scaling(self):
        """Parameter count should increase with scaling."""
        config_1x = ScalingConfig(
            name="1x",
            hidden_dim=64,
            neurons_per_layer=128,
            num_columns=1,
            seed=42
        )
        config_2x = ScalingConfig(
            name="2x",
            hidden_dim=128,
            neurons_per_layer=256,
            num_columns=2,
            seed=42
        )
        
        model_1x = create_model_from_config(config_1x)
        model_2x = create_model_from_config(config_2x)
        
        params_1x = count_parameters(model_1x)
        params_2x = count_parameters(model_2x)
        
        assert params_2x > params_1x

class TestScalingVariantTraining:
    """Test training of individual scaling variants."""
    
    def test_train_scaling_variant_1x(self, temp_output_dir):
        """Should train 1x variant successfully."""
        config = ScalingConfig(
            name="1x",
            hidden_dim=64,
            neurons_per_layer=128,
            num_columns=1,
            seed=42,
            epochs=2,  # Reduced for faster testing
            batch_size=16
        )
        
        # Temporarily override output path for test
        original_log_path = "data/logs/gradient_norms_scaling.json"
        test_log_path = os.path.join(temp_output_dir, "gradient_norms_scaling.json")
        
        result = train_scaling_variant(config)
        
        assert isinstance(result, ScalingResult)
        assert result.name == "1x"
        assert result.mae > 0
        assert result.time > 0
        assert result.params > 0
    
    def test_train_scaling_variant_reproducibility(self, temp_output_dir):
        """Same config with same seed should produce same results."""
        config = ScalingConfig(
            name="1x",
            hidden_dim=64,
            neurons_per_layer=128,
            num_columns=1,
            seed=42,
            epochs=2,
            batch_size=16
        )
        
        result1 = train_scaling_variant(config)
        result2 = train_scaling_variant(config)
        
        # MAE should be identical with same seed
        assert result1.mae == result2.mae

class TestScalingResults:
    """Test scaling results handling."""
    
    def test_run_scaling_study_generates_results(self, temp_output_dir):
        """Should run full scaling study and generate results."""
        # Override output path for test
        import src.experiments.scaling as scaling_module
        
        original_save = scaling_module.save_scaling_results
        
        def mock_save(results, output_path=None):
            output_path = os.path.join(temp_output_dir, "scaling_results.json")
            original_save(results, output_path)
        
        scaling_module.save_scaling_results = mock_save
        
        try:
            results = run_scaling_study()
            assert len(results) >= 1  # At least one variant should complete
            
            # Verify result schema
            for r in results:
                assert hasattr(r, 'name')
                assert hasattr(r, 'columns')
                assert hasattr(r, 'params')
                assert hasattr(r, 'mae')
                assert hasattr(r, 'time')
        finally:
            scaling_module.save_scaling_results = original_save
    
    def test_save_scaling_results_creates_json(self, temp_output_dir):
        """Should create valid JSON file with correct schema."""
        results = [
            ScalingResult(
                name="1x",
                columns="1x",
                params=1000,
                mae=0.05,
                time=10.5,
                seed=42
            ),
            ScalingResult(
                name="2x",
                columns="2x",
                params=2000,
                mae=0.04,
                time=20.3,
                seed=42
            )
        ]
        
        output_path = os.path.join(temp_output_dir, "scaling_results.json")
        save_scaling_results(results, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "variants" in data
        assert len(data["variants"]) == 2
        
        for variant in data["variants"]:
            assert "columns" in variant
            assert "params" in variant
            assert "mae" in variant
            assert "time" in variant
            
            assert isinstance(variant["columns"], str)
            assert isinstance(variant["params"], int)
            assert isinstance(variant["mae"], float)
            assert isinstance(variant["time"], float)
