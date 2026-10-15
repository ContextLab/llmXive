"""
Contract tests for the ingestion step.
Ensures that the mandatory output artifacts are created and have
a plausible structure.
"""
import pathlib

import pandas as pd
import pytest

from llmxive_toolkit import paths

@pytest.fixture(scope="session")
def ingestion_outputs():
    """Run the ingestion step once for the whole test session."""
    # Import the ingest function lazily to avoid side‑effects during import time.
    from src.pipeline.ingest import ingest

    # URLs are taken from the verified plan (same as quickstart).
    swe_gym_url = (
        "https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/"
        "train-00000-of-00001.parquet"
    )
    multi_swe_rl_url = (
        "https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/"
        "c/OpenMathLib__OpenBLAS_dataset.jsonl"
    )
    # Run ingestion (checksums are optional; we skip them here)
    ingest(swe_gym_url, multi_swe_rl_url, expected_checksums=None)

    # Return the paths we expect to exist
    return {
        "raw_swe_gym": paths.data("raw_swe_gym.parquet"),
        "raw_multi_swe_rl": paths.data("raw_multi_swe_rl.jsonl"),
        "patches_csv": paths.data("patches.csv"),
        "logs_dir": paths.data("execution_logs"),
    }

def test_raw_files_exist(ingestion_outputs):
    assert ingestion_outputs["raw_swe_gym"].is_file(), "raw_swe_gym.parquet missing"
    assert ingestion_outputs["raw_multi_swe_rl"].is_file(), "raw_multi_swe_rl.jsonl missing"

def test_patches_csv_structure(ingestion_outputs):
    csv_path = ingestion_outputs["patches_csv"]
    assert csv_path.is_file(), "patches.csv missing"
    df = pd.read_csv(csv_path)
    # Must contain the required columns
    required = {"patch_id", "language", "source_code", "label"}
    assert required.issubset(set(df.columns)), f"Missing columns in patches.csv: {required - set(df.columns)}"
    # Basic sanity check: at least 3 500 rows as specified
    assert len(df) >= 3500, f"Expected >=3500 patches, found {len(df)}"

def test_execution_logs_exist(ingestion_outputs):
    logs_dir = ingestion_outputs["logs_dir"]
    assert logs_dir.is_dir(), "execution_logs directory missing"
    # Ensure there is a log file for every patch listed in patches.csv
    df = pd.read_csv(ingestion_outputs["patches_csv"])
    missing = []
    for pid in df["patch_id"]:
        log_file = logs_dir / f"{pid}.log"
        if not log_file.is_file():
            missing.append(pid)
    assert not missing, f"Missing log files for {len(missing)} patches"
