"""
Contract test for T085: Validate lmm_summary.schema.yaml against LMM output files.

This test validates that both the Wald-Z and Satterthwaite LMM summary CSV files
conform to the lmm_summary.schema.yaml specification.
"""

import csv
import json
import os
import sys
from pathlib import Path

import pytest
import yaml

# Add project root to path for imports if running from tests directory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_results_dir, get_contracts_dir
from validate_schemas import load_schema, validate_csv_against_schema


@pytest.fixture
def schema_path():
    """Path to the LMM summary schema."""
    contracts_dir = get_contracts_dir()
    return contracts_dir / "lmm_summary.schema.yaml"


@pytest.fixture
def wald_results_path():
    """Path to the Wald-Z LMM summary CSV."""
    results_dir = get_results_dir()
    return results_dir / "lmm_summary_wald.csv"


@pytest.fixture
def satterthwaite_results_path():
    """Path to the Satterthwaite LMM summary CSV."""
    results_dir = get_results_dir()
    return results_dir / "lmm_summary_satterthwaite.csv"


@pytest.fixture
def schema(schema_path):
    """Load the LMM summary schema."""
    return load_schema(schema_path)


def test_schema_exists(schema_path):
    """Verify that the schema file exists."""
    assert schema_path.exists(), f"Schema file not found: {schema_path}"


def test_wald_results_exist(wald_results_path):
    """Verify that the Wald-Z results file exists."""
    assert wald_results_path.exists(), (
        f"Wald-Z results file not found: {wald_results_path}. "
        "Ensure code/04_fit_lmm.py has been executed."
    )


def test_satterthwaite_results_exist(satterthwaite_results_path):
    """Verify that the Satterthwaite results file exists."""
    assert satterthwaite_results_path.exists(), (
        f"Satterthwaite results file not found: {satterthwaite_results_path}. "
        "Ensure code/04_fit_lmm_satterthwaite.py has been executed."
    )


def test_wald_results_against_schema(schema, wald_results_path):
    """Validate Wald-Z results CSV against the LMM summary schema."""
    is_valid, errors = validate_csv_against_schema(wald_results_path, schema)
    
    if not is_valid:
        error_msg = "\n".join([f"  - {err}" for err in errors])
        pytest.fail(f"Wald-Z results failed schema validation:\n{error_msg}")


def test_satterthwaite_results_against_schema(schema, satterthwaite_results_path):
    """Validate Satterthwaite results CSV against the LMM summary schema."""
    is_valid, errors = validate_csv_against_schema(satterthwaite_results_path, schema)
    
    if not is_valid:
        error_msg = "\n".join([f"  - {err}" for err in errors])
        pytest.fail(f"Satterthwaite results failed schema validation:\n{error_msg}")


def test_wald_results_contains_required_columns(wald_results_path, schema):
    """Verify Wald-Z results contain all required columns from schema."""
    if not wald_results_path.exists():
        pytest.skip("Wald-Z results file does not exist yet")

    with open(wald_results_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    required_columns = schema.get("required_columns", [])
    missing_columns = [col for col in required_columns if col not in headers]

    assert not missing_columns, (
        f"Wald-Z results missing required columns: {missing_columns}. "
        f"Required: {required_columns}"
    )


def test_satterthwaite_results_contains_required_columns(satterthwaite_results_path, schema):
    """Verify Satterthwaite results contain all required columns from schema."""
    if not satterthwaite_results_path.exists():
        pytest.skip("Satterthwaite results file does not exist yet")

    with open(satterthwaite_results_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    required_columns = schema.get("required_columns", [])
    missing_columns = [col for col in required_columns if col not in headers]

    assert not missing_columns, (
        f"Satterthwaite results missing required columns: {missing_columns}. "
        f"Required: {required_columns}"
    )


def test_satterthwaite_results_contains_df_column(satterthwaite_results_path):
    """Verify Satterthwaite results contain the df_Satterthwaite column."""
    if not satterthwaite_results_path.exists():
        pytest.skip("Satterthwaite results file does not exist yet")

    with open(satterthwaite_results_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    assert "df_Satterthwaite" in headers, (
        "Satterthwaite results must contain 'df_Satterthwaite' column. "
        f"Found columns: {headers}"
    )