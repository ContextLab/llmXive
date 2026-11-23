"""
Unit tests for the Dependency Chain Depth Analyzer.
"""
import pytest
from prompts.dependency_analyzer import calculate_dependency_depth, analyze_variant_depth
from models.data_models import PromptVariant

def test_empty_prompt():
    """Test that empty prompt returns depth 0."""
    assert calculate_dependency_depth("") == 0
    assert calculate_dependency_depth("   ") == 0

def test_simple_prompt_no_keywords():
    """Test a simple prompt with no instruction keywords."""
    prompt = "Write a function to add two numbers."
    # Should return 1 as there is at least one instruction
    assert calculate_dependency_depth(prompt) >= 1

def test_single_instruction_keyword():
    """Test a prompt with a single instruction keyword."""
    prompt = "First, write a function to add two numbers."
    depth = calculate_dependency_depth(prompt)
    assert depth >= 1

def test_chained_instructions():
    """Test a prompt with chained instructions."""
    prompt = """
    First, define a function.
    Next, implement the logic.
    Then, return the result.
    """
    depth = calculate_dependency_depth(prompt)
    # Should detect a chain of at least 3
    assert depth >= 3

def test_conditional_instructions():
    """Test a prompt with conditional instructions."""
    prompt = """
    If the input is negative, return an error.
    Otherwise, proceed with the calculation.
    """
    depth = calculate_dependency_depth(prompt)
    # Should detect the conditional structure
    assert depth >= 1

def test_dependency_references():
    """Test a prompt with explicit dependency references."""
    prompt = """
    Step 1: Define the input.
    Step 2: Based on the previous step, validate the input.
    Step 3: Following the validation, process the data.
    """
    depth = calculate_dependency_depth(prompt)
    # Should detect the dependencies and return a depth > 1
    assert depth > 1

def test_analyze_variant_depth():
    """Test the analyze_variant_depth function with a PromptVariant object."""
    variant = PromptVariant(
        variant_id="test-1",
        problem_id="prob-1",
        complexity_label="simple",
        prompt_text="First, do this. Next, do that.",
        token_count=10,
        structural_element_count={"examples": 0, "constraints": 0, "steps": 2},
        dependency_depth=0
    )
    
    depth = analyze_variant_depth(variant)
    assert depth >= 2  # Should detect at least 2 steps

def test_complex_nested_instructions():
    """Test a prompt with complex nested instructions."""
    prompt = """
    First, initialize the system.
    If the system is ready, then:
      Next, load the configuration.
      Then, start the services.
      If services start, finally:
        Next, run the tests.
    """
    depth = calculate_dependency_depth(prompt)
    # Should detect a deep chain
    assert depth >= 4