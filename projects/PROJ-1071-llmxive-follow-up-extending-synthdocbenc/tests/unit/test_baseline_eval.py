import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import tempfile
import shutil
import math

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.baseline_eval import (
    get_middle_third_pages,
    get_first_last_third_pages,
    create_question_for_page,
    evaluate_model,
    save_baseline_metrics,
    load_documents,
    load_vlm_config
)
from code.models.document import Document, Page, MiddleThirdMetadata
from code.models.evaluation import EvaluationResult

# --- Fixtures ---

@pytest.fixture
def sample_document():
    """Create a sample document with 30 pages for testing."""
    pages = [
        Page(page_number=i, text_density=0.5, layout_info={"type": "text"})
        for i in range(1, 31)
    ]
    
    metadata = MiddleThirdMetadata(
        start_page=11,
        end_page=20,
        text_density_avg=0.5
    )
    
    doc = Document(
        doc_id="test_doc_001",
        pages=pages,
        metadata=metadata
    )
    
    return doc

@pytest.fixture
def multi_doc_sample():
    """Create a list of sample documents."""
    docs = []
    for i in range(3):
        doc_id = f"test_doc_{i:03d}"
        pages = [
            Page(page_number=p, text_density=0.5, layout_info={"type": "text"})
            for p in range(1, 31)
        ]
        metadata = MiddleThirdMetadata(
            start_page=11,
            end_page=20,
            text_density_avg=0.5
        )
        docs.append(Document(doc_id=doc_id, pages=pages, metadata=metadata))
    return docs

# --- Tests for Positional Splitting Logic ---

def test_get_middle_third_pages(sample_document):
    """Test that middle third pages are correctly identified."""
    middle_pages = get_middle_third_pages(sample_document)
    
    assert len(middle_pages) == 10
    page_numbers = [p.page_number for p in middle_pages]
    assert page_numbers == list(range(11, 21))

def test_get_middle_third_pages_non_divisible_by_three():
    """Test middle third logic for document length not divisible by 3."""
    # 29 pages: first 9, middle 11 (10-20), last 9
    pages = [
        Page(page_number=i, text_density=0.5, layout_info={})
        for i in range(1, 30)
    ]
    metadata = MiddleThirdMetadata(
        start_page=10,
        end_page=20,
        text_density_avg=0.5
    )
    doc = Document(doc_id="test_29", pages=pages, metadata=metadata)
    
    middle_pages = get_middle_third_pages(doc)
    assert len(middle_pages) == 11
    assert [p.page_number for p in middle_pages] == list(range(10, 21))

def test_get_first_last_third_pages(sample_document):
    """Test that first and last third pages are correctly identified."""
    other_pages = get_first_last_third_pages(sample_document)
    
    # 30 pages, so first 10 and last 10
    assert len(other_pages) == 20
    page_numbers = sorted([p.page_number for p in other_pages])
    
    # First third: 1-10, Last third: 21-30
    expected = list(range(1, 11)) + list(range(21, 31))
    assert page_numbers == expected

def test_get_first_last_third_pages_non_divisible_by_three():
    """Test first/last third logic for document length not divisible by 3."""
    # 29 pages: first 9 (1-9), last 9 (21-29)
    pages = [
        Page(page_number=i, text_density=0.5, layout_info={})
        for i in range(1, 30)
    ]
    metadata = MiddleThirdMetadata(
        start_page=10,
        end_page=20,
        text_density_avg=0.5
    )
    doc = Document(doc_id="test_29", pages=pages, metadata=metadata)
    
    other_pages = get_first_last_third_pages(doc)
    assert len(other_pages) == 18
    page_numbers = sorted([p.page_number for p in other_pages])
    expected = list(range(1, 10)) + list(range(21, 30))
    assert page_numbers == expected

# --- Tests for Question Generation ---

def test_create_question_for_page():
    """Test question generation for different page types."""
    page = Page(page_number=15, text_density=0.6, layout_info={})
    
    middle_question = create_question_for_page(page, "middle")
    assert "middle third" in middle_question
    assert "15" in middle_question
    
    other_question = create_question_for_page(page, "first/last")
    assert "first/last third" in other_question
    assert "15" in other_question

# --- Tests for Accuracy Calculation & Evaluation ---

def test_evaluate_model_with_mock(sample_document):
    """Test model evaluation with mocked inference."""
    with patch('code.baseline_eval.run_vlm_inference') as mock_inference:
        # Mock inference to return deterministic results
        def mock_inference_impl(doc, page, question):
            if "middle" in question:
                return {"correct": False, "latency": 0.1, "answer": "test"}
            else:
                return {"correct": True, "latency": 0.1, "answer": "test"}
        
        mock_inference.side_effect = mock_inference_impl
        
        result = evaluate_model("test_model", [sample_document])
        
        assert result.model_name == "test_model"
        assert result.middle_accuracy == 0.0  # All middle pages incorrect
        assert result.other_accuracy == 1.0   # All other pages correct
        assert result.middle_total == 10
        assert result.other_total == 20

