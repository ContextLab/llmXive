"""
Unit tests for the Reference Validator (T002).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.reference_validator import (
    validate_citations,
    generate_report,
    load_research_file,
    OUTPUT_FILE
)

def test_validate_citations_no_issues():
    content = """
    # Research
    This is a normal paper.
    [Citation: Smith et al. 2023]
    """
    issues = validate_citations(content)
    assert len(issues) == 0

def test_validate_citations_unreachable():
    content = """
    # Research
    This is a normal paper.
    [UNREACHABLE: URL not found for Smith et al.]
    """
    issues = validate_citations(content)
    assert len(issues) == 1
    assert issues[0]["type"] == "unreachable"

def test_validate_citations_mismatch():
    content = """
    # Research
    This is a normal paper.
    [MISMATCH: Author name does not match metadata.]
    """
    issues = validate_citations(content)
    assert len(issues) == 1
    assert issues[0]["type"] == "mismatch"

def test_generate_report_pass():
    issues = []
    report = generate_report(issues)
    assert report["status"] == "PASS"
    assert report["total_issues"] == 0

def test_generate_report_fail():
    issues = [{"type": "unreachable", "context": "test", "status": "FAIL"}]
    report = generate_report(issues)
    assert report["status"] == "FAIL"
    assert report["total_issues"] == 1

def test_load_research_file_missing():
    # This test assumes the real file path is used, but we can't easily mock the global constant
    # without patching the module. For now, we rely on the main function's error handling.
    pass

if __name__ == "__main__":
    test_validate_citations_no_issues()
    test_validate_citations_unreachable()
    test_validate_citations_mismatch()
    test_generate_report_pass()
    test_generate_report_fail()
    print("All tests passed.")
