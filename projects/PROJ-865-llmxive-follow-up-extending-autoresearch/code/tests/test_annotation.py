"""
Tests for the annotation pipeline (T011b).
"""
import json
import sys
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import setup_logging
from utils.config import set_seed

# Setup logging for tests
setup_logging(level=20) # INFO

def test_schema_validation():
    """Test that valid data passes schema validation."""
    from code_02_annotation_distillation.annotate_failures import load_schema, validate_against_schema
    
    # Load schema
    project_root = Path(__file__).parent.parent
    schema_path = project_root / "specs" / "001-llmxive-followup" / "contracts" / "failure_case.schema.yaml"
    schema = load_schema(schema_path)
    
    # Valid data
    valid_data = [
        {
            "task_id": "test_001",
            "raw_error_log": "SyntaxError: invalid syntax",
            "ground_truth_resolution": "Fix syntax",
            "annotated_structural_feature": "Syntactic Error"
        }
    ]
    
    # Should not raise
    assert validate_against_schema(valid_data, schema) is True

def test_invalid_feature():
    """Test that invalid structural features are caught."""
    from code_02_annotation_distillation.annotate_failures import load_schema, validate_against_schema
    
    project_root = Path(__file__).parent.parent
    schema_path = project_root / "specs" / "001-llmxive-followup" / "contracts" / "failure_case.schema.yaml"
    schema = load_schema(schema_path)
    
    invalid_data = [
        {
            "task_id": "test_001",
            "raw_error_log": "Error",
            "ground_truth_resolution": "Fix",
            "annotated_structural_feature": "Invalid Feature Name"
        }
    ]
    
    with pytest.raises(ValueError):
        validate_against_schema(invalid_data, schema)

def test_heuristic_classification():
    """Test the heuristic classifier logic."""
    from code_02_annotation_distillation.annotate_failures import classify_failure_heuristic
    
    assert classify_failure_heuristic("SyntaxError: invalid syntax") == "Syntactic Error"
    assert classify_failure_heuristic("Infinite loop detected") == "Logical Loop"
    assert classify_failure_heuristic("Ambiguous variable") == "Semantic Ambiguity"
    assert classify_failure_heuristic("Missing context: config") == "Missing Context"
    assert classify_failure_heuristic("Random crash") == "Unstructured"

def test_full_pipeline_output():
    """
    Test that the main function produces the expected output file.
    This assumes the input data (parsed_traces.json) exists or is mocked.
    """
    # This test would require mocking the input file or ensuring T010 ran.
    # For unit testing, we focus on the logic functions.
    pass