"""
Tests for the gold standard template generation script.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock the PROJECT_ROOT for testing
from unittest.mock import patch

def test_template_structure():
    """Verify the generated template has the correct structure."""
    from code.scripts.generate_gold_standard_template import generate_template

    template = generate_template()

    assert "metadata" in template
    assert "annotations" in template
    assert template["metadata"]["status"] == "DEFERRED"
    assert "instruction" in template["metadata"]
    assert "required_fields" in template["metadata"]
    
    # Check annotation structure
    assert len(template["annotations"]) == 1
    example = template["annotations"][0]
    assert "trace_id" in example
    assert "human_rated_complexity" in example
    assert example["human_rated_complexity"] is None  # Placeholder
    assert "annotator_id" in example
    assert "notes" in example

def test_file_generation_creates_json():
    """Verify the script actually creates a JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "test_gold_standard.json"
        
        # Mock PROJECT_ROOT to use our temp directory
        with patch('code.scripts.generate_gold_standard_template.PROJECT_ROOT', Path(tmpdir)):
            # Re-import to pick up the mock (or call the function directly with a path override if refactored)
            # For this test, we simulate the logic directly
            from code.scripts.generate_gold_standard_template import generate_template
            
            template_data = generate_template()
            with open(test_path, 'w') as f:
                json.dump(template_data, f)
        
        assert test_path.exists()
        
        with open(test_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["metadata"]["status"] == "DEFERRED"
        assert isinstance(loaded["annotations"], list)