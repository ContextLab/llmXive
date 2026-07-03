"""
Unit tests for the prompt parser module.

These tests verify the structural element counting logic
and complexity score calculation.
"""

import pytest
from code.prompts.parser import (
    count_examples,
    count_constraints,
    count_instructions,
    count_definitions,
    count_comments,
    parse_prompt_structure,
    StructuralMetrics,
    calculate_complexity_score
)


class TestCountExamples:
    """Tests for example counting logic."""

    def test_empty_text(self):
        assert count_examples("") == 0
        assert count_examples(None) == 0

    def test_explicit_example_markers(self):
        text = "Here is an example: Input: 1 Output: 2"
        assert count_examples(text) >= 1

    def test_repl_style(self):
        text = ">>> func(1)\n2"
        assert count_examples(text) >= 1

    def test_input_output_pairs(self):
        text = "Input: 5\nOutput: 10\nInput: 3\nOutput: 6"
        assert count_examples(text) >= 2

    def test_no_examples(self):
        text = "This is just a description without examples."
        assert count_examples(text) == 0


class TestCountConstraints:
    """Tests for constraint counting logic."""

    def test_empty_text(self):
        assert count_constraints("") == 0

    def test_constraints_section(self):
        text = "Constraints: The input must be positive."
        assert count_constraints(text) >= 1

    def test_modal_verbs(self):
        text = "You must not use loops. You should optimize."
        assert count_constraints(text) >= 2

    def test_complexity_requirements(self):
        text = "Time complexity must be O(n). Memory limit is 256MB."
        assert count_constraints(text) >= 2

    def test_input_ranges(self):
        text = "1 <= n <= 100"
        assert count_constraints(text) >= 1


class TestCountInstructions:
    """Tests for instruction counting logic."""

    def test_empty_text(self):
        assert count_instructions("") == 0

    def test_task_marker(self):
        text = "Your task is to write a function."
        assert count_instructions(text) >= 1

    def test_numbered_list(self):
        text = "1. First step.\n2. Second step."
        assert count_instructions(text) >= 2

    def test_imperative_verbs(self):
        text = "Write a function. Implement the logic."
        assert count_instructions(text) >= 2

    def test_minimum_instruction(self):
        text = "Do something."
        assert count_instructions(text) >= 1


class TestCountDefinitions:
    """Tests for definition counting logic."""

    def test_empty_text(self):
        assert count_definitions("") == 0

    def test_function_definition(self):
        text = "def my_function(x):\n    return x"
        assert count_definitions(text) >= 1

    def test_class_definition(self):
        text = "class MyClass:\n    pass"
        assert count_definitions(text) >= 1

    def test_multiple_definitions(self):
        text = "def func1(): pass\ndef func2(): pass\nclass A: pass"
        assert count_definitions(text) >= 3


class TestCountComments:
    """Tests for comment counting logic."""

    def test_empty_text(self):
        assert count_comments("") == 0

    def test_single_line_comment(self):
        text = "# This is a comment\nx = 1"
        assert count_comments(text) >= 1

    def test_docstring(self):
        text = '"""This is a docstring."""\ndef f(): pass'
        assert count_comments(text) >= 1


class TestParsePromptStructure:
    """Tests for the main parsing function."""

    def test_complex_prompt(self):
        text = """
        Your task is to implement a function.
        Constraints:
        - Must be O(n)
        - Input must be positive

        Example:
        >>> solve(5)
        10

        def solve(n):
            # Implementation here
            pass
        """
        metrics = parse_prompt_structure(text)

        assert metrics.example_count >= 1
        assert metrics.constraint_count >= 1
        assert metrics.instruction_count >= 1
        assert metrics.definition_count >= 1
        assert metrics.comment_count >= 1
        assert metrics.total_structural_elements > 0
        assert metrics.complexity_score > 0

    def test_simple_prompt(self):
        text = "Write a function to add two numbers."
        metrics = parse_prompt_structure(text)

        assert metrics.example_count == 0
        assert metrics.constraint_count == 0
        assert metrics.instruction_count >= 1
        assert metrics.total_structural_elements >= 1

    def test_empty_prompt(self):
        metrics = parse_prompt_structure("")
        assert metrics.total_structural_elements == 0
        assert metrics.complexity_score == 0


class TestCalculateComplexityScore:
    """Tests for complexity score calculation."""

    def test_zero_metrics(self):
        metrics = StructuralMetrics()
        assert calculate_complexity_score(metrics) == 0.0

    def test_example_weight(self):
        metrics = StructuralMetrics(example_count=5)
        score = calculate_complexity_score(metrics)
        assert score == 5 * 2.0

    def test_constraint_weight(self):
        metrics = StructuralMetrics(constraint_count=3)
        score = calculate_complexity_score(metrics)
        assert score == 3 * 1.5

    def test_combined_weights(self):
        metrics = StructuralMetrics(
            example_count=2,
            constraint_count=1,
            instruction_count=1
        )
        expected = (2 * 2.0) + (1 * 1.5) + (1 * 1.0)
        assert calculate_complexity_score(metrics) == expected