"""
Unit tests for the symbolic explanation generator.
"""
import pytest
import json
import os
import tempfile
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from generate.symbolic_explanation import (
    SymbolicSolver,
    generate_symbolic_explanation,
    CommutativityRule,
    AssociativityRule,
    DistributiveRule,
    IdentityElementRule
)


class TestCommutativityRule:
    """Tests for the commutativity rule."""

    def test_addition_swap(self):
        rule = CommutativityRule()
        result = rule.apply("2 + 3")
        assert result is not None
        assert result[0] == "3 + 2"
        assert "commutativity" in result[1]

    def test_multiplication_swap(self):
        rule = CommutativityRule()
        result = rule.apply("4 * 5")
        assert result is not None
        assert result[0] == "5 * 4"

    def test_no_swap_identical_operands(self):
        rule = CommutativityRule()
        result = rule.apply("3 + 3")
        assert result is None

    def test_non_matching_expression(self):
        rule = CommutativityRule()
        result = rule.apply("2 - 3")
        assert result is None


class TestAssociativityRule:
    """Tests for the associativity rule."""

    def test_left_to_right_association(self):
        rule = AssociativityRule()
        result = rule.apply("(2 + 3) + 4")
        assert result is not None
        assert result[0] == "2 + (3 + 4)"

    def test_right_to_left_association(self):
        rule = AssociativityRule()
        result = rule.apply("2 + (3 + 4)")
        assert result is not None
        assert result[0] == "(2 + 3) + 4"

    def test_multiplication_associativity(self):
        rule = AssociativityRule()
        result = rule.apply("(2 * 3) * 4")
        assert result is not None
        assert result[0] == "2 * (3 * 4)"


class TestDistributiveRule:
    """Tests for the distributivity rule."""

    def test_distribute_left(self):
        rule = DistributiveRule()
        result = rule.apply("2 * (3 + 4)")
        assert result is not None
        assert result[0] == "(2 * 3) + (2 * 4)"

    def test_distribute_right(self):
        rule = DistributiveRule()
        result = rule.apply("(3 + 4) * 2")
        assert result is not None
        assert result[0] == "(2 * 3) + (2 * 4)"


class TestIdentityElementRule:
    """Tests for the identity element rule."""

    def test_add_zero_left(self):
        rule = IdentityElementRule()
        result = rule.apply("0 + 5")
        assert result is not None
        assert result[0] == "5"

    def test_add_zero_right(self):
        rule = IdentityElementRule()
        result = rule.apply("5 + 0")
        assert result is not None
        assert result[0] == "5"

    def test_mul_one_left(self):
        rule = IdentityElementRule()
        result = rule.apply("1 * 7")
        assert result is not None
        assert result[0] == "7"

    def test_mul_one_right(self):
        rule = IdentityElementRule()
        result = rule.apply("7 * 1")
        assert result is not None
        assert result[0] == "7"


class TestSymbolicSolver:
    """Tests for the full symbolic solver."""

    def test_simple_addition(self):
        solver = SymbolicSolver()
        result = solver.solve("P001", "2 + 3")
        assert result["problem_id"] == "P001"
        assert result["final_value"] == 5
        assert len(result["trace"]) > 1

    def test_identity_simplification(self):
        solver = SymbolicSolver()
        result = solver.solve("P002", "5 * 1")
        assert result["final_value"] == 5
        rules_applied = [t for t in result["trace"] if t["rule_applied"] == "identity_element"]
        assert len(rules_applied) >= 1

    def test_distributive_simplification(self):
        solver = SymbolicSolver()
        result = solver.solve("P003", "2 * (3 + 4)")
        # Should apply distributivity then evaluate
        assert result["final_value"] == 14
        rules_applied = [t for t in result["trace"] if t["rule_applied"] == "distributivity"]
        assert len(rules_applied) >= 1

    def test_trace_structure(self):
        solver = SymbolicSolver()
        result = solver.solve("P004", "1 + 2")
        assert "trace" in result
        for step in result["trace"]:
            assert "step" in step
            assert "expression" in step
            assert "rule_applied" in step
            assert "explanation" in step


class TestGenerateSymbolicExplanation:
    """Tests for the file I/O function."""

    def test_write_json_trace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_trace.json")
            result = generate_symbolic_explanation("TEST001", "2 + 2", output_path)

            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded["problem_id"] == "TEST001"
            assert loaded["final_value"] == 4