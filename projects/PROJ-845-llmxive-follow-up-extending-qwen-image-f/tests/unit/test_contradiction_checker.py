"""
Unit tests for the contradiction detection module.
"""
import pytest
from unittest.mock import Mock

from models.synthetic_problem import SyntheticProblem
from generators.contradiction_checker import (
    is_problem_solvable,
    filter_contradictions,
    _parse_literal,
    _solve_satisfiability
)


class TestParseLiteral:
    def test_positive_literal(self):
        var, is_pos = _parse_literal("A")
        assert var == "A"
        assert is_pos is True

    def test_negative_literal(self):
        var, is_pos = _parse_literal("not A")
        assert var == "A"
        assert is_pos is False

    def test_whitespace_handling(self):
        var, is_pos = _parse_literal("  not A  ")
        assert var == "A"
        assert is_pos is False


class TestSolveSatisfiability:
    def test_simple_satisfiable(self):
        premises = ["A and B"]
        result = _solve_satisfiability(premises, 2)
        assert result is not None
        assert result.get("A") is True
        assert result.get("B") is True

    def test_simple_unsatisfiable(self):
        # A and not A is unsatisfiable
        premises = ["A and not A"]
        result = _solve_satisfiability(premises, 1)
        assert result is None

    def test_disjunction_satisfiable(self):
        premises = ["A or B"]
        result = _solve_satisfiability(premises, 2)
        assert result is not None
        # At least one should be true
        assert result.get("A") is True or result.get("B") is True

    def test_empty_premises(self):
        result = _solve_satisfiability([], 0)
        assert result == {}


class TestIsProblemSolvable:
    def test_solvable_problem(self):
        problem = SyntheticProblem(
            id="test_1",
            premises=["A and B"],
            operators=["and"],
            solution="A",
            entropy_level="low",
            metadata={}
        )
        assert is_problem_solvable(problem) is True

    def test_unsolvable_problem(self):
        problem = SyntheticProblem(
            id="test_2",
            premises=["A and not A"],
            operators=["and", "not"],
            solution="B",
            entropy_level="low",
            metadata={}
        )
        assert is_problem_solvable(problem) is False

    def test_complex_satisfiable(self):
        problem = SyntheticProblem(
            id="test_3",
            premises=["A or B", "not A"],
            operators=["or", "not"],
            solution="B",
            entropy_level="medium",
            metadata={}
        )
        assert is_problem_solvable(problem) is True


class TestFilterContradictions:
    def test_filter_removes_unsolvable(self):
        problems = [
            SyntheticProblem(
                id="solvable_1",
                premises=["A and B"],
                operators=["and"],
                solution="A",
                entropy_level="low",
                metadata={}
            ),
            SyntheticProblem(
                id="unsolvable_1",
                premises=["A and not A"],
                operators=["and", "not"],
                solution="B",
                entropy_level="low",
                metadata={}
            ),
            SyntheticProblem(
                id="solvable_2",
                premises=["A or B"],
                operators=["or"],
                solution="A",
                entropy_level="high",
                metadata={}
            )
        ]
        
        filtered = filter_contradictions(problems)
        
        assert len(filtered) == 2
        assert all(p.id != "unsolvable_1" for p in filtered)
        assert any(p.id == "solvable_1" for p in filtered)
        assert any(p.id == "solvable_2" for p in filtered)

    def test_all_solvable(self):
        problems = [
            SyntheticProblem(
                id="s1",
                premises=["A"],
                operators=[],
                solution="A",
                entropy_level="low",
                metadata={}
            ),
            SyntheticProblem(
                id="s2",
                premises=["B"],
                operators=[],
                solution="B",
                entropy_level="low",
                metadata={}
            )
        ]
        
        filtered = filter_contradictions(problems)
        assert len(filtered) == 2

    def test_all_unsolvable(self):
        problems = [
            SyntheticProblem(
                id="u1",
                premises=["A and not A"],
                operators=["and", "not"],
                solution="B",
                entropy_level="low",
                metadata={}
            ),
            SyntheticProblem(
                id="u2",
                premises=["B and not B"],
                operators=["and", "not"],
                solution="A",
                entropy_level="low",
                metadata={}
            )
        ]
        
        filtered = filter_contradictions(problems)
        assert len(filtered) == 0