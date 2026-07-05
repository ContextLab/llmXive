"""
Contract test for data ingestion output schema (T010).

This test verifies that the output of `code/data_ingestion.py` adheres to the
expected schema defined for User Story 1. It ensures that:
1. The output file `data/raw/nrel_perovskites.csv` exists.
2. The CSV contains the required columns: `formula`, `T_d`, `atomic_fraction_A`,
   `weighted_ionic_radius`, `atomic_fraction_B`, `atomic_fraction_X`,
   `weighted_electronegativity`, `weighted_formation_enthalpy`,
   `weighted_first_ionization_energy`, `variance_ionic_radius`, `variance_electronegativity`,
   `T_d_uncertainty`, `source`, `instrument_model`, `precision`.
3. Critical numeric columns (`T_d`, `atomic_fraction_A`, `weighted_ionic_radius`, etc.)
   are not null for the first 10 rows (or all rows if fewer than 10).

Prerequisites:
- `code/data_ingestion.py` must have been executed successfully to generate the CSV.
- The CSV must be located at `data/raw/nrel_perovskites.csv`.
"""
import csv
import os
import pytest
from pathlib import Path

# Define the expected columns based on the data model and task requirements
EXPECTED_COLUMNS = {
    "formula",
    "T_d",
    "atomic_fraction_A",
    "weighted_ionic_radius",
    "atomic_fraction_B",
    "atomic_fraction_X",
    "weighted_electronegativity",
    "weighted_formation_enthalpy",
    "weighted_first_ionization_energy",
    "variance_ionic_radius",
    "variance_electronegativity",
    "T_d_uncertainty",
    "source",
    "instrument_model",
    "precision"
}

REQUIRED_NUMERIC_COLUMNS = {
    "T_d",
    "atomic_fraction_A",
    "weighted_ionic_radius",
    "atomic_fraction_B",
    "atomic_fraction_X",
    "weighted_electronegativity",
    "weighted_formation_enthalpy",
    "weighted_first_ionization_energy",
    "variance_ionic_radius",
    "variance_electronegativity",
    "T_d_uncertainty"
}

OUTPUT_PATH = Path("data/raw/nrel_perovskites.csv")


class TestDataIngestionSchema:
    """Contract tests for the data ingestion output schema."""

    def test_output_file_exists(self):
        """Verify that the data ingestion script produced the output file."""
        assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} does not exist. Run code/data_ingestion.py first."

    def test_required_columns_present(self):
        """Verify that all required columns are present in the CSV header."""
        with open(OUTPUT_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            actual_columns = set(reader.fieldnames)
            
            missing_columns = EXPECTED_COLUMNS - actual_columns
            extra_columns = actual_columns - EXPECTED_COLUMNS
            
            assert not missing_columns, f"Missing required columns: {missing_columns}"
            
            # Log extra columns but don't fail (schema extension is allowed)
            if extra_columns:
                pytest.skip(f"Extra columns found (allowed): {extra_columns}")

    def test_numeric_columns_not_null(self):
        """Verify that critical numeric columns contain non-null values."""
        rows_checked = 0
        with open(OUTPUT_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows_checked += 1
                if rows_checked > 10:
                    break
                
                for col in REQUIRED_NUMERIC_COLUMNS:
                    value = row.get(col)
                    assert value is not None and value.strip() != "", \
                        f"Column '{col}' contains null/empty value in row {rows_checked}"

    def test_formula_format(self):
        """Verify that the 'formula' column contains valid chemical formula strings."""
        import re
        # Basic regex for chemical formula (e.g., CsPbI3, CH3NH3PbI3)
        formula_pattern = re.compile(r"^[A-Za-z0-9\(\)\[\]]+$")
        
        with open(OUTPUT_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                formula = row.get("formula", "")
                assert formula_pattern.match(formula), f"Invalid formula format: {formula}"
                break  # Check only the first row for format validity

    def test_t_d_positive(self):
        """Verify that T_d values are positive (thermal decomposition temperature)."""
        with open(OUTPUT_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t_d = row.get("T_d")
                if t_d is not None and t_d.strip() != "":
                    val = float(t_d)
                    assert val > 0, f"T_d value {val} is not positive"
                    break  # Check only the first valid row

    def test_atomic_fractions_sum_to_one(self):
        """Verify that atomic fractions for A, B, and X sites sum to approximately 1.0."""
        with open(OUTPUT_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    frac_a = float(row.get("atomic_fraction_A", 0) or 0)
                    frac_b = float(row.get("atomic_fraction_B", 0) or 0)
                    frac_x = float(row.get("atomic_fraction_X", 0) or 0)
                    
                    total = frac_a + frac_b + frac_x
                    # Allow small floating point error
                    assert abs(total - 1.0) < 1e-5, \
                        f"Atomic fractions sum to {total}, expected ~1.0"
                    break  # Check only the first valid row
                except ValueError:
                    # Skip rows where conversion fails (e.g., empty values)
                    continue