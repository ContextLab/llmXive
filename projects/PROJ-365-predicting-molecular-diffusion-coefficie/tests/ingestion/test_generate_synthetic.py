"""
Contract test for T007b: Validate synthetic dataset generation.
"""
import csv
import json
import pytest
from pathlib import Path
import sys

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingestion.generate_synthetic import generate_synthetic_dataset, RANDOM_SEED, NUM_ROWS


def test_generated_csv_schema(tmp_path):
    """Verify the generated CSV has the correct columns."""
    output_file = tmp_path / "dataset.csv"
    generate_synthetic_dataset(output_file, num_rows=10, seed=RANDOM_SEED)

    assert output_file.exists(), "Generated CSV file does not exist."

    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

    expected_columns = ["smiles", "solvent", "diffusion_coefficient", "viscosity", "dielectric_constant"]
    assert fieldnames == expected_columns, f"Expected columns {expected_columns}, got {fieldnames}"

    # Verify row count
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 10, f"Expected 10 rows, got {len(rows)}"


def test_generated_data_types(tmp_path):
    """Verify data types in the generated CSV."""
    output_file = tmp_path / "dataset.csv"
    generate_synthetic_dataset(output_file, num_rows=5, seed=RANDOM_SEED)

    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # smiles should be string
            assert isinstance(row["smiles"], str)
            assert len(row["smiles"]) > 0

            # solvent should be string
            assert isinstance(row["solvent"], str)

            # numeric fields should be convertible to float
            float(row["diffusion_coefficient"])
            float(row["viscosity"])
            float(row["dielectric_constant"])


def test_deterministic_output(tmp_path):
    """Verify that running with the same seed produces the same output."""
    output_file_1 = tmp_path / "dataset_1.csv"
    output_file_2 = tmp_path / "dataset_2.csv"

    generate_synthetic_dataset(output_file_1, num_rows=20, seed=RANDOM_SEED)
    generate_synthetic_dataset(output_file_2, num_rows=20, seed=RANDOM_SEED)

    with open(output_file_1, "r", encoding="utf-8") as f1, open(output_file_2, "r", encoding="utf-8") as f2:
        content_1 = f1.read()
        content_2 = f2.read()

    assert content_1 == content_2, "Output is not deterministic with the same seed."