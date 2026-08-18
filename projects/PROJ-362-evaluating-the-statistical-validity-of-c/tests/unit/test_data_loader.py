import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import logging

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_loader import validate_qrels_schema, load_schema, fetch_with_retry

@pytest.fixture
def mock_schema():
    return {
        "type": "object",
        "properties": {
            "query_id": {"type": "integer"},
            "doc_id": {"type": "integer"},
            "relevance": {"type": "integer"}
        }
    }

@pytest.fixture
def valid_qrels():
    return [
        {"query_id": 1, "doc_id": 100, "relevance": 2},
        {"query_id": 1, "doc_id": 101, "relevance": 1},
        {"query_id": 2, "doc_id": 102, "relevance": 0},
    ]

def test_validate_qrels_schema_valid(mock_schema, valid_qrels, caplog):
    """Test that valid qrels pass validation."""
    with caplog.at_level(logging.WARNING):
        result = validate_qrels_schema(valid_qrels, mock_schema)
    
    assert len(result) == 3
    assert result[0]["relevance"] == 2
    # Check that no errors were logged for valid data
    assert "Missing required field" not in caplog.text
    assert "is not an integer" not in caplog.text

def test_validate_qrels_schema_zero_relevance_warning(mock_schema, caplog):
    """Test that zero-relevance queries trigger a warning."""
    qrels_with_zero = [
        {"query_id": 1, "doc_id": 100, "relevance": 2},
        {"query_id": 1, "doc_id": 101, "relevance": 0},
    ]
    
    with caplog.at_level(logging.WARNING):
        result = validate_qrels_schema(qrels_with_zero, mock_schema)
    
    assert len(result) == 2
    assert any("Zero-relevance query detected" in record.message for record in caplog.records)

def test_validate_qrels_schema_missing_field(mock_schema, caplog):
    """Test that missing fields cause rows to be skipped."""
    qrels_missing = [
        {"query_id": 1, "doc_id": 100, "relevance": 2},
        {"query_id": 1, "relevance": 1},  # Missing doc_id
    ]
    
    with caplog.at_level(logging.WARNING):
        result = validate_qrels_schema(qrels_missing, mock_schema)
    
    assert len(result) == 1
    assert "Missing required field 'doc_id'" in caplog.text

def test_validate_qrels_schema_wrong_type(mock_schema, caplog):
    """Test that non-integer fields cause rows to be skipped."""
    qrels_wrong_type = [
        {"query_id": 1, "doc_id": 100, "relevance": 2},
        {"query_id": "A", "doc_id": 101, "relevance": 1},  # query_id is string
    ]
    
    with caplog.at_level(logging.WARNING):
        result = validate_qrels_schema(qrels_wrong_type, mock_schema)
    
    assert len(result) == 1
    assert "is not an integer" in caplog.text