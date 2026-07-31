"""
Tests for the limitation disclosure verification script.

These tests verify that the verification script correctly identifies:
1. Valid artifacts with proper limitation disclosures
2. Invalid artifacts missing limitation disclosures
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import nbformat

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from verification.verify_limitations import (
    check_json_file,
    check_notebook,
    check_python_script,
    verify_all_artifacts
)
from viz.templates import get_limitation_header, get_limitation_footer


class TestCheckJsonFile:
    """Tests for check_json_file function."""
    
    def test_valid_json_with_limitations(self, tmp_path):
        """Test that a valid JSON with limitations passes."""
        data = {
            "results": [{"tag": "python", "trend": "up"}],
            "limitations": "This analysis has certain limitations..."
        }
        
        filepath = tmp_path / "test.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        is_valid, issues = check_json_file(filepath)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_valid_json_with_metadata_limitations(self, tmp_path):
        """Test that a valid JSON with metadata.limitations passes."""
        data = {
            "results": [{"tag": "python", "trend": "up"}],
            "metadata": {
                "limitations": "This analysis has certain limitations..."
            }
        }
        
        filepath = tmp_path / "test.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        is_valid, issues = check_json_file(filepath)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_invalid_json_missing_limitations(self, tmp_path):
        """Test that a JSON without limitations fails."""
        data = {
            "results": [{"tag": "python", "trend": "up"}]
        }
        
        filepath = tmp_path / "test.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        is_valid, issues = check_json_file(filepath)
        
        assert is_valid is False
        assert len(issues) > 0
        assert any("Missing" in issue for issue in issues)
    
    def test_invalid_json_empty_limitations(self, tmp_path):
        """Test that a JSON with empty limitations fails."""
        data = {
            "results": [{"tag": "python", "trend": "up"}],
            "limitations": ""
        }
        
        filepath = tmp_path / "test.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        is_valid, issues = check_json_file(filepath)
        
        assert is_valid is False
        assert len(issues) > 0
        assert any("empty" in issue.lower() for issue in issues)
    
    def test_invalid_json_file(self, tmp_path):
        """Test that an invalid JSON file fails."""
        filepath = tmp_path / "test.json"
        with open(filepath, 'w') as f:
            f.write("not valid json {")
        
        is_valid, issues = check_json_file(filepath)
        
        assert is_valid is False
        assert len(issues) > 0
        assert any("Invalid JSON" in issue for issue in issues)

class TestCheckNotebook:
    """Tests for check_notebook function."""
    
    def test_valid_notebook_with_limitations(self, tmp_path):
        """Test that a valid notebook with limitations passes."""
        nb = nbformat.v4.new_notebook()
        
        # Add header cell
        header = get_limitation_header()
        nb.cells.append(nbformat.v4.new_markdown_cell(header))
        
        # Add content cell
        nb.cells.append(nbformat.v4.new_code_cell("# Analysis code"))
        
        # Add footer cell
        footer = get_limitation_footer()
        nb.cells.append(nbformat.v4.new_markdown_cell(footer))
        
        filepath = tmp_path / "test.ipynb"
        with open(filepath, 'w') as f:
            nbformat.write(nb, f)
        
        is_valid, issues = check_notebook(filepath)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_invalid_notebook_missing_header(self, tmp_path):
        """Test that a notebook missing header fails."""
        nb = nbformat.v4.new_notebook()
        
        # Add content cell
        nb.cells.append(nbformat.v4.new_code_cell("# Analysis code"))
        
        # Add footer cell
        footer = get_limitation_footer()
        nb.cells.append(nbformat.v4.new_markdown_cell(footer))
        
        filepath = tmp_path / "test.ipynb"
        with open(filepath, 'w') as f:
            nbformat.write(nb, f)
        
        is_valid, issues = check_notebook(filepath)
        
        assert is_valid is False
        assert len(issues) > 0
        assert any("header" in issue.lower() for issue in issues)
    
    def test_invalid_notebook_missing_footer(self, tmp_path):
        """Test that a notebook missing footer fails."""
        nb = nbformat.v4.new_notebook()
        
        # Add header cell
        header = get_limitation_header()
        nb.cells.append(nbformat.v4.new_markdown_cell(header))
        
        # Add content cell
        nb.cells.append(nbformat.v4.new_code_cell("# Analysis code"))
        
        filepath = tmp_path / "test.ipynb"
        with open(filepath, 'w') as f:
            nbformat.write(nb, f)
        
        is_valid, issues = check_notebook(filepath)
        
        assert is_valid is False
        assert len(issues) > 0
        assert any("footer" in issue.lower() for issue in issues)
    
    def test_invalid_notebook_empty(self, tmp_path):
        """Test that an empty notebook fails."""
        nb = nbformat.v4.new_notebook()
        
        filepath = tmp_path / "test.ipynb"
        with open(filepath, 'w') as f:
            nbformat.write(nb, f)
        
        is_valid, issues = check_notebook(filepath)
        
        assert is_valid is False
        assert len(issues) > 0
        assert any("no cells" in issue.lower() for issue in issues)

class TestCheckPythonScript:
    """Tests for check_python_script function."""
    
    def test_valid_script_with_injection(self, tmp_path):
        """Test that a valid script with injection passes."""
        content = """
        from viz.templates import get_limitation_header, inject_limitation_to_notebook
        
        def main():
            header = get_limitation_header()
            inject_limitation_to_notebook("test.ipynb")
        """
        
        filepath = tmp_path / "test.py"
        with open(filepath, 'w') as f:
            f.write(content)
        
        is_valid, issues = check_python_script(filepath)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_invalid_script_missing_import(self, tmp_path):
        """Test that a script missing import fails."""
        content = """
        def main():
            print("No imports")
        """
        
        filepath = tmp_path / "test.py"
        with open(filepath, 'w') as f:
            f.write(content)
        
        is_valid, issues = check_python_script(filepath)
        
        assert is_valid is False
        assert len(issues) > 0
        assert any("import" in issue.lower() for issue in issues)
    
    def test_invalid_script_missing_injection(self, tmp_path):
        """Test that a script missing injection call fails."""
        content = """
        from viz.templates import get_limitation_header
        
        def main():
            header = get_limitation_header()
            print(header)
        """
        
        filepath = tmp_path / "test.py"
        with open(filepath, 'w') as f:
            f.write(content)
        
        is_valid, issues = check_python_script(filepath)
        
        assert is_valid is False
        assert len(issues) > 0
        assert any("call" in issue.lower() for issue in issues)

class TestVerifyAllArtifacts:
    """Tests for verify_all_artifacts function."""
    
    def test_verify_all_artifacts_structure(self):
        """Test that verify_all_artifacts returns expected structure."""
        results = verify_all_artifacts()
        
        assert "total_files" in results
        assert "passed" in results
        assert "failed" in results
        assert "details" in results
        assert isinstance(results["details"], list)
        
        # Check that passed + failed equals total
        assert results["passed"] + results["failed"] == results["total_files"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])