"""
Unit tests for Few-shot prompt structure validation.
Tests that the few-shot prompt generation adheres to the expected format
defined in the project specifications for User Story 2.
"""
import pytest
from typing import List, Dict, Any

from src.evaluation.prompts import create_few_shot_prompt, format_examples


class TestFewShotPromptStructure:
    """Test cases for Few-shot prompt generation."""

    def test_prompt_contains_examples(self):
        """Verify that the prompt includes the required 3 examples."""
        examples = [
            {
                "description": "Example 1 description",
                "code": "def example1():\n    return 1",
                "test": "assert example1() == 1"
            },
            {
                "description": "Example 2 description",
                "code": "def example2():\n    return 2",
                "test": "assert example2() == 2"
            },
            {
                "description": "Example 3 description",
                "code": "def example3():\n    return 3",
                "test": "assert example3() == 3"
            }
        ]
        
        task_description = "Test task description"
        prompt = create_few_shot_prompt(task_description, examples)
        
        # Verify all examples are present in the prompt
        for i, example in enumerate(examples):
            assert example["description"] in prompt, f"Example {i+1} description missing"
            assert example["code"] in prompt, f"Example {i+1} code missing"
            assert example["test"] in prompt, f"Example {i+1} test missing"

    def test_prompt_contains_task_description(self):
        """Verify that the prompt includes the target task description."""
        examples = [
            {
                "description": "Example 1",
                "code": "def ex(): pass",
                "test": "assert True"
            },
            {
                "description": "Example 2",
                "code": "def ex(): pass",
                "test": "assert True"
            },
            {
                "description": "Example 3",
                "code": "def ex(): pass",
                "test": "assert True"
            }
        ]
        
        task_description = "Write a function that adds two numbers"
        prompt = create_few_shot_prompt(task_description, examples)
        
        assert task_description in prompt, "Task description not found in prompt"

    def test_prompt_structure_order(self):
        """Verify the logical order: Examples -> Task Description -> Instruction."""
        examples = [
            {
                "description": "First example",
                "code": "def first(): pass",
                "test": "assert True"
            },
            {
                "description": "Second example",
                "code": "def second(): pass",
                "test": "assert True"
            },
            {
                "description": "Third example",
                "code": "def third(): pass",
                "test": "assert True"
            }
        ]
        
        task_description = "Target task"
        prompt = create_few_shot_prompt(task_description, examples)
        
        # Check that examples appear before the task description
        first_example_pos = prompt.find("First example")
        task_pos = prompt.find("Target task")
        
        assert first_example_pos != -1, "First example not found"
        assert task_pos != -1, "Task description not found"
        assert first_example_pos < task_pos, "Examples should appear before task description"

    def test_prompt_with_empty_examples(self):
        """Verify behavior when examples list is empty (should not crash)."""
        task_description = "Test task"
        with pytest.raises((ValueError, AssertionError)):
            create_few_shot_prompt(task_description, [])

    def test_prompt_contains_generation_instruction(self):
        """Verify that the prompt ends with a clear instruction to generate code."""
        examples = [
            {
                "description": "Ex 1",
                "code": "def ex(): pass",
                "test": "assert True"
            },
            {
                "description": "Ex 2",
                "code": "def ex(): pass",
                "test": "assert True"
            },
            {
                "description": "Ex 3",
                "code": "def ex(): pass",
                "test": "assert True"
            }
        ]
        
        task_description = "Test task"
        prompt = create_few_shot_prompt(task_description, examples)
        
        # Check for common instruction keywords
        instruction_keywords = ["write", "implement", "generate", "solution"]
        found_instruction = any(keyword in prompt.lower() for keyword in instruction_keywords)
        
        assert found_instruction, "Prompt should contain an instruction to generate code"

    def test_format_examples_function(self):
        """Test the helper function that formats examples for the prompt."""
        examples = [
            {
                "description": "Example A",
                "code": "def a():\n    return 'a'",
                "test": "assert a() == 'a'"
            },
            {
                "description": "Example B",
                "code": "def b():\n    return 'b'",
                "test": "assert b() == 'b'"
            },
            {
                "description": "Example C",
                "code": "def c():\n    return 'c'",
                "test": "assert c() == 'c'"
            }
        ]
        
        formatted = format_examples(examples)
        
        assert isinstance(formatted, str), "format_examples should return a string"
        assert "Example A" in formatted, "First example missing from formatted output"
        assert "Example B" in formatted, "Second example missing from formatted output"
        assert "Example C" in formatted, "Third example missing from formatted output"
        assert "def a():" in formatted, "Code block missing from formatted output"

    def test_few_shot_prompt_example_count(self):
        """Verify that exactly 3 examples are used in the prompt construction."""
        # Create exactly 3 examples
        examples = [
            {
                "description": f"Example {i+1}",
                "code": f"def func_{i+1}():\n    return {i+1}",
                "test": f"assert func_{i+1}() == {i+1}"
            }
            for i in range(3)
        ]
        
        task_description = "Test task"
        prompt = create_few_shot_prompt(task_description, examples)
        
        # Count occurrences of example markers
        example_count = sum(1 for i in range(1, 4) if f"Example {i}" in prompt)
        assert example_count == 3, f"Expected 3 examples, found {example_count}"