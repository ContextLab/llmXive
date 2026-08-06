import pytest
import logging
from code.data_loader import validate_qrels_schema, process_and_validate_qrels, SCHEMA
import datasets

# Set up logging to capture warnings
@pytest.fixture(autouse=True)
def setup_logging(capsys):
    logging.basicConfig(level=logging.WARNING)
    yield

def test_validate_qrels_schema_valid_record():
    """Test validation of a valid qrels record."""
    record = {
        "query_id": 1,
        "doc_id": 100,
        "relevance": 2
    }
    assert validate_qrels_schema(record, SCHEMA) is True

def test_validate_qrels_schema_missing_field():
    """Test validation fails for missing required field."""
    record = {
        "query_id": 1,
        "doc_id": 100
        # Missing 'relevance'
    }
    assert validate_qrels_schema(record, SCHEMA) is False

def test_validate_qrels_schema_wrong_type():
    """Test validation fails for wrong field type."""
    record = {
        "query_id": "not_an_int",  # Should be integer
        "doc_id": 100,
        "relevance": 2
    }
    assert validate_qrels_schema(record, SCHEMA) is False

def test_validate_qrels_schema_float_to_int_conversion():
    """Test that float integers are converted to int."""
    record = {
        "query_id": 1.0,
        "doc_id": 100,
        "relevance": 2
    }
    # This should pass and convert the float to int
    assert validate_qrels_schema(record, SCHEMA) is True
    assert record["query_id"] == 1  # Should be converted

def test_process_and_validate_qrels_zero_relevance_warning(caplog):
    """Test that zero-relevance queries trigger warnings."""
    # Create a mock dataset with a zero-relevance record
    data = [
        {"query_id": 1, "doc_id": 100, "relevance": 0},
        {"query_id": 1, "doc_id": 101, "relevance": 1},
        {"query_id": 2, "doc_id": 200, "relevance": 0}
    ]
    
    # Create a mock dataset object
    class MockDataset:
        def __iter__(self):
            return iter(data)
        def __len__(self):
            return len(data)
    
    mock_ds = MockDataset()
    
    # Process and capture warnings
    with caplog.at_level(logging.WARNING):
        records = list(process_and_validate_qrels(mock_ds, SCHEMA))
    
    # Check that warnings were logged for zero-relevance
    assert any("Zero-relevance query found" in record for record in caplog.messages)
    # We should have 3 valid records (0-relevance is still valid, just warned about)
    assert len(records) == 3

def test_process_and_validate_qrels_invalid_record_skipped():
    """Test that invalid records are skipped during processing."""
    data = [
        {"query_id": 1, "doc_id": 100, "relevance": 2},  # Valid
        {"query_id": 2, "doc_id": 200},  # Invalid - missing relevance
        {"query_id": 3, "doc_id": 300, "relevance": 1}  # Valid
    ]
    
    class MockDataset:
        def __iter__(self):
            return iter(data)
        def __len__(self):
            return len(data)
    
    mock_ds = MockDataset()
    records = list(process_and_validate_qrels(mock_ds, SCHEMA))
    
    # Should only have 2 valid records
    assert len(records) == 2
    assert records[0]["query_id"] == 1
    assert records[1]["query_id"] == 3
