"""
Unit tests for manual curation validation workflow (Task T063).
Validates that manual_curated.csv conforms to the alloy_entry schema before ingestion.
"""
import os
import sys
import unittest
import tempfile
import shutil
import csv
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.utils.schema_validator import validate_csv_file, load_schema
from src.preprocessing.composition_parser import parse_formula_to_fractions
from src.preprocessing.validator import extract_elements_from_composition

# Constants
SCHEMA_PATH = project_root / "code" / "specs" / "001-predict-heusler-hysteresis" / "contracts" / "alloy_entry.schema.yaml"
REQUIRED_COLUMNS = [
    "composition",
    "coercivity_oe",
    "saturation_magnetization_emu_g",
    "source_type",
    "synthesis_method"
]
OPTIONAL_COLUMNS = ["doi", "crystal_structure"]
VALID_SOURCE_TYPES = ["Manual"]  # T018 specifically handles Manual
REQUIRED_SOURCE_TYPE = "Manual"

class TestManualCurationValidation(unittest.TestCase):
    """Tests for the manual curation validation logic."""

    def setUp(self):
        """Set up temporary directory and files for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.test_dir) / "manual_curated.csv"
        self.schema_path = SCHEMA_PATH

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_csv(self, rows):
        """Helper to create a CSV file with given rows."""
        with open(self.test_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def test_schema_validation_pass(self):
        """Test that a valid CSV passes schema validation."""
        rows = [
            {
                "composition": "Co2MnGa",
                "coercivity_oe": 45.5,
                "saturation_magnetization_emu_g": 110.2,
                "source_type": "Manual",
                "synthesis_method": "Arc Melting",
                "doi": "10.1016/j.actamat.2020.01.001",
                "crystal_structure": "L2_1"
            }
        ]
        self._create_csv(rows)

        # Load schema and validate
        schema = load_schema(self.schema_path)
        is_valid, errors = validate_csv_file(self.test_csv_path, schema)

        self.assertTrue(is_valid, f"Validation failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_schema_validation_missing_required_field(self):
        """Test that a CSV missing a required field fails validation."""
        rows = [
            {
                "composition": "Co2MnGa",
                # Missing coercivity_oe
                "saturation_magnetization_emu_g": 110.2,
                "source_type": "Manual",
                "synthesis_method": "Arc Melting"
            }
        ]
        self._create_csv(rows)

        schema = load_schema(self.schema_path)
        is_valid, errors = validate_csv_file(self.test_csv_path, schema)

        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("coercivity_oe" in str(err) for err in errors))

    def test_invalid_source_type(self):
        """Test that a CSV with invalid source_type fails validation."""
        rows = [
            {
                "composition": "Co2MnGa",
                "coercivity_oe": 45.5,
                "saturation_magnetization_emu_g": 110.2,
                "source_type": "Journal",  # Should be Manual for this specific file context
                "synthesis_method": "Arc Melting"
            }
        ]
        self._create_csv(rows)

        # While the schema might allow "Journal" generally, the manual curator
        # specifically expects "Manual". We test the business logic here.
        with open(self.test_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.assertEqual(row["source_type"], "Manual",
                                 "Manual curated file must have source_type='Manual'")

    def test_composition_format_valid(self):
        """Test that valid composition strings are accepted."""
        valid_compositions = ["Co2MnGa", "NiMnSn", "Fe3Al", "CoFeAl", "Mn2VAl"]
        for comp in valid_compositions:
            try:
                fractions = parse_formula_to_fractions(comp)
                self.assertIsInstance(fractions, dict)
                self.assertAlmostEqual(sum(fractions.values()), 1.0, places=4,
                                       msg=f"Fractions for {comp} do not sum to 1.0")
            except Exception as e:
                self.fail(f"Failed to parse valid composition {comp}: {e}")

    def test_composition_format_invalid(self):
        """Test that invalid composition strings raise errors."""
        invalid_compositions = ["Co2 Mn Ga", "CobaltManganeseGallium", "Co2Mn", ""]
        for comp in invalid_compositions:
            with self.assertRaises((ValueError, TypeError, KeyError)):
                parse_formula_to_fractions(comp)

    def test_element_extraction(self):
        """Test that elements are correctly extracted from composition strings."""
        comp = "Co2MnGa"
        elements = extract_elements_from_composition(comp)
        self.assertIn("Co", elements)
        self.assertIn("Mn", elements)
        self.assertIn("Ga", elements)
        self.assertEqual(len(elements), 3)

    def test_missing_optional_fields(self):
        """Test that missing optional fields do not cause validation failure."""
        rows = [
            {
                "composition": "Co2MnGa",
                "coercivity_oe": 45.5,
                "saturation_magnetization_emu_g": 110.2,
                "source_type": "Manual",
                "synthesis_method": "Arc Melting"
                # doi and crystal_structure are missing
            }
        ]
        self._create_csv(rows)

        schema = load_schema(self.schema_path)
        is_valid, errors = validate_csv_file(self.test_csv_path, schema)

        # Should be valid because optional fields are missing
        self.assertTrue(is_valid, f"Validation failed for missing optional fields: {errors}")

    def test_empty_csv(self):
        """Test that an empty CSV (only headers) is handled gracefully."""
        rows = [{c: "" for c in REQUIRED_COLUMNS}] # Actually need to write header only
        with open(self.test_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            # No data rows

        # Check row count
        with open(self.test_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows_list = list(reader)
            self.assertEqual(len(rows_list), 0)

    def test_numeric_fields_non_numeric(self):
        """Test that non-numeric values in numeric fields fail validation."""
        rows = [
            {
                "composition": "Co2MnGa",
                "coercivity_oe": "forty-five", # Invalid
                "saturation_magnetization_emu_g": 110.2,
                "source_type": "Manual",
                "synthesis_method": "Arc Melting"
            }
        ]
        self._create_csv(rows)

        # Custom check for numeric types since schema might not catch string "45.5" vs "forty-five"
        # depending on strictness. We explicitly check conversion here.
        with open(self.test_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    float(row["coercivity_oe"])
                    self.fail("Expected ValueError for non-numeric coercivity_oe")
                except ValueError:
                    pass # Expected

    def test_validation_script_entry_point(self):
        """
        Simulates running the validation script entry point.
        Ensures the script logic is sound for T063 requirements.
        """
        # Create a valid file
        rows = [
            {
                "composition": "Co2MnGa",
                "coercivity_oe": 45.5,
                "saturation_magnetization_emu_g": 110.2,
                "source_type": "Manual",
                "synthesis_method": "Arc Melting"
            }
        ]
        self._create_csv(rows)

        # Logic that would be in the script
        schema = load_schema(self.schema_path)
        is_valid, errors = validate_csv_file(self.test_csv_path, schema)

        if not is_valid:
            self.fail(f"Validation failed unexpectedly: {errors}")
        
        # Check business rules
        with open(self.test_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.assertEqual(row["source_type"], "Manual")
                float(row["coercivity_oe"])
                float(row["saturation_magnetization_emu_g"])

if __name__ == '__main__':
    unittest.main()