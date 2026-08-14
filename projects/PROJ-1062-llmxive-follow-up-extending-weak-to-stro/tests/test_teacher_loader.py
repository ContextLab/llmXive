"""
Unit tests for teacher model loader.

Tests cover:
- Model loading with int8 quantization
- Pre-RL and post-RL model loading
- Memory constraint verification
- Error handling for missing checkpoints
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import torch

from models.teacher_loader import TeacherLoader, MAX_RAM_GB, HARD_FLOOR_BATCH_SIZE


class TestTeacherLoader:
    """Tests for TeacherLoader class."""
    
    @pytest.fixture
    def mock_transformers(self):
        """Mock transformers library components."""
        with patch('models.teacher_loader.AutoModelForCausalLM') as mock_model, \
             patch('models.teacher_loader.AutoTokenizer') as mock_tokenizer, \
             patch('models.teacher_loader.BitsAndBytesConfig') as mock_quant, \
             patch('models.teacher_loader.AutoConfig') as mock_config:
            
            # Setup mocks
            mock_model_instance = MagicMock()
            mock_model_instance.to.return_value = mock_model_instance
            mock_model.from_pretrained.return_value = mock_model_instance
            
            mock_tokenizer_instance = MagicMock()
            mock_tokenizer_instance.pad_token = None
            mock_tokenizer_instance.eos_token = "<eos>"
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
            
            mock_quant_instance = MagicMock()
            mock_quant.return_value = mock_quant_instance
            
            mock_config_instance = MagicMock()
            mock_config_instance.to_dict.return_value = {'num_parameters': 7_000_000_000}
            mock_config.from_pretrained.return_value = mock_config_instance
            
            yield {
                'model': mock_model,
                'tokenizer': mock_tokenizer,
                'quant': mock_quant,
                'config': mock_config
            }
    
    @pytest.fixture
    def mock_memory_monitor(self):
        """Mock memory monitor."""
        with patch('models.teacher_loader.MemoryMonitor') as mock_monitor:
            mock_monitor_instance = MagicMock()
            mock_monitor_instance.get_current_ram_usage_gb.return_value = 4.0
            mock_monitor.return_value = mock_monitor_instance
            yield mock_monitor
    
    @pytest.fixture
    def mock_hard_floor(self):
        """Mock hard floor enforcer."""
        with patch('models.teacher_loader.HardFloorEnforcer') as mock_floor:
            mock_floor_instance = MagicMock()
            mock_floor.return_value = mock_floor_instance
            yield mock_floor
    
    def test_init_defaults(self):
        """Test default initialization parameters."""
        loader = TeacherLoader(model_id="test-model")
        
        assert loader.model_id == "test-model"
        assert loader.checkpoint_path is None
        assert loader.use_post_rl is False
        assert loader.max_memory_gb == MAX_RAM_GB
        assert loader.device_map == "auto"
        assert loader.offload_folder == "offload"
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        loader = TeacherLoader(
            model_id="custom-model",
            checkpoint_path="/path/to/checkpoint",
            use_post_rl=True,
            max_memory_gb=8.0,
            device_map="cpu",
            offload_folder="/tmp/offload"
        )
        
        assert loader.model_id == "custom-model"
        assert loader.checkpoint_path == "/path/to/checkpoint"
        assert loader.use_post_rl is True
        assert loader.max_memory_gb == 8.0
        assert loader.device_map == "cpu"
        assert loader.offload_folder == "/tmp/offload"
    
    def test_compute_quantization_config(self):
        """Test quantization configuration creation."""
        loader = TeacherLoader(model_id="test-model")
        config = loader._compute_quantization_config()
        
        assert config.load_in_8bit is True
        assert config.llm_int8_threshold == 6.0
        assert config.llm_int8_has_fp16_weight is False
        assert config.llm_int8_skip_modules == ["lm_head"]
        assert config.llm_int8_enable_fp32_cpu_offload is True
    
    def test_verify_model_size_success(self):
        """Test successful model size verification."""
        loader = TeacherLoader(model_id="test-model", max_memory_gb=10.0)
        
        # 7B params * 1 byte * 1.2 overhead = ~8.4 GB < 10 GB
        result = loader._verify_model_size(7_000_000_000)
        
        assert result is True
    
    def test_verify_model_size_failure(self):
        """Test model size verification failure."""
        loader = TeacherLoader(model_id="test-model", max_memory_gb=5.0)
        
        # 7B params * 1 byte * 1.2 overhead = ~8.4 GB > 5 GB
        with pytest.raises(RuntimeError, match="exceeds memory constraint"):
            loader._verify_model_size(7_000_000_000)
    
    def test_load_pre_rl_model(self, mock_transformers, mock_memory_monitor, mock_hard_floor):
        """Test loading a pre-RL teacher model."""
        loader = TeacherLoader(model_id="test-model", use_post_rl=False)
        
        model, tokenizer = loader.load()
        
        # Verify model was loaded
        assert model is not None
        assert tokenizer is not None
        
        # Verify from_pretrained was called
        mock_transformers['model'].from_pretrained.assert_called_once()
        mock_transformers['tokenizer'].from_pretrained.assert_called_once()
        
        # Verify quantization config was created
        mock_transformers['quant'].assert_called_once()
    
    def test_load_post_rl_model(self, mock_transformers, mock_memory_monitor, mock_hard_floor):
        """Test loading a post-RL teacher model with adapters."""
        with patch('models.teacher_loader.PeftModel') as mock_peft:
            mock_peft_instance = MagicMock()
            mock_peft.from_pretrained.return_value = mock_peft_instance
            
            loader = TeacherLoader(
                model_id="test-model",
                checkpoint_path="/path/to/checkpoint",
                use_post_rl=True
            )
            
            model, tokenizer = loader.load()
            
            # Verify PeftModel.from_pretrained was called
            mock_peft.from_pretrained.assert_called_once()
    
    def test_load_missing_checkpoint(self, mock_transformers, mock_memory_monitor, mock_hard_floor):
        """Test loading fails when checkpoint doesn't exist."""
        with patch('models.teacher_loader.Path') as mock_path:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance
            
            loader = TeacherLoader(
                model_id="test-model",
                checkpoint_path="/nonexistent/path",
                use_post_rl=True
            )
            
            with pytest.raises(FileNotFoundError, match="Post-RL checkpoint not found"):
                loader.load()
    
    def test_unload(self, mock_transformers, mock_memory_monitor, mock_hard_floor):
        """Test model unloading."""
        loader = TeacherLoader(model_id="test-model")
        
        # Load first
        model, tokenizer = loader.load()
        
        # Unload
        loader.unload()
        
        assert loader.model is None
        assert loader.tokenizer is None
    
    def test_load_pre_rl_teacher_static_method(self, mock_transformers, mock_memory_monitor, mock_hard_floor):
        """Test static method for loading pre-RL teacher."""
        model, tokenizer = TeacherLoader.load_pre_rl_teacher("test-model")
        
        assert model is not None
        assert tokenizer is not None
    
    def test_load_post_rl_teacher_static_method(self, mock_transformers, mock_memory_monitor, mock_hard_floor):
        """Test static method for loading post-RL teacher."""
        with patch('models.teacher_loader.PeftModel') as mock_peft:
            mock_peft_instance = MagicMock()
            mock_peft.from_pretrained.return_value = mock_peft_instance
            
            model, tokenizer = TeacherLoader.load_post_rl_teacher(
                "test-model",
                "/path/to/checkpoint"
            )
            
            assert model is not None
            assert tokenizer is not None
    
    def test_load_memory_warning(self, mock_transformers, mock_hard_floor):
        """Test memory warning when RAM usage is high."""
        with patch('models.teacher_loader.MemoryMonitor') as mock_monitor:
            mock_monitor_instance = MagicMock()
            mock_monitor_instance.get_current_ram_usage_gb.return_value = 7.0  # > 90% of 7GB
            mock_monitor.return_value = mock_monitor_instance
            
            loader = TeacherLoader(model_id="test-model", max_memory_gb=7.0)
            
            with patch.object(loader, 'load') as mock_load:
                mock_load.return_value = (MagicMock(), MagicMock())
                model, tokenizer = loader.load()
                
                # Hard floor should be enforced
                mock_hard_floor.return_value.enforce_hard_floor.assert_called()