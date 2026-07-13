import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from config import get_config_dict
from modality_comparison import (
    load_text_results,
    compute_text_saa,
    compute_vla_saa_comparison,
    generate_report,
    main
)

@pytest.fixture
def mock_results_data():
    """Generate mock results data for testing."""
    text_results = {
        "results": [
            {"id": 1, "saa": 1.0, "is_correct_answer": True, "is_spatially_correct": True},
            {"id": 2, "saa": 0.0, "is_correct_answer": True, "is_spatially_correct": False},
            {"id": 3, "saa": 1.0, "is_correct_answer": True, "is_spatially_correct": True},
        ]
    }
    
    visual_results = {
        "results": [
            {"id": 1, "saa": 0.5, "is_correct_answer": True, "is_spatially_correct": False},
            {"id": 2, "saa": 1.0, "is_correct_answer": True, "is_spatially_correct": True},
        ]
    }
    
    return text_results, visual_results

@pytest.fixture
def temp_results_dir(mock_results_data):
    """Create a temporary directory with mock results files."""
    text_results, visual_results = mock_results_data
    
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir) / "results"
        results_dir.mkdir()
        
        # Write text results
        with open(results_dir / "text_pipeline_results.json", 'w') as f:
            json.dump(text_results, f)
        
        # Write visual results
        with open(results_dir / "visual_eval_results.json", 'w') as f:
            json.dump(visual_results, f)
        
        yield results_dir

def test_compute_text_saa(mock_results_data):
    """Test SAA computation from text results."""
    text_results, _ = mock_results_data
    saa = compute_text_saa(text_results)
    # (1.0 + 0.0 + 1.0) / 3 = 0.666...
    assert abs(saa - 0.6666666) < 0.0001

def test_compute_vla_saa_comparison(mock_results_data):
    """Test the comparison logic between modalities."""
    text_results, visual_results = mock_results_data
    text_saa, visual_saa, details = compute_vla_saa_comparison(text_results, visual_results)
    
    assert abs(text_saa - 0.6666666) < 0.0001
    assert abs(visual_saa - 0.75) < 0.0001
    assert "delta" in details
    assert details["text_hallucination_count"] == 1
    assert details["visual_hallucination_count"] == 1

def test_generate_report_creates_file(temp_results_dir):
    """Test that generate_report creates a valid markdown file."""
    text_results = load_text_results()
    with open(temp_results_dir / "visual_eval_results.json", 'r') as f:
        visual_results = json.load(f)
    
    _, _, details = compute_vla_saa_comparison(text_results, visual_results)
    
    output_path = temp_results_dir / "test_report.md"
    generate_report(details, output_path)
    
    assert output_path.exists()
    
    content = output_path.read_text()
    assert "# Modality Comparison Report" in content
    assert "Text-Only" in content
    assert "Visual-Only" in content
    assert "Strict Attributed Accuracy" in content

@patch('modality_comparison.get_config_dict')
@patch('modality_comparison.load_text_results')
@patch('modality_comparison.compute_vla_saa_comparison')
@patch('modality_comparison.generate_report')
def test_main_execution(
    mock_gen_report,
    mock_comp,
    mock_load_text,
    mock_config,
    temp_results_dir,
    mock_results_data
):
    """Test the main function execution flow."""
    mock_config.return_value = {"results_dir": str(temp_results_dir)}
    mock_load_text.return_value = mock_results_data[0]
    mock_comp.return_value = (0.5, 0.6, {"delta": 0.1, "text_hallucination_count": 0, "visual_hallucination_count": 0, "total_text_samples": 10, "total_visual_samples": 10})
    
    main()
    
    mock_load_text.assert_called_once()
    mock_comp.assert_called_once()
    mock_gen_report.assert_called_once()