"""
Unit tests for T000 - Spec-Task Alignment Review
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

import spec_alignment

def test_load_file_content_existing():
    """Test loading an existing file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("# Test Content")
        temp_path = Path(f.name)
    
    try:
        content = spec_alignment.load_file_content(temp_path)
        assert content == "# Test Content"
    finally:
        temp_path.unlink()

def test_load_file_content_missing():
    """Test loading a non-existing file."""
    result = spec_alignment.load_file_content(Path("/non/existent/path.md"))
    assert result is None

def test_check_path_existence():
    """Test path existence checking."""
    # Test existing path (current directory)
    assert spec_alignment.check_path_existence(".")
    
    # Test non-existing path
    assert not spec_alignment.check_path_existence("non_existent_directory")

def test_analyze_spec_tasks_alignment_basic():
    """Test basic alignment analysis."""
    spec_content = "FR-001: Requirement 1\nNFR-001: Performance requirement"
    tasks_content = "- [T001] FR-001: Implement requirement 1\n- [T002] NFR-001: Optimize performance"
    
    results = spec_alignment.analyze_spec_tasks_alignment(spec_content, tasks_content)
    
    assert "contradictions" in results
    assert "missing_requirements" in results
    assert "path_inconsistencies" in results
    assert "missing_dependencies" in results
    assert "suggestions" in results
    
    # Should not have missing requirements since both are addressed
    assert len(results["missing_requirements"]) == 0

def test_analyze_spec_tasks_alignment_missing():
    """Test alignment analysis with missing requirements."""
    spec_content = "FR-001: Requirement 1\nFR-002: Requirement 2"
    tasks_content = "- [T001] FR-001: Implement requirement 1"
    
    results = spec_alignment.analyze_spec_tasks_alignment(spec_content, tasks_content)
    
    # Should have one missing requirement
    assert len(results["missing_requirements"]) == 1
    assert results["missing_requirements"][0]["requirement"] == "FR-002"

def test_generate_report_empty_issues():
    """Test report generation with no issues."""
    results = {
        "contradictions": [],
        "missing_requirements": [],
        "path_inconsistencies": [],
        "missing_dependencies": [],
        "suggestions": ["All checks passed."]
    }
    
    report = spec_alignment.generate_report(results)
    
    assert "Alignment Status: PASSED" in report
    assert "No contradictions or missing elements" in report

def test_generate_report_with_issues():
    """Test report generation with issues."""
    results = {
        "contradictions": [{"type": "PATH", "description": "Path mismatch", "severity": "HIGH"}],
        "missing_requirements": [],
        "path_inconsistencies": [],
        "missing_dependencies": [],
        "suggestions": []
    }
    
    report = spec_alignment.generate_report(results)
    
    assert "Alignment Status: NEEDS ATTENTION" in report
    assert "Contradictions" in report
    assert "Path mismatch" in report

def test_main_execution():
    """Test main execution with mock files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock spec and tasks files
        spec_file = temp_path / "spec.md"
        tasks_file = temp_path / "tasks.md"
        docs_dir = temp_path / "docs"
        docs_dir.mkdir()
        
        spec_file.write_text("FR-001: Test requirement")
        tasks_file.write_text("- [T001] FR-001: Implement requirement")
        
        # Mock PROJECT_ROOT
        with patch.object(spec_alignment, 'PROJECT_ROOT', temp_path):
            with patch.object(spec_alignment, 'SPEC_PATH', spec_file):
                with patch.object(spec_alignment, 'TASKS_PATH', tasks_file):
                    with patch.object(spec_alignment, 'REPORT_PATH', docs_dir / "spec_alignment_report.md"):
                        result = spec_alignment.main()
                        
                        # Should complete successfully
                        assert result == 0
                        
                        # Report should be generated
                        report_path = docs_dir / "spec_alignment_report.md"
                        assert report_path.exists()
                        assert "Alignment Status" in report_path.read_text()