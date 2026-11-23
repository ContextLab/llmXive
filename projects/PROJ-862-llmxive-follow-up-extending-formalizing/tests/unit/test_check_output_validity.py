import pytest
import torch
from unittest.mock import patch, MagicMock
from data_loader import ConfigurationError
from validity_check import check_output_validity
from config import ValidityConfig

def test_check_output_validity_passes():
    """Test that valid output passes the check."""
    model_output = ["The capital of France is Paris."]
    expected_answer = ["The capital of France is Paris."]
    
    config = ValidityConfig(f1_threshold=0.85, perplexity_multiplier=2.0)
    
    # Mock BERTScore to return high F1
    with patch('validity_check.bert_score_func') as mock_bert:
        # Mock returns P, R, F1 tensors
        mock_bert.return_value = (torch.tensor([0.9]), torch.tensor([0.9]), torch.tensor([0.9]))
        
        # Mock the model loading and perplexity calculation
        # We need to ensure the perplexity check passes
        # The function loads 'gpt2' internally. We will mock the tokenizer and model
        # to return a low loss.
        
        with patch('validity_check.AutoTokenizer.from_pretrained') as mock_tok, \
             patch('validity_check.AutoModelForCausalLM.from_pretrained') as mock_mod:
            
            # Setup mock tokenizer
            mock_tok_instance = MagicMock()
            mock_tok_instance.return_value = {'input_ids': torch.tensor([[1, 2, 3]])}
            mock_tok.return_value = mock_tok_instance
            
            # Setup mock model
            mock_mod_instance = MagicMock()
            mock_mod_instance.eval.return_value = None
            
            # Mock the output of the model call to have low loss
            mock_outputs = MagicMock()
            mock_outputs.loss = torch.tensor([0.1]) # Low loss -> Low perplexity
            mock_mod_instance.return_value = mock_outputs
            
            mock_mod.return_value = mock_mod_instance
            
            result = check_output_validity(model_output, expected_answer, config)
            
            assert result['passed'] is True
            assert result['bertscore_f1'] == 0.9
            assert 'perplexity' in result

def test_check_output_validity_fails_f1():
    """Test that low BERTScore fails the check."""
    model_output = ["The capital of France is London."]
    expected_answer = ["The capital of France is Paris."]
    
    config = ValidityConfig(f1_threshold=0.85, perplexity_multiplier=2.0)
    
    with patch('validity_check.bert_score_func') as mock_bert:
        # Mock low F1
        mock_bert.return_value = (torch.tensor([0.5]), torch.tensor([0.5]), torch.tensor([0.5]))
        
        with patch('validity_check.AutoTokenizer.from_pretrained'), \
             patch('validity_check.AutoModelForCausalLM.from_pretrained'):
            
            result = check_output_validity(model_output, expected_answer, config)
            
            assert result['passed'] is False
            assert result['bertscore_f1'] == 0.5

def test_check_output_validity_missing_expected_answer():
    """Test that missing expected_answer raises ConfigurationError (FR-006)."""
    model_output = ["Some output."]
    expected_answer = [] # Empty list simulates missing column data
    
    config = ValidityConfig(f1_threshold=0.85, perplexity_multiplier=2.0)
    
    with pytest.raises(ConfigurationError, match="lacks an 'expected_answer' column"):
        check_output_validity(model_output, expected_answer, config)

def test_check_output_validity_none_expected_answer():
    """Test that None expected_answer raises ConfigurationError (FR-006)."""
    model_output = ["Some output."]
    expected_answer = None
    
    config = ValidityConfig(f1_threshold=0.85, perplexity_multiplier=2.0)
    
    with pytest.raises(ConfigurationError, match="lacks an 'expected_answer' column"):
        check_output_validity(model_output, expected_answer, config)

def test_check_output_validity_high_perplexity():
    """Test that high perplexity fails the check."""
    model_output = ["Random gibberish text that makes no sense at all."]
    expected_answer = ["The correct answer."]
    
    config = ValidityConfig(f1_threshold=0.85, perplexity_multiplier=2.0)
    
    with patch('validity_check.bert_score_func') as mock_bert:
        # Assume F1 passes for this test to isolate perplexity
        mock_bert.return_value = (torch.tensor([0.9]), torch.tensor([0.9]), torch.tensor([0.9]))
        
        with patch('validity_check.AutoTokenizer.from_pretrained') as mock_tok, \
             patch('validity_check.AutoModelForCausalLM.from_pretrained') as mock_mod:
            
            mock_tok_instance = MagicMock()
            mock_tok_instance.return_value = {'input_ids': torch.tensor([[1, 2, 3]])}
            mock_tok.return_value = mock_tok_instance
            
            mock_mod_instance = MagicMock()
            mock_mod_instance.eval.return_value = None
            
            # Mock high loss for model_output
            mock_outputs_model = MagicMock()
            mock_outputs_model.loss = torch.tensor([10.0]) # High loss
            
            # Mock low loss for expected_answer (baseline)
            mock_outputs_base = MagicMock()
            mock_outputs_base.loss = torch.tensor([0.1])
            
            # We need to handle two calls to model()
            call_count = [0]
            def side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_outputs_model
                else:
                    return mock_outputs_base
            
            mock_mod_instance.return_value.side_effect = side_effect
            mock_mod.return_value = mock_mod_instance
            
            result = check_output_validity(model_output, expected_answer, config)
            
            assert result['passed'] is False
            assert result['perplexity'] > result['perplexity_bound']
