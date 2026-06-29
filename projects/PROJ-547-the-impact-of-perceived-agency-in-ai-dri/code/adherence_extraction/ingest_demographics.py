from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path
from typing import Union

import pandas as pd
import yaml
from jsonschema import ValidationError, validate

from logging.pipeline_logger import get_logger, log_dict
from utils.error_handler import PipelineError

def _load_schema(schema_path: Path) -> dict:
    """Load a JSON‑Schema from a YAML file."""
    if not schema_path.is_file():
        raise PipelineError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_dataframe(df: pd.DataFrame, schema: dict) -> None:
    """Validate a DataFrame against a JSON‑Schema."""
    records = df.to_dict(orient="records")
    try:
        validate(instance=records, schema=schema)
    except ValidationError as exc:
        raise PipelineError(f"Schema validation error: {exc.message}") from exc

def ingest_demographics(input_path: Union[str, Path]) -> pd.DataFrame:
    """
    Ingest a demographics file (CSV or JSON), validate it against the
    ``contracts/demographics.schema.yaml`` schema, and write a cleaned CSV
    to ``data/processed/demographics.csv``.

    Parameters
    ----------
    input_path: str or Path
        Path to the demographics file.

    Returns
    -------
    pd.DataFrame
        The validated demographics data.
    """
    logger = get_logger()
    path = Path(input_path)

    if not path.is_file():
        logger.error("Demographics file not found", extra={"path": str(path)})
        raise PipelineError(f"Demographics file not found: {path}")

    logger.info("Reading demographics file", extra={"path": str(path)})

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() == ".json":
        df = pd.read_json(path)
    else:
        logger.error("Unsupported file type for demographics", extra={"path": str(path)})
        raise PipelineError(f"Unsupported file type: {path.suffix}")

    # Load and validate schema
    schema_path = Path("contracts/demographics.schema.yaml")
    schema = _load_schema(schema_path)
    _validate_dataframe(df, schema)

    # Write validated data
    output_path = Path("data/processed/demographics.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    logger.info(
        "Demographics ingestion completed",
        extra={"input": str(path), "output": str(output_path), "rows": len(df)},
    )
    return df

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest demographics data, validate against schema, and output CSV."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the demographics file (CSV or JSON).",
    )
    return parser

def main(argv: list[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        ingest_demographics(args.input_file)
    except PipelineError as exc:
        logger = get_logger()
        logger.error("Demographics ingestion failed", exc_info=exc)
        sys.exit(1)

if __name__ == "__main__":
    main()
