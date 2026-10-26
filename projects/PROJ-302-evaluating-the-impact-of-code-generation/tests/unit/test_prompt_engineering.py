"""
Unit test for ``code.prompt_engineering``.

The test runs the ``main()`` function and then checks that
``data/processed/intent_prompts.parquet`` exists and contains the
expected columns with at least one row.
"""

import os

import pandas as pd
from llmxive_toolkit import paths, get_logger

from code.prompt_engineering import main

log = get_logger(__name__)

def test_prompt_engineering_creates_output(tmp_path, monkeypatch):
    """
    Execute the prompt‑engineering script and verify the output artifact.
    """
    # Ensure the repository root is the project root (pytest runs from the
    # project directory, but we guard against accidental cwd changes).
    project_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(project_root)

    # Run the script – it will create a fallback commit_messages.parquet if
    # none exists, then produce intent_prompts.parquet.
    main()

    output_path = paths.data("processed", "intent_prompts.parquet")
    assert output_path.is_file(), f"{output_path} was not created"

    df = pd.read_parquet(output_path)
    # Basic schema validation
    expected_cols = {"pr_id", "prompt", "complexity_indicator"}
    assert expected_cols.issubset(df.columns), f"Missing columns in {output_path}"
    assert len(df) > 0, "Output parquet is empty"

    # Spot‑check that prompts are non‑empty strings and complexity is valid.
    for _, row in df.iterrows():
        assert isinstance(row["prompt"], str) and row["prompt"].strip(), "Empty prompt"
        assert row["complexity_indicator"] in {"simple", "moderate", "complex"}, \
            f"Invalid complexity: {row['complexity_indicator']}"