def test_evaluate_model_partial_accuracy(multi_doc_sample):
    """Test accuracy calculation with mixed correct/incorrect results."""
    with patch('code.baseline_eval.run_vlm_inference') as mock_inference:
        call_count = [0]
        
        def mock_inference_impl(doc, page, question):
            call_count[0] += 1
            # Make 50% of middle questions correct, 50% of others correct
            is_middle = "middle" in question
            if is_middle:
                # 5 correct out of 10 per doc * 3 docs = 15 total correct middle
                # We need to track globally or per doc. Let's do per doc logic via call count
                # Actually, let's just make it deterministic based on page number
                return {"correct": (page.page_number % 2 == 0), "latency": 0.1, "answer": "test"}
            else:
                return {"correct": (page.page_number % 2 == 0), "latency": 0.1, "answer": "test"}
        
        mock_inference.side_effect = mock_inference_impl
        
        result = evaluate_model("test_partial", multi_doc_sample)
        
        # 3 docs * 10 middle pages = 30 middle pages total. Even pages: 12, 14, ..., 20 (5 per doc) -> 15 correct
        assert result.middle_total == 30
        assert result.middle_accuracy == 0.5
        
        # 3 docs * 20 other pages = 60 other pages total. Even pages: 50% -> 30 correct
        assert result.other_total == 60
        assert result.other_accuracy == 0.5

# --- Tests for Metrics Saving & Delta Calculation ---

def test_save_baseline_metrics(tmp_path):
    """Test saving baseline metrics to JSON."""
    # Create sample results
    results = [
        EvaluationResult(
            model_name="model_1",
            results=[],
            middle_accuracy=0.4,
            other_accuracy=0.9,
            middle_total=10,
            other_total=20
        ),
        EvaluationResult(
            model_name="model_2",
            results=[],
            middle_accuracy=0.3,
            other_accuracy=0.85,
            middle_total=10,
            other_total=20
        )
    ]
    
    output_path = tmp_path / "baseline_metrics.json"
    save_baseline_metrics(results, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "per_model_accuracy" in data
    assert "positional_bias_trends" in data
    assert "delta_middle_vs_others" in data
    assert "bias_threshold_met" in data
    
    # Check delta calculation: avg((0.9-0.4) + (0.85-0.3)) / 2 = (0.5 + 0.55) / 2 = 0.525
    expected_delta = 0.525
    assert abs(data["delta_middle_vs_others"] - expected_delta) < 0.001
    
    # Check threshold met (delta >= 0.05)
    assert data["bias_threshold_met"] == True

def test_save_baseline_metrics_threshold_not_met(tmp_path):
    """Test saving baseline metrics when bias threshold is not met."""
    # Create results with small delta
    results = [
        EvaluationResult(
            model_name="model_1",
            results=[],
            middle_accuracy=0.8,
            other_accuracy=0.82,
            middle_total=10,
            other_total=20
        )
    ]
    
    output_path = tmp_path / "baseline_metrics.json"
    save_baseline_metrics(results, str(output_path))
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # Delta should be 0.02, which is less than 0.05
    assert data["delta_middle_vs_others"] == 0.02
    assert data["bias_threshold_met"] == False

def test_save_baseline_metrics_empty_list(tmp_path):
    """Test saving baseline metrics with empty results list."""
    output_path = tmp_path / "baseline_metrics_empty.json"
    save_baseline_metrics([], str(output_path))
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data["per_model_accuracy"] == {}
    assert data["positional_bias_trends"] == {}
    assert data["delta_middle_vs_others"] == 0.0
    assert data["bias_threshold_met"] == False

def test_save_baseline_metrics_single_model(tmp_path):
    """Test saving baseline metrics with a single model."""
    results = [
        EvaluationResult(
            model_name="single_model",
            results=[],
            middle_accuracy=0.1,
            other_accuracy=0.9,
            middle_total=10,
            other_total=20
        )
    ]
    
    output_path = tmp_path / "single_model_metrics.json"
    save_baseline_metrics(results, str(output_path))
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data["delta_middle_vs_others"] == 0.8
    assert data["bias_threshold_met"] == True

# --- Tests for Loading Helpers (if needed for completeness) ---

def test_load_vlm_config_missing_file(tmp_path):
    """Test loading VLM config when file doesn't exist."""
    config_path = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        load_vlm_config(str(config_path))

def test_load_documents_empty_dir(tmp_path):
    """Test loading documents from an empty directory."""
    # Create empty dir
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # This should return empty list or raise, depending on implementation.
    # Assuming it returns empty list based on typical patterns, but if it raises:
    try:
        docs = load_documents(str(data_dir))
        assert isinstance(docs, list)
        assert len(docs) == 0
    except FileNotFoundError:
        # If implementation raises on empty, that's also acceptable behavior
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])