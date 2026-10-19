"""
Script to generate the raw ESOL dataset with string molecule IDs.
This ensures that the contract test `test_dataset_schema.py` sees
the `molecule_id` column as a string (object dtype) rather than an
integer, satisfying the schema's type requirement.
"""
import yaml
import pandas as pd
from pathlib import Path

# Import the toolkit helper for path management and logging
from llmxive_toolkit import paths, get_logger

# skfp provides the real ESOL (Lipophilicity) dataset
from skfp.datasets.moleculenet import load_lipophilicity


def main() -> None:
    """
    Load the real ESOL dataset, add a string-prefixed molecule_id column,
    and write it to `data/raw/esol.csv` using the project's path helpers.
    """
    log = get_logger(__name__)

    # Resolve the path to the dataset schema to obtain the required column order
    schema_path = (
        paths.root
        / "specs"
        / "001-predicting-molecular-properties-from-top"
        / "contracts"
        / "dataset.schema.yaml"
    )
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    required_columns = schema.get("required", [])

    # Load the real ESOL (Lipophilicity) dataset via skfp
    X, y = load_lipophilicity()

    # Extract SMILES strings – skfp may return a DataFrame or a raw array
    if isinstance(X, pd.DataFrame):
        if "smiles" in X.columns:
            smiles_series = X["smiles"]
        else:
            smiles_series = X.iloc[:, 0]
    else:
        smiles_series = pd.Series(list(X))

    # Build a DataFrame with the required fields
    df = pd.DataFrame({"smiles": smiles_series, "logP": y})

    # Create a string molecule_id column with a non‑numeric prefix
    df.insert(0, "molecule_id", [f"mol_{i}" for i in range(len(df))])

    # Re‑order columns to match the schema exactly
    df = df[[col for col in required_columns]]

    # Write the CSV to the canonical raw data location
    raw_path: Path = paths.data("raw", "esol.csv")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_path, index=False)

    log.info(
        f"Generated raw ESOL dataset with {len(df)} rows at {raw_path}"
    )


if __name__ == "__main__":
    main()
