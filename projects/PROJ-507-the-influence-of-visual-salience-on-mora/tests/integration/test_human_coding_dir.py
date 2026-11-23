import pytest
import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths

def test_human_coding_directory_structure():
    """
    Verify that the human coding directory and its required artifacts exist
    and contain the expected structure.
    """
    coding_dir = paths.data("raw", "human_coding")
    template_path = coding_dir / "annotations_template.csv"
    readme_path = coding_dir / "README.md"

    # 1. Check directory exists
    assert coding_dir.is_dir(), "data/raw/human_coding/ directory should exist"

    # 2. Check README exists
    assert readme_path.is_file(), "README.md should exist in the human coding directory"

    # 3. Check template CSV exists
    assert template_path.is_file(), "annotations_template.csv should exist"

    # 4. Check CSV headers
    df = pd.read_csv(template_path)
    expected_headers = ["scenario_id", "annotator_1", "annotator_2", "annotator_3"]
    assert list(df.columns) == expected_headers, f"CSV headers should be {expected_headers}, got {list(df.columns)}"

    # 5. Check row count matches candidates_filtered.csv (if available)
    candidates_path = paths.data("processed", "candidates_filtered.csv")
    if candidates_path.is_file():
        candidates_df = pd.read_csv(candidates_path)
        assert len(df) == len(candidates_df), "Template row count should match the number of candidates"
    else:
        pytest.skip("T001 output (candidates_filtered.csv) not found; skipping row count verification")