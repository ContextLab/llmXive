"""
Unit tests for the newly added logging subsystem and parquet loaders.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from code.setup_logging import (
    get_data_quality_logger,
    get_exclusion_logger,
    get_model_diagnostics_logger,
)
from code.loaders import load_parquet_as_df, chunked_parquet_loader

def test_loggers_create_files(tmp_path: Path):
    """
    Ensure each logger creates its log file in the expected location.
    """
    # Override the results/logs directory for the test
    from llmxive_toolkit import paths

    # Monkey‑patch the paths to point inside the temporary directory
    original_logs_dir = paths.results("logs")
    paths.results = lambda *parts: tmp_path / Path(*parts)

    # Re‑create loggers (they will use the patched path)
    dq_logger = get_data_quality_logger()
    ex_logger = get_exclusion_logger()
    md_logger = get_model_diagnostics_logger()

    # Emit a single message to each logger
    dq_logger.info("dq test")
    ex_logger.info("ex test")
    md_logger.info("md test")

    # Verify files exist and contain the messages
    for name in ["data_quality.log", "exclusion.log", "model_diagnostics.log"]:
        log_file = tmp_path / name
        assert log_file.is_file()
        content = log_file.read_text()
        assert f"{name.split('.')[0]} test" in content

    # Restore original path function to avoid side effects
    paths.results = lambda *parts: original_logs_dir / Path(*parts)

def test_load_parquet_as_df(tmp_path: Path):
    """
    Verify that ``load_parquet_as_df`` loads a file correctly and raises
    ``FileNotFoundError`` when the path does not exist.
    """
    # Create a tiny DataFrame and write it as parquet
    df_original = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    parquet_path = tmp_path / "test.parquet"
    df_original.to_parquet(parquet_path)

    # Successful load
    df_loaded = load_parquet_as_df(parquet_path)
    pd.testing.assert_frame_equal(df_original, df_loaded)

    # Missing file
    with pytest.raises(FileNotFoundError):
        load_parquet_as_df(parquet_path.parent / "nonexistent.parquet")

def test_chunked_parquet_loader(tmp_path: Path):
    """
    Check that the chunked loader yields DataFrames of at most the requested size.
    """
    rows = 250
    df = pd.DataFrame({"x": range(rows), "y": range(rows, 2 * rows)})
    parquet_path = tmp_path / "big.parquet"
    df.to_parquet(parquet_path)

    # Chunk size smaller than total rows
    batches = list(chunked_parquet_loader(parquet_path, batch_size=100))
    assert len(batches) == 3  # 100 + 100 + 50
    assert sum(len(b) for b in batches) == rows
    assert all(isinstance(b, pd.DataFrame) for b in batches)
    assert max(len(b) for b in batches) <= 100