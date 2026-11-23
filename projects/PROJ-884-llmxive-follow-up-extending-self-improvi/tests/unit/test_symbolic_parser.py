"""
Unit tests for the symbolic parser module.
"""

import json
import pytest
from pathlib import Path
import tempfile
import os

from code.symbolic.parser import (
    FormalConstraintType,
    FormalConstraint,
    PuzzleParser,
    main
)
from code.symbolic.exclusion_logger import ExclusionLogger
from code.exceptions import PARSE_FAILURE


class TestFormalConstraint:
    """Tests for the FormalConstraint dataclass."""

    def test_equality_constraint(self):
        """Test creation of an equality constraint."""
        constraint = FormalConstraint(
            constraint_type=FormalConstraintType.EQUALITY,
            variables=["x", "y"],
            value=5
        )
        assert constraint.constraint_type == FormalConstraintType.EQUALITY
        assert constraint.variables == ["x", "y"]
        assert constraint.value == 5

    def test_to_dict(self):
        """Test conversion to dictionary."""
        constraint = FormalConstraint(
            constraint_type=FormalConstraintType.IN_RANGE,
            variables=["x"],
            min_val=0,
            max_val=10,
            metadata={"source": "test"}
        )
        result = constraint.to_dict()
        assert result["type"] == "in_range"
        assert result["variables"] == ["x"]
        assert result["min"] == 0
        assert result["max"] == 10
        assert result["metadata"]["source"] == "test"

    def test_to_dict_with_optional_fields(self):
        """Test that optional fields are omitted when None."""
        constraint = FormalConstraint(
            constraint_type=FormalConstraintType.EQUALITY,
            variables=["x"]
        )
        result = constraint.to_dict()
        assert "value" not in result
        assert "min" not in result
        assert "max" not in result
        assert "operator" not in result


