"""
Simple integration test for the data quality report generation.
"""

from pathlib import Path

import pandas as pd

from code.analysis.data_quality_report import main, compute_null_percentages


def test_compute_null_percentages(tmp_path: Path):
    # Create a tiny dataset with known missing values
    data = {
        "crossing_number": [3, None, 5],
        "braid_index": [2, 2, None],
        "volume": [1.2, 2.3, 3.4],
        "alternating": [True, None, False],
    }
    df = pd.DataFrame(data)
    rows = compute_null_percentages(df)
    # Expect 1 null in crossing_number, 1 in braid_index, 0 in volume, 1 in alternating
    expected = {
        "crossing_number": ("1", "33.33%"),
        "braid_index": ("1", "33.33%"),
        "volume": ("0", "0.00%"),
        "alternating": ("1", "33.33%"),
    }
    for row in rows:
        exp_null, exp_pct = expected[row["field"]]
        assert row["null_count"] == exp_null
        assert row["null_percent"] == exp_pct


def test_main_writes_report(tmp_path: Path):
    # Prepare a minimal cleaned CSV
    csv_path = tmp_path / "knots_cleaned.csv"
    df = pd.DataFrame(
        {
            "crossing_number": [3, 4],
            "braid_index": [2, 2],
            "volume": [1.0, 2.0],
            "alternating": [True, False],
        }
    )
    df.to_csv(csv_path, index=False)

    output_md = tmp_path / "data_quality_report.md"
    # Run main with explicit paths
    main(input_path=csv_path, output_path=output_md)

    assert output_md.is_file()
    content = output_md.read_text()
    assert "# Data Quality Report" in content
    assert "| crossing_number | 0 | 0.00% |" in content
    assert "| braid_index | 0 | 0.00% |" in content


# The test suite will be discovered by pytest automatically.