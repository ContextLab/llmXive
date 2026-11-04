"""
Unit tests for the ``code.models.symbolic_state`` module.

These tests verify that:
1. The mapper produces a Parquet file with the expected schema.
2. Ambiguous embeddings are detected and logged.
3. Non‑ambiguous embeddings receive a ``high`` confidence.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test.
from code.models.symbolic_state import map_embeddings, _is_ambiguous

def _create_dummy_embeddings(tmp_dir: Path) -> Path:
    """
    Helper that creates a small Parquet file with two embedding records:
    - ``ambiguous``: first two dimensions equal → low confidence.
    - ``clear``: first two dimensions differ → high confidence.
    """
    embeddings = [
        {
            "task_id": "T001",
            "embedding_vector": [0.0, 0.0] + [0.0] * 510,  # ambiguous
        },
        {
            "task_id": "T002",
            "embedding_vector": [1.0, 2.0] + [0.0] * 510,  # clear
        },
    ]
    df = pd.DataFrame(embeddings)
    embed_path = tmp_dir / "semantic_embeddings.parquet"
    df.to_parquet(embed_path, index=False)
    return embed_path

def test_is_ambiguous_detection():
    """Direct test of the internal ambiguity predicate."""
    assert _is_ambiguous([0.0, 0.0, 1.0]) is True
    assert _is_ambiguous([1.0, 2.0, 3.0]) is False
    # Edge case: fewer than two dimensions – should be non‑ambiguous.
    assert _is_ambiguous([42.0]) is False

def test_map_embeddings_creates_output_and_log():
    """
    End‑to‑end test of the mapper.

    * A temporary directory is used so the test does not interfere with
      the real project data.
    * After mapping, the output Parquet file is inspected for correct
      ``mapping_confidence`` values.
    * The log file is checked for the presence of the ``AmbiguousMapping``
      marker.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Prepare dummy input embeddings.
        input_parquet = _create_dummy_embeddings(tmp_path)

        # Define where the mapper should write its outputs.
        output_parquet = tmp_path / "symbolic_states.parquet"
        log_file = tmp_path / "mapping_log.txt"

        # Run the mapper.
        df_out = map_embeddings(
            input_path=input_parquet,
            output_path=output_parquet,
            log_path=log_file,
        )

        # -----------------------------------------------------------------
        # Verify the Parquet output.
        # -----------------------------------------------------------------
        assert output_parquet.is_file(), "Output Parquet file was not created"

        # Load the file again to ensure it was written correctly.
        df_loaded = pd.read_parquet(output_parquet)

        # Expected columns.
        expected_cols = {
            "task_id",
            "state_id",
            "mapping_confidence",
            "embedding_vector",
        }
        assert set(df_loaded.columns) == expected_cols

        # Check confidence values.
        conf_T001 = df_loaded.loc[
            df_loaded["task_id"] == "T001", "mapping_confidence"
        ].iloc[0]
        conf_T002 = df_loaded.loc[
            df_loaded["task_id"] == "T002", "mapping_confidence"
        ].iloc[0]

        assert conf_T001 == "low", "Ambiguous embedding should be low confidence"
        assert conf_T002 == "high", "Clear embedding should be high confidence"

        # -----------------------------------------------------------------
        # Verify the log file.
        # -----------------------------------------------------------------
        assert log_file.is_file(), "Log file was not created"
        log_contents = log_file.read_text(encoding="utf-8")
        # Only the ambiguous record should have generated a log entry.
        assert (
            "AmbiguousMapping: task_id=T001" in log_contents
        ), "Ambiguous mapping not logged"
        assert (
            "AmbiguousMapping: task_id=T002" not in log_contents
        ), "Non‑ambiguous mapping incorrectly logged"

        # The function should also return the DataFrame it wrote.
        pd.testing.assert_frame_equal(df_out.sort_index(axis=1), df_loaded.sort_index(axis=1))