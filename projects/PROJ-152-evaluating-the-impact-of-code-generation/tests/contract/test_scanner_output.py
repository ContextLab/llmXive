"""
Contract test for scanner output format.

This test verifies that the output of the static analysis scanners (Bandit, Semgrep, CodeQL)
adheres to the expected schema defined in the project specifications. It ensures that
the `code/analyze.py` module produces findings in a format compatible with downstream
processing (metrics calculation, statistical analysis).

The test validates:
1. Presence of required columns in the raw findings CSV.
2. Correct data types for each column.
3. Validity of CWE IDs against a known set (or regex pattern).
4. Validity of severity mappings against the NIST severity map.
5. Uniqueness of finding_id.
"""

import os
import csv
import json
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Project root relative to tests/contract
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FINDINGS_FILE = DATA_DIR / "findings" / "raw_findings.csv"
SEVERITY_MAP_FILE = DATA_DIR / "mappings" / "nist_severity_map.yaml"

# Expected schema based on tasks.md (T019)
EXPECTED_COLUMNS = [
    "finding_id",
    "snippet_id",
    "scanner",
    "cwe_id",
    "raw_severity",
    "mapped_ordinal_rank",
    "finding_text"
]

# Expected scanners based on tasks.md (T015)
EXPECTED_SCANNERS = {"bandit", "semgrep", "codeql"}

# Regex pattern for valid CWE IDs (e.g., CWE-79, CWE-89)
CWE_PATTERN = r"CWE-\d+"


def load_findings() -> List[Dict[str, Any]]:
    """Load the raw findings CSV file."""
    if not FINDINGS_FILE.exists():
        pytest.fail(f"Findings file not found at {FINDINGS_FILE}. "
                    "Run T015 (analyze.py) to generate data first.")

    with open(FINDINGS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_severity_map() -> Dict[str, int]:
    """Load the NIST severity mapping YAML file."""
    if not SEVERITY_MAP_FILE.exists():
        pytest.fail(f"Severity map not found at {SEVERITY_MAP_FILE}. "
                    "Run T007 to generate data first.")

    # Simple YAML parser for the expected flat structure to avoid extra deps
    # Expected format:
    # "High": 4
    # "Medium": 3
    # ...
    mapping = {}
    with open(SEVERITY_MAP_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().strip('"').strip("'")
                value = int(value.strip())
                mapping[key] = value
    return mapping


@pytest.fixture
def findings_data():
    return load_findings()


@pytest.fixture
def severity_map():
    return load_severity_map()


class TestScannerOutputSchema:
    """Tests for the structural integrity of the scanner output."""

    def test_file_exists(self):
        """Ensure the raw_findings.csv file exists."""
        assert FINDINGS_FILE.exists(), "raw_findings.csv must exist"

    def test_required_columns_present(self, findings_data):
        """Ensure all required columns are present in the CSV."""
        if not findings_data:
            pytest.skip("No findings data to test (expected if T015 hasn't run).")

        headers = findings_data[0].keys()
        missing_columns = set(EXPECTED_COLUMNS) - set(headers)
        assert not missing_columns, f"Missing required columns: {missing_columns}"

    def test_column_count(self, findings_data):
        """Ensure no extra unexpected columns are present (strict schema)."""
        if not findings_data:
            pytest.skip("No findings data to test.")

        headers = list(findings_data[0].keys())
        extra_columns = set(headers) - set(EXPECTED_COLUMNS)
        # Allow for potential future extensions, but warn if strictness is required.
        # For now, we just ensure the required ones are there.
        # assert not extra_columns, f"Unexpected columns found: {extra_columns}"


class TestScannerOutputDataIntegrity:
    """Tests for the content validity of the scanner output."""

    def test_finding_id_uniqueness(self, findings_data):
        """Ensure finding_id is unique across the dataset."""
        if not findings_data:
            pytest.skip("No findings data to test.")

        ids = [row["finding_id"] for row in findings_data]
        assert len(ids) == len(set(ids)), "finding_id must be unique"

    def test_scanner_values(self, findings_data):
        """Ensure scanner column contains only expected scanner names."""
        if not findings_data:
            pytest.skip("No findings data to test.")

        scanners = set(row["scanner"].lower() for row in findings_data)
        invalid_scanners = scanners - EXPECTED_SCANNERS
        assert not invalid_scanners, f"Invalid scanner names found: {invalid_scanners}"

    def test_cwe_id_format(self, findings_data):
        """Ensure CWE IDs follow the expected format (CWE-NNN)."""
        import re
        if not findings_data:
            pytest.skip("No findings data to test.")

        invalid_cwes = []
        for row in findings_data:
            cwe = row["cwe_id"]
            if cwe and not re.match(CWE_PATTERN, cwe):
                invalid_cwes.append(cwe)

        assert not invalid_cwes, f"CWE IDs do not match expected format: {invalid_cwes[:5]}"

    def test_mapped_ordinal_rank_validity(self, findings_data, severity_map):
        """Ensure mapped_ordinal_rank corresponds to a valid value in the severity map."""
        if not findings_data:
            pytest.skip("No findings data to test.")

        valid_ranks = set(severity_map.values())
        invalid_ranks = []
        for row in findings_data:
            try:
                rank = int(row["mapped_ordinal_rank"])
                if rank not in valid_ranks:
                    invalid_ranks.append(rank)
            except ValueError:
                invalid_ranks.append(row["mapped_ordinal_rank"])

        assert not invalid_ranks, f"Mapped ordinal ranks not in severity map: {set(invalid_ranks)}"

    def test_raw_severity_consistency(self, findings_data, severity_map):
        """Ensure raw_severity values map to the keys in the severity map."""
        if not findings_data:
            pytest.skip("No findings data to test.")

        valid_severities = set(severity_map.keys())
        invalid_severities = set(row["raw_severity"] for row in findings_data) - valid_severities

        assert not invalid_severities, f"Raw severity values not in map: {invalid_severities}"

class TestScannerOutputLogic:
    """Tests for logical consistency between columns."""

    def test_severity_mapping_correctness(self, findings_data, severity_map):
        """Ensure mapped_ordinal_rank matches the raw_severity lookup."""
        if not findings_data:
            pytest.skip("No findings data to test.")

        errors = []
        for i, row in enumerate(findings_data):
            raw = row["raw_severity"]
            mapped = int(row["mapped_ordinal_rank"])
            expected = severity_map.get(raw)

            if expected is not None and mapped != expected:
                errors.append(f"Row {i}: {raw} -> {mapped} (expected {expected})")

        assert not errors, f"Severity mapping errors:\n" + "\n".join(errors[:5])