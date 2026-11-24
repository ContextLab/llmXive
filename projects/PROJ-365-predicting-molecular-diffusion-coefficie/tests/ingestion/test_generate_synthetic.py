import csv
import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

# Import the script's main function to trigger dataset generation
from ingestion.generate_synthetic import main as generate_main

# Path to the schema defined in the specs directory
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specs" / "001-predicting-molecular-diffusion-coefficie" / "contracts" / "ingestion_schema.schema.yaml"

@pytest.fixture(scope="module")
def synthetic_csv_path():
    """
    Runs the synthetic data generator once for the test session and returns the path
    to the generated CSV file.
    """
    generate_main()  # This creates data/raw/dataset.csv
    csv_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "dataset.csv"
    assert csv_path.is_file(), f"Expected synthetic CSV at {csv_path}"
    return csv_path

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_row_count(synthetic_csv_path):
    """The CSV must contain exactly 500 data rows (excluding the header)."""
    with open(synthetic_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # First row is header
    assert len(rows) - 1 == 500, f"Expected 500 data rows, found {len(rows)-1}"

def test_schema_validation(synthetic_csv_path):
    """Each row must conform to the ingestion schema."""
    schema = load_schema()
    with open(synthetic_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):  # start=2 accounts for header line number
            # Convert numeric fields to appropriate types for validation
            try:
                row["diffusion_coefficient"] = float(row["diffusion_coefficient"])
                row["viscosity"] = float(row["viscosity"])
                row["dielectric_constant"] = float(row["dielectric_constant"])
            except ValueError as e:
                raise AssertionError(f"Row {idx} has non‑numeric value where a number is expected: {e}")

            try:
                validate(instance=row, schema=schema)
            except ValidationError as ve:
                raise AssertionError(f"Schema validation failed for row {idx}: {ve.message}")