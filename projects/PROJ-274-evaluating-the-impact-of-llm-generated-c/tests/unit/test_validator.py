import pytest
import json
import os
from pathlib import Path
from code.utils.validator import (
    tokenize_title, 
    calculate_jaccard_similarity, 
    validate_reference, 
    validate_citation, 
    validate_document_references,
    main
)

def test_tokenize_title():
    assert tokenize_title("Hello World") == ["hello", "world"]
    assert tokenize_title("") == []
    assert tokenize_title("Test-Case 123") == ["test", "case", "123"]

def test_jaccard_similarity():
    # Identical sets
    assert calculate_jaccard_similarity(["a", "b"], ["a", "b"]) == 1.0
    # Disjoint sets
    assert calculate_jaccard_similarity(["a"], ["b"]) == 0.0
    # Partial overlap
    result = calculate_jaccard_similarity(["a", "b", "c"], ["b", "c", "d"])
    assert result == 2/3  # 2 common / 4 total unique

def test_validate_document_references_missing_file():
    result = validate_document_references("non_existent_file.md")
    assert result["status"] == "error"
    assert result["valid"] is False

def test_validate_document_references_valid():
    # Create a temporary valid research file for testing
    test_dir = Path("specs/001-evaluating-the-impact-of-llm-generated-c")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_research.md"
    
    content = """
    # Statistical Methodology Appendix
    ## 1. Pre-specified Analysis Approach (Welch's ANOVA as primary, Levene's for diagnostics only)
    ## 2. Assumptions (Normality, Homogeneity)
    ## 3. Power Analysis (Variance estimation focus)
    """
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    try:
        result = validate_document_references(str(test_file))
        assert result["valid"] is True
        assert result["status"] == "all_valid"
        assert len(result["missing_sections"]) == 0
    finally:
        if test_file.exists():
            test_file.unlink()

def test_validate_document_references_missing_sections():
    test_dir = Path("specs/001-evaluating-the-impact-of-llm-generated-c")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_research_partial.md"
    
    # Missing section 3
    content = """
    # Statistical Methodology Appendix
    ## 1. Pre-specified Analysis Approach (Welch's ANOVA as primary, Levene's for diagnostics only)
    ## 2. Assumptions (Normality, Homogeneity)
    """
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    try:
        result = validate_document_references(str(test_file))
        assert result["valid"] is False
        assert result["status"] == "missing_sections"
        assert len(result["missing_sections"]) == 1
    finally:
        if test_file.exists():
            test_file.unlink()

def test_main_creates_lock_file():
    # Ensure the real research.md exists for the test
    research_path = Path("specs/001-evaluating-the-impact-of-llm-generated-c/research.md")
    # We assume this file exists based on the task context
    # If it doesn't, the test will fail, which is expected if the setup is wrong
    
    lock_file = Path("state/research_validated.lock")
    if lock_file.exists():
        lock_file.unlink()
    
    # Run main
    exit_code = main()
    
    assert exit_code == 0
    assert lock_file.exists()
    
    # Clean up
    lock_file.unlink()