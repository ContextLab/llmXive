import pytest
import json
import os
import tempfile
from pathlib import Path
from tools.reference_validator import ReferenceValidator, Citation, ValidationResult

@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create directories
        (tmpdir / "idea").mkdir()
        (tmpdir / "technical-design").mkdir()
        (tmpdir / "implementation-plan").mkdir()
        (tmpdir / "paper").mkdir()
        
        # Create test files with citations
        (tmpdir / "idea" / "concept.md").write_text(
            "This is a concept based on [1] and [2014].\n"
            "Another reference to [2]."
        )
        
        (tmpdir / "paper" / "draft.tex").write_text(
            "As shown in Ref. [3], the results are significant.\n"
            "See also [1]."
        )
        
        # Create a bibliography file
        bib_data = {
            "1": {"title": "Paper One", "author": "Author A"},
            "2": {"title": "Paper Two", "author": "Author B"},
            "3": {"title": "Paper Three", "author": "Author C"},
            "2014": {"title": "Year 2014 Paper", "author": "Author D"}
        }
        (tmpdir / "paper" / "references.json").write_text(json.dumps(bib_data))
        
        yield tmpdir

def test_scan_files(temp_project):
    """Test that the validator correctly scans files and finds citations."""
    validator = ReferenceValidator(project_root=str(temp_project))
    citations = validator.scan_files()
    
    assert len(citations) == 5  # [1], [2014], [2], Ref. [3], [1]
    
    # Check specific citations
    keys = [c.parsed_key for c in citations]
    assert "1" in keys
    assert "2014" in keys
    assert "2" in keys
    assert "3" in keys

def test_validate_citations(temp_project):
    """Test that citations are validated correctly against bibliography."""
    validator = ReferenceValidator(project_root=str(temp_project))
    validator.load_bibliography()
    validator.scan_files()
    
    result = validator.validate()
    
    assert result.total_citations == 5
    assert result.valid_citations == 5  # All keys exist in bib
    assert result.invalid_citations == 0

def test_validate_missing_citations(temp_project):
    """Test validation when a citation key is missing from bibliography."""
    # Modify a file to include a missing reference
    (temp_project / "idea" / "concept.md").write_text(
        "This is a concept based on [1] and [999]."
    )
    
    validator = ReferenceValidator(project_root=str(temp_project))
    validator.load_bibliography()
    validator.scan_files()
    
    result = validator.validate()
    
    assert result.total_citations == 2
    assert result.valid_citations == 1
    assert result.invalid_citations == 1
    
    # Check the error message
    invalid_cites = [c for c in result.details if c.validity_status == "invalid"]
    assert len(invalid_cites) == 1
    assert "999" in invalid_cites[0].parsed_key
    assert "not found" in invalid_cites[0].error_message

def test_generate_report(temp_project):
    """Test that the report is generated correctly."""
    validator = ReferenceValidator(project_root=str(temp_project))
    validator.load_bibliography()
    validator.scan_files()
    validator.validate()
    
    report_path = validator.generate_report(output_dir=str(temp_project / "reports"))
    
    assert os.path.exists(report_path)
    assert report_path.endswith(".json")
    
    # Verify report content
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    assert "summary" in report_data
    assert "citations" in report_data
    assert report_data["summary"]["total"] == 5

def test_no_bibliography(temp_project):
    """Test behavior when no bibliography is found."""
    # Remove bibliography file
    (temp_project / "paper" / "references.json").unlink()
    
    validator = ReferenceValidator(project_root=str(temp_project))
    validator.load_bibliography()
    validator.scan_files()
    
    result = validator.validate()
    
    # All citations should be invalid due to missing bibliography
    assert result.invalid_citations == 5
    assert result.valid_citations == 0

def test_non_existent_directory(temp_project):
    """Test handling of non-existent directories."""
    # Modify scan_dirs to include a non-existent directory
    validator = ReferenceValidator(project_root=str(temp_project))
    validator.scan_dirs = ["non_existent_dir", "idea"]
    
    citations = validator.scan_files()
    
    # Should still find citations in 'idea'
    assert len(citations) > 0