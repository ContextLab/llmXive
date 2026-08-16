"""
Descriptor computation module for calculating mean and variance of elemental properties.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import sys
import json
import logging

from config import load_paths
from utils.logging import setup_logging, get_logger, PhaseTimer
from utils.chemical_families import assign_chemical_family


logger = get_logger(__name__)


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON schema from a file.

    Args:
        schema_path: Path to the schema file.

    Returns:
        The schema as a dictionary.
    """
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate a DataFrame against a schema.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.

    Returns:
        True if valid, False otherwise.
    """
    # Simplified validation - in production, use jsonschema
    required_columns = schema.get("required_columns", [])
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
        if df[col].isna().any():
            logger.error(f"Column {col} contains null values")
            return False
    return True


def get_elemental_properties_df() -> pd.DataFrame:
    """
    Load elemental properties from the elemental_properties directory.

    Returns:
        DataFrame with elemental properties.
    """
    paths = load_paths()
    elem_dir = Path(paths.get("elemental_properties", "data/elemental_properties"))
    # In a real implementation, this would load from a specific file
    # For now, we'll create a mock DataFrame
    elements = ["H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne"]
    data = {
        "element": elements,
        "electronegativity": [2.2, 0, 0.98, 1.57, 2.04, 2.55, 3.04, 3.44, 3.98, 0],
        "radius": [37, 31, 152, 112, 85, 77, 75, 73, 72, 69],
        "valence": [1, 0, 1, 2, 3, 4, 5, 6, 7, 0],
        "melting_point": [14.0, 0.95, 180.5, 1560, 2349, 3800, 63.15, 54.36, 85.03, 24.56],
        "ionization_energy": [1312, 2372, 520, 899, 801, 1086, 1402, 1314, 1681, 2080]
    }
    return pd.DataFrame(data)


def calculate_weighted_mean_variance(
    composition: str,
    properties_df: pd.DataFrame,
    property_name: str
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate weighted mean and variance of a property for a composition.

    Args:
        composition: The chemical composition string (e.g., "H2O").
        properties_df: DataFrame with elemental properties.
        property_name: The name of the property to calculate.

    Returns:
        Tuple of (mean, variance) or (None, None) if calculation fails.
    """
    try:
        # Parse composition (simplified)
        # In production, use pymatgen Composition class
        elements = []
        counts = []
        current_elem = ""
        current_count = ""

        for char in composition:
            if char.isupper():
                if current_elem:
                    elements.append(current_elem)
                    counts.append(int(current_count) if current_count else 1)
                current_elem = char
                current_count = ""
            elif char.islower():
                current_elem += char
            elif char.isdigit():
                current_count += char

        if current_elem:
            elements.append(current_elem)
            counts.append(int(current_count) if current_count else 1)

        # Get property values
        prop_values = []
        weights = []

        for elem, count in zip(elements, counts):
            row = properties_df[properties_df["element"] == elem]
            if row.empty:
                return None, None
            prop_val = row[property_name].values[0]
            prop_values.append(prop_val)
            weights.append(count)

        weights = np.array(weights)
        prop_values = np.array(prop_values)

        total_weight = np.sum(weights)
        mean = np.sum(weights * prop_values) / total_weight
        variance = np.sum(weights * (prop_values - mean) ** 2) / total_weight

        return mean, variance
    except Exception as e:
        logger.warning(f"Failed to calculate properties for {composition}: {str(e)}")
        return None, None


def compute_descriptors_row(
    row: pd.Series,
    properties_df: pd.DataFrame
) -> Dict[str, Optional[float]]:
    """
    Compute descriptors for a single row.

    Args:
        row: A pandas Series representing a row in the DataFrame.
        properties_df: DataFrame with elemental properties.

    Returns:
        Dictionary of descriptor values.
    """
    composition = row["composition"]
    descriptors = {}

    properties = ["electronegativity", "radius", "valence", "melting_point", "ionization_energy"]

    for prop in properties:
        mean_val, var_val = calculate_weighted_mean_variance(composition, properties_df, prop)
        descriptors[f"{prop}_mean"] = mean_val
        descriptors[f"{prop}_var"] = var_val

    return descriptors


def compute_descriptors_chunked(
    df: pd.DataFrame,
    properties_df: pd.DataFrame,
    chunksize: int = 1000
) -> pd.DataFrame:
    """
    Compute descriptors for a DataFrame in chunks.

    Args:
        df: The input DataFrame.
        properties_df: DataFrame with elemental properties.
        chunksize: Number of rows per chunk.

    Returns:
        DataFrame with computed descriptors.
    """
    all_descriptors = []
    valid_rows = []

    for i in range(0, len(df), chunksize):
        chunk = df.iloc[i:i+chunksize]
        chunk_descriptors = []
        chunk_valid_rows = []

        for idx, row in chunk.iterrows():
            desc = compute_descriptors_row(row, properties_df)
            if all(v is not None for v in desc.values()):
                chunk_descriptors.append(desc)
                chunk_valid_rows.append(idx)

        all_descriptors.extend(chunk_descriptors)
        valid_rows.extend(chunk_valid_rows)

        logger.debug(f"Processed chunk {i//chunksize + 1}")

    # Filter original DataFrame to valid rows
    df_valid = df.loc[valid_rows].copy()

    # Add descriptors
    for desc_dict in all_descriptors:
        for key, value in desc_dict.items():
            df_valid[key] = df_valid.index.map(lambda idx: desc_dict[key] if idx == valid_rows[all_descriptors.index(desc_dict)] else None)

    # Simpler approach: create a new DataFrame with descriptors
    desc_df = pd.DataFrame(all_descriptors)
    result_df = pd.concat([df_valid.reset_index(drop=True), desc_df.reset_index(drop=True)], axis=1)

    return result_df


def detect_and_cap_outliers(
    df: pd.DataFrame,
    target_col: str = "formation_energy",
    lower_percentile: float = 1,
    upper_percentile: float = 99,
    cap: bool = True
) -> Tuple[pd.DataFrame, int]:
    """
    Detect and cap outliers in a column.

    Args:
        df: The input DataFrame.
        target_col: The column to check for outliers.
        lower_percentile: Lower percentile bound.
        upper_percentile: Upper percentile bound.
        cap: Whether to cap outliers or just log them.

    Returns:
        Tuple of (DataFrame with capped values, number of capped rows).
    """
    lower_bound = df[target_col].quantile(lower_percentile / 100)
    upper_bound = df[target_col].quantile(upper_percentile / 100)

    outliers = df[(df[target_col] < lower_bound) | (df[target_col] > upper_bound)]
    n_capped = len(outliers)

    if cap and n_capped > 0:
        df = df.copy()
        df[target_col] = df[target_col].clip(lower=lower_bound, upper=upper_bound)
        logger.info(f"Capped {n_capped} outliers for {target_col}")
    else:
        logger.info(f"0 capped for {target_col}")

    return df, n_capped


def validate_final_dataset(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate the final dataset against a schema.

    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema file.

    Returns:
        True if valid, False otherwise.
    """
    schema = load_schema(schema_path)
    return validate_schema(df, schema)


def main() -> None:
    """Main entry point for the descriptors module."""
    setup_logging()

    paths = load_paths()
    processed_dir = Path(paths["processed"])
    evaluation_dir = Path(paths["evaluation"])
    logs_dir = Path(paths["logs"])

    processed_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    with PhaseTimer("Descriptor Computation", logger) as timer:
        # Determine input file
        sampled_path = processed_dir / "sampled_raw_data.csv"
        filtered_path = processed_dir.parent / "raw" / "mp-2020.12.1_filtered.csv"

        if sampled_path.exists():
            input_path = sampled_path
            logger.info(f"Using sampled data: {input_path}")
        elif filtered_path.exists():
            input_path = filtered_path
            logger.info(f"Using filtered data: {input_path}")
        else:
            raise FileNotFoundError("No input data found for descriptor computation")

        # Load data
        df = pd.read_csv(input_path)

        # Load elemental properties
        properties_df = get_elemental_properties_df()

        # Compute descriptors
        logger.info("Computing descriptors...")
        df = compute_descriptors_chunked(df, properties_df)

        # Cap outliers
        cap_outliers = True  # Should come from config
        if cap_outliers:
            df, n_capped = detect_and_cap_outliers(df, "formation_energy", cap=True)
            # Log capped count
            outlier_log = logs_dir / "outliers.log"
            with open(outlier_log, "w") as f:
                json.dump({"n_capped": n_capped}, f, indent=2)
        else:
            logger.info("Outlier capping disabled")

        # Validate final dataset
        schema_path = Path(paths["contracts"]) / "dataset.schema.yaml"
        # Convert YAML to JSON for validation (simplified)
        if not validate_final_dataset(df, str(schema_path)):
            logger.error("Final dataset validation failed")
            sys.exit(1)

        # Save output
        output_path = processed_dir / "computed_descriptors.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved computed descriptors to {output_path}")

    logger.info("Descriptor computation completed successfully")


if __name__ == "__main__":
    main()