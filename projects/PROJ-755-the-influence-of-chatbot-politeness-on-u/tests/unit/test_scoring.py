import pytest
import numpy as np
from code.utils.scoring import score_utterances_batch, aggregate_dialogue_scores, standardize_scores
from unittest.mock import patch, MagicMock
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class TestScoreUtterancesBatch:
    """Unit tests for batched politeness scoring with BERT."""
    
    @patch('code.utils.scoring.AutoTokenizer.from_pretrained')
    @patch('code.utils.scoring.AutoModelForSequenceClassification.from_pretrained')
    def test_basic_scoring(self, mock_model, mock_tokenizer):
        """Test basic scoring functionality with mock model."""
        # Setup mocks
        mock_tokenizer.return_value = MagicMock()
        mock_tokenizer.return_value.return_value = {
            'input_ids': torch.tensor([[101, 123, 456, 102]]),
            'attention_mask': torch.tensor([[1, 1, 1, 1]])
        }
        
        mock_model_instance = MagicMock()
        mock_model_instance.logits = torch.tensor([[0.2, 0.8]])
        mock_model.return_value = mock_model_instance
        
        utterances = ["Hello, how are you?", "I'm doing great, thanks!"]
        
        # Call function
        scores = score_utterances_batch(utterances, batch_size=2)
        
        # Assertions
        assert len(scores) == 2
        assert all(isinstance(s, float) for s in scores)
        assert all(0 <= s <= 1 for s in scores)
        
    @patch('code.utils.scoring.AutoTokenizer.from_pretrained')
    @patch('code.utils.scoring.AutoModelForSequenceClassification.from_pretrained')
    def test_empty_utterances(self, mock_model, mock_tokenizer):
        """Test handling of empty input."""
        scores = score_utterances_batch([])
        assert scores == []
        
    @patch('code.utils.scoring.AutoTokenizer.from_pretrained')
    @patch('code.utils.scoring.AutoModelForSequenceClassification.from_pretrained')
    def test_cpu_forced(self, mock_model, mock_tokenizer):
        """Test that device is forced to CPU."""
        mock_tokenizer.return_value = MagicMock()
        mock_tokenizer.return_value.return_value = {
            'input_ids': torch.tensor([[101, 123, 102]]),
            'attention_mask': torch.tensor([[1, 1, 1]])
        }
        
        mock_model_instance = MagicMock()
        mock_model_instance.logits = torch.tensor([[0.3, 0.7]])
        mock_model.return_value = mock_model_instance
        
        scores = score_utterances_batch(["Test"], device=0)
        
        # Verify model was moved to CPU
        mock_model_instance.to.assert_called_with(-1)
        
    @patch('code.utils.scoring.AutoTokenizer.from_pretrained')
    @patch('code.utils.scoring.AutoModelForSequenceClassification.from_pretrained')
    def test_batch_size_reduction_on_error(self, mock_model, mock_tokenizer):
        """Test fallback to batch_size=1 on memory error."""
        call_count = [0]
        
        def mock_inference(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise MemoryError("Simulated memory error")
            return torch.tensor([[0.5, 0.5]])
        
        mock_tokenizer.return_value = MagicMock()
        mock_tokenizer.return_value.return_value = {
            'input_ids': torch.tensor([[101, 123, 102]]),
            'attention_mask': torch.tensor([[1, 1, 1]])
        }
        
        mock_model_instance = MagicMock()
        mock_model_instance.logits = mock_inference
        mock_model.return_value = mock_model_instance
        
        scores = score_utterances_batch(["Test"], batch_size=16)
        
        # Should have retried with batch_size=1
        assert len(scores) == 1

class TestAggregateDialogueScores:
    """Unit tests for dialogue score aggregation."""
    
    def test_basic_aggregation(self):
        """Test basic mean calculation per dialogue."""
        utterance_scores = [
            {"dialogue_id": "d1", "politeness_score": 0.8},
            {"dialogue_id": "d1", "politeness_score": 0.6},
            {"dialogue_id": "d2", "politeness_score": 0.9}
        ]
        
        result = aggregate_dialogue_scores(utterance_scores)
        
        assert result["d1"] == 0.7  # (0.8 + 0.6) / 2
        assert result["d2"] == 0.9
        
    def test_empty_input(self):
        """Test handling of empty input."""
        result = aggregate_dialogue_scores([])
        assert result == {}
        
    def test_single_utterance(self):
        """Test with single utterance per dialogue."""
        utterance_scores = [
            {"dialogue_id": "d1", "politeness_score": 0.5}
        ]
        
        result = aggregate_dialogue_scores(utterance_scores)
        assert result["d1"] == 0.5

class TestStandardizeScores:
    """Unit tests for score standardization."""
    
    def test_zscore_standardization(self):
        """Test Z-score standardization."""
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        standardized = standardize_scores(scores, method="zscore")
        
        # Check mean is approximately 0
        assert abs(np.mean(standardized)) < 1e-6
        # Check std is approximately 1
        assert abs(np.std(standardized) - 1.0) < 1e-6
        
    def test_minmax_standardization(self):
        """Test Min-Max standardization."""
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        standardized = standardize_scores(scores, method="minmax")
        
        # Check min is 0 and max is 1
        assert min(standardized) == 0.0
        assert max(standardized) == 1.0
        
    def test_empty_scores(self):
        """Test handling of empty input."""
        result = standardize_scores([])
        assert result == []
        
    def test_constant_scores(self):
        """Test handling of constant scores (std=0)."""
        scores = [2.0, 2.0, 2.0]
        standardized = standardize_scores(scores, method="zscore")
        assert all(s == 0.0 for s in standardized)
        
    def test_invalid_method(self):
        """Test error on invalid method."""
        with pytest.raises(ValueError):
            standardize_scores([1.0, 2.0], method="invalid")
