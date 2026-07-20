import os
import sys
import json
import hashlib
import logging
from pathlib import Path
import yaml
import jsonschema
import pandas as pd

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str):
    actual = compute_sha256(file_path)
    if actual != expected_checksum:
        raise ValueError(f"Checksum mismatch for {file_path}")

def load_schema(path: Path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(csv_path: Path, schema_path: Path):
    schema = load_schema(schema_path)
    df = pd.read_csv(csv_path)
    required = schema.get('required', [])
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column {col} in {csv_path}")

def validate_json_against_schema(json_path: Path, schema_path: Path):
    schema = load_schema(schema_path)
    with open(json_path, 'r') as f:
        data = json.load(f)
    jsonschema.validate(data, schema)

def run_quickstart_validation():
    root = Path(__file__).parent.parent
    # Check outputs exist
    assert (root / "data" / "processed" / "dataset_cleaned.csv").exists()
    assert (root / "data" / "outputs" / "best_model.pkl").exists()
    assert (root / "data" / "outputs" / "model_results.json").exists()
    assert (root / "data" / "outputs" / "feature_importance.json").exists()
    assert (root / "data" / "outputs" / "variance_partition.csv").exists()
    
    # Validate schemas
    validate_csv_against_schema(
        root / "data" / "processed" / "dataset_cleaned.csv",
        root / "contracts" / "dataset.schema.yaml"
    )
    validate_json_against_schema(
        root / "data" / "outputs" / "model_results.json",
        root / "contracts" / "model_output.schema.yaml"
    )
    logger.info("Validation passed.")

def main():
    logging.basicConfig(level=logging.INFO)
    run_quickstart_validation()

if __name__ == "__main__":
    main()