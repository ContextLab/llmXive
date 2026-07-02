"""
Tests for LEP_Exclusion_Data schema generation and validation.
"""
import os
import json
import csv
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_models import (
    LEP_Exclusion_Data, 
    generate_lep_exclusion_schema_file, 
    create_sample_lep_dataset
)

def test_schema_generation():
    """Test that the schema file is generated correctly."""
    output_path = "data/schemas/LEP_Exclusion_Data.json"
    result_path = generate_lep_exclusion_schema_file(output_path)
    
    assert os.path.exists(result_path), f"Schema file not created at {result_path}"
    
    with open(result_path, 'r') as f:
        schema = json.load(f)
    
    assert schema["title"] == "LEP_Exclusion_Data"
    assert "properties" in schema
    assert "m_V_MeV" in schema["properties"]
    assert "epsilon" in schema["properties"]
    assert "required" in schema
    assert len(schema["required"]) == 6

def test_sample_dataset_generation():
    """Test that the sample dataset is generated and valid."""
    output_path = "data/raw/lep_sample.csv"
    result_path = create_sample_lep_dataset(output_path)
    
    assert os.path.exists(result_path), f"Sample data not created at {result_path}"
    
    with open(result_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) > 0, "Sample dataset is empty"
    
    # Check that all rows validate
    for row in rows:
        LEP_Exclusion_Data.validate(row)
        # Check types
        assert isinstance(float(row["m_V_MeV"]), float)
        assert isinstance(float(row["epsilon"]), float)
        assert row["limit_type"] in ["95_CL", "68_CL"]

def test_dataclass_creation():
    """Test creating LEP_Exclusion_Data instances."""
    data = {
        "m_V_MeV": 100.0,
        "alpha_D": 0.1,
        "epsilon": 1e-4,
        "limit_type": "95_CL",
        "source": "LEP_2014",
        "is_excluded": True
    }
    
    obj = LEP_Exclusion_Data.from_dict(data)
    assert obj.m_V_MeV == 100.0
    assert obj.epsilon == 1e-4
    assert obj.is_excluded is True

def test_validation_failure():
    """Test that validation fails on missing fields."""
    with pytest.raises(ValueError):
        LEP_Exclusion_Data.validate({"m_V_MeV": 100.0}) # Missing other fields
    
    with pytest.raises(TypeError):
        LEP_Exclusion_Data.validate({
            "m_V_MeV": "not_a_number",
            "alpha_D": 0.1,
            "epsilon": 1e-4,
            "limit_type": "95_CL",
            "source": "test",
            "is_excluded": True
        })
