"""
Integration tests for T014: LLM Explanation Generation.
Tests the full pipeline execution and output validation.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the function to test
# Note: We mock the heavy model loading in unit tests, but here we test the logic flow
# assuming the model loads. For a true integration test in CI, we might mock the model.
# However, per instructions, we write real code. We will mock the heavy parts for speed.
from unittest.mock import patch, MagicMock

from code.utils.config import MAX_TOKENS

# Import the logic functions directly to avoid model loading in tests
from code import data_curation as dc

def test_complexity_labeling_logic():
    """Test T009: Verify complexity labels are valid."""
    # Low
    assert dc.label_complexity(5) == "low"
    assert dc.label_complexity(10) == "low"
    # Medium
    assert dc.label_complexity(11) == "medium"
    assert dc.label_complexity(25) == "medium"
    # High
    assert dc.label_complexity(26) == "high"
    assert dc.label_complexity(100) == "high"

def test_cyclomatic_complexity_calculation():
    """Test T013 logic: Calculate complexity correctly."""
    simple_code = "x = 1"
    assert dc.calculate_cyclomatic_complexity(simple_code) == 1

    if_code = "if x > 0:\n    pass"
    assert dc.calculate_cyclomatic_complexity(if_code) == 2

    loop_code = "for i in range(10):\n    if i % 2 == 0:\n        pass"
    # Base 1 + for + if = 3
    assert dc.calculate_cyclomatic_complexity(loop_code) == 3

@patch('code.data_curation.load_dataset')
@patch('code.data_curation.AutoModelForCausalLM.from_pretrained')
@patch('code.data_curation.AutoTokenizer.from_pretrained')
def test_pipeline_output_structure(mock_tokenizer, mock_model, mock_load_dataset):
    """
    Test T014: Verify the pipeline produces the correct output structure.
    Mocks the heavy model and dataset loading to focus on logic.
    """
    # Setup mocks
    mock_dataset_iter = iter([
        {"code": "def foo(): pass", "docstring": "foo"},
        {"code": "x = 1", "docstring": "x"},
        {"code": "if True: pass", "docstring": "if"},
    ])
    mock_load_dataset.return_value.__iter__ = lambda self: mock_dataset_iter

    mock_tokenizer_instance = MagicMock()
    mock_tokenizer_instance.eos_token_id = 0
    mock_tokenizer_instance.return_value = {"input_ids": [[1, 2, 3]], "attention_mask": [[1, 1, 1]]}
    mock_tokenizer_instance.decode.return_value = "Explanation text here."
    mock_tokenizer.return_value = mock_tokenizer_instance

    mock_model_instance = MagicMock()
    mock_model_instance.generate.return_value = [[1, 2, 3, 4, 5]]
    mock_model.return_value = mock_model_instance

    # Create a temporary file for output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Run pipeline
        results = dc.run_curation_pipeline(tmp_path, n_samples=3)

        # Assertions
        assert len(results) == 3
        assert all("snippet_id" in r for r in results)
        assert all("code" in r for r in results)
        assert all("complexity" in r for r in results)
        assert all("explanation" in r for r in results)
        assert all("token_count" in r for r in results)
        assert all("model_used" in r for r in results)
        assert all("status" in r for r in results)

        # Check complexity labels are valid
        valid_labels = {"low", "medium", "high"}
        for r in results:
            assert r["complexity"] in valid_labels

        # Check status
        # Since we mocked the generation to succeed, status should be success
        # unless we injected an error.
        assert all(r["status"] == "success" for r in results)

        # Verify file exists and is valid JSON
        assert os.path.exists(tmp_path)
        with open(tmp_path, "r") as f:
            data = json.load(f)
            assert len(data) == 3

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_governance_check():
    """Test T000/T014 governance logic."""
    # Test when not amended
    with patch.dict(os.environ, {"CONSTITUTION_AMENDED": "false"}):
        assert dc.check_governance() is False

    # Test when amended
    with patch.dict(os.environ, {"CONSTITUTION_AMENDED": "true"}):
        assert dc.check_governance() is True
