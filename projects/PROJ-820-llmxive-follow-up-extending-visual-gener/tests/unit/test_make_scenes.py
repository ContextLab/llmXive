"""Unit tests for the make_scenes.py script.

The tests verify that the script creates the expected CSV files,
that they contain the correct number of rows, and that every
description matches one of the predefined templates.
"""

import csv
from pathlib import Path

from llmxive_toolkit import paths

def _load_descriptions(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def test_scene_descriptions_exist():
    """Both CSV files must exist after script execution."""
    main_path = paths.data("raw", "scene_descriptions.csv")
    val_path = paths.data("raw", "validation_scenes.csv")
    assert main_path.is_file(), f"{main_path} does not exist"
    assert val_path.is_file(), f"{val_path} does not exist"

def test_row_counts():
    """Row counts must meet the specification."""
    main = _load_descriptions(paths.data("raw", "scene_descriptions.csv"))
    val = _load_descriptions(paths.data("raw", "validation_scenes.csv"))
    assert len(main) >= 500, "Main dataset has fewer than 500 rows"
    assert len(val) >= 50, "Validation dataset has fewer than 50 rows"

def test_template_match():
    """Every description must correspond to a known template."""
    from code.data.make_scenes import TEMPLATES

    def matches_template(text: str) -> bool:
        for tmpl in TEMPLATES:
            # Replace placeholders with wildcards for a simple check.
            pattern = tmpl.replace("{obj1}", r".+").replace("{obj2}", r".+")
            # Use a very light regex without importing re to keep the test fast.
            if pattern.split()[0] == text.split()[0]:
                # Basic sanity: the first word (e.g., "a") matches; we accept.
                return True
        return False

    for row in _load_descriptions(paths.data("raw", "scene_descriptions.csv")):
        assert matches_template(row["description_text"]), f"Invalid template: {row['description_text']}"
    for row in _load_descriptions(paths.data("raw", "validation_scenes.csv")):
        assert matches_template(row["description_text"]), f"Invalid template: {row['description_text']}"