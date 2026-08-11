"""
Unit tests for PMD Utility Module.
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.pmd_utils import (
    parse_pmd_xml_output,
    aggregate_metrics_by_sample,
    SMELL_TYPE_MAPPING,
    _parse_violation_element
)
from utils.data_models import SmellMetric


def test_parse_empty_xml():
    """Test parsing empty XML string."""
    result = parse_pmd_xml_output("")
    assert result == []


def test_parse_valid_pmd_xml():
    """Test parsing a valid PMD XML output."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <pmd>
        <file name="test.py">
            <violation ruleset="Design" rule="LongMethod" priority="1" beginline="10" endline="50">
                Method is too long
            </violation>
        </file>
    </pmd>
    """
    metrics = parse_pmd_xml_output(xml_content)
    assert len(metrics) == 1
    assert metrics[0].smell_type == "Long Method"
    assert metrics[0].file_path == "test.py"
    assert metrics[0].line_start == 10
    assert metrics[0].description == "Method is too long"


def test_parse_multiple_violations():
    """Test parsing XML with multiple violations."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <pmd>
        <file name="test.py">
            <violation ruleset="Design" rule="LongMethod" priority="1" beginline="10">
                Long method
            </violation>
            <violation ruleset="Design" rule="DuplicatedCode" priority="2" beginline="20">
                Duplicate code
            </violation>
        </file>
    </pmd>
    """
    metrics = parse_pmd_xml_output(xml_content)
    assert len(metrics) == 2
    types = [m.smell_type for m in metrics]
    assert "Long Method" in types
    assert "Duplicated Code" in types


def test_aggregate_metrics():
    """Test aggregating metrics for a sample."""
    metrics = [
        SmellMetric(
            sample_id="sample_1",
            smell_type="Long Method",
            count=1,
            threshold_used=0,
            continuous_metric_value=1.0,
            file_path="test.py"
        ),
        SmellMetric(
            sample_id="sample_1",
            smell_type="Long Method",
            count=1,
            threshold_used=0,
            continuous_metric_value=1.0,
            file_path="test.py"
        ),
        SmellMetric(
            sample_id="sample_1",
            smell_type="Duplicated Code",
            count=1,
            threshold_used=0,
            continuous_metric_value=1.0,
            file_path="test.py"
        )
    ]
    
    aggregated = aggregate_metrics_by_sample(metrics, "sample_1")
    
    assert len(aggregated) == 2
    # One should be Long Method with count 2
    long_method = next((m for m in aggregated if m.smell_type == "Long Method"), None)
    assert long_method is not None
    assert long_method.count == 2
    
    dup_code = next((m for m in aggregated if m.smell_type == "Duplicated Code"), None)
    assert dup_code is not None
    assert dup_code.count == 1


def test_mapping_constants():
    """Test that smell type mapping constants are defined."""
    assert "LongMethod" in SMELL_TYPE_MAPPING
    assert SMELL_TYPE_MAPPING["LongMethod"] == "Long Method"
    assert "DuplicatedCode" in SMELL_TYPE_MAPPING
    assert SMELL_TYPE_MAPPING["DuplicatedCode"] == "Duplicated Code"
