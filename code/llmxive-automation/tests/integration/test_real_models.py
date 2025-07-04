"""Integration tests with real HuggingFace models"""

import pytest
import os
from unittest.mock import patch
import torch

from src.model_manager import ModelManager
from src.conversation_manager import ConversationManager
from src.task_executor import TaskExecutor
from src.github_handler import GitHubHandler


# Skip all tests if no GPU or in CI environment
pytestmark = pytest.mark.skipif(
    os.environ.get('CI') == 'true' or not torch.cuda.is_available(),
    reason="Integration tests require GPU and should not run in CI"
)


class TestRealModelIntegration:
    """Integration tests using real small models from HuggingFace"""
    
    @pytest.fixture(scope="class")
    def model_manager(self):
        """Create real ModelManager"""
        return ModelManager(cache_dir=os.path.expanduser("~/.cache/huggingface"))
    
    @pytest.fixture(scope="class")
    def small_model_and_tokenizer(self, model_manager):
        """Load a real small model for testing"""
        # Try to load a very small model
        model_candidates = [
            "microsoft/phi-2",  # 2.7B
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # 1.1B
            "Qwen/Qwen1.5-0.5B-Chat",  # 0.5B
        ]
        
        for model_id in model_candidates:
            model, tokenizer = model_manager._load_model(model_id)
            if model and tokenizer:
                return model, tokenizer
        
        pytest.skip("Could not load any small model")
    
    @pytest.fixture
    def conversation_manager(self, small_model_and_tokenizer):
        """Create ConversationManager with real model"""
        model, tokenizer = small_model_and_tokenizer
        return ConversationManager(model, tokenizer)
    
    def test_real_model_loading(self, model_manager):
        """Test loading real models from HuggingFace"""
        # Get trending models
        models = model_manager._get_trending_models()
        assert len(models) > 0
        
        # Find a suitable small model
        suitable_model = None
        for model_info in models[:10]:  # Check first 10
            if model_info['size_gb'] < 2.0:
                suitable_model = model_info
                break
        
        if suitable_model:
            model, tokenizer = model_manager._load_model(suitable_model['model_id'])
            assert model is not None
            assert tokenizer is not None
    
    def test_real_brainstorm_generation(self, conversation_manager):
        """Test real idea generation"""
        prompt = """Generate a novel research idea in machine learning.
        
Field: Machine Learning
Idea: [2-3 sentences about a novel ML approach]
ID: ml-test-001
Keywords: [3-5 keywords]"""
        
        response = conversation_manager.query_model(
            prompt, 
            task_type="BRAINSTORM_IDEA",
            max_new_tokens=200
        )
        
        assert response is not None
        assert len(response) > 50  # Should generate substantial content
        
        # Check if response contains expected elements
        response_lower = response.lower()
        assert any(word in response_lower for word in ['field', 'idea', 'machine learning'])
    
    def test_real_code_generation(self, conversation_manager):
        """Test real code generation"""
        prompt = """Write a Python function that calculates the mean of a list.

def calculate_mean(numbers):"""
        
        response = conversation_manager.query_model(
            prompt,
            task_type="WRITE_CODE",
            max_new_tokens=150
        )
        
        assert response is not None
        assert "def" in response or "return" in response
    
    def test_real_review_generation(self, conversation_manager):
        """Test real review generation"""
        prompt = """Review this research idea:
        
"Develop a quantum-inspired neural network that uses superposition principles for feature representation."

Provide:
Strengths: [list 2-3 strengths]
Concerns: [list 2-3 concerns]
Score: [0.0-1.0]"""
        
        response = conversation_manager.query_model(
            prompt,
            task_type="REVIEW_TECHNICAL_DESIGN",
            max_new_tokens=300
        )
        
        assert response is not None
        assert any(word in response.lower() for word in ['strength', 'concern', 'score'])
    
    def test_different_model_formats(self, model_manager):
        """Test that different model architectures work"""
        test_models = [
            ("microsoft/phi-2", "Instruct:"),
            ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", None),
            ("Qwen/Qwen1.5-0.5B-Chat", "<|im_start|>"),
        ]
        
        for model_id, expected_format in test_models:
            model, tokenizer = model_manager._load_model(model_id)
            if model and tokenizer:
                cm = ConversationManager(model, tokenizer)
                
                # Test formatting
                formatted = cm._format_prompt("Test", "System")
                if expected_format:
                    assert expected_format in formatted
                
                # Test generation
                response = cm.query_model("Hello", max_new_tokens=20)
                assert response is not None
    
    @pytest.mark.slow
    def test_full_task_execution_with_real_model(self, small_model_and_tokenizer):
        """Test complete task execution with real model"""
        model, tokenizer = small_model_and_tokenizer
        
        # Mock GitHub handler
        with patch('src.github_handler.Github'):
            github = GitHubHandler("fake_token")
            github.get_backlog_ideas.return_value = []
            github.create_issue.return_value = None
            
            # Create real conversation manager and executor
            conv_mgr = ConversationManager(model, tokenizer)
            executor = TaskExecutor(conv_mgr, github)
            
            # Execute brainstorm task
            result = executor.execute_brainstorm({})
            
            # Should attempt to generate idea even if parsing fails
            assert 'success' in result
            assert 'error' in result or 'idea' in result
    
    def test_memory_usage(self, small_model_and_tokenizer):
        """Test memory usage with quantized models"""
        model, tokenizer = small_model_and_tokenizer
        
        if torch.cuda.is_available():
            # Check GPU memory usage
            initial_memory = torch.cuda.memory_allocated()
            
            # Run inference
            cm = ConversationManager(model, tokenizer)
            response = cm.query_model("Test prompt", max_new_tokens=50)
            
            final_memory = torch.cuda.memory_allocated()
            memory_used_gb = (final_memory - initial_memory) / (1024**3)
            
            # Should use less than 4GB even for inference
            assert memory_used_gb < 4.0
    
    def test_response_parsing_with_real_outputs(self, conversation_manager):
        """Test parsing real model outputs"""
        from src.response_parser import ResponseParser
        parser = ResponseParser()
        
        # Generate a structured response
        prompt = """Generate output in this exact format:
        
Field: Computer Science
Idea: A novel approach to distributed computing
ID: cs-dist-001
Keywords: distributed, computing, novel"""
        
        response = conversation_manager.query_model(prompt, max_new_tokens=200)
        
        # Try to parse it
        parsed = parser.parse_brainstorm_response(response)
        # Real models might not follow format perfectly
        # Just check that parsing doesn't crash
        assert parsed is None or isinstance(parsed, dict)
    
    def test_edge_cases_with_real_model(self, conversation_manager):
        """Test edge cases with real model"""
        # Very short prompt
        response1 = conversation_manager.query_model("Hi", max_new_tokens=10)
        assert response1 is not None
        
        # Very long prompt (should handle truncation)
        long_prompt = "x" * 5000
        response2 = conversation_manager.query_model(long_prompt, max_new_tokens=50)
        assert response2 is not None
        
        # Special characters
        response3 = conversation_manager.query_model(
            "Generate: 你好 🚀 <|test|>", 
            max_new_tokens=30
        )
        assert response3 is not None
    
    @pytest.mark.parametrize("task_type,expected_keywords", [
        ("BRAINSTORM_IDEA", ["research", "novel", "approach"]),
        ("WRITE_CODE", ["def", "return", "function"]),
        ("REVIEW_TECHNICAL_DESIGN", ["strengths", "concerns", "recommendation"]),
        ("WRITE_TESTS", ["test", "assert", "pytest"]),
    ])
    def test_task_specific_generation(self, conversation_manager, task_type, expected_keywords):
        """Test that different task types produce appropriate outputs"""
        # Create task-appropriate prompt
        prompts = {
            "BRAINSTORM_IDEA": "Generate a research idea about neural networks",
            "WRITE_CODE": "Write a function to sort a list",
            "REVIEW_TECHNICAL_DESIGN": "Review this idea: Use AI for weather prediction",
            "WRITE_TESTS": "Write a test for a function that adds two numbers",
        }
        
        response = conversation_manager.query_model(
            prompts[task_type],
            task_type=task_type,
            max_new_tokens=200
        )
        
        assert response is not None
        # Check if response is somewhat relevant (real models may vary)
        response_lower = response.lower()
        assert any(kw in response_lower for kw in expected_keywords + [task_type.lower().replace('_', ' ')])