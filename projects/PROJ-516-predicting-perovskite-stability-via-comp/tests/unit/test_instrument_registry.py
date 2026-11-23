"""
Unit tests for the instrument_registry module.
"""

import os
import tempfile
import logging
from pathlib import Path
import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.instrument_registry import (
    get_precision,
    reload_registry,
    get_registry_details,
    generate_missing_instrumentation_report,
    DEFAULT_PRECISION
)

logging.basicConfig(level=logging.WARNING)


@pytest.fixture
def temp_registry_csv(tmp_path):
    """Create a temporary CSV registry file for testing."""
    csv_content = """instrument_model,manufacturer,precision_celsius
    Q50,TA Instruments,1.0
    TGA/DSC 1,Mettler Toledo,2.5
    Pyris 1 TGA,PerkinElmer,1.5
    """
    csv_file = tmp_path / "test_registry.csv"
    csv_file.write_text(csv_content)
    return csv_file


def test_get_precision_known_instrument(temp_registry_csv):
    """Test lookup of a known instrument model."""
    # Temporarily override the global registry path for testing
    import utils.instrument_registry as reg_module
    original_path = reg_module.REGISTRY_FILE
    reg_module.REGISTRY_FILE = temp_registry_path = temp_registry_csv

    try:
        reload_registry()
        precision = get_precision("Q50")
        assert precision == 1.0, f"Expected 1.0, got {precision}"
    finally:
        reg_module.REGISTRY_FILE = original_path
        reload_registry()  # Reset


def test_get_precision_unknown_instrument(temp_registry_csv):
    """Test lookup of an unknown instrument model falls back to default."""
    import utils.instrument_registry as reg_module
    original_path = reg_module.REGISTRY_FILE
    reg_module.REGISTRY_FILE = temp_registry_path = temp_registry_csv

    try:
        reload_registry()
        precision = get_precision("Unknown Model XYZ")
        assert precision == DEFAULT_PRECISION, f"Expected {DEFAULT_PRECISION}, got {precision}"
    finally:
        reg_module.REGISTRY_FILE = original_path
        reload_registry()


def test_get_precision_case_insensitive(temp_registry_csv):
    """Test that lookup is case-insensitive."""
    import utils.instrument_registry as reg_module
    original_path = reg_module.REGISTRY_FILE
    reg_module.REGISTRY_FILE = temp_registry_path = temp_registry_csv

    try:
        reload_registry()
        precision_upper = get_precision("Q50")
        precision_lower = get_precision("q50")
        precision_mixed = get_precision("Q50")
        assert precision_upper == precision_lower == precision_mixed == 1.0
    finally:
        reg_module.REGISTRY_FILE = original_path
        reload_registry()


def test_get_precision_empty_string(temp_registry_csv):
    """Test that empty string returns default precision."""
    import utils.instrument_registry as reg_module
    original_path = reg_module.REGISTRY_FILE
    reg_module.REGISTRY_FILE = temp_registry_path = temp_registry_csv

    try:
        reload_registry()
        precision = get_precision("")
        assert precision == DEFAULT_PRECISION
    finally:
        reg_module.REGISTRY_FILE = original_path
        reload_registry()


def test_get_precision_missing_file():
    """Test behavior when registry file is missing."""
    import utils.instrument_registry as reg_module
    original_path = reg_module.REGISTRY_FILE
    non_existent = Path("/non/existent/path.csv")
    reg_module.REGISTRY_FILE = non_existent

    try:
        reload_registry()
        precision = get_precision("Any Model")
        assert precision == DEFAULT_PRECISION
    finally:
        reg_module.REGISTRY_FILE = original_path
        reload_registry()


def test_get_registry_details(temp_registry_csv):
    """Test that registry details are populated correctly."""
    import utils.instrument_registry as reg_module
    original_path = reg_module.REGISTRY_FILE
    reg_module.REGISTRY_FILE = temp_registry_path = temp_registry_csv

    try:
        reload_registry()
        details = get_registry_details()
        assert len(details) == 3
        assert details[0]['instrument_model'] == 'Q50'
        assert details[0]['precision_celsius'] == 1.0
    finally:
        reg_module.REGISTRY_FILE = original_path
        reload_registry()