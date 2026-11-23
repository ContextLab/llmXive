import pytest
import pandas as pd
from pydantic import BaseModel, ValidationError
from typing import List

# Define a simple schema for ASV table
class ASVRow(BaseModel):
    sample_id: str
    asv_id: str
    count: int

def test_asv_schema_valid():
    """Test that valid ASV data passes schema validation."""
    data = [
        {'sample_id': 'S1', 'asv_id': 'ASV1', 'count': 100},
        {'sample_id': 'S1', 'asv_id': 'ASV2', 'count': 200},
        {'sample_id': 'S2', 'asv_id': 'ASV1', 'count': 150}
    ]
    
    # Validate each row
    for row in data:
        ASVRow(**row)  # Should not raise

def test_asv_schema_invalid_missing_field():
    """Test that missing required field fails validation."""
    data = [
        {'sample_id': 'S1', 'asv_id': 'ASV1'}  # Missing 'count'
    ]
    
    with pytest.raises(ValidationError):
        ASVRow(**data[0])

def test_asv_schema_invalid_type():
    """Test that wrong type fails validation."""
    data = [
        {'sample_id': 'S1', 'asv_id': 'ASV1', 'count': 'not_a_number'}
    ]
    
    with pytest.raises(ValidationError):
        ASVRow(**data[0])