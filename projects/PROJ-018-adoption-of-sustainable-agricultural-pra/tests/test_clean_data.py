"""Simple integration test for the cleaning pipeline.

The test checks that the pipeline runs without raising and that the
expected output file exists.
"""

import os
from pathlib import Path

import pytest

from code_02_clean_data import main as clean_main  # type: ignore

@pytest.mark.parametrize("seed", [None, 123])
def test_cleaning_produces_file(tmp_path, seed):
    # Ensure a clean environment
    os.chdir(tmp_path)

    # Create a minimal raw CSV that satisfies required columns
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "survey_data.csv"
    raw_path.write_text(
        "age,education,farm_size,credit,adoption,membership,extension_visits,collective_action,knowledge_exchange\\n"
        "35,12,2.5,1000,yes,member,yes,yes,no\\n"
        "42,8,1.0,500,no,nonmember,no,no,yes\\n"
    )

    # Run the cleaning script
    if seed is not None:
        clean_main(["--seed", str(seed)])
    else:
        clean_main([])

    # Assert the processed file exists
    processed_path = Path("data/processed/cleaned_data.csv")
    assert processed_path.is_file()

    # Basic sanity check on content
    df = pd.read_csv(processed_path)
    assert "age" in df.columns
    assert len(df) == 2  # both rows kept (no >30% missing)