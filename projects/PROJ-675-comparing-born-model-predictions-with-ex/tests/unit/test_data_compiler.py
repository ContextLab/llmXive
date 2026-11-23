"""
Unit tests for the data compiler module.

Tests verify:
1. Data fetching functions return expected structure
2. Precision requirements are met (ionic radii >= 0.01 Å)
3. Uncertainty fields are populated
4. Metadata file is created with required fields
"""

import json
import csv
from pathlib import Path
import pytest

# Import the module under test
import code.data_compiler as data_compiler


class TestIonicRadiiPrecision:
    """Test that ionic radii meet the required precision."""

    def test_ionic_radii_precision_requirement(self):
        """Verify ionic radii have at least 0.01 Å precision."""
        # Create a mock session
        class MockSession:
            pass

        session = MockSession()
        radii = data_compiler.fetch_nist_ionic_radii(session)

        # Check that all radii have at least 0.01 Å precision
        for ion, radius in radii.items():
            # Radius should be a float with at most 2 decimal places
            assert isinstance(radius, (int, float)), f"Radius for {ion} is not numeric"
            # Check precision: radius should be representable with 0.01 Å steps
            precision_check = round(radius, 2) == radius
            assert precision_check, f"Ionic radius for {ion} ({radius}) does not meet 0.01 Å precision"


class TestDielectricConstants:
    """Test dielectric constant data structure and precision."""

    def test_dielectric_constant_structure(self):
        """Verify dielectric constants have required fields."""
        class MockSession:
            pass

        session = MockSession()
        constants = data_compiler.fetch_dielectric_constants(session)

        for solvent, info in constants.items():
            assert "epsilon" in info, f"Missing epsilon for {solvent}"
            assert "uncertainty" in info, f"Missing uncertainty for {solvent}"
            assert "temp_c" in info, f"Missing temperature for {solvent}"
            assert isinstance(info["epsilon"], (int, float)), f"Epsilon for {solvent} is not numeric"
            assert isinstance(info["uncertainty"], (int, float)), f"Uncertainty for {solvent} is not numeric"


class TestSolvationData:
    """Test solvation energy data structure."""

    def test_solvation_data_structure(self):
        """Verify solvation data has required fields."""
        class MockSession:
            pass

        session = MockSession()
        data = data_compiler.fetch_experimental_solvation_energies(session)

        assert len(data) > 0, "Solvation data is empty"

        required_fields = ["ion", "solvent", "deltaG", "uncertainty", "charge", "radius_type"]
        for record in data:
            for field in required_fields:
                assert field in record, f"Missing field '{field}' in solvation record"

            # Verify uncertainty is present and numeric
            assert isinstance(record["uncertainty"], (int, float)), "Uncertainty must be numeric"
            assert record["uncertainty"] > 0, "Uncertainty must be positive"


class TestDatasetCompilation:
    """Test the full compilation pipeline."""

    def test_compiled_dataset_exists_and_valid(self):
        """Verify the compiled dataset file exists and has required fields."""
        # Run compilation
        data_compiler.compile_experimental_dataset()

        # Check file exists
        output_file = Path(data_compiler.DATA_DIR) / "experimental_solvation.csv"
        assert output_file.exists(), f"Output file {output_file} was not created"

        # Read and validate CSV
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        assert len(records) >= 30, f"Expected at least 30 records, got {len(records)}"

        required_columns = [
            "ion_identifier",
            "solvent_identifier",
            "experimental_deltaG",
            "deltaG_uncertainty",
            "epsilon",
            "epsilon_uncertainty",
            "radius",
            "charge",
            "radius_type",
            "temperature",
            "source_citation",
            "instrument_metadata",
        ]

        if records:
            first_record = records[0]
            for col in required_columns:
                assert col in first_record, f"Missing column '{col}' in output CSV"


    def test_metadata_file_created(self):
        """Verify metadata JSON file is created with required fields."""
        # Run compilation
        data_compiler.compile_experimental_dataset()

        # Check file exists
        metadata_file = Path(data_compiler.DATA_DIR) / "metadata.json"
        assert metadata_file.exists(), f"Metadata file {metadata_file} was not created"

        # Read and validate JSON
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        required_fields = [
            "dataset_version",
            "compilation_timestamp",
            "total_records",
            "source_citations",
            "uncertainty_coverage_percentage",
        ]

        for field in required_fields:
            assert field in metadata, f"Missing field '{field}' in metadata.json"

        # Verify uncertainty coverage is 100%
        assert metadata["uncertainty_coverage_percentage"] == 100.0, "Uncertainty coverage should be 100%"

        # Verify precision requirements are documented
        assert "precision_requirements_met" in metadata, "Missing precision_requirements_met in metadata"
        assert metadata["precision_requirements_met"]["ionic_radii_precision_A"] == 0.01, "Ionic radii precision should be 0.01 Å"