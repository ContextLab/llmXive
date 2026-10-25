"""
Unit tests for the puzzle generator.
Checks that generated instances conform to the JSON schema
defined in `contracts/dataset.schema.yaml`.
"""

import json
import tempfile
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

from code.dataset.generator import PuzzleGenerator, PuzzleType, DataGenerationError

# Load the contract schema once
with open("contracts/dataset.schema.yaml", "r", encoding="utf-8") as f:
    SCHEMA = json.load(f)

def test_generate_small_dataset(tmp_path: Path):
    """
    Generate a minimal dataset (4x4 Sudoku + pathfinding) and
    validate each puzzle against the schema.
    """
    generator = PuzzleGenerator(seed=123, source_id="test_run")
    output_file = generator.generate_puzzles(
        n_values=[4],
        count=1,
        puzzle_types=[PuzzleType.SUDOKU, PuzzleType.PATHFINDING],
        output_dir=str(tmp_path)
    )

    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Header presence
    assert "header" in data
    assert data["header"]["total_instances"] == 2

    puzzles = data["puzzles"]
    assert len(puzzles) == 2

    for puzzle in puzzles:
        # Validate against the contract schema
        try:
            validate(instance=puzzle, schema=SCHEMA)
        except ValidationError as ve:
            pytest.fail(f"Puzzle failed schema validation: {ve}")

def test_invalid_type_raises():
    """
    Requesting an unknown puzzle type should raise DataGenerationError.
    """
    generator = PuzzleGenerator()
    with pytest.raises(DataGenerationError):
        generator.generate_puzzles(
            n_values=[4],
            count=1,
            puzzle_types=[PuzzleType.SUDOKU, "unknown_type"],  # type: ignore
            output_dir="."
        )
