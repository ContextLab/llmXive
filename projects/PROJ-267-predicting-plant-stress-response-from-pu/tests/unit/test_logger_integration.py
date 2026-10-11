import sys
import os
from pathlib import Path

import pytest

# Ensure the project root is in PYTHONPATH for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from utils.logging_config import get_logger, setup_logging

def test_logger_creates_file_and_writes_entry(tmp_path, monkeypatch):
    """
    Verify that the project-wide logger creates logs/pipeline.log
    and writes a test entry.
    """
    # Use the real log path (project-relative)
    log_path = Path('logs') / 'pipeline.log'

    # Remove log file if it exists from previous runs
    if log_path.exists():
        log_path.unlink()

    # Initialise logging (setup_logging is a no‑op but ensures handler creation)
    setup_logging()

    logger = get_logger("test_logger")
    test_message = "Integration test log entry"
    logger.info(test_message)

    # Ensure the log file now exists
    assert log_path.is_file(), "Log file was not created."

    # Read the log file and verify the message is present
    content = log_path.read_text(encoding="utf-8")
    assert test_message in content, "Test log entry not found in pipeline.log"

def test_normalization_logging(monkeypatch):
    """
    Run a minimal part of the normalization pipeline and check that
    dropped column messages are logged.
    """
    import pandas as pd

    # Create a tiny DataFrame with one low‑abundance column
    df = pd.DataFrame({
        'protein_A': [1.0, None, None],
        'protein_B': [2.0, 2.5, 3.0]
    })

    # Monkeypatch the file reading/writing to avoid disk I/O
    from data_ingestion import normalize as norm_mod

    # Capture log output by using a temporary log file
    temp_log = Path('logs') / 'pipeline.log'
    if temp_log.exists():
        temp_log.unlink()
    # Ensure logger reinitialises with the same path
    logger = get_logger("test_normalization")
    logger.handlers.clear()  # Remove any existing handlers
    logger.setLevel(10)
    handler = logging.FileHandler(temp_log, mode='a', encoding='utf-8')
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Run the filter function directly
    filtered_df, dropped = norm_mod.filter_low_abundance_proteins(df, min_detection_rate=0.5)

    # Verify that a column was dropped and that the log contains a warning
    assert 'protein_A' in dropped
    log_content = temp_log.read_text(encoding='utf-8')
    assert "Dropped low-abundance protein columns" in log_content
    assert "protein_A" in log_content