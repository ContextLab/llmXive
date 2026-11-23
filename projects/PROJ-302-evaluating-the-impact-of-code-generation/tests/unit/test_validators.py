import pytest
from utils.validators import ValidationError, validate_schema, scan_pii, validate_batch

def test_validate_schema_valid():
    """Test schema validation with valid data."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        },
        "required": ["name"]
    }
    
    data = {"name": "Alice", "age": 30}
    result = validate_schema(data, schema)
    
    assert result is True

def test_validate_schema_invalid():
    """Test schema validation with invalid data."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    }
    
    data = {"age": 30}  # Missing required 'name'
    
    with pytest.raises(ValidationError):
        validate_schema(data, schema)

def test_scan_pii_no_pii():
    """Test PII scanning with no PII present."""
    data = {
        "name": "Project Alpha",
        "description": "A software project"
    }
    
    result = scan_pii(data)
    assert result is False

def test_scan_pii_with_pii():
    """Test PII scanning with PII present."""
    data = {
        "email": "user@example.com",
        "name": "John Doe"
    }
    
    result = scan_pii(data)
    assert result is True

def test_validate_batch():
    """Test batch validation."""
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}
        },
        "required": ["id"]
    }
    
    batch = [
        {"id": 1},
        {"id": 2},
        {"id": 3}
    ]
    
    results = validate_batch(batch, schema)
    assert all(results)

def test_validate_batch_with_invalid():
    """Test batch validation with some invalid items."""
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}
        },
        "required": ["id"]
    }
    
    batch = [
        {"id": 1},
        {"name": "invalid"},  # Missing id
        {"id": 3}
    ]
    
    results = validate_batch(batch, schema)
    assert results == [True, False, True]