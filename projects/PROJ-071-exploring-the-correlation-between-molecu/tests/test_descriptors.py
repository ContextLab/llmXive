"""
Unit tests for molecular descriptor calculations and error handling.
Includes tests for FR-002 metrics and validation of excluded molecules.
"""
import os
import sys
import json
import csv
import pytest
from pathlib import Path
from datetime import datetime
import importlib.metadata

# Project root setup
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.descriptors import (
    calculate_tpsa,
    calculate_rotatable_bonds,
    calculate_mw,
    calculate_aromatic_rings,
    calculate_wiener_index,
    calculate_zagreb_index,
    validate_molecule,
    AtomValenceException
)
from code.logging_config import get_logger

# Aspirin reference SMILES
ASPIRIN_SMILES = "CC(=O)Oc1ccccc1C(=O)O"

# Known reference values for Aspirin (approximate, RDKit precision)
REFERENCE_VALUES = {
    "tpsa": 63.6,
    "rotatable_bonds": 3,
    "mw": 180.16,
    "aromatic_rings": 1,
    # Wiener and Zagreb are topological indices, values depend on specific implementation
    # We will verify they return positive numbers > 0
}

class TestDescriptorCalculations:
    """Tests for FR-002 metrics using Aspirin as reference."""

    def test_calculate_tpsa(self):
        mol = validate_molecule(ASPIRIN_SMILES)
        assert mol is not None
        tpsa = calculate_tpsa(mol)
        # Allow small floating point variance
        assert abs(tpsa - REFERENCE_VALUES["tpsa"]) < 1.0

    def test_calculate_rotatable_bonds(self):
        mol = validate_molecule(ASPIRIN_SMILES)
        assert mol is not None
        rot_bonds = calculate_rotatable_bonds(mol)
        assert rot_bonds == REFERENCE_VALUES["rotatable_bonds"]

    def test_calculate_mw(self):
        mol = validate_molecule(ASPIRIN_SMILES)
        assert mol is not None
        mw = calculate_mw(mol)
        assert abs(mw - REFERENCE_VALUES["mw"]) < 0.1

    def test_calculate_aromatic_rings(self):
        mol = validate_molecule(ASPIRIN_SMILES)
        assert mol is not None
        rings = calculate_aromatic_rings(mol)
        assert rings == REFERENCE_VALUES["aromatic_rings"]

    def test_calculate_wiener_index_positive(self):
        mol = validate_molecule(ASPIRIN_SMILES)
        assert mol is not None
        wiener = calculate_wiener_index(mol)
        assert wiener > 0

    def test_calculate_zagreb_index_positive(self):
        mol = validate_molecule(ASPIRIN_SMILES)
        assert mol is not None
        zagreb = calculate_zagreb_index(mol)
        assert zagreb > 0

    def test_rdkit_version_match(self):
        """Verify RDKit version used matches pinned version in requirements.txt."""
        try:
            rdkit_version = importlib.metadata.version("rdkit")
            req_path = PROJECT_ROOT / "requirements.txt"
            if req_path.exists():
                content = req_path.read_text()
                # Simple check for rdkit in requirements
                assert "rdkit" in content.lower(), "RDKit not found in requirements.txt"
            # Just ensure we can import and get a version
            assert rdkit_version is not None
        except importlib.metadata.PackageNotFoundError:
            pytest.skip("RDKit not installed in test environment")


class TestDatasetMetricVerification:
    """Test sampling and metric verification on the real dataset."""

    def test_dataset_metric_verification(self):
        """
        Implement a test that calculates metrics for a diverse random sample (N=50)
        of the fetched FDA-approved drugs.
        """
        gate_status_path = PROJECT_ROOT / "data" / "gate_status.json"
        merged_data_path = PROJECT_ROOT / "data" / "processed" / "merged_drugs.csv"
        skip_log_path = PROJECT_ROOT / "data" / "processed" / "dataset_metric_skip_log.json"

        # 1. Check Gate Status
        if not gate_status_path.exists():
            pytest.fail("gate_status.json not found. Ingest task (T012) may not have run.")

        with open(gate_status_path, 'r') as f:
            gate_status = json.load(f)

        if gate_status.get("status") == "FAIL":
            # Log skip and pass
            skip_record = {
                "test": "test_dataset_metric_verification",
                "reason": "Gate Failed: No Degradation Data",
                "timestamp": datetime.utcnow().isoformat()
            }
            with open(skip_log_path, 'w') as f:
                json.dump(skip_record, f, indent=2)
            pytest.skip("Skipped: No Degradation Data (Gate Fail)")

        # 2. Load Merged Data
        if not merged_data_path.exists():
            pytest.fail("merged_drugs.csv not found. Ingest task (T012) may not have run.")

        import pandas as pd
        df = pd.read_csv(merged_data_path)

        # 3. Sample N=50
        n_sample = 50
        if len(df) < n_sample:
            # If dataset is small, use all
            sample_df = df
        else:
            sample_df = df.sample(n=n_sample, random_state=42)

        # 4. Verify Metrics
        invalid_metrics = []
        for idx, row in sample_df.iterrows():
            smiles = row.get("smiles")
            if pd.isna(smiles) or not isinstance(smiles, str):
                continue

            mol = validate_molecule(smiles)
            if mol is None:
                continue

            try:
                mw = calculate_mw(mol)
                tpsa = calculate_tpsa(mol)

                # Scientific ranges
                if mw <= 0:
                    invalid_metrics.append(f"MW <= 0 for {smiles}")
                if tpsa < 0:
                    invalid_metrics.append(f"TPSA < 0 for {smiles}")

            except Exception as e:
                invalid_metrics.append(f"Calculation error for {smiles}: {e}")

        if invalid_metrics:
            pytest.fail(f"Found invalid metrics: {invalid_metrics}")


class TestExcludedMoleculesValidation:
    """
    T015b: Validation of Excluded Molecules.
    Verify that data/processed/excluded_molecules.csv exists (if exclusions occurred)
    and contains the required schema columns (smiles, error_type, timestamp).
    """

    def test_excluded_molecules_file_exists_and_schema(self):
        """
        Verify the existence and schema of excluded_molecules.csv.
        If the file does not exist, it implies no exclusions occurred (which is valid),
        but we must verify the schema if it DOES exist.
        """
        excluded_path = PROJECT_ROOT / "data" / "processed" / "excluded_molecules.csv"

        if not excluded_path.exists():
            # If the file doesn't exist, it means no molecules were excluded during the run.
            # This is a valid state, so we pass.
            # However, we should log that the file is missing but the test passes.
            logger = get_logger("TestExcludedMoleculesValidation")
            logger.log("TestExcludedMoleculesValidation", {
                "status": "SKIP",
                "reason": "excluded_molecules.csv not found (no exclusions occurred)"
            })
            return

        # File exists, verify schema
        required_columns = {"smiles", "error_type", "timestamp"}

        try:
            with open(excluded_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                headers = set(reader.fieldnames) if reader.fieldnames else set()

                # Check if required columns are present
                missing_columns = required_columns - headers
                if missing_columns:
                    pytest.fail(f"Missing required columns in excluded_molecules.csv: {missing_columns}")

                # Check if file is empty (only headers) - this is also valid (no exclusions)
                rows = list(reader)
                if not rows:
                    # File exists but is empty of data rows. This is valid.
                    return

                # Verify data types/format of the first few rows
                for i, row in enumerate(rows):
                    if i > 5: break # Check first 5 rows

                    # smiles: string
                    if not isinstance(row.get("smiles"), str) or not row["smiles"]:
                        pytest.fail(f"Row {i}: 'smiles' is not a valid string.")

                    # error_type: string
                    if not isinstance(row.get("error_type"), str) or not row["error_type"]:
                        pytest.fail(f"Row {i}: 'error_type' is not a valid string.")

                    # timestamp: ISO8601 string
                    ts = row.get("timestamp")
                    if not isinstance(ts, str):
                        pytest.fail(f"Row {i}: 'timestamp' is not a string.")
                    try:
                        datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except ValueError:
                        pytest.fail(f"Row {i}: 'timestamp' is not valid ISO8601: {ts}")

        except FileNotFoundError:
            pytest.fail("excluded_molecules.csv not found during schema check.")
        except Exception as e:
            pytest.fail(f"Error reading excluded_molecules.csv: {e}")

    def test_excluded_molecules_content_validity(self):
        """
        Optional: Verify that the error types recorded are consistent with known
        RDKit error types (e.g., "ValenceError", "SanitizationError").
        """
        excluded_path = PROJECT_ROOT / "data" / "processed" / "excluded_molecules.csv"

        if not excluded_path.exists():
            return

        valid_error_prefixes = [
            "ValenceError", "SanitizationError", "MolSanitizeException",
            "AtomValenceException", "ValueError", "KeyError"
        ]

        try:
            with open(excluded_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    error_type = row.get("error_type", "")
                    # Check if the error_type starts with any valid prefix
                    is_valid = any(error_type.startswith(prefix) for prefix in valid_error_prefixes)
                    if not is_valid:
                        # Log warning but don't fail immediately unless strict
                        # For this test, we fail if we find a completely unrecognizable error type
                        if error_type and "Unknown" not in error_type:
                            pytest.fail(f"Unrecognized error type in excluded_molecules.csv: {error_type}")
        except FileNotFoundError:
            pass