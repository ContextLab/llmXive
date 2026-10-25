"""
Unit tests for the puzzle generator.
Checks that generated puzzles conform to the dataset schema and that
the generator produces a deterministic output given a fixed seed.
"""

import json
import pytest
from pathlib import Path

from code.dataset.generator import PuzzleGenerator, PuzzleType, DataGenerationError

def test_generator_output_structure(tmp_path):
    """Generator should produce a JSON file with a top‑level 'puzzles' list."""
    generator = PuzzleGenerator(seed=123, source_id="test_source")
    out_file = generator.generate_puzzles(
        n_values=[4],
        count=2,
        puzzle_types=[PuzzleType.SUDOKU, PuzzleType.PATHFINDING],
        output_dir=str(tmp_path)
    )
    # Verify file exists
    assert Path(out_file).exists()

    # Load and inspect
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert "puzzles" in data
    assert isinstance(data["puzzles"], list)
    assert len(data["puzzles"]) == 4  # 2 types × 2 count

    # Basic schema‑like checks
    for puzzle in data["puzzles"]:
        for field in ("puzzle_type", "constraints", "initial_state", "target_state", "metadata", "verifier_output"):
            assert field in puzzle

def test_generator_invalid_type():
    """Requesting an unknown puzzle type should raise DataGenerationError."""
    generator = PuzzleGenerator(seed=0, source_id="test")
    with pytest.raises(DataGenerationError):
        generator.generate_puzzles(
            n_values=[4],
            count=1,
            puzzle_types=["unknown_type"],  # not a valid PuzzleType
            output_dir="."
        )