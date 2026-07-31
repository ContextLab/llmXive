"""
Tests for T003: validate_phase0.py
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from research.validate_phase0 import (
    load_json_file,
    read_text_file,
    validate_power_calculation_json,
    validate_citations_json,
    validate_research_md,
    main
)

def test_validate_power_calculation_json_valid():
    data = {
        'effect_size': 0.25,
        'alpha': 0.05,
        'target_power': 0.80,
        'required_n': 128,
        'calculated_n': 128,
        'test_type': 'anova'
    }
    # Should not raise
    validate_power_calculation_json(data)

def test_validate_power_calculation_json_missing_key():
    data = {
        'effect_size': 0.25,
        'alpha': 0.05,
        # missing 'target_power'
    }
    with pytest.raises(ValueError, match="missing required keys"):
        validate_power_calculation_json(data)

def test_validate_power_calculation_json_invalid_n():
    data = {
        'effect_size': 0.25,
        'alpha': 0.05,
        'target_power': 0.80,
        'required_n': -10,
        'calculated_n': 128,
        'test_type': 'anova'
    }
    with pytest.raises(ValueError, match="positive number"):
        validate_power_calculation_json(data)

def test_validate_citations_json_valid():
    data = {
        'citations': [
            {'title': 'Test', 'status': 'valid', 'overlap': 0.8},
            {'title': 'Test2', 'status': 'valid', 'overlap': 0.7}
        ]
    }
    validate_citations_json(data)

def test_validate_citations_json_invalid_status():
    data = {
        'citations': [
            {'title': 'Test', 'status': 'invalid', 'overlap': 0.8}
        ]
    }
    with pytest.raises(ValueError, match="status=invalid"):
        validate_citations_json(data)

def test_validate_citations_json_low_overlap():
    data = {
        'citations': [
            {'title': 'Test', 'status': 'valid', 'overlap': 0.6}
        ]
    }
    with pytest.raises(ValueError, match="overlap too low"):
        validate_citations_json(data)

def test_validate_research_md_valid(tmp_path):
    power_json = {
        'effect_size': 0.25,
        'alpha': 0.05,
        'target_power': 0.80,
        'required_n': 128,
        'calculated_n': 128,
        'test_type': 'anova'
    }
    
    content = """
    # Research Plan

    | Effect Size | Alpha | Target Power | Required N | Calculated N |
    | --- | --- | --- | --- | --- |
    | 0.25 | 0.05 | 0.80 | 128 | 128 |
    """
    # Should not raise
    validate_research_md(content, power_json)

def test_validate_research_md_missing_header():
    power_json = {
        'effect_size': 0.25,
        'alpha': 0.05,
        'target_power': 0.80,
        'required_n': 128,
        'calculated_n': 128,
        'test_type': 'anova'
    }
    
    content = """
    # Research Plan

    | Effect Size | Alpha | Target Power | Required N |
    | --- | --- | --- | --- |
    | 0.25 | 0.05 | 0.80 | 128 |
    """
    with pytest.raises(ValueError, match="missing required column header"):
        validate_research_md(content, power_json)

def test_validate_research_md_value_mismatch():
    power_json = {
        'effect_size': 0.25,
        'alpha': 0.05,
        'target_power': 0.80,
        'required_n': 128,
        'calculated_n': 128,
        'test_type': 'anova'
    }
    
    content = """
    # Research Plan

    | Effect Size | Alpha | Target Power | Required N | Calculated N |
    | --- | --- | --- | --- | --- |
    | 0.50 | 0.05 | 0.80 | 128 | 128 |
    """
    with pytest.raises(ValueError, match="Effect Size mismatch"):
        validate_research_md(content, power_json)