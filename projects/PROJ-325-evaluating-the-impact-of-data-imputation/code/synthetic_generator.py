import os
import sys
import logging
import json
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

def generate_synthetic_data(
    n_samples: int,
    mean: float,
    variance: float,
    missingness_rate: float,
    missingness_mechanism: str = "MCAR",
    seed: int = 42
) -> pd.DataFrame:
    """Generates synthetic data with specified parameters."""

    np.random.seed(seed)  # Set seed for reproducibility
    data = np.random.normal(mean, np.sqrt(variance), n_samples)
    df = pd.DataFrame({"value": data})

    # Introduce missingness based on the mechanism
    if missingness_mechanism == "MCAR":
        mask = np.random.rand(n_samples) < missingness_rate
    elif missingness_mechanism == "MAR":
        # Example: Missingness depends on the value itself (more complex MAR can be designed)
        mask = (df["value"] < 0) & (np.random.rand(n_samples) < missingness_rate)
    else:
        raise ValueError("Invalid missingness mechanism.")

    df.loc[mask, "value"] = np.nan  # Introduce NaN values for missing data

    return df


def validate_schema(data: pd.DataFrame, schema_path: str) -> bool:
    """Validates the generated data against a JSON schema."""
    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Simple validation (can be expanded with more complex checks)
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a Pandas DataFrame.")
        if not all(col in data.columns for col in schema["properties"].keys()):
            raise ValueError("Data does not match the required columns.")

        return True  # Validation passed

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logging.error(f"Schema validation failed: {e}")
        return False


def main():
    """Main function to generate and save synthetic data."""

    n_samples = 1000
    mean = 50.0
    variance = 25.0
    missingness_rate = 0.2
    missingness_mechanism = "MAR"
    seed = 42  # Use a fixed seed for reproducibility

    data = generate_synthetic_data(n_samples, mean, variance, missingness_rate, missingness_mechanism, seed)

    output_path = Path("data/processed/synthetic_mar_v1.csv")
    data.to_csv(output_path, index=False)

    schema_path = "contracts/dataset.schema.yaml"
    if validate_schema(data, schema_path):
        logging.info("Data validated successfully against the schema.")
    else:
        logging.error("Schema validation failed.")


    # Prepare metadata for output artifact
    metadata = {
        "true_mean": mean,
        "true_variance": variance,
        "missingness_mechanism": missingness_mechanism
    }

    with open(Path("data/processed/synthetic_mar_v1_meta.json"), "w") as f:
        json.dump(metadata, f)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
