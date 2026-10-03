"""
Assemble the final dataset for the project.

This script merges three core data sources:

1. ``data/raw/materials_project_data.json`` – raw Materials Project records.
2. ``data/raw/nist_data.json`` – NIST melting‑point / latent‑heat data.
3. ``data/processed/features.csv`` – computed descriptors (elemental & graph).

The merged result is written to ``data/processed/final_dataset.csv``.

The merge key is assumed to be ``material_id`` (or ``mp_id`` if that column
is present). The script is defensive: it will attempt to locate a suitable
identifier column in each source and fall back to an inner join on the
intersection of columns.

The script is deliberately lightweight and avoids importing the project's
``utils`` package (which has a complex import graph) – it uses the standard
``logging`` module directly.
"""

import json
import logging
from pathlib import Path

import pandas as pd


LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


def _load_json_as_df(json_path: Path) -> pd.DataFrame:
    """Load a JSON file that contains a list of dictionaries into a DataFrame."""
    LOGGER.info("Loading JSON data from %s", json_path)
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # The JSON is expected to be a list of dicts; if it's a dict with a
    # ``data`` key, extract that.
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    df = pd.DataFrame(data)
    LOGGER.info("Loaded %d records from %s", len(df), json_path)
    return df


def _determine_id_column(dfs):
    """
    Determine a common identifier column among the provided DataFrames.

    Preference order:
    1. ``material_id``
    2. ``mp_id``
    3. Any column that appears in all DataFrames.
    """
    candidates = ["material_id", "mp_id"]
    for col in candidates:
        if all(col in df.columns for df in dfs):
            return col
    # Fallback: intersection of columns
    common = set(dfs[0].columns)
    for df in dfs[1:]:
        common &= set(df.columns)
    if common:
        chosen = sorted(common)[0]  # deterministic choice
        LOGGER.warning(
            "Using fallback identifier column '%s' (present in all sources)",
            chosen,
        )
        return chosen
    raise ValueError(
        "No common identifier column found among the input data sources."
    )


def assemble_final_dataset(
    materials_json_path: Path,
    nist_json_path: Path,
    features_csv_path: Path,
    output_csv_path: Path,
) -> None:
    """
    Merge the three input sources and write the combined dataset to CSV.

    Parameters
    ----------
    materials_json_path: Path
        Path to ``materials_project_data.json``.
    nist_json_path: Path
        Path to ``nist_data.json``.
    features_csv_path: Path
        Path to the pre‑computed ``features.csv``.
    output_csv_path: Path
        Destination path for the final merged CSV.
    """
    # Load data
    materials_df = _load_json_as_df(materials_json_path)
    nist_df = _load_json_as_df(nist_json_path)
    features_df = pd.read_csv(features_csv_path)

    # Determine the identifier column to join on
    id_col = _determine_id_column([materials_df, nist_df, features_df])
    LOGGER.info("Merging on identifier column '%s'", id_col)

    # Perform merges – keep all records that have descriptor features
    merged = materials_df.merge(
        nist_df, on=id_col, how="left", suffixes=("", "_nist")
    )
    merged = merged.merge(
        features_df, on=id_col, how="left", suffixes=("", "_feat")
    )

    # Basic sanity check
    if merged.empty:
        raise RuntimeError("Resulting merged dataset is empty.")

    # Ensure output directory exists
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    merged.to_csv(output_csv_path, index=False)
    LOGGER.info(
        "Final dataset written to %s with %d rows and %d columns",
        output_csv_path,
        merged.shape[0],
        merged.shape[1],
    )


def main() -> None:
    """Entry‑point for ``python -m code.data.assemble_final_dataset``."""
    # Resolve paths relative to the project root
    project_root = Path(__file__).resolve().parents[2]
    materials_json = project_root / "data" / "raw" / "materials_project_data.json"
    nist_json = project_root / "data" / "raw" / "nist_data.json"
    features_csv = project_root / "data" / "processed" / "features.csv"
    output_csv = project_root / "data" / "processed" / "final_dataset.csv"

    assemble_final_dataset(
        materials_json_path=materials_json,
        nist_json_path=nist_json,
        features_csv_path=features_csv,
        output_csv_path=output_csv,
    )


if __name__ == "__main__":
    main()
