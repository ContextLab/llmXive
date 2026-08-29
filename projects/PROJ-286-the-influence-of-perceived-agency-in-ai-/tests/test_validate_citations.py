import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.research.validate_citations import (
    tokenize, calculate_similarity, validate_citation, 
    PRIMARY_SOURCE_TRUTH
)

def test_tokenize():
    text = "Hello World"
    tokens = tokenize(text)
    assert "hello" in tokens
    assert "world" in tokens

def test_calculate_similarity():
    s1 = "The quick brown fox"
    s2 = "The quick brown fox"
    assert calculate_similarity(s1, s2) == 1.0

    s3 = "The quick brown fox"
    s4 = "The slow brown dog"
    sim = calculate_similarity(s3, s4)
    assert 0.0 < sim < 1.0

def test_validate_citation_structure():
    # Test against Primary Source Truth
    truth = PRIMARY_SOURCE_TRUTH["Lee & See (2004)"]
    result = validate_citation(truth["title"], truth["doi"], "Lee & See (2004)")
    assert result["status"] == "verified"
    assert result["claimed_doi"] == truth["doi"]

def test_validate_citation_mismatch():
    # Test with wrong DOI
    result = validate_citation("Trust in Automation", "10.0000/fake", "Lee & See (2004)")
    assert result["status"] == "failed"
    assert "DOI mismatch" in result["message"]

    # Test with wrong title
    result = validate_citation("Wrong Title", "10.1207/s15327566ijhc1601_4", "Lee & See (2004)")
    assert result["status"] == "failed"
    assert "Title mismatch" in result["message"]

def test_validate_citation_not_found():
    result = validate_citation("Some Title", "10.0000/fake", "Unknown Author (2099)")
    assert result["status"] == "failed"
    assert "not found in Primary Source Truth" in result["message"]

def test_main_execution():
    # Create temporary files for spec and plan
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "spec.md"
        plan_path = Path(tmpdir) / "plan.md"
        output_path = Path(tmpdir) / "validation_report.json"

        # Write valid content
        spec_content = """
        ## References
        Lee & See (2004) "Trust in Automation: Designing for Appropriate Reliance" (DOI: 10.1207/s15327566ijhc1601_4)
        """
        plan_content = """
        ## Plan
        Langer (1975) "The Illusion of Control" (DOI: 10.1037/h0076860)
        """

        spec_path.write_text(spec_content)
        plan_path.write_text(plan_content)

        # Run main
        from code.research.validate_citations import main
        import sys

        # Mock sys.argv
        original_argv = sys.argv
        sys.argv = [
            "validate_citations.py",
            "--spec", str(spec_path),
            "--plan", str(plan_path),
            "--output", str(output_path)
        ]

        try:
            main()
            # Check output
            assert output_path.exists()
            with open(output_path) as f:
                report = json.load(f)
            assert report["status"] == "verified"
            assert len(report["citations"]) == 2
        finally:
            sys.argv = original_argv
