import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add code root to path for imports
code_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(code_root))

from src.data.generate_jsvulndb_mapping import generate_mapping_document, write_mapping_json, JSVULNDB_TO_BIGVUL_MAPPING

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path / "data" / "logs"

def test_generate_mapping_document_structure():
    """Verify the mapping document has the required top-level keys."""
    doc = generate_mapping_document()
    
    assert "source_dataset" in doc
    assert doc["source_dataset"] == "JSVulnDB"
    
    assert "target_schema" in doc
    assert "BigVul" in doc["target_schema"]
    
    assert "field_mappings" in doc
    assert isinstance(doc["field_mappings"], dict)
    
    assert "transformation_rules" in doc
    assert "notes" in doc

def test_field_mappings_correctness():
    """Verify specific field mappings are present and correct."""
    doc = generate_mapping_document()
    mappings = doc["field_mappings"]
    
    # Check critical mappings
    assert mappings["jsvulndb_id"] == "snippet_id"
    assert mappings["vulnerable"] == "ground_truth_label"
    assert mappings["cwe"] == "cwe_id"
    assert mappings["category"] == "vulnerability_type"
    assert mappings["code"] == "code"
    assert mappings["language"] == "language"

def test_write_mapping_json(tmp_path):
    """Verify the JSON writing function creates a valid file."""
    output_dir = tmp_path / "data" / "logs"
    output_file = output_dir / "test_mapping.json"
    
    doc = generate_mapping_document()
    write_mapping_json(doc, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded_doc = json.load(f)
    
    assert loaded_doc == doc
    assert loaded_doc["source_dataset"] == "JSVulnDB"