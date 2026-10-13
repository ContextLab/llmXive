import json
import os
from pathlib import Path

import pytest

# Import the functions we need to test
from generation.prompt_engine import (
    generate_baseline_prompt,
    generate_experimental_prompt,
    _extract_descriptor,
)

def test_generate_baseline_prompt():
    text = "a cup balancing on a tilted book"
    assert generate_baseline_prompt(text) == text

def test_extract_descriptor():
    constraints = {"natural_language_descriptor": "Object A must be above Object B."}
    assert _extract_descriptor(constraints) == "Object A must be above Object B."

    # Missing key should yield empty string
    assert _extract_descriptor({}) == ""

def test_generate_experimental_prompt_deterministic():
    description = "a cup balancing on a tilted book"
    constraints = {"natural_language_descriptor": "Object A must be above Object B."}
    exp_prompt = generate_experimental_prompt(description, constraints)
    # Should be a single line concatenation of description and descriptor
    assert exp_prompt == f"{description} Object A must be above Object B."

    # When descriptor is missing, experimental falls back to baseline
    exp_prompt_no_desc = generate_experimental_prompt(description, {})
    assert exp_prompt_no_desc == description

def test_prompt_files_created(tmp_path):
    # Create a minimal scene CSV
    csv_path = tmp_path / "scenes.csv"
    csv_path.write_text("scene_id,description_text\nscene_001,a cup on a table\n")

    # Create a matching physics JSON with descriptor
    physics_dir = tmp_path / "physics"
    physics_dir.mkdir()
    (physics_dir / "scene_001.json").write_text(
        json.dumps({"natural_language_descriptor": "Object must stay upright."})
    )

    # Run the engine
    from generation.prompt_engine import run_prompt_engineering

    run_prompt_engineering(
        scenes_csv=str(csv_path),
        physics_dir=str(physics_dir),
        output_dir=str(tmp_path / "prompts"),
    )

    # Verify files exist and are single‑line non‑empty
    baseline_file = tmp_path / "prompts" / "scene_001_baseline.txt"
    experimental_file = tmp_path / "prompts" / "scene_001_experimental.txt"

    assert baseline_file.is_file()
    assert experimental_file.is_file()

    baseline_content = baseline_file.read_text().strip()
    experimental_content = experimental_file.read_text().strip()

    assert baseline_content == "a cup on a table"
    assert experimental_content == "a cup on a table Object must stay upright."
    assert "\n" not in baseline_content
    assert "\n" not in experimental_content