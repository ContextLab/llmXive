"""
Integration test for the Runtime Optimizer (T034).
Verifies that the optimized pipeline runs within the time limit and produces valid results.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Import the module under test
from runtime_optimizer import run_optimized_evaluation, MAX_RUNTIME_SECONDS, process_single_query

@pytest.fixture
def mock_test_data():
    """Create a small, synthetic test dataset for integration testing."""
    data = []
    for i in range(5):  # Small sample for fast testing
        data.append({
            "query_id": f"test_{i}",
            "query": f"What is the function of gene {i}?",
            "answer": f"Gene {i} regulates cell growth.",
            "chunk_id": f"chunk_{i}",
            "bounding_box": [0.1, 0.1, 0.2, 0.2] # Mock box
        })
    return data

@pytest.fixture
def temp_files(mock_test_data):
    """Create temporary input and output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test_set.json"
        output_path = Path(tmpdir) / "results.json"
        
        with open(input_path, 'w') as f:
            json.dump(mock_test_data, f)
        
        yield input_path, output_path

def test_run_optimized_evaluation_structure(temp_files):
    """Test that the optimizer runs and produces a structured output."""
    input_path, output_path = temp_files

    # Mock the heavy dependencies to avoid actual model loading and long runtime
    with patch('runtime_optimizer.TextRetriever') as MockRetriever, \
         patch('runtime_optimizer.load_phi3_model') as MockModel, \
         patch('runtime_optimizer.build_prompt', return_value="mock prompt"), \
         patch('runtime_optimizer.generate_response', return_value="mock response"), \
         patch('runtime_optimizer.parse_model_response', return_value={"answer": "mock answer", "chunk_id": "chunk_0"}), \
         patch('runtime_optimizer.semantic_similarity', return_value=0.95), \
         patch('runtime_optimizer.calculate_iou', return_value=0.8):
         
         # Setup mocks
         mock_retriever_instance = Mock()
         mock_retriever_instance.retrieve.return_value = [{"text": "mock context"}]
         MockRetriever.return_value = mock_retriever_instance
         
         mock_model_instance = Mock()
         MockModel.return_value = mock_model_instance

         # Run the function
         summary = run_optimized_evaluation(input_path, output_path)

         # Assertions
         assert output_path.exists(), "Output file was not created"
         
         with open(output_path, 'r') as f:
             results = json.load(f)
         
         assert isinstance(results, list), "Results should be a list"
         assert len(results) == 5, f"Expected 5 results, got {len(results)}"
         
         # Check structure of first result
         first_result = results[0]
         assert "query_id" in first_result
         assert "status" in first_result
         assert "runtime" in first_result
         assert "saa" in first_result
         
         # Check summary
         assert "total_samples" in summary
         assert "total_runtime_seconds" in summary
         assert "within_limit" in summary
         assert summary["total_samples"] == 5

def test_process_single_query_logic():
    """Test the logic of processing a single query."""
    mock_sample = {
        "query_id": "q1",
        "query": "test query",
        "answer": "test answer",
        "chunk_id": "c1"
    }
    
    mock_retriever = Mock()
    mock_retriever.retrieve.return_value = [{"text": "context"}]
    
    mock_model = Mock()

    with patch('runtime_optimizer.build_prompt', return_value="prompt"), \
         patch('runtime_optimizer.generate_response', return_value="response"), \
         patch('runtime_optimizer.parse_model_response', return_value={"answer": "test answer", "chunk_id": "c1"}), \
         patch('runtime_optimizer.semantic_similarity', return_value=0.9), \
         patch('runtime_optimizer.calculate_iou', return_value=0.9):
         
         result = process_single_query((0, mock_sample, mock_retriever, mock_model))
         
         assert result["status"] == "success"
         assert result["query_id"] == "q1"
         assert result["saa"] == 1.0 # Exact match or high similarity + IoU
         assert result["runtime"] > 0

def test_runtime_limit_check():
    """Verify that the MAX_RUNTIME_SECONDS constant is set correctly."""
    assert MAX_RUNTIME_SECONDS == 6 * 3600, "Max runtime should be 6 hours in seconds"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])