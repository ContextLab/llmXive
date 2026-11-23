"""
Unit tests for the RAG Pipeline.

Tests verify:
1. Model loading fallback logic (mocked).
2. Prompt construction.
3. Pipeline initialization.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
import sys

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.rag_pipeline import RAGPipeline, create_rag_pipeline, SYSTEM_PROMPT_TEMPLATE
from src.data.models import CodeSnippet


class MockRetriever:
    """Mock retriever for testing."""
    def retrieve(self, query, top_k=5):
        return [
            CodeSnippet(
                id="mock_1",
                language="python",
                code="def hello():\n    print('world')",
                query_id="q1",
                relevance_score=0.9
            ),
            CodeSnippet(
                id="mock_2",
                language="java",
                code="public class Main { public static void main(String[] args) {} }",
                query_id="q1",
                relevance_score=0.8
            )
        ]


def test_pipeline_initialization():
    """Test that the pipeline initializes correctly."""
    retriever = MockRetriever()
    pipeline = create_rag_pipeline(retriever, random_seed=42)
    
    assert pipeline.retriever is retriever
    assert pipeline.random_seed == 42
    assert not pipeline._model_loaded


def test_construct_prompt():
    """Test prompt construction with snippets."""
    retriever = MockRetriever()
    pipeline = create_rag_pipeline(retriever)
    
    query = "How do I print hello world?"
    snippets = retriever.retrieve(query)
    
    prompt = pipeline._construct_prompt(query, snippets)
    
    assert "How do I print hello world?" in prompt
    assert "def hello():" in prompt
    assert "public class Main" in prompt
    assert prompt.startswith("Below is a query")


@patch('src.models.rag_pipeline.load_generator_model')
def test_load_model_primary_success(mock_load_model):
    """Test successful loading of primary model."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = None
    mock_tokenizer.eos_token = ""
    
    mock_load_model.return_value = (mock_model, mock_tokenizer)
    
    retriever = MockRetriever()
    pipeline = create_rag_pipeline(retriever)
    
    # Force load
    pipeline._load_model_if_needed()
    
    assert pipeline._model_loaded
    mock_load_model.assert_called_once()
    # Check primary model ID was used
    call_args = mock_load_model.call_args
    assert call_args[0][0] == "Salesforce/codegen-350M-mono"


@patch('src.models.rag_pipeline.load_generator_model')
@patch('src.models.rag_pipeline.get_available_ram_gb')
def test_load_model_fallback_on_memory(mock_ram, mock_load_model):
    """Test fallback to phi-1.5 when RAM is low."""
    # Simulate low RAM
    mock_ram.return_value = 3.0  # Below 7GB threshold
    
    # Primary fails, Fallback succeeds
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = None
    mock_tokenizer.eos_token = ""
    
    # First call (primary) raises
    mock_load_model.side_effect = [
        RuntimeError("OOM Error"),
        (mock_model, mock_tokenizer)
    ]
    
    retriever = MockRetriever()
    pipeline = create_rag_pipeline(retriever)
    
    pipeline._load_model_if_needed()
    
    assert pipeline._model_loaded
    assert mock_load_model.call_count == 2
    
    # Verify fallback model ID
    fallback_call = mock_load_model.call_args_list[1]
    assert fallback_call[0][0] == "microsoft/phi-1.5"
    # Verify quantization was requested for fallback
    assert fallback_call[1]['use_quantization'] is True


@patch('src.models.rag_pipeline.load_generator_model')
@patch('src.models.rag_pipeline.get_available_ram_gb')
def test_load_model_both_fail(mock_ram, mock_load_model):
    """Test error when both models fail."""
    mock_ram.return_value = 3.0
    mock_load_model.side_effect = RuntimeError("All models failed")
    
    retriever = MockRetriever()
    pipeline = create_rag_pipeline(retriever)
    
    with pytest.raises(RuntimeError, match="Failed to load any generator model"):
        pipeline._load_model_if_needed()
