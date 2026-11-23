import sys
from pathlib import Path

import pandas as pd
import pytest

# Import the module under test.  The repository layout ensures that
# ``src`` is on the import path when the test runner starts from the
# project root.
from src.experiment.ingest import main as ingest_main


def _run_ingest(tmp_path: Path, rows: list[dict]) -> pd.DataFrame:
    """
    Helper that writes ``rows`` to a temporary CSV, invokes the ingest
    script via ``main()``, and returns the resulting DataFrame.
    """
    input_csv = tmp_path / "recruitment_export.csv"
    pd.DataFrame(rows).to_csv(input_csv, index=False)

    # Simulate command‑line invocation
    sys.argv = ["ingest.py", str(input_csv)]
    ingest_main()

    output_csv = Path("data/measurements/human_ratings.csv")
    assert output_csv.exists(), "Ingest script did not produce the expected output file"
    return pd.read_csv(output_csv)


def test_ingest_basic(tmp_path: Path):
    """
    Verify that a well‑formed CSV with the canonical column names is
    copied unchanged to the target location.
    """
    rows = [
        {"image_id": "img_001", "participant_id": "p_01", "complexity_score": 4},
        {"image_id": "img_002", "participant_id": "p_02", "complexity_score": 7},
    ]
    out_df = _run_ingest(tmp_path, rows)

    assert list(out_df.columns) == ["image_id", "participant_id", "complexity_score"]
    assert len(out_df) == 2
    assert out_df.iloc[0]["image_id"] == "img_001"
    assert out_df.iloc[1]["complexity_score"] == 7


def test_ingest_with_alternative_column_names(tmp_path: Path):
    """
    The ingest script should recognise alternative column names (e.g.
    ``image`` instead of ``image_id`` and ``rating`` instead of
    ``complexity_score``) and still produce a correctly‑shaped output.
    """
    rows = [
        {"image": "img_A", "participant": "p_A", "rating": 5},
        {"stimulus_id": "img_B", "user_id": "p_B", "score": 8},
    ]
    out_df = _run_ingest(tmp_path, rows)

    assert list(out_df.columns) == ["image_id", "participant_id", "complexity_score"]
    assert out_df.iloc[0]["image_id"] == "img_A"
    assert out_df.iloc[1]["participant_id"] == "p_B"
    assert out_df.iloc[1]["complexity_score"] == 8


def test_ingest_missing_required_column(tmp_path: Path):
    """
    If the input CSV lacks any of the required fields (or their aliases),
    the script must raise a ``ValueError`` with a clear message.
    """
    rows = [
        {"image_id": "img_X", "rating": 3},  # missing participant identifier
    ]
    input_csv = tmp_path / "bad.csv"
    pd.DataFrame(rows).to_csv(input_csv, index=False)

    sys.argv = ["ingest.py", str(input_csv)]
    with pytest.raises(ValueError, match="missing required columns"):
        ingest_main()