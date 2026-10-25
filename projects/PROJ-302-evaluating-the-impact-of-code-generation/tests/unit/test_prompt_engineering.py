"""
Unit test for ``code.prompt_engineering``.

The test simply runs the ``main`` function and checks that the expected
output parquet file exists, contains at least one row, and has the three
required columns.
"""

import os
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths
from code.prompt_engineering import main as prompt_main


@pytest.fixture(scope="module")
def output_path():
    """Path to the generated intent prompts parquet file."""
    return paths.data("processed", "intent_prompts.parquet")


def test_prompt_engineering_creates_parquet(tmp_path, monkeypatch, output_path):
    """
    Run the prompt engineering script and verify the output.
    """
    # Ensure a clean state: delete any existing file
    if output_path.exists():
        output_path.unlink()

    # Execute the main routine
    prompt_main()

    # Verify file was created
    assert output_path.is_file(), f"{output_path} was not created"

    # Load and inspect the parquet
    df = pd.read_parquet(output_path)
    assert not df.empty, "Output parquet contains no rows"

    expected_columns = {"pr_id", "prompt", "complexity_indicator"}
    assert expected_columns.issubset(df.columns), f"Missing columns: {expected_columns - set(df.columns)}"

    # Basic sanity check on content
    assert df["prompt"].apply(lambda x: isinstance(x, str) and len(x) > 0).all()
    assert df["complexity_indicator"].isin(["simple", "moderate", "complex"]).all()