"""
Data Saver module for the knot complexity analysis project.

This module provides functionality to persist the raw knot atlas data
(as JSON) and the cleaned, tabular knot data (as CSV). It is used by the
pipeline step identified as T018.

Public API:
    - DataSaver: class with static methods for saving raw and cleaned data.
    - main(): entry point that downloads, parses, validates, and saves the
      datasets to the appropriate locations under the ``data/`` directory.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

# Import the downloader and parser from the existing project API surface.
# These imports are guaranteed to exist according to the provided API list.
from download.knot_atlas_loader import download_knot_atlas_data
from data.parser import parse_knot_atlas_data, ParsedKnotData


class DataSaver:
    """
    Utility class offering static methods to persist raw and cleaned knot data.
    """

    @staticmethod
    def save_raw(raw_records: List[Dict[str, Any]], output_path: Path) -> None:
        """
        Serialize a list of raw knot records to a JSON file.

        Parameters
        ----------
        raw_records: List[Dict[str, Any]]
            The raw records as returned by ``download_knot_atlas_data``.
        output_path: Path
            Destination file path (must include filename, e.g.
            ``data/raw/knot_atlas_raw.json``).
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure the objects are JSON‑serialisable; ``download_knot_atlas_data``
        # returns either dicts or dataclass instances.  For dataclasses we
        # fall back to their ``__dict__`` representation.
        serialisable = [
            record if isinstance(record, dict) else record.__dict__
            for record in raw_records
        ]
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(serialisable, f, ensure_ascii=False, indent=2)

    @staticmethod
    def save_cleaned(df: pd.DataFrame, output_path: Path) -> None:
        """
        Write a cleaned DataFrame to CSV.

        Parameters
        ----------
        df: pd.DataFrame
            The cleaned knot data.
        output_path: Path
            Destination CSV file (e.g. ``data/processed/knots_cleaned.csv``).
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    @staticmethod
    def save_raw_and_cleaned_data(
        raw_records: List[Dict[str, Any]],
        cleaned_df: pd.DataFrame,
        raw_path: Path,
        cleaned_path: Path,
    ) -> None:
        """
        Convenience wrapper that saves both raw JSON and cleaned CSV in one call.
        """
        DataSaver.save_raw(raw_records, raw_path)
        DataSaver.save_cleaned(cleaned_df, cleaned_path)


def main() -> None:
    """
    Pipeline entry point for T018.

    Steps:
    1. Download the raw knot atlas data.
    2. Persist the raw JSON to ``data/raw/knot_atlas_raw.json``.
    3. Parse the raw records into ``ParsedKnotData`` objects.
    4. Convert the parsed objects into a pandas DataFrame.
    5. Persist the cleaned DataFrame to ``data/processed/knots_cleaned.csv``.

    The function prints short status messages so that users running the script
    directly (``python code/data/data_saver.py``) receive immediate feedback.
    """
    # 1. Download raw data
    raw_records = download_knot_atlas_data()

    # 2. Define output locations
    raw_output_path = Path("data/raw/knot_atlas_raw.json")
    cleaned_output_path = Path("data/processed/knots_cleaned.csv")

    # 3. Parse raw records into structured objects
    parsed_records: List[ParsedKnotData] = parse_knot_atlas_data(raw_records)

    # 4. Convert to DataFrame – we rely on the dataclass ``asdict``‑like
    #    attribute dictionary for each parsed record.
    df = pd.DataFrame([record.__dict__ for record in parsed_records])

    # 5. Save both artefacts
    DataSaver.save_raw_and_cleaned_data(
        raw_records=raw_records,
        cleaned_df=df,
        raw_path=raw_output_path,
        cleaned_path=cleaned_output_path,
    )

    print(f"Raw knot atlas data saved to: {raw_output_path}")
    print(f"Cleaned knot data saved to: {cleaned_output_path}")


if __name__ == "__main__":
    # When executed as a script, run the pipeline step.
    main()