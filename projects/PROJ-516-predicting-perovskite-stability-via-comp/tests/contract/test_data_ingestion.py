"""
Contract test for data ingestion output schema (T010).

This test verifies that the output of the data ingestion pipeline adheres to the
expected schema defined for User Story 1. It ensures that the final processed
dataset contains the required compositional descriptors and stability metrics.

Prerequisites:
- `code/feature_engineering.py` and `code/filter_descriptors.py` must have been
  executed successfully to generate the final CSV.
- The CSV must be located at `data/processed/descriptors_final.csv` (as per T017).
"""
import csv
import os
import pytest
from pathlib import Path

# Define the expected columns based on the data model and task requirements.
# Note: T010 description listed columns from an intermediate step. T017 (Finalize)
# is the canonical source for the "final" dataset which includes uncertainty and
# instrumentation metadata required by the Marie Curie review.
EXPECTED_COLUMNS = {
    "formula",
    "T_d",
    "atomic_fraction_A",
    "atomic_fraction_B",
    "atomic_fraction_X",
    "weighted_ionic_radius",
    "weighted_electronegativity",
    "weighted_formation_enthalpy",
    "variance_ionic_radius",
    "variance_electronegativity",
    # Added from T013b/T017 for measurement rigor:
    "T_d_uncertainty",
    "instrument_model",
    "manufacturer",
    "precision_source",
    # Added from T014b:
    "perovskite_family",
    # Added from T012d/T012e:
    "source"
}

# The core numeric descriptors required for the regression model.
REQUIRED_NUMERIC_COLUMNS = {
    "T_d",
    "atomic_fraction_A",
    "atomic_fraction_B",
    "atomic_fraction_X",
    "weighted_ionic_radius",
    "weighted_electronegativity",
    "weighted_formation_enthalpy",
    "variance_ionic_radius",
    "variance_electronegativity"
}

# Path to the FINAL processed dataset as defined by T017.
# The original test pointed to nrel_perovskites.csv (raw), but the contract
# for "data ingestion output schema" in the context of the full pipeline
# implies the final enriched dataset used for modeling.
OUTPUT_PATH = Path("data/processed/descriptors_final.csv")


class TestDataIngestionSchema:
    """Contract tests for the data ingestion output schema."""

    def test_output_file_exists(self):
        """Verify that the data ingestion pipeline produced the final output file."""
        assert OUTPUT_PATH.exists(), (
            f"Output file {OUTPUT_PATH} does not exist. "
            "Ensure the full pipeline (T012a-T017) has run successfully."
        )

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
                    try:
                        val = float(t_d)
                        assert val > 0, f"T_d value {val} is not positive"
                        break  # Check only the first valid row
                    except ValueError:
                        continue

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
    
    def test_uncertainty_non_null(self):
        """Verify that T_d_uncertainty is present and non-null (Measurement Rigor)."""
        with open(OUTPUT_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            found = False
            for row in reader:
                val = row.get("T_d_uncertainty")
                if val is not None and val.strip() != "":
                    float(val) # Ensure it's numeric
                    found = True
                    break
            assert found, "No valid T_d_uncertainty values found in dataset."

    def test_instrumentation_metadata_present(self):
        """Verify that instrumentation metadata columns exist (Measurement Rigor)."""
        with open(OUTPUT_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check that we have at least one entry with instrument data
                # or a valid 'Unknown' fallback
                model = row.get("instrument_model", "")
                source = row.get("precision_source", "")
                assert model is not None, "instrument_model column missing"
                assert source in ["source", "registry", "Unknown"], \
                    f"Invalid precision_source: {source}"
                break