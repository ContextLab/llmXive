"""Unit tests for ConversationManager with real model interactions"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import torch

from src.conversation_manager import ConversationManager


class TestConversationManager:
    """Test suite for ConversationManager"""
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock model"""
        model = MagicMock()
        model.name_or_path = "microsoft/phi-2"
        model.generate = Mock(return_value=torch.tensor([[1, 2, 3, 4, 5]]))
        model.config = MagicMock()
        model.config.max_position_embeddings = 2048
        return model
    
    @pytest.fixture
    def mock_tokenizer(self):
        """Create a mock tokenizer"""
        tokenizer = MagicMock()
        tokenizer.model_max_length = 2048
        tokenizer.encode = Mock(return_value=[1, 2, 3, 4, 5])
        tokenizer.decode = Mock(return_value="Test response from model")
        tokenizer.pad_token_id = 0
        tokenizer.eos_token_id = 1
        tokenizer.apply_chat_template = Mock(return_value="Formatted prompt")
        return tokenizer
    
    @pytest.fixture
    def conversation_manager(self, mock_model, mock_tokenizer):
        """Create ConversationManager instance"""
        return ConversationManager(mock_model, mock_tokenizer)
    
    def test_initialization(self, conversation_manager):
        """Test ConversationManager initialization"""
        assert conversation_manager.model is not None
        assert conversation_manager.tokenizer is not None
        assert conversation_manager.model_name == "microsoft/phi-2"
    
    def test_get_system_prompt(self, conversation_manager):
        """Test system prompt generation for different task types"""
        task_types = [
            "BRAINSTORM_IDEA",
            "WRITE_CODE",
            "REVIEW_TECHNICAL_DESIGN",
            "WRITE_TESTS"
        ]
        
        for task_type in task_types:
            prompt = conversation_manager._get_system_prompt(task_type)
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            
            # Check for task-specific content
            if task_type == "BRAINSTORM_IDEA":
                assert "creative" in prompt.lower()
            elif task_type == "WRITE_CODE":
                assert "python" in prompt.lower()
            elif task_type == "REVIEW_TECHNICAL_DESIGN":
                assert "review" in prompt.lower()
    
    def test_format_prompt_phi_model(self, conversation_manager):
        """Test prompt formatting for Phi models"""
        conversation_manager.model_name = "microsoft/phi-2"
        
        user_prompt = "Test prompt"
        system_prompt = "You are a helpful assistant"
        
        formatted = conversation_manager._format_prompt(user_prompt, system_prompt)
        
        assert "Instruct:" in formatted
        assert user_prompt in formatted
        assert "Output:" in formatted
    
    def test_format_prompt_qwen_model(self, conversation_manager):
        """Test prompt formatting for Qwen models"""
        conversation_manager.model_name = "Qwen/Qwen-1.5B"
        
        user_prompt = "Test prompt"
        system_prompt = "You are a helpful assistant"
        
        formatted = conversation_manager._format_prompt(user_prompt, system_prompt)
        
        assert "<|im_start|>" in formatted
        assert "<|im_end|>" in formatted
        assert "system" in formatted
        assert "user" in formatted
    
    def test_format_prompt_gemma_model(self, conversation_manager):
        """Test prompt formatting for Gemma models"""
        conversation_manager.model_name = "google/gemma-2b"
        
        user_prompt = "Test prompt"
        system_prompt = "You are a helpful assistant"
        
        formatted = conversation_manager._format_prompt(user_prompt, system_prompt)
        
        assert "<start_of_turn>" in formatted
        assert "<end_of_turn>" in formatted
        assert "user" in formatted
        assert "model" in formatted
    
    def test_format_prompt_default(self, conversation_manager):
        """Test default prompt formatting"""
        conversation_manager.model_name = "unknown/model"
        
        user_prompt = "Test prompt"
        system_prompt = "You are a helpful assistant"
        
        formatted = conversation_manager._format_prompt(user_prompt, system_prompt)
        
        assert system_prompt in formatted
        assert user_prompt in formatted
        assert "Human:" in formatted
        assert "Assistant:" in formatted
    
    def test_query_model_success(self, conversation_manager, mock_tokenizer):
        """Test successful model query"""
        # Mock tokenizer to handle chat template
        mock_tokenizer.apply_chat_template = None  # Simulate no chat template
        
        prompt = "Generate a research idea"
        response = conversation_manager.query_model(prompt, task_type="BRAINSTORM_IDEA")
        
        assert response is not None
        assert response == "Test response from model"
        assert conversation_manager.model.generate.called
    
    def test_query_model_with_max_tokens(self, conversation_manager):
        """Test model query with custom max tokens"""
        prompt = "Write long code"
        response = conversation_manager.query_model(
            prompt, 
            task_type="WRITE_CODE",
            max_new_tokens=2000
        )
        
        # Check generate was called with correct max_new_tokens
        generate_kwargs = conversation_manager.model.generate.call_args[1]
        assert generate_kwargs['max_new_tokens'] == 2000
    
    def test_query_model_error_handling(self, conversation_manager):
        """Test error handling in model query"""
        # Make generate raise an exception
        conversation_manager.model.generate.side_effect = Exception("CUDA out of memory")
        
        response = conversation_manager.query_model("Test prompt")
        
        assert response is None  # Should return None on error
    
    def test_query_model_with_temperature(self, conversation_manager):
        """Test model query with different temperatures"""
        prompt = "Be creative"
        
        # Creative task should have higher temperature
        conversation_manager.query_model(prompt, task_type="BRAINSTORM_IDEA")
        generate_kwargs = conversation_manager.model.generate.call_args[1]
        assert generate_kwargs['temperature'] == 0.8
        
        # Code task should have lower temperature
        conversation_manager.query_model(prompt, task_type="WRITE_CODE")
        generate_kwargs = conversation_manager.model.generate.call_args[1]
        assert generate_kwargs['temperature'] == 0.3
    
    def test_conversation_history(self, conversation_manager):
        """Test conversation history tracking"""
        prompts = ["First prompt", "Second prompt", "Third prompt"]
        
        for prompt in prompts:
            conversation_manager.query_model(prompt)
        
        # Check generate was called for each prompt
        assert conversation_manager.model.generate.call_count == len(prompts)
    
    @patch('torch.cuda.is_available')
    def test_device_handling(self, mock_cuda, mock_model, mock_tokenizer):
        """Test proper device handling"""
        # Test with CUDA available
        mock_cuda.return_value = True
        cm = ConversationManager(mock_model, mock_tokenizer)
        
        cm.query_model("Test")
        # Should attempt to use CUDA
        
        # Test with CUDA not available
        mock_cuda.return_value = False
        cm = ConversationManager(mock_model, mock_tokenizer)
        
        cm.query_model("Test")
        # Should fall back to CPU
    
    def test_prompt_truncation(self, conversation_manager, mock_tokenizer):
        """Test handling of long prompts"""
        # Create a very long prompt
        long_prompt = "x" * 10000
        
        # Mock tokenizer to return many tokens
        mock_tokenizer.encode.return_value = list(range(3000))
        mock_tokenizer.model_max_length = 2048
        
        response = conversation_manager.query_model(long_prompt)
        
        # Should still work despite long prompt
        assert response is not None
    
    def test_different_task_personas(self, conversation_manager):
        """Test that different tasks get appropriate personas"""
        tasks_and_keywords = {
            "BRAINSTORM_IDEA": ["innovative", "creative", "scientist"],
            "WRITE_CODE": ["experienced", "programmer", "python"],
            "REVIEW_PAPER": ["peer reviewer", "thorough", "constructive"],
            "WRITE_TESTS": ["QA engineer", "comprehensive", "edge cases"]
        }
        
        for task, keywords in tasks_and_keywords.items():
            prompt = conversation_manager._get_system_prompt(task)
            for keyword in keywords:
                assert keyword in prompt.lower()
    
    def test_model_specific_formatting(self, conversation_manager):
        """Test that each model type gets properly formatted"""
        model_formats = {
            "microsoft/phi-2": "Instruct:",
            "Qwen/Qwen1.5-1.8B": "<|im_start|>",
            "google/gemma-2b-it": "<start_of_turn>",
            "TinyLlama/TinyLlama-1.1B": "Human:",  # Default format
        }
        
        for model_name, expected_format in model_formats.items():
            conversation_manager.model_name = model_name
            formatted = conversation_manager._format_prompt("Test", "System")
            assert expected_format in formatted