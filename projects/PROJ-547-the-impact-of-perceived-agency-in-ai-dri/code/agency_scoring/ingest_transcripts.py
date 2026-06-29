from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import pandas as pd

# Logging utilities
from logging.pipeline_logger import get_logger, log_dict


def ingest_transcripts(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Ingest a transcript file (CSV or JSON) and return a DataFrame with the required
    columns: ``session_id`` and ``utterances``.

    Parameters
    ----------
    file_path: Union[str, Path]
        Path to the transcript file.

    Returns
    -------
    pd.DataFrame
        DataFrame containing ``session_id`` and ``utterances`` columns.

    Raises
    ------
    FileNotFoundError
        If the supplied path does not exist.
    ValueError
        If the file type is unsupported or required columns are missing.
    """
    logger = get_logger()
    path = Path(file_path)

    if not path.exists():
        logger.error(f"Transcript file not found: {path}")
        raise FileNotFoundError(f"Transcript file not found: {path}")

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        logger.error(f"Unsupported transcript file type: {path.suffix}")
        raise ValueError(f"Unsupported transcript file type: {path.suffix}")

    required_columns = {"session_id", "utterances"}
    missing = required_columns.difference(df.columns)
    if missing:
        logger.error(f"Missing required columns in transcript file: {missing}")
        raise ValueError(f"Missing required columns in transcript file: {missing}")

    # Log successful ingestion
    log_dict(
        {
            "step": "ingest_transcripts",
            "status": "completed",
            "file": str(path),
            "rows": len(df),
        }
    )
    return df


def main() -> None:
    """
    CLI entry point for manual testing. Expects a single argument: the path to the
    transcript file. Prints the resulting DataFrame to stdout.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Ingest transcript file")
    parser.add_argument("input_path", type=str, help="Path to CSV or JSON transcript file")
    args = parser.parse_args()

    df = ingest_transcripts(args.input_path)
    print(df.head())