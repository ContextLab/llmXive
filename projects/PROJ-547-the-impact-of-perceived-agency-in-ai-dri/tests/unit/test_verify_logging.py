import json
from pathlib import Path

import pytest

from logging.logging.run_dummy_log import main as dummy_log_main
from logging.verify_logging import main as verify_main


def test_logging_completeness(tmp_path: Path):
    # Run a dummy log to generate a log file
    dummy_log_main(log_dir=tmp_path)

    # Verify completeness
    result_path = tmp_path / "completeness_metric.json"
    verify_main(log_dir=tmp_path, output_path=result_path)

    with result_path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert "completeness" in metrics
    assert metrics["completeness"] >= 0.95