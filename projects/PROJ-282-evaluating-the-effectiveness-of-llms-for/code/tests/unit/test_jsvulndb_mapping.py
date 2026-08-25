"""
Unit tests for T011a: JSVulnDB to BigVul Mapping.
"""
import json
import tempfile
from pathlib import Path
import pytest

from src.data.generate_jsvulndb_mapping import (
    generate_mapping_document,
    JSVULNDB_TO_BIGVUL_MAPPING
)

def test_mapping_document_structure():
    """Verify the generated mapping document has required keys."""
    doc = generate_mapping_document()
    
    assert "description" in doc
    assert "field_mappings" in doc
    assert "validation_rules" in doc
    assert "example_transformation" in doc
    
    # Check specific field mappings exist
    mappings = doc["field_mappings"]
    required_fields = ["code", "ground_truth_label", "language", "cwe_category", "file_name", "line_number"]
    for field in required_fields:
        assert field in mappings, f"Missing mapping for field: {field}"

def test_ground_truth_label_logic():
    """Verify that ground_truth_label is set to constant 1."""
    doc = generate_mapping_document()
    label_map = doc["field_mappings"]["ground_truth_label"]
    
    assert label_map["transformation"] == "Constant value 1 (JSVulnDB is a vulnerability dataset, all entries are vulnerable)."
    assert label_map["default_value"] == 1

def test_language_logic():
    """Verify that language is set to constant 'javascript'."""
    doc = generate_mapping_document()
    lang_map = doc["field_mappings"]["language"]
    
    assert lang_map["transformation"] == "Constant value 'javascript'."
    assert lang_map["default_value"] == "javascript"

def test_cwe_normalization():
    """Verify CWE mapping includes normalization logic."""
    doc = generate_mapping_document()
    cwe_map = doc["field_mappings"]["cwe_category"]
    
    assert "CWE-" in cwe_map["transformation"]
    assert "uppercase" in cwe_map["transformation"].lower()

def test_example_transformation_validity():
    """Verify the example transformation matches the defined schema."""
    doc = generate_mapping_document()
    example = doc["example_transformation"]
    output = example["output"]
    
    # Check keys
    expected_keys = ["code", "ground_truth_label", "language", "cwe_category", "file_name", "line_number"]
    for key in expected_keys:
        assert key in output, f"Missing key in example output: {key}"
    
    # Check types
    assert isinstance(output["code"], str)
    assert isinstance(output["ground_truth_label"], int)
    assert isinstance(output["language"], str)
    assert isinstance(output["cwe_category"], str)
    assert isinstance(output["file_name"], str)
    assert isinstance(output["line_number"], int)

def test_mapping_file_writing():
    """Test that the mapping can be written to a JSON file and read back."""
    doc = generate_mapping_document()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "test_mapping.json"
        
        # Write
        from src.data.generate_jsvulndb_mapping import write_mapping_json
        write_mapping_json(doc, tmp_path)
        
        # Read back
        assert tmp_path.exists()
        with open(tmp_path, 'r') as f:
            loaded_doc = json.load(f)
        
        assert loaded_doc == doc