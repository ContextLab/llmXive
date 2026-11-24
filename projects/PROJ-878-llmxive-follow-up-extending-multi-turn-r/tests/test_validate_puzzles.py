"""
Unit tests for the ``validate_puzzles.py`` script.

The tests generate a tiny, *real* synthetic dataset using the existing
``code.graph_generator`` module, write it to temporary JSONL files, then
invoke the validation logic to ensure that:

1. A correctly‑structured file passes validation.
2. An incorrectly‑structured file raises a ``ValueError``.
3. The line‑count check works as expected.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from code.graph_generator import generate_set
from code.validate_puzzles import load_schema, validate_file

# Load the contract once for reuse
SCHEMA_PATH = Path("contracts") / "synthetic_puzzle.schema.yaml"
SCHEMA = load_schema(SCHEMA_PATH)


def write_jsonl(puzzles, file_path):
    """Write a list of puzzle dicts to a JSONL file."""
    with open(file_path, "w", encoding="utf-8") as f:
        for p in puzzles:
            f.write(json.dumps(p) + "\n")


def test_validation_success(tmp_path):
    """A correctly‑generated file should validate without error."""
    puzzles = generate_set(
        count=5,
        depth_range=(1, 2),
        branch_range=(1.0, 2.0),
        seed=123,
    )
    file_path = tmp_path / "valid.jsonl"
    write_jsonl(puzzles, file_path)

    # No exception means success
    validate_file(file_path, SCHEMA, expected_count=5)


def test_validation_schema_error(tmp_path):
    """Corrupting a required field should raise a ``ValueError``."""
    puzzles = generate_set(
        count=3,
        depth_range=(1, 1),
        branch_range=(1.0, 1.0),
        seed=456,
    )
    # Remove a required field from the first puzzle
    del puzzles[0]["ground_truth"]
    file_path = tmp_path / "invalid_schema.jsonl"
    write_jsonl(puzzles, file_path)

    with pytest.raises(ValueError, match="Schema validation failed"):
        validate_file(file_path, SCHEMA, expected_count=3)


def test_validation_count_mismatch(tmp_path):
    """If the file contains fewer lines than expected, a ``ValueError`` is raised."""
    puzzles = generate_set(
        count=4,
        depth_range=(1, 1),
        branch_range=(1.0, 1.0),
        seed=789,
    )
    file_path = tmp_path / "count_mismatch.jsonl"
    write_jsonl(puzzles, file_path)

    # Expect a count mismatch (expecting 5 but only 4 present)
    with pytest.raises(ValueError, match="contains 4 records; expected 5"):
        validate_file(file_path, SCHEMA, expected_count=5)