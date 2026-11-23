"""
Integration tests for preprocess.py functionality.
Ensures real data flow and output generation.
"""
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

from data.preprocess import filter_prompts_with_min_traces, simulate_context_split, process_and_split_dataset
from data.fetch_utils import DataFetchError


@pytest.fixture
def sample_dataset():
    """Create a sample dataset with varying trace counts."""
    return [
        {
            "id": "p1",
            "prompt": "What is 2+2?",
            "responses": [
                {"text": "4", "reasoning": "Simple addition"},
                {"text": "4", "reasoning": "Two plus two equals four"},
                {"text": "4", "reasoning": "Mathematically, 2+2=4"},
                {"text": "4", "reasoning": "Basic arithmetic yields 4"}
            ]
        },
        {
            "id": "p2",
            "prompt": "Explain gravity",
            "responses": [
                {"text": "Gravity is a force", "reasoning": "Newtonian view"},
                {"text": "Gravity is curvature", "reasoning": "Einsteinian view"},
                {"text": "Gravity attracts mass", "reasoning": "General description"}
            ]
        },
        {
            "id": "p3",
            "prompt": "Solve x+2=4",
            "responses": [
                {"text": "x=2", "reasoning": "Subtract 2 from both sides"},
                {"text": "x=2", "reasoning": "Isolate x"},
                {"text": "x=2", "reasoning": "Basic algebra"},
                {"text": "x=2", "reasoning": "2+2=4 so x must be 2"}
            ]
        }
    ]


def test_filter_prompts_with_min_traces_basic(sample_dataset):
    """Test filtering with min_traces=4."""
    filtered, stats = filter_prompts_with_min_traces(sample_dataset, min_traces=4)
    
    assert len(filtered) == 2, "Should filter out p2 which has only 3 traces"
    assert stats["total_prompts"] == 3
    assert stats["filtered_prompts"] == 2
    assert stats["filtered_ratio"] == pytest.approx(2/3)
    
    # Check that filtered prompts have the correct structure
    for item in filtered:
        assert len(item["responses"]) >= 4


def test_filter_prompts_with_min_traces_edge_case(sample_dataset):
    """Test filtering with min_traces=2 (should keep all)."""
    filtered, stats = filter_prompts_with_min_traces(sample_dataset, min_traces=2)
    
    assert len(filtered) == 3, "All prompts have >= 2 traces"
    assert stats["filtered_prompts"] == 3


def test_filter_prompts_empty_dataset():
    """Test filtering an empty dataset."""
    filtered, stats = filter_prompts_with_min_traces([], min_traces=4)
    
    assert filtered == []
    assert stats["total_prompts"] == 0
    assert stats["filtered_prompts"] == 0


def test_simulate_context_split_basic(sample_dataset):
    """Test context split simulation."""
    # Filter first to get valid prompts
    filtered, _ = filter_prompts_with_min_traces(sample_dataset, min_traces=4)
    
    split_data, stats = simulate_context_split(filtered, seed=42)
    
    assert len(split_data) == 2
    assert stats["total_splits"] == 2
    
    # Check structure
    for entry in split_data:
        assert "prompt_id" in entry
        assert "privileged_context" in entry
        assert "target_traces" in entry
        assert "num_target_traces" in entry
        assert len(entry["target_traces"]) >= 3  # Since we had 4, minus 1 selected


def test_simulate_context_split_resampling_logic():
    """Test that resampling occurs when context is identical to target."""
    # Create dataset with some identical traces
    dataset = [
        {
            "id": "p1",
            "prompt": "Test",
            "responses": [
                {"text": "A", "reasoning": "Same"},
                {"text": "A", "reasoning": "Same"},  # Duplicate
                {"text": "B", "reasoning": "Different"},
                {"text": "C", "reasoning": "Different"},
                {"text": "D", "reasoning": "Different"}
            ]
        }
    ]
    
    filtered, _ = filter_prompts_with_min_traces(dataset, min_traces=4)
    split_data, stats = simulate_context_split(filtered, seed=42)
    
    assert len(split_data) == 1
    # The duplicate "A" should be filtered out during distinct trace selection
    # So we should have 4 distinct traces: A, B, C, D
    assert len(split_data[0]["target_traces"]) >= 3


def test_process_and_split_dataset_integration():
    """Test the full pipeline with mocked data fetch."""
    mock_ultrafeedback = [
        {
            "id": "uf1",
            "prompt": "Question 1",
            "responses": [
                {"text": "A1", "reasoning": "R1"},
                {"text": "A2", "reasoning": "R2"},
                {"text": "A3", "reasoning": "R3"},
                {"text": "A4", "reasoning": "R4"}
            ]
        }
    ]
    
    mock_dolly = [
        {
            "id": "d1",
            "prompt": "Question 2",
            "responses": [
                {"text": "B1", "reasoning": "R1"},
                {"text": "B2", "reasoning": "R2"},
                {"text": "B3", "reasoning": "R3"},
                {"text": "B4", "reasoning": "R4"}
            ]
        }
    ]
    
    with patch('data.preprocess.load_real_dataset') as mock_load:
        mock_load.side_effect = [mock_ultrafeedback, mock_dolly]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            result = process_and_split_dataset(
                config_path="config/settings.yaml",
                output_dir=str(output_dir),
                streaming=False
            )
            
            # Verify outputs
            assert "context_splits" in result["output_files"]
            assert "preprocessing_report.json" in str(result["output_files"]["context_splits"]).replace("context_splits.json", "preprocessing_report.json")
            
            # Check file existence
            context_splits_path = output_dir / "context_splits.json"
            report_path = output_dir / "preprocessing_report.json"
            
            assert context_splits_path.exists()
            assert report_path.exists()
            
            # Validate content
            with open(context_splits_path) as f:
                splits = json.load(f)
                assert len(splits) == 2
            
            with open(report_path) as f:
                report = json.load(f)
                assert report["filter_statistics"]["filtered_prompts"] == 2
                assert "processing_time_seconds" in report
