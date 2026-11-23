import pytest
import pandas as pd
from code.prompt_engineering import _determine_complexity, _build_prompt

def test_determine_complexity_simple():
    assert _determine_complexity("Update README.md") == "simple"
    assert _determine_complexity("Fix typo in docs") == "moderate" # 'fix' is moderate
    assert _determine_complexity("random text") == "simple"

def test_determine_complexity_moderate():
    assert _determine_complexity("Add user login feature") == "moderate"
    assert _determine_complexity("Implement new API endpoint") == "moderate"
    assert _determine_complexity("Fix bug in parser") == "moderate"

def test_determine_complexity_complex():
    assert _determine_complexity("Rewrite the memory allocator for performance") == "complex"
    assert _determine_complexity("Refactor core architecture") == "complex"
    assert _determine_complexity("Optimize database queries for scalability") == "complex"

def test_build_prompt():
    msg = "Add user authentication"
    comp = "moderate"
    prompt = _build_prompt(msg, comp)
    assert "moderate-complexity" in prompt
    assert "Add user authentication" in prompt
    assert prompt.startswith("Write a")

def test_determine_complexity_invalid_input():
    assert _determine_complexity(None) == "simple"
    assert _determine_complexity(123) == "simple"