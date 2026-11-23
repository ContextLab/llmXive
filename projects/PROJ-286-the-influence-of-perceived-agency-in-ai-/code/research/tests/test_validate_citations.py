"""
Unit tests for the citation validation module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from code.research.validate_citations import (
    tokenize,
    calculate_similarity,
    calculate_similarity_empty,
    validate_citation_structure,
    validate_citation,
    main
)
import sys
import io

def test_tokenize():
    """Test tokenization of a string."""
    text = "Lee & See (2004)"
    tokens = tokenize(text)
    assert "lee" in tokens
    assert "see" in tokens
    assert "2004" in tokens
    assert "&" not in tokens

def test_calculate_similarity():
    """Test similarity calculation between two strings."""
    str1 = "Trust in Automation"
    str2 = "Trust in Automated Systems"
    similarity = calculate_similarity(str1, str2)
    assert 0.0 <= similarity <= 1.0
    # Should have significant overlap
    assert similarity > 0.5

def test_calculate_similarity_empty():
    """Test similarity calculation with empty strings."""
    assert calculate_similarity("", "") == 0.0
    assert calculate_similarity("test", "") == 0.0
    assert calculate_similarity("", "test") == 0.0

def test_validate_citation_structure():
    """Test validation of citation structure."""
    valid_citations = [
        "Lee & See (2004)",
        "Langer (1975)",
        "Author A & Author B (2020)"
    ]
    
    invalid_citations = [
        "Lee & See 2004",  # Missing parentheses
        "Lee See (2004)",  # Missing ampersand (format issue)
        "Lee & See (24)",  # Wrong year format
        "Lee & See"  # Missing year
    ]
    
    for citation in valid_citations:
        # Should not raise an exception
        try:
            validate_citation_structure(citation)
        except Exception:
            pytest.fail(f"Valid citation {citation} raised an exception")
    
    for citation in invalid_citations:
        # Should raise ValueError
        with pytest.raises(ValueError):
            validate_citation_structure(citation)

def validate_citation_structure(citation: str):
    """
    Validate that a citation string has the expected structure.
    Expected format: 'Author(s) (Year)'
    """
    import re
    pattern = r'^.+?\s*\(\d{4}\)$'
    if not re.match(pattern, citation):
        raise ValueError(f"Invalid citation format: {citation}")

def test_main_execution():
    """Test the main function execution."""
    # Create temporary files for input and output
    with tempfile.TemporaryDirectory() as tmpdir:
        input_citations = "Lee & See (2004), Langer (1975)"
        output_file = Path(tmpdir) / "validation_report.json"
        
        # Mock command line arguments
        original_argv = sys.argv
        sys.argv = [
            "validate_citations.py",
            "--citations", input_citations,
            "--output", str(output_file)
        ]
        
        try:
            result = main()
            assert result == 0
            assert output_file.exists()
            
            # Verify output content
            with open(output_file, 'r') as f:
                report = json.load(f)
            
            assert "results" in report
            assert len(report["results"]) == 2
            assert report["citations_validated"] == 2
        finally:
            sys.argv = original_argv
