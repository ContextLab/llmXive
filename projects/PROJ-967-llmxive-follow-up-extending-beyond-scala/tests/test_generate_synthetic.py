"""
Tests for the synthetic data generator (T039).

Verifies that the generated data adheres to the schema defined in
contracts/dataset.schema.yaml.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the module to test
from code.generate_synthetic_fallback import generate_synthetic_row, generate_synthetic_dataset, DIMENSIONS

@pytest.fixture
def schema_path():
    """Return the path to the schema file."""
    return Path("contracts/dataset.schema.yaml")

@pytest.fixture
def sample_row():
    """Generate a single sample row for testing."""
    import random
    rng = random.Random(42)
    return generate_synthetic_row(0, rng)

def test_row_structure(sample_row):
    """Test that a generated row has all required fields."""
    required_fields = [
        "prompt", "image_path", "teacher_logits", 
        "student_scalar", "human_annotations", "primary_dimension", "sample_id"
    ]
    for field in required_fields:
        assert field in sample_row, f"Missing required field: {field}"

def test_teacher_logits_format(sample_row):
    """Test that teacher_logits is a list of 4 numbers."""
    import ast
    logits = ast.literal_eval(sample_row["teacher_logits"])
    assert isinstance(logits, list), "teacher_logits must be a list"
    assert len(logits) == 4, "teacher_logits must have 4 elements"
    for val in logits:
        assert isinstance(val, float), "Each logit must be a float"

def test_human_annotations_format(sample_row):
    """Test that human_annotations has all 4 dimensions."""
    import ast
    annotations = ast.literal_eval(sample_row["human_annotations"])
    assert isinstance(annotations, dict), "human_annotations must be a dict"
    for dim in DIMENSIONS:
        assert dim in annotations, f"Missing dimension: {dim}"
        assert isinstance(annotations[dim], float), f"{dim} must be a float"

def test_primary_dimension_value(sample_row):
    """Test that primary_dimension is one of the valid dimensions."""
    assert sample_row["primary_dimension"] in DIMENSIONS

def test_synthetic_dataset_creation(schema_path):
    """Test that the generated dataset file adheres to the schema."""
    if not schema_path.exists():
        pytest.skip("Schema file not found, skipping schema validation test")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_synthetic.csv"
        generate_synthetic_dataset(output_file, count=10, seed=42)
        
        # Verify file exists
        assert output_file.exists(), "Output file was not created"
        
        # Verify row count
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 10, f"Expected 10 rows, got {len(rows)}"
            
            # Validate each row
            for i, row in enumerate(rows):
                # Check structure
                assert "sample_id" in row
                assert "primary_dimension" in row
                assert row["primary_dimension"] in DIMENSIONS
                
                # Check types
                import ast
                try:
                    logits = ast.literal_eval(row["teacher_logits"])
                    assert len(logits) == 4
                    annotations = ast.literal_eval(row["human_annotations"])
                    assert len(annotations) == 4
                except Exception as e:
                    pytest.fail(f"Row {i} has invalid format: {e}")

def test_schema_compliance(schema_path):
    """Verify the schema file exists and is valid YAML."""
    assert schema_path.exists(), "Schema file must exist for T039"
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    assert "properties" in schema
    assert "required" in schema
    assert "prompt" in schema["properties"]
    assert "human_annotations" in schema["properties"]
    assert "primary_dimension" in schema["properties"]