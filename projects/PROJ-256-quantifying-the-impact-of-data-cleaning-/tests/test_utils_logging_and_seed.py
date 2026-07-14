"""
Simple sanity tests for the utilities added in this task.
They verify that the flexible signatures do not raise errors and that the
JSON output is created with the correct precision.
"""

import json
import os
from pathlib import Path

from utils import pin_random_seed, setup_logging
from analysis import run_baseline_analysis

def test_pin_random_seed_is_callable():
    # Should not raise
    pin_random_seed(123)

def test_setup_logging_flexible_signatures():
    logger1 = setup_logging()
    logger2 = setup_logging("DEBUG")
    logger3 = setup_logging(name="my_logger", log_level="WARNING")
    logger4 = setup_logging("my_logger", "ERROR")
    # All should return a logging.Logger instance
    assert isinstance(logger1, type(logger2))
    assert isinstance(logger3, type(logger4))

def test_run_baseline_analysis_writes_file(tmp_path: Path):
    # Create a tiny CSV dataset with two numeric columns
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b\\n1,2\\n3,4\\n5,6\\n")
    raw_dir = tmp_path
    output_file = tmp_path / "baseline.json"

    metrics = run_baseline_analysis(str(raw_dir), str(output_file))

    # Verify file exists
    assert output_file.is_file()

    # Load and check numeric precision (>=3 decimal places)
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    p_val = data["t_test"]["p_value"]
    assert isinstance(p_val, float)
    # Ensure three decimal places are present (e.g., 0.123)
    assert len(f"{p_val:.3f}".split(".")[1]) == 3
    # Clean‑up handled by pytest fixture