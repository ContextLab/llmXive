"""
Unit tests for the Mock Data Generator (T015b).

Verifies that:
1. The mock data file is generated at the correct path.
2. The JSON structure matches the expected schema.
3. The specific records (valid, no-abstract, invalid-age) are present.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the generator function
# Adjust import path based on project structure
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.mock_data_generator import generate_mock_data, PROJECT_ROOT, DATA_RAW_DIR, OUTPUT_FILE


class TestMockDataGenerator:
    """Tests for the mock data generation logic."""

    def test_file_generation(self):
        """Test that the mock data file is created."""
        # Ensure the file doesn't exist before running
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink()

        # Run the generator
        result_path = generate_mock_data()

        # Verify the file exists
        assert result_path.exists(), f"Mock data file was not created at {result_path}"
        assert result_path == OUTPUT_FILE

    def test_json_structure(self):
        """Test that the generated JSON has the correct top-level structure."""
        # Regenerate to ensure fresh data
        generate_mock_data()

        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert "total_count" in data
        assert "studies" in data
        assert "generated_at" in data
        assert "source" in data
        assert data["total_count"] == 3
        assert len(data["studies"]) == 3

    def test_record_1_valid_study(self):
        """Test Record 1: Valid study (age 8, ASD, social outcome, abstract present)."""
        generate_mock_data()

        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        record = data["studies"][0]

        # Verify ID
        assert record["id"] == "NCT00000001"

        # Verify Age Range (Valid: 6-12)
        assert record["age_range"]["min"] == 8
        assert record["age_range"]["max"] == 10

        # Verify Diagnosis
        assert record["diagnosis"] == "ASD"

        # Verify Outcomes (Social)
        assert "Social Responsiveness Scale (SRS)" in record["outcomes"]

        # Verify Abstract Present
        assert record["abstract"] is not None
        assert "text" in record["abstract"]
        assert len(record["abstract"]["text"]) > 0

    def test_record_2_no_abstract(self):
        """Test Record 2: Valid study, NO abstract (Triggers T020 exclusion logic)."""
        generate_mock_data()

        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        record = data["studies"][1]

        # Verify ID
        assert record["id"] == "NCT00000002"

        # Verify Age Range (Valid: 6-12)
        assert record["age_range"]["min"] == 9
        assert record["age_range"]["max"] == 12

        # Verify Diagnosis
        assert record["diagnosis"] == "ASD"

        # Verify Outcomes (Social)
        assert "ABC Irritability Subscale" in record["outcomes"]

        # Verify Abstract MISSING (None)
        assert record["abstract"] is None

    def test_record_3_invalid_age(self):
        """Test Record 3: Invalid study (age 15, out of 6-12 range)."""
        generate_mock_data()

        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        record = data["studies"][2]

        # Verify ID
        assert record["id"] == "NCT00000003"

        # Verify Age Range (Invalid: > 12)
        assert record["age_range"]["min"] == 15
        assert record["age_range"]["max"] == 17

        # Verify Diagnosis
        assert record["diagnosis"] == "ASD"

    def test_schema_compliance(self):
        """Test that all records contain the required fields for schema validation."""
        generate_mock_data()

        required_fields = [
            "id", "title", "registry", "age_range", "diagnosis", "outcomes",
            "abstract", "intervention_components", "delivery_format",
            "social_skill_domain", "follow_up", "rater_type", "blinded_assessment_flag"
        ]

        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for i, record in enumerate(data["studies"]):
            for field in required_fields:
                assert field in record, f"Record {i} is missing required field: {field}"
                
                # Type checks for specific fields
                if field == "age_range":
                    assert "min" in record[field]
                    assert "max" in record[field]
                    assert isinstance(record[field]["min"], int)
                    assert isinstance(record[field]["max"], int)
                elif field == "outcomes":
                    assert isinstance(record[field], list)
                elif field == "abstract":
                    # Can be null or dict
                    assert record[field] is None or isinstance(record[field], dict)
                elif field == "blinded_assessment_flag":
                    assert isinstance(record[field], bool)
                elif field == "rater_type":
                    assert record[field] in ["blinded", "unblinded", "mixed"]
                elif field == "delivery_format":
                    assert record[field] in ["caregiver-mediated", "child-led", "mixed", "not-reported"]