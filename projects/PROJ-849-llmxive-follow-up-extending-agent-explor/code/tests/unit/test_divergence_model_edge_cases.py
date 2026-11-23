import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.models.divergence_model import (
    DivergenceModel,
    DivergenceResult,
    DivergenceModelError
)

class TestDivergenceModelEdgeCases:
    """Unit tests for edge cases in divergence model: missing prefixes and zero retrieval."""

    @pytest.fixture
    def model(self):
        """Create a mock model to avoid loading heavy transformers."""
        with patch('src.models.divergence_model.DistilBertTokenizer.from_pretrained'), \
             patch('src.models.divergence_model.DistilBertModel.from_pretrained') as mock_model_class:
            
            mock_model = MagicMock()
            mock_model_class.return_value = mock_model
            mock_model.device = 'cpu'
            mock_model.eval.return_value = None
            
            model = DivergenceModel()
            model.device = 'cpu'
            return model

    def test_missing_thinking_prefix_returns_skipped(self, model):
        """Test that missing thinking prefix results in a skipped record."""
        result = model.calculate_divergence(
            thinking_prefix="",
            tool_descriptions=["tool1", "tool2"]
        )
        
        assert result.skipped is True
        assert result.error == "Missing thinking prefix"
        assert result.semantic_divergence_score == 0.0
        assert result.thinking_prefix_vector is None
        assert result.tool_centroid_vector is None

    def test_whitespace_only_thinking_prefix_skipped(self, model):
        """Test that whitespace-only thinking prefix is treated as missing."""
        result = model.calculate_divergence(
            thinking_prefix="   \n\t  ",
            tool_descriptions=["tool1"]
        )
        
        assert result.skipped is True
        assert result.error == "Missing thinking prefix"

    def test_zero_retrieval_returns_max_divergence(self, model):
        """Test that zero tool retrieval results in max divergence (1.0)."""
        # Mock the encode method to return a valid vector for thinking prefix
        with patch.object(model, '_encode_text', return_value=np.array([1.0, 0.0, 0.0])):
            result = model.calculate_divergence(
                thinking_prefix="I need to solve this math problem",
                tool_descriptions=[]
            )
            
            assert result.skipped is False
            assert result.error == "Zero retrieval: No tool descriptions found"
            assert result.semantic_divergence_score == 1.0
            assert result.tool_centroid_vector is None
            assert result.thinking_prefix_vector is not None

    def test_all_tool_descriptions_empty_returns_max_divergence(self, model):
        """Test when tool descriptions list contains only empty strings."""
        with patch.object(model, '_encode_text', return_value=np.array([1.0, 0.0, 0.0])):
            result = model.calculate_divergence(
                thinking_prefix="Solve this",
                tool_descriptions=["", "   ", "\n"]
            )
            
            assert result.skipped is False
            assert result.error == "Failed to encode any tool descriptions"
            assert result.semantic_divergence_score == 1.0
            assert result.tool_centroid_vector is None

    def test_normal_case_with_valid_inputs(self, model):
        """Test normal case to ensure edge case handling doesn't break valid flow."""
        thinking_vec = np.array([1.0, 0.0, 0.0])
        tool_vec1 = np.array([0.8, 0.1, 0.1])
        tool_vec2 = np.array([0.7, 0.2, 0.1])
        
        def mock_encode(text):
            if "thinking" in text:
                return thinking_vec
            return tool_vec1 if "tool1" in text else tool_vec2

        with patch.object(model, '_encode_text', side_effect=mock_encode):
            result = model.calculate_divergence(
                thinking_prefix="thinking trace",
                tool_descriptions=["tool1 desc", "tool2 desc"]
            )
            
            assert result.skipped is False
            assert result.error is None
            assert 0.0 <= result.semantic_divergence_score <= 1.0
            assert result.tool_centroid_vector is not None
            assert result.thinking_prefix_vector is not None

    def test_encoding_failure_in_thinking_prefix(self, model):
        """Test when encoding the thinking prefix fails."""
        with patch.object(model, '_encode_text', side_effect=DivergenceModelError("Encoding failed")):
            result = model.calculate_divergence(
                thinking_prefix="Valid text",
                tool_descriptions=["tool1"]
            )
            
            assert result.skipped is True
            assert "Failed to encode thinking prefix" in result.error
            assert result.semantic_divergence_score == 0.0