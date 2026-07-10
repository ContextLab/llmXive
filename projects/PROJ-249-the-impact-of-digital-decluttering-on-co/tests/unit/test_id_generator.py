"""
Unit tests for the Pseudonymous ID Generator (T006).

Validates:
- ID format adherence (P\d{3})
- Sequence generation correctness
- CSV loading and validation
- Uniqueness and availability logic
"""
import pytest
import os
import csv
import tempfile
from pathlib import Path

from scoring.id_generator import (
    validate_id_format,
    parse_id_suffix,
    generate_sequence_ids,
    load_ids_from_csv,
    get_next_available_id,
    IDGenerator,
    ID_PATTERN
)

class TestIDFormatValidation:
    def test_valid_ids(self):
        assert validate_id_format("P001") is True
        assert validate_id_format("P099") is True
        assert validate_id_format("P100") is True
        assert validate_id_format("P999") is True

    def test_invalid_ids(self):
        assert validate_id_format("P00") is False      # Too short
        assert validate_id_format("P1000") is False    # Too long
        assert validate_id_format("001") is False      # Missing P
        assert validate_id_format("A001") is False     # Wrong letter
        assert validate_id_format("P00a") is False     # Non-digit
        assert validate_id_format("") is False
        assert validate_id_format("P 001") is False    # Space

    def test_regex_pattern(self):
        # Ensure the regex matches the expected strings
        assert ID_PATTERN.match("P123")
        assert not ID_PATTERN.match("123")
        assert not ID_PATTERN.match("P12")

class TestParseSuffix:
    def test_parse_suffix(self):
        assert parse_id_suffix("P001") == 1
        assert parse_id_suffix("P099") == 99
        assert parse_id_suffix("P123") == 123
        assert parse_id_suffix("P999") == 999

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            parse_id_suffix("A001")
        with pytest.raises(ValueError):
            parse_id_suffix("P00")

class TestSequenceGeneration:
    def test_generate_basic(self):
        ids = generate_sequence_ids(start=1, count=3)
        assert ids == ["P001", "P002", "P003"]

    def test_generate_offset(self):
        ids = generate_sequence_ids(start=10, count=2)
        assert ids == ["P010", "P011"]

    def test_generate_max(self):
        ids = generate_sequence_ids(start=999, count=1)
        assert ids == ["P999"]

    def test_generate_overflow(self):
        with pytest.raises(ValueError):
            generate_sequence_ids(start=999, count=2)

    def test_generate_invalid_start(self):
        with pytest.raises(ValueError):
            generate_sequence_ids(start=0, count=1)
        with pytest.raises(ValueError):
            generate_sequence_ids(start=1000, count=1)

class TestCSVLoading:
    def test_load_valid_csv(self):
        # Create a temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['participant_id', 'name'])
            writer.writerow(['P001', 'Alice'])
            writer.writerow(['P002', 'Bob'])
            writer.writerow(['P100', 'Charlie'])
            temp_path = f.name

        try:
            ids = load_ids_from_csv(temp_path)
            assert len(ids) == 3
            assert "P001" in ids
            assert "P002" in ids
            assert "P100" in ids
        finally:
            os.unlink(temp_path)

    def test_load_csv_custom_column(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['pid', 'subject'])
            writer.writerow(['P005', 'Test'])
            temp_path = f.name

        try:
            ids = load_ids_from_csv(temp_path, id_column='pid')
            assert len(ids) == 1
            assert ids[0] == "P005"
        finally:
            os.unlink(temp_path)

    def test_load_csv_invalid_ids_skipped(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['participant_id'])
            writer.writerow(['P001'])
            writer.writerow(['INVALID']) # Should be skipped
            writer.writerow(['P002'])
            temp_path = f.name

        try:
            ids = load_ids_from_csv(temp_path)
            # Only valid ones should be returned
            assert len(ids) == 2
            assert "INVALID" not in ids
        finally:
            os.unlink(temp_path)

    def test_load_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_ids_from_csv("non_existent_file.csv")

    def test_load_csv_no_valid_ids(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['participant_id'])
            writer.writerow(['BAD'])
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_ids_from_csv(temp_path)
        finally:
            os.unlink(temp_path)

class TestNextAvailableID:
    def test_next_available_simple(self):
        existing = ["P001", "P002"]
        next_id = get_next_available_id(existing)
        assert next_id == "P003"

    def test_next_available_with_gaps(self):
        existing = ["P001", "P003"]
        next_id = get_next_available_id(existing)
        assert next_id == "P002"

    def test_next_available_start_override(self):
        existing = ["P001"]
        next_id = get_next_available_id(existing, start=5)
        assert next_id == "P005"

    def test_next_available_all_used(self):
        existing = [f"P{i:03d}" for i in range(1, 1000)]
        with pytest.raises(RuntimeError):
            get_next_available_id(existing)

class TestIDGeneratorClass:
    def test_generator_initialization(self):
        gen = IDGenerator(seed=42)
        assert gen._used_ids == set()

    def test_generator_add_existing(self):
        gen = IDGenerator()
        gen.add_existing_ids(["P001", "P002"])
        assert "P001" in gen._used_ids
        assert "P002" in gen._used_ids

    def test_generator_add_invalid(self):
        gen = IDGenerator()
        with pytest.raises(ValueError):
            gen.add_existing_ids(["INVALID"])

    def test_generator_generate_unique(self):
        gen = IDGenerator()
        ids = gen.generate(count=3)
        assert len(ids) == 3
        assert all(validate_id_format(pid) for pid in ids)
        assert len(set(ids)) == 3 # All unique

    def test_generator_generate_after_existing(self):
        gen = IDGenerator()
        gen.add_existing_ids(["P001", "P002"])
        new_id = gen.generate(count=1)[0]
        assert new_id == "P003"
        assert new_id in gen._used_ids

    def test_generator_exhaustion(self):
        gen = IDGenerator()
        # Fill up to 999
        existing = [f"P{i:03d}" for i in range(1, 1000)]
        gen.add_existing_ids(existing)
        
        with pytest.raises(RuntimeError):
            gen.generate(count=1)

    def test_generator_reset(self):
        gen = IDGenerator()
        gen.add_existing_ids(["P001"])
        gen.reset()
        assert len(gen._used_ids) == 0