import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch

from hypernetwork.adapter_generator import (
    validate_base_model_compatibility,
    check_memory_usage,
    ASTFeatureDataset,
    load_frozen_base_model,
    train_mlp_projection
)
from utils.config import Config


class TestValidateBaseModelCompatibility:
    """Tests for base model compatibility validation (FR-009)."""
    
    def test_compatible_model_returns_true(self):
        """Test that a compatible model returns True."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a mock config file
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text('{"model_type": "llama", "hidden_size": 768, "is_encoder_decoder": false}')
            
            config = Config()
            config.hidden_size = 768
            
            # Mock the AutoConfig.from_pretrained
            with patch('hypernetwork.adapter_generator.AutoConfig') as mock_config:
                mock_instance = Mock()
                mock_instance.model_type = "llama"
                mock_instance.hidden_size = 768
                mock_instance.is_encoder_decoder = False
                mock_config.from_pretrained.return_value = mock_instance
                
                result = validate_base_model_compatibility(tmp_dir, config)
                assert result is True
    
    def test_incompatible_hidden_size_raises_error(self):
        """Test that incompatible hidden size raises ValueError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text('{"model_type": "llama", "hidden_size": 512, "is_encoder_decoder": false}')
            
            config = Config()
            config.hidden_size = 768  # Different from model
            
            with patch('hypernetwork.adapter_generator.AutoConfig') as mock_config:
                mock_instance = Mock()
                mock_instance.model_type = "llama"
                mock_instance.hidden_size = 512
                mock_instance.is_encoder_decoder = False
                mock_config.from_pretrained.return_value = mock_instance
                
                with pytest.raises(ValueError, match="Model hidden size.*incompatible"):
                    validate_base_model_compatibility(tmp_dir, config)
    
    def test_non_causal_model_raises_error(self):
        """Test that non-causal models raise ValueError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text('{"model_type": "bert", "hidden_size": 768, "is_encoder_decoder": true}')
            
            config = Config()
            config.hidden_size = 768
            
            with patch('hypernetwork.adapter_generator.AutoConfig') as mock_config:
                mock_instance = Mock()
                mock_instance.model_type = "bert"
                mock_instance.hidden_size = 768
                mock_instance.is_encoder_decoder = True
                mock_config.from_pretrained.return_value = mock_instance
                
                with pytest.raises(ValueError, match="Incompatible model type"):
                    validate_base_model_compatibility(tmp_dir, config)
    
    def test_missing_model_path_raises_error(self):
        """Test that missing model path raises ValueError."""
        config = Config()
        config.hidden_size = 768
        
        with pytest.raises(ValueError, match="does not exist"):
            validate_base_model_compatibility("/nonexistent/path", config)


class TestCheckMemoryUsage:
    """Tests for memory usage checking."""
    
    def test_memory_below_threshold_returns_true(self):
        """Test that memory usage below threshold returns True."""
        with patch('hypernetwork.adapter_generator.resource.getrusage') as mock_usage:
            mock_usage.return_value.ru_maxrss = 1024 * 1024  # 1GB
            result = check_memory_usage(threshold_gb=7.0)
            assert result is True
    
    def test_memory_above_threshold_returns_false(self):
        """Test that memory usage above threshold returns False."""
        with patch('hypernetwork.adapter_generator.resource.getrusage') as mock_usage:
            # 8GB in KB (Linux)
            mock_usage.return_value.ru_maxrss = 8 * 1024 * 1024
            result = check_memory_usage(threshold_gb=7.0)
            assert result is False


class TestASTFeatureDataset:
    """Tests for AST feature dataset."""
    
    def test_dataset_length(self):
        """Test that dataset length matches feature count."""
        features = {
            'token_histogram': [1, 2, 3, 4, 5],
            'complexity': 5
        }
        dataset = ASTFeatureDataset(features)
        assert len(dataset) == 5
    
    def test_dataset_getitem(self):
        """Test that dataset returns correct item."""
        features = {
            'token_histogram': [1, 2, 3],
            'complexity': 5
        }
        graph_features = {'centrality': [0.1, 0.2, 0.3]}
        dataset = ASTFeatureDataset(features, graph_features)
        
        item = dataset[0]
        assert item['index'] == 0
        assert item['ast_features'] == features
        assert item['graph_features'] == graph_features


class TestLoadFrozenBaseModel:
    """Tests for loading frozen base model."""
    
    def test_model_is_frozen(self):
        """Test that loaded model parameters are frozen."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a minimal mock model
            config = Config()
            config.base_model_path = tmp_dir
            
            with patch('hypernetwork.adapter_generator.AutoModelForCausalLM') as mock_model:
                mock_instance = Mock()
                mock_instance.parameters.return_value = [Mock()]
                mock_model.from_pretrained.return_value = mock_instance
                
                model = load_frozen_base_model(tmp_dir, config)
                
                # Verify parameters were frozen
                for param in model.parameters.return_value:
                    assert param.requires_grad is False


class TestTrainMLPProjection:
    """Tests for MLP projection training."""
    
    def test_training_creates_adapter(self):
        """Test that training creates an adapter file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = Config()
            config.hidden_size = 768
            
            features = {
                'token_histogram': [1, 2, 3],
                'complexity': 5
            }
            graph_features = {'centrality': [0.1, 0.2, 0.3]}
            dataset = ASTFeatureDataset(features, graph_features)
            
            # Mock the base model
            mock_model = Mock()
            
            output_path = Path(tmp_dir) / "adapter.safetensors"
            
            # Mock the MLPProjection and verify_projection_shape
            with patch('hypernetwork.adapter_generator.MLPProjection') as mock_mlp:
                with patch('hypernetwork.adapter_generator.verify_projection_shape'):
                    mock_mlp_instance = Mock()
                    mock_mlp_instance.parameters.return_value = [Mock()]
                    mock_mlp.return_value = mock_mlp_instance
                    
                    result_path = train_mlp_projection(
                        base_model=mock_model,
                        feature_dataset=dataset,
                        config=config,
                        output_path=str(output_path),
                        epochs=1,
                        learning_rate=1e-3
                    )
                    
                    assert Path(result_path).exists()