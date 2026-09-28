"""
Unit tests for reference_validator.py
"""
import pytest
import os
import json
import tempfile
from pathlib import Path

# Import the module under test
# Assuming the test is run from the project root or code is in PYTHONPATH
from code.reference_validator import (
    normalize_text,
    calculate_title_overlap,
    validate_reference,
    validate_references_list,
    load_references_from_file,
    save_validation_report
)

class TestNormalizeText:
    def test_lower_case(self):
        assert normalize_text("Hello World") == "hello world"

    def test_remove_punctuation(self):
        assert normalize_text("Hello, World!") == "hello world"

    def test_collapse_whitespace(self):
        assert normalize_text("Hello   World") == "hello world"

    def test_combined(self):
        assert normalize_text("Hello,   World!") == "hello world"

    def test_empty(self):
        assert normalize_text("") == ""

class TestCalculateTitleOverlap:
    def test_identical(self):
        assert calculate_title_overlap("A B C", "A B C") == 1.0

    def test_partial_overlap(self):
        # {A, B, C} vs {C, D, E} -> intersection {C}, union {A, B, C, D, E} -> 1/5 = 0.2
        assert calculate_title_overlap("A B C", "C D E") == 0.2

    def test_no_overlap(self):
        assert calculate_title_overlap("A B", "C D") == 0.0

    def test_case_insensitive(self):
        assert calculate_title_overlap("A B C", "a b c") == 1.0

    def test_empty_strings(self):
        assert calculate_title_overlap("", "") == 0.0

    def test_one_empty(self):
        assert calculate_title_overlap("A B", "") == 0.0

class TestValidateReference:
    def test_valid_with_high_overlap(self):
        ref = {'doi': '10.1234/test', 'title': 'A B C D E'}
        source = {'title': 'A B C D E'}
        res = validate_reference(ref, source)
        assert res['valid'] is True
        assert res['overlap_score'] == 1.0

    def test_invalid_with_low_overlap(self):
        ref = {'doi': '10.1234/test', 'title': 'A B C'}
        source = {'title': 'X Y Z'}
        res = validate_reference(ref, source)
        assert res['valid'] is False
        assert res['overlap_score'] == 0.0
        assert "Title overlap" in res['errors'][0]

    def test_missing_doi(self):
        ref = {'title': 'A B C'}
        res = validate_reference(ref)
        assert res['valid'] is False
        assert "Missing DOI" in res['errors']

    def test_no_source_metadata(self):
        ref = {'doi': '10.1234/test', 'title': 'A B C'}
        res = validate_reference(ref, source_metadata=None)
        assert res['valid'] is True # Assumed valid if no check possible

class TestValidateReferencesList:
    def test_mixed_validity(self):
        refs = [
            {'doi': '1', 'title': 'A B C'},
            {'doi': '2', 'title': 'X Y Z'}
        ]
        source = {'title': 'A B C'}
        report = validate_references_list(refs, source)
        assert report['total'] == 2
        assert report['valid'] == 1
        assert report['invalid'] == 1

class TestLoadReferencesFromFile:
    def test_load_valid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{'doi': '1', 'title': 'Test'}], f)
            temp_path = f.name

        try:
            refs = load_references_from_file(temp_path)
            assert len(refs) == 1
            assert refs[0]['doi'] == '1'
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        refs = load_references_from_file("nonexistent_file.json")
        assert refs == []

class TestSaveValidationReport:
    def test_save_report(self):
        report = {'total': 1, 'valid': 1, 'invalid': 0, 'details': []}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        os.unlink(temp_path) # Remove the empty file, we want save to create it

        try:
            save_validation_report(report, temp_path)
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == report
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)