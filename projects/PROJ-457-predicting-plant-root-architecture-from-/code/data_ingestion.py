import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from config import get_config, setup_logging


def get_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "code" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_data_source_type_column(df: pd.DataFrame) -> str:
    """
    Detect the data source type column.
    Checks for 'data_source_type' or known aliases.
    Raises ValueError if not found.
    """
    aliases = ["data_source_type", "source_type", "experiment_type", "data_origin"]
    for col in aliases:
        if col in df.columns:
            return col
    raise ValueError(
        f"Could not detect data source type column. "
        f"Expected one of: {aliases}. "
        f"Available columns: {list(df.columns)}"
    )


def filter_by_data_source_type(
    df: pd.DataFrame, logger: logging.Logger
) -> Tuple[pd.DataFrame, int]:
    """
    Filter out rows where data_source_type indicates 'manipulated' or 'controlled'.
    Returns filtered dataframe and count of excluded rows.
    """
    if df.empty:
        return df, 0

    source_col = get_data_source_type_column(df)
    exclude_values = [
        "manipulated",
        "controlled",
        "nutrient_manipulation",
        "treatment",
    ]

    mask = ~df[source_col].isin(exclude_values)
    excluded_count = (~mask).sum()

    filtered_df = df[mask].reset_index(drop=True)
    logger.info(
        f"Filtered by data_source_type: excluded {excluded_count} rows "
        f"(values: {exclude_values})"
    )
    return filtered_df, excluded_count


def filter_by_missing_nutrients(
    df: pd.DataFrame,
    p_n_available: bool,
    logger: logging.Logger,
) -> Tuple[pd.DataFrame, int]:
    """
    If p_n_available is True, exclude rows where Phosphorus or Nitrogen values are missing (NaN).
    Do NOT impute.
    Returns filtered dataframe and count of excluded rows.
    """
    if not p_n_available:
        logger.info("p_n_available is False. Skipping missing nutrient filter.")
        return df, 0

    if df.empty:
        return df, 0

    nutrient_cols = ["phosphorus", "nitrogen"]
    missing_cols = [c for c in nutrient_cols if c in df.columns]

    if not missing_cols:
        logger.warning(
            f"Expected nutrient columns {nutrient_cols} not found in dataframe. "
            f"Skipping missing nutrient filter."
        )
        return df, 0

    initial_count = len(df)
    mask = df[missing_cols].notna().all(axis=1)
    excluded_count = (~mask).sum()

    filtered_df = df[mask].reset_index(drop=True)
    logger.info(
        f"Filtered by missing nutrients: excluded {excluded_count} rows "
        f"(columns checked: {missing_cols})"
    )
    return filtered_df, excluded_count


def filter_by_sample_size(
    df: pd.DataFrame,
    min_samples: int = 20,
    logger: logging.Logger = None,
) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Exclude species with n < min_samples.
    Returns filtered dataframe, count of excluded species, and list of excluded species names.
    """
    if df.empty:
        return df, 0, []

    if "species" not in df.columns:
        logger.warning("No 'species' column found. Cannot filter by sample size.")
        return df, 0, []

    species_counts = df["species"].value_counts()
    excluded_species = species_counts[species_counts < min_samples].index.tolist()
    excluded_count = len(excluded_species)

    mask = df["species"].isin(species_counts[species_counts >= min_samples].index)
    filtered_df = df[mask].reset_index(drop=True)

    if logger:
        logger.info(
            f"Filtered by sample size (n<{min_samples}): excluded {excluded_count} species, "
            f"{len(df) - len(filtered_df)} rows"
        )
        logger.debug(f"Excluded species: {excluded_species}")

    return filtered_df, excluded_count, excluded_species


def write_species_counts_report(
    total_species_input: int,
    excluded_species_count: int,
    excluded_species_list: List[str],
    rows_excluded_by_source: int,
    rows_excluded_by_missing_nutrients: int,
    rows_excluded_by_sample_size: int,
    config: Dict[str, Any],
    logger: logging.Logger,
) -> Path:
    """
    Write a JSON file containing species counts and exclusion metrics.
    """
    report_path = Path(config["ARTIFACTS_PATH"]) / "reports" / "species_counts.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "total_species_input": int(total_species_input),
        "excluded_species_count": int(excluded_species_count),
        "excluded_species_list": excluded_species_list,
        "rows_excluded_by_source": int(rows_excluded_by_source),
        "rows_excluded_by_missing_nutrients": int(rows_excluded_by_missing_nutrients),
        "rows_excluded_by_sample_size": int(rows_excluded_by_sample_size),
    }

    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Species counts report written to {report_path}")
    return report_path


def load_processed_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the processed dataset from disk.
    """
    data_path = Path(config["DATA_PATH"]) / "processed" / "merged_dataset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found: {data_path}")
    return pd.read_csv(data_path)


def main():
    """
    Main entry point for T015c: Filter by Missing Nutrients.
    This function assumes T014b has set p_n_available in state.json.
    """
    config = get_config()
    logger = setup_logging(config)

    logger.info("Starting T015c: Filter by Missing Nutrients")

    # Load state to check p_n_available
    state_path = Path(config["ARTIFACTS_PATH"]) / "state.json"
    if not state_path.exists():
        logger.error("State file not found. Run T014a first.")
        sys.exit(1)

    with open(state_path, "r") as f:
        state = json.load(f)

    p_n_available = state.get("p_n_available", False)
    logger.info(f"p_n_available flag from state: {p_n_available}")

    # Load processed data (output of T013/T015b)
    try:
        df = load_processed_data(config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    initial_rows = len(df)
    logger.info(f"Loaded dataset with {initial_rows} rows")

    # Apply missing nutrient filter
    df_filtered, excluded_count = filter_by_missing_nutrients(
        df, p_n_available, logger
    )

    final_rows = len(df_filtered)
    logger.info(
        f"T015c complete. Excluded {excluded_count} rows due to missing nutrients. "
        f"Remaining rows: {final_rows}"
    )

    # Save filtered data (optional, but good practice for pipeline)
    output_path = Path(config["DATA_PATH"]) / "processed" / "filtered_nutrients.csv"
    df_filtered.to_csv(output_path, index=False)
    logger.info(f"Filtered data saved to {output_path}")

    # Note: The actual writing of species_counts.json is handled by T015e,
    # which aggregates counts from all filter steps. T015c returns the count.
    # We return the count via stdout for potential chaining, though in a real
    # pipeline this would be managed by a workflow engine.
    print(json.dumps({"rows_excluded_by_missing_nutrients": excluded_count}))

    return 0


if __name__ == "__main__":
    sys.exit(main())
