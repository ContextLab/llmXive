"""
Unit tests for the validate_report module (T026).
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.validate_report import (
    load_report,
    parse_annotated_bits,
    validate_report_structure,
    validate_sorting,
    save_validation_result
)

@pytest.fixture
def temp_report_file():
    """Create a temporary markdown file with fake report content."""
    content = """
    # Feature Importance Report

    ## Top Annotated Bits

    ### Bit 101: Methyl group
    Score: 0.45

    ### Bit 202: Ethyl group
    Score: 0.42

    ### Bit 303: Phenyl ring
    Score: 0.38

    ### Bit 404: Hydroxyl group
    Score: 0.35

    ### Bit 505: Carboxyl group
    Score: 0.30

    ### Bit 606: Amino group
    Score: 0.28

    ### Bit 707: Chlorine atom
    Score: 0.25

    ### Bit 808: Bromine atom
    Score: 0.22

    ### Bit 909: Nitro group
    Score: 0.20

    ### Bit 1010: Sulfate group
    Score: 0.18

    ### Bit 1111: Fluorine atom
    Score: 0.16

    ### Bit 1212: Iodine atom
    Score: 0.15

    ### Bit 1313: Carbonyl group
    Score: 0.14

    ### Bit 1414: Ether linkage
    Score: 0.13

    ### Bit 1515: Amide bond
    Score: 0.12

    ### Bit 1616: Ester bond
    Score: 0.11

    ### Bit 1717: Ketone group
    Score: 0.10

    ### Bit 1818: Aldehyde group
    Score: 0.09

    ### Bit 1919: Thiol group
    Score: 0.08

    ### Bit 2020: Nitrile group
    Score: 0.07
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        path = Path(f.name)
    yield path
    os.unlink(path)

@pytest.fixture
def temp_short_report_file():
    """Create a temporary markdown file with fewer than 20 bits."""
    content = """
    # Feature Importance Report

    ### Bit 101: Methyl group
    Score: 0.45

    ### Bit 202: Ethyl group
    Score: 0.42

    ### Bit 303: Phenyl ring
    Score: 0.38
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        path = Path(f.name)
    yield path
    os.unlink(path)

def test_load_report_success(temp_report_file):
    content = load_report(temp_report_file)
    assert "Feature Importance Report" in content
    assert "Bit 101" in content

def test_load_report_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_report(Path("/nonexistent/path/report.md"))

def test_parse_annotated_bits(temp_report_file):
    content = load_report(temp_report_file)
    bits = parse_annotated_bits(content)
    assert len(bits) == 20
    # Check if they are distinct
    assert len(set(bits)) == 20
    # Check if the first one is 101
    assert bits[0] == 101

def test_parse_annotated_bits_short_report(temp_short_report_file):
    content = load_report(temp_short_report_file)
    bits = parse_annotated_bits(content)
    assert len(bits) == 3

def test_validate_sorting():
    # The function currently just checks length > 0
    assert validate_sorting([1, 2, 3]) is True
    assert validate_sorting([]) is False

def test_validate_report_structure_pass(temp_report_file):
    content = load_report(temp_report_file)
    result = validate_report_structure(content)
    assert result["status"] == "pass"
    assert result["bit_count"] == 20
    assert result["minimum_required"] == 20
    assert "Requirement met" in result["message"]

def test_validate_report_structure_fail(temp_short_report_file):
    content = load_report(temp_short_report_file)
    result = validate_report_structure(content)
    assert result["status"] == "fail"
    assert result["bit_count"] == 3
    assert "Requirement not met" in result["message"]

def test_save_validation_result(tmp_path):
    result = {
        "status": "pass",
        "bit_count": 25,
        "minimum_required": 20,
        "is_sorted": True,
        "has_header": True,
        "message": "Test message"
    }
    output_path = tmp_path / "test_check.json"
    save_validation_result(result, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data["status"] == "pass"
    assert saved_data["bit_count"] == 25