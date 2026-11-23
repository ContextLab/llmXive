import pytest
import json
import os
from pathlib import Path
import tempfile
import shutil

# We mock the heavy dependencies since we are testing the save logic
# The actual pipeline logic is tested in integration tests.
# Here we test the formatting and saving functions.

# Mock imports to avoid heavy loading during unit tests
import sys
from unittest.mock import MagicMock, patch

# Mock config module
mock_config = MagicMock()
mock_config.get_config_dict.return_value = {
    'paths': {
        'processed_data': '/fake/path',
        'results': '/fake/results',
        'baseline_saa': '/fake/baseline.json'
    }
}
sys.modules['config'] = mock_config

# Mock metrics module
mock_metrics = MagicMock()
mock_metrics.semantic_similarity.return_value = 0.9
mock_metrics.compute_saa.return_value = True
mock_metrics.calculate_iou.return_value = 1.0
sys.modules['metrics'] = mock_metrics

# Mock reasoning module
mock_reasoning = MagicMock()
mock_reasoning.process_test_set.return_value = []
mock_reasoning.load_phi3_model.return_value = MagicMock()
mock_reasoning.build_prompt.return_value = "test prompt"
mock_reasoning.parse_model_response.return_value = {"answer": "test", "chunk_id": "1"}
mock_reasoning.generate_response.return_value = "test response"
sys.modules['reasoning'] = mock_reasoning

# Mock retriever module
mock_retriever = MagicMock()
mock_retriever.TextRetriever.return_value = MagicMock()
mock_retriever.load_processed_data.return_value = []
sys.modules['retriever'] = mock_retriever

# Mock baseline_ref module
mock_baseline = MagicMock()
mock_baseline.load_baseline_saa.return_value = 0.5
sys.modules['baseline_ref'] = mock_baseline

from save_intermediate_results import format_results_for_saving, save_intermediate_results

def test_format_results_for_saving():
    """Test that non-serializable types are converted correctly."""
    input_data = [
        {
            "query_index": 1,
            "semantic_similarity": 0.95,
            "is_answer_correct": True,
            "iou_score": 1.0,
            "extra_obj": object(), # Non-serializable
            "nested": {"key": "value"}
        }
    ]
    
    result = format_results_for_saving(input_data)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["query_index"] == 1
    assert result[0]["semantic_similarity"] == 0.95
    assert result[0]["is_answer_correct"] is True
    assert result[0]["iou_score"] == 1.0
    assert "extra_obj" in result[0] # Should be converted to string
    assert isinstance(result[0]["extra_obj"], str)
    assert result[0]["nested"] == {"key": "value"}

def test_save_intermediate_results(tmp_path):
    """Test that results are saved correctly to a JSON file."""
    test_results = [
        {"query_index": 0, "answer": "A", "score": 0.8},
        {"query_index": 1, "answer": "B", "score": 0.9}
    ]
    
    output_file = tmp_path / "results.json"
    
    success = save_intermediate_results(test_results, output_file)
    
    assert success is True
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert len(loaded) == 2
    assert loaded[0]["query_index"] == 0
    assert loaded[1]["answer"] == "B"

def test_save_intermediate_results_creates_directories(tmp_path):
    """Test that save function creates parent directories if they don't exist."""
    test_results = [{"query_index": 0}]
    
    # Deep nested path that doesn't exist
    output_file = tmp_path / "deep" / "nested" / "results.json"
    
    success = save_intermediate_results(test_results, output_file)
    
    assert success is True
    assert output_file.exists()

def test_save_intermediate_results_handles_empty_list(tmp_path):
    """Test saving an empty list of results."""
    output_file = tmp_path / "empty.json"
    
    success = save_intermediate_results([], output_file)
    
    assert success is True
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == []
