import json
import os
import tempfile
import pytest
import yaml
from code.validation import run_schema_validation

def create_temp_file(content: str, suffix: str):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=suffix) as f:
        f.write(content)
        return f.name

def test_schema_validation_pass():
    schema = """
    $schema: http://json-schema.org/draft-07/schema#
    type: object
    required:
      - data
    properties:
      data:
        type: array
        items:
          type: object
          required:
            - id
          properties:
            id:
              type: integer
    """
    
    data = {"data": [{"id": 1}, {"id": 2}]}
    
    schema_file = create_temp_file(schema, ".yaml")
    data_file = create_temp_file(json.dumps(data), ".json")
    report_file = create_temp_file("", ".json")
    
    try:
        result = run_schema_validation(data_file, schema_file, report_file)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # Check report file exists and is valid JSON
        assert os.path.exists(report_file)
        with open(report_file, 'r') as f:
            report = json.load(f)
        assert report["valid"] is True
    finally:
        os.unlink(schema_file)
        os.unlink(data_file)
        os.unlink(report_file)

def test_schema_validation_fail_missing_key():
    schema = """
    $schema: http://json-schema.org/draft-07/schema#
    type: object
    required:
      - required_field
    properties:
      required_field:
        type: string
    """
    
    data = {"other_field": "value"}
    
    schema_file = create_temp_file(schema, ".yaml")
    data_file = create_temp_file(json.dumps(data), ".json")
    report_file = create_temp_file("", ".json")
    
    try:
        result = run_schema_validation(data_file, schema_file, report_file)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("required_field" in err for err in result["errors"])
    finally:
        os.unlink(schema_file)
        os.unlink(data_file)
        os.unlink(report_file)

def test_schema_validation_file_not_found():
    schema_file = create_temp_file("type: object", ".yaml")
    data_file = "non_existent_file.json"
    report_file = create_temp_file("", ".json")
    
    try:
        result = run_schema_validation(data_file, schema_file, report_file)
        assert result["valid"] is False
        assert any("not found" in err.lower() for err in result["errors"])
    finally:
        os.unlink(schema_file)
        os.unlink(report_file)