class TestPuzzleParser:
    """Tests for the PuzzleParser class."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return PuzzleParser()

    def test_parse_sudoku_puzzle(self, parser):
        """Test parsing a Sudoku puzzle."""
        puzzle = {
            "id": "sudoku_001",
            "type": "sudoku",
            "constraints": [],
            "initial_state": {
                "grid_size": 9,
                "grid": [
                    [5, 3, 0, 0, 7, 0, 0, 0, 0],
                    [6, 0, 0, 1, 9, 5, 0, 0, 0],
                    [0, 9, 8, 0, 0, 0, 0, 6, 0],
                    [8, 0, 0, 0, 6, 0, 0, 0, 3],
                    [4, 0, 0, 8, 0, 3, 0, 0, 1],
                    [7, 0, 0, 0, 2, 0, 0, 0, 6],
                    [0, 6, 0, 0, 0, 0, 2, 8, 0],
                    [0, 0, 0, 4, 1, 9, 0, 0, 5],
                    [0, 0, 0, 0, 8, 0, 0, 7, 9]
                ]
            },
            "target_state": {}
        }

        constraints, metadata = parser.parse_puzzle(puzzle)

        assert len(constraints) > 0
        assert metadata["puzzle_type"] == "sudoku"
        assert metadata["has_initial_state"] is True
        assert metadata["has_target_state"] is False

        # Check that we have equality constraints for fixed values
        equality_constraints = [
            c for c in constraints
            if c.constraint_type == FormalConstraintType.EQUALITY
        ]
        assert len(equality_constraints) > 0

    def test_parse_pathfinding_puzzle(self, parser):
        """Test parsing a pathfinding puzzle."""
        puzzle = {
            "id": "path_001",
            "type": "pathfinding",
            "constraints": [],
            "initial_state": {
                "grid_size": 5,
                "start": [0, 0],
                "obstacles": [[1, 1], [2, 2]]
            },
            "target_state": {
                "end": [4, 4]
            }
        }

        constraints, metadata = parser.parse_puzzle(puzzle)

        assert len(constraints) > 0
        assert metadata["puzzle_type"] == "pathfinding"

        # Check for start and end constraints
        start_constraints = [
            c for c in constraints
            if c.constraint_type == FormalConstraintType.PATH_START
        ]
        end_constraints = [
            c for c in constraints
            if c.constraint_type == FormalConstraintType.PATH_END
        ]

        assert len(start_constraints) == 1
        assert len(end_constraints) == 1

    def test_parse_unknown_puzzle_type(self, parser):
        """Test that unknown puzzle types raise an error."""
        puzzle = {
            "id": "unknown_001",
            "type": "unknown_type",
            "constraints": [],
            "initial_state": {},
            "target_state": {}
        }

        with pytest.raises(PARSE_FAILURE):
            parser.parse_puzzle(puzzle)

    def test_parse_empty_constraints(self, parser):
        """Test parsing a puzzle with no constraints."""
        puzzle = {
            "id": "empty_001",
            "type": "sudoku",
            "constraints": [],
            "initial_state": {
                "grid_size": 3,
                "grid": [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            },
            "target_state": {}
        }

        # This should still parse the implicit constraints (row, col, block)
        constraints, metadata = parser.parse_puzzle(puzzle)
        assert len(constraints) > 0

    def test_parse_constraints_from_file(self, parser, tmp_path):
        """Test parsing constraints from a JSON file."""
        # Create test data
        test_data = [
            {
                "id": "test_001",
                "type": "sudoku",
                "constraints": [],
                "initial_state": {
                    "grid_size": 3,
                    "grid": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
                },
                "target_state": {}
            }
        ]

        input_file = tmp_path / "puzzles.json"
        output_file = tmp_path / "parsed.json"

        with open(input_file, 'w') as f:
            json.dump(test_data, f)

        results = parser.parse_constraints_from_file(
            str(input_file),
            str(output_file)
        )

        assert "test_001" in results
        assert "constraints" in results["test_001"]

        # Verify output file was created
        assert output_file.exists()
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        assert "test_001" in output_data

    def test_parse_invalid_constraint_description(self, parser):
        """Test parsing an invalid constraint description."""
        puzzle = {
            "id": "invalid_001",
            "type": "sudoku",
            "constraints": [
                {"type": "invalid_type", "variables": ["x"]}
            ],
            "initial_state": {
                "grid_size": 3,
                "grid": [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            },
            "target_state": {}
        }

        # Should not raise, just skip invalid constraints
        constraints, metadata = parser.parse_puzzle(puzzle)
        # Should still have row/col/block constraints
        assert len(constraints) > 0


class TestPuzzleParserExclusionLogging:
    """Tests for exclusion logging in the parser."""

    def test_exclusion_logging_on_error(self):
        """Test that exclusions are logged when parsing fails."""
        exclusion_logger = ExclusionLogger()
        parser = PuzzleParser(exclusion_logger=exclusion_logger)

        puzzle = {
            "id": "error_001",
            "type": "invalid",
            "constraints": [],
            "initial_state": {},
            "target_state": {}
        }

        try:
            parser.parse_puzzle(puzzle)
        except PARSE_FAILURE:
            pass

        # Check that an exclusion was logged
        exclusions = exclusion_logger.get_exclusions()
        assert len(exclusions) > 0
        assert exclusions[0].puzzle_id == "error_001"
        assert exclusions[0].error_type == "PARSE_FAILURE"


class TestParserMain:
    """Tests for the main() function."""

    def test_main_with_valid_input(self, tmp_path):
        """Test main() with valid input."""
        # Create test data
        test_data = [
            {
                "id": "test_001",
                "type": "sudoku",
                "constraints": [],
                "initial_state": {
                    "grid_size": 3,
                    "grid": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
                },
                "target_state": {}
            }
        ]

        input_file = tmp_path / "puzzles.json"
        output_file = tmp_path / "parsed.json"

        with open(input_file, 'w') as f:
            json.dump(test_data, f)

        # Mock sys.argv
        import sys
        original_argv = sys.argv
        sys.argv = ["parser.py", "--input", str(input_file), "--output", str(output_file)]

        try:
            main()
        finally:
            sys.argv = original_argv

        # Verify output was created
        assert output_file.exists()