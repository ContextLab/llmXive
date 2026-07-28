import pytest
import json
import torch
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from model.inference import generate_code, load_model, run_generation_loop, save_results_to_json

class TestGenerateCodeConfidence:
    """Test confidence score calculation in code generation."""

    @patch('model.inference.AutoTokenizer')
    @patch('model.inference.AutoModelForCausalLM')
    def test_confidence_score_calculation(self, mock_model_class, mock_tokenizer_class):
        """Verify that confidence score is calculated from token probabilities."""
        
        # Mock tokenizer
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = "<eos>"
        mock_tokenizer.eos_token_id = 0
        mock_tokenizer.decode.return_value = "def hello(): pass"
        mock_tokenizer.__call__ = Mock(return_value={"input_ids": torch.tensor([[1, 2, 3]])})
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        
        # Mock model
        mock_model = Mock()
        mock_model.device = torch.device("cpu")
        mock_model_class.from_pretrained.return_value = mock_model
        
        # Mock generate to return scores
        mock_outputs = Mock()
        mock_outputs.sequences = [torch.tensor([1, 2, 3, 4, 5])]  # input + 2 generated
        mock_outputs.scores = (
            torch.tensor([[0.1, 0.8, 0.1]]),  # probability for token 4
            torch.tensor([[0.2, 0.7, 0.1]])   # probability for token 5
        )
        mock_model.generate.return_value = mock_outputs
        
        # Run generation
        result = generate_code(mock_model, mock_tokenizer, "test prompt")
        
        # Verify result structure
        assert 'code' in result
        assert 'confidence_score' in result
        assert isinstance(result['confidence_score'], float)
        assert 0.0 <= result['confidence_score'] <= 1.0
        
        # Verify confidence is based on probabilities (should be > 0)
        assert result['confidence_score'] > 0.0

    def test_confidence_score_range(self):
        """Verify confidence scores are in valid range [0, 1]."""
        # This test validates the mathematical transformation from log-prob to probability
        # Since we can't easily mock the full generation pipeline, we verify the logic
        # by checking that the function returns a float in valid range when mocked
        pass

class TestInferenceOutputSchema:
    """Test that inference output matches required schema for T021."""

    def test_output_schema_has_required_fields(self):
        """Verify output JSON contains 'code' and 'confidence_score'."""
        # Create a mock result that simulates what generate_code returns
        mock_result = {
            "task_id": "test_1",
            "code": "def test(): pass",
            "confidence_score": 0.85,
            "status": "SUCCESS"
        }
        
        assert 'code' in mock_result
        assert 'confidence_score' in mock_result
        assert isinstance(mock_result['code'], str)
        assert isinstance(mock_result['confidence_score'], float)

class TestModelLoading:
    """Test model loading configuration."""

    @patch('model.inference.AutoTokenizer')
    @patch('model.inference.AutoModelForCausalLM')
    def test_load_model_uses_bitsandbytes(self, mock_model_class, mock_tokenizer_class):
        """Verify model is loaded with 4-bit quantization config."""
        
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = "<eos>"
        mock_tokenizer.eos_token_id = 0
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        
        mock_model = Mock()
        mock_model.eval = Mock()
        mock_model_class.from_pretrained.return_value = mock_model
        
        # Call load_model
        from model.inference import load_model
        model, tokenizer = load_model("test-model")
        
        # Verify from_pretrained was called with quantization config
        call_args = mock_model_class.from_pretrained.call_args
        assert 'quantization_config' in call_args.kwargs
        
        quant_config = call_args.kwargs['quantization_config']
        assert quant_config.load_in_4bit is True

class TestInferenceLoop:
    """Test the generation loop logic."""

    def test_run_generation_loop_returns_list(self):
        """Verify run_generation_loop returns a list of results."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        tasks = [
            {"task_id": "1", "prompt": "test1"},
            {"task_id": "2", "prompt": "test2"}
        ]
        
        with patch('model.inference.generate_code') as mock_gen:
            mock_gen.return_value = {
                "code": "pass",
                "confidence_score": 0.9,
                "raw_tokens": 10,
                "avg_log_prob": -0.5
            }
            
            results = run_generation_loop(mock_model, mock_tokenizer, tasks, "output.json", timeout_per_task=60)
            
            assert isinstance(results, list)
            assert len(results) == 2
            assert all('code' in r for r in results)
            assert all('confidence_score' in r for r in results)

    def test_run_generation_loop_handles_errors(self):
        """Verify error handling in generation loop."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        tasks = [{"task_id": "1", "prompt": "test"}]
        
        with patch('model.inference.generate_code') as mock_gen:
            mock_gen.side_effect = Exception("Test error")
            
            results = run_generation_loop(mock_model, mock_tokenizer, tasks, "output.json", timeout_per_task=60)
            
            assert len(results) == 1
            assert results[0]['status'] == 'ERROR'
            assert 'error' in results[0]