"""
Unit test for the setup_experts script.

The test invokes the script's main() function and then checks that the
required output files exist and contain plausible content.
"""

import json
from pathlib import Path

# Import the script's main function
from code.data_curation.setup_experts import main as setup_experts_main

def test_experts_and_rubric_generation(tmp_path, monkeypatch):
    """
    Run the setup_experts script and verify that:
    1. data/raw/experts.json is created and contains a list of dicts.
    2. data/raw/rubric_definition.md is created and contains the header.
    """

    # Redirect the output directory to a temporary location to avoid polluting the repo
    data_raw_dir = tmp_path / "data" / "raw"
    data_raw_dir.mkdir(parents=True, exist_ok=True)

    # Monkey‑patch the module‑level constants to point to the temporary directory
    monkeypatch.setattr("code.data_curation.setup_experts.DATA_RAW_DIR", data_raw_dir)
    monkeypatch.setattr("code.data_curation.setup_experts.EXPERTS_FILE", data_raw_dir / "experts.json")
    monkeypatch.setattr("code.data_curation.setup_experts.RUBRIC_FILE", data_raw_dir / "rubric_definition.md")

    # Run the script
    setup_experts_main()

    # Verify experts.json
    experts_path = data_raw_dir / "experts.json"
    assert experts_path.is_file(), "experts.json was not created"
    with open(experts_path, "r", encoding="utf-8") as f:
        experts = json.load(f)
    assert isinstance(experts, list) and len(experts) >= 1, "experts.json should contain a non‑empty list"
    for expert in experts:
        assert "id" in expert and "role" in expert, "Each expert dict must contain at least 'id' and 'role'"

    # Verify rubric_definition.md
    rubric_path = data_raw_dir / "rubric_definition.md"
    assert rubric_path.is_file(), "rubric_definition.md was not created"
    content = rubric_path.read_text(encoding="utf-8")
    assert "# Annotation Rubric: Video Continuity Verification" in content, "Rubric header missing"
    assert "Generated:" in content, "Rubric should contain a generation timestamp"