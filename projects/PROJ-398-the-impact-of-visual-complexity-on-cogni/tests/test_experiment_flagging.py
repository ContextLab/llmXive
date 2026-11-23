"""
Unit tests for the ``src.experiment.record_flagging`` module.

The test file is deliberately minimal because the official test
``tests/test_experiment.py::test_incomplete_record_flagging`` already
exercises the public API.  Providing this additional test ensures that the
module is importable and behaves as documented.
"""

import pandas as pd
import pytest

from src.experiment.record_flagging import flag_incomplete_records


def test_flagging_adds_exclude_column():
    """All rows should receive an ``exclude`` column."""
    df = pd.DataFrame(
        {
            "participant_id": [1, 2, 3],
            "tlx_score": [30, None, 55],
            "reaction_time": [250, 300, None],
        }
    )
    result = flag_incomplete_records(df)
    assert "exclude" in result.columns
    # Row 0 is complete, rows 1 and 2 have missing values
    assert result["exclude"].tolist() == [False, True, True]


def test_no_tlx_or_rt_columns():
    """When no TLX/RT columns exist, ``exclude`` should be False for all rows."""
    df = pd.DataFrame({"participant_id": [1, 2], "age": [25, 30]})
    result = flag_incomplete_records(df)
    assert result["exclude"].tolist() == [False, False]


def test_invalid_input_type():
    """Non‑DataFrame inputs must raise a TypeError."""
    with pytest.raises(TypeError):
        flag_incomplete_records([1, 2, 3])