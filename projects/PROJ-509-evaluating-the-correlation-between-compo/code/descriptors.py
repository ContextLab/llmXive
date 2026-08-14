import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import sys
import json
import logging

from config import load_paths
from utils.io import load_dataframe_safely
from utils.chemical_families import assign_chemical_family

logger = logging.getLogger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON schema from a file."""
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate a DataFrame against a schema."""
    required_cols = schema.get("required_columns", [])
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    return True


def get_elemental_properties_df() -> pd.DataFrame:
    """Load elemental properties from the data directory."""
    paths = load_paths()
    file_path = paths["data_elemental"] / "elemental_properties.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Elemental properties file not found: {file_path}")
    return pd.read_csv(file_path)


def calculate_weighted_mean_variance(
    formula: str,
    properties_df: pd.DataFrame,
    property_name: str,
) -> Tuple[float, float]:
    """Calculate weighted mean and variance for a property given a formula."""
    from pymatgen.core import Composition

    try:
        comp = Composition(formula)
    except Exception as e:
        logger.warning(f"Could not parse formula {formula}: {e}")
        return np.nan, np.nan

    elements = comp.elements
    if not elements:
        return np.nan, np.nan

    weights = []
    values = []
    for el in elements:
        if el.symbol in properties_df["element"].values:
            row = properties_df[properties_df["element"] == el.symbol].iloc[0]
            val = row.get(property_name)
            if pd.isna(val):
                continue
            weights.append(comp[el])
            values.append(val)
        else:
            logger.warning(f"Element {el.symbol} not found in properties DB")

    if not weights:
        return np.nan, np.nan

    w = np.array(weights)
    v = np.array(values)
    w_sum = w.sum()
    mean = np.sum(w * v) / w_sum
    variance = np.sum(w * (v - mean) ** 2) / w_sum
    return mean, variance


def compute_descriptors_row(row: pd.Series, properties_df: pd.DataFrame) -> pd.Series:
    """Compute descriptors for a single row."""
    formula = row.get("formula_pretty") or row.get("formula")
    if pd.isna(formula):
        return row

    props = [
        "electronegativity",
        "atomic_radius",
        "valence_electrons",
        "melting_point",
        "ionization_energy",
    ]
    for prop in props:
        mean, var = calculate_weighted_mean_variance(formula, properties_df, prop)
        row[f"{prop}_mean"] = mean
        row[f"{prop}_var"] = var
    return row


def compute_descriptors_chunked(
    input_path: Path,
    output_path: Path,
    properties_df: pd.DataFrame,
    chunk_size: int = 10000,
) -> None:
    """Compute descriptors in chunks to save memory."""
    logger.info(f"Starting chunked descriptor computation from {input_path}")
    first_chunk = True
    total_rows = 0

    for chunk in pd.read_csv(input_path, chunksize=chunk_size):
        processed = chunk.apply(
            lambda r: compute_descriptors_row(r, properties_df), axis=1
        )
        if first_chunk:
            processed.to_csv(output_path, index=False)
            first_chunk = False
        else:
            processed.to_csv(output_path, mode="a", header=False, index=False)
        total_rows += len(chunk)
        logger.info(f"Processed {total_rows} rows")

    logger.info(f"Finished computing descriptors for {total_rows} rows")


def detect_and_cap_outliers(
    df: pd.DataFrame,
    target_col: str,
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0,
) -> Tuple[pd.DataFrame, int]:
    """Detect and cap outliers based on percentiles."""
    if lower_percentile >= upper_percentile:
        raise ValueError("lower_percentile must be less than upper_percentile")

    lower_bound = np.percentile(df[target_col], lower_percentile)
    upper_bound = np.percentile(df[target_col], upper_percentile)

    initial_count = len(df)
    df[target_col] = df[target_col].clip(lower=lower_bound, upper=upper_bound)
    capped_count = initial_count - len(df[df[target_col] == df[target_col]])

    # Count rows that were actually capped
    capped_rows = (
        (df[target_col] == lower_bound) | (df[target_col] == upper_bound)
    ).sum()

    return df, int(capped_rows)


def validate_final_dataset(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate the final dataset against the schema."""
    required_cols = schema.get("required_columns", [])
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
        if df[col].isna().any():
            logger.error(f"Column {col} contains null values")
            return False
    return True


def main() -> None:
    """Main entry point for descriptor computation."""
    logging.basicConfig(level=logging.INFO)
    paths = load_paths()

    # Determine input file based on sampling
    raw_input = paths["data_processed"] / "sampled_raw_data.csv"
    if not raw_input.exists():
        raw_input = paths["data_raw"] / "mp-2020.12.1_filtered.csv"

    if not raw_input.exists():
        raise FileNotFoundError(f"Input file not found: {raw_input}")

    properties_df = get_elemental_properties_df()
    schema = load_schema(paths["base"] / "contracts" / "dataset.schema.yaml")

    output_path = paths["data_processed"] / "computed_descriptors.csv"

    # Compute descriptors
    compute_descriptors_chunked(raw_input, output_path, properties_df)

    # Load and cap outliers
    df = pd.read_csv(output_path)
    if CAP_OUTLIERS:
        df, capped_count = detect_and_cap_outliers(df, "formation_energy_per_atom")
        logger.info(f"Capped {capped_count} outlier values")
        with open(paths["data_logs"] / "outliers.log", "w") as f:
            f.write(f"Capped {capped_count} outlier values\n")
        df.to_csv(output_path, index=False)
    else:
        logger.info("Outlier capping disabled")
        with open(paths["data_logs"] / "outliers.log", "w") as f:
            f.write("Outlier capping disabled\n")

    # Validate
    if not validate_final_dataset(df, schema):
        raise ValueError("Final dataset validation failed")

    logger.info("Descriptor computation complete")


if __name__ == "__main__":
    main()
