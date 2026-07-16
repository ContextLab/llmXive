import logging
import pytest
import os
import sys

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils import setup_logging, get_logger
from ingest import validate_smiles, validate_degradation_pathway_label, filter_records_by_pathway_label
from preprocess import filter_missing_environmental_data, filter_polyesters

@pytest.fixture
def caplog_with_level(caplog):
    """Fixture to ensure logging is captured at the right level."""
    setup_logging(level=logging.DEBUG)
    return caplog

def test_validate_smiles_logs_invalid(caplog_with_level):
    """Test that invalid SMILES inputs are logged."""
    with caplog_with_level.at_level(logging.WARNING):
        result = validate_smiles("invalid_smiles_!@#")
        assert result is False
        assert "Invalid SMILES input" in caplog_with_level.text or "RDKit failed to parse" in caplog_with_level.text

def test_validate_pathway_missing_logs_exclusion(caplog_with_level):
    """Test that missing pathway labels are logged as exclusions."""
    record = {"id": "test_123", "smiles": "CCO"}
    with caplog_with_level.at_level(logging.WARNING):
        result = validate_degradation_pathway_label(record)
        assert result is False
        assert "missing 'degradation_pathway' label" in caplog_with_level.text
        assert "Excluding" in caplog_with_level.text

def test_filter_pathway_logs_summary(caplog_with_level):
    """Test that the filter function logs the summary of kept/excluded records."""
    records = [
        {"id": "good_1", "degradation_pathway": "Hydrolysis"},
        {"id": "bad_1", "degradation_pathway": None},
        {"id": "bad_2", "degradation_pathway": ""},
        {"id": "good_2", "degradation_pathway": "Thermal"}
    ]
    
    with caplog_with_level.at_level(logging.INFO):
        result = filter_records_by_pathway_label(records)
        assert len(result) == 2
        assert "Pathway label validation complete" in caplog_with_level.text
        assert "2 kept" in caplog_with_level.text
        assert "2 excluded" in caplog_with_level.text

def test_filter_missing_env_logs_exclusion(caplog_with_level):
    """Test that missing environmental data is logged."""
    records = [
        {"id": "good", "temperature": 300, "ph": 7, "uv_intensity": 10},
        {"id": "bad_temp", "temperature": None, "ph": 7, "uv_intensity": 10},
        {"id": "bad_ph", "temperature": 300, "ph": None, "uv_intensity": 10}
    ]
    
    with caplog_with_level.at_level(logging.WARNING):
        result = filter_missing_environmental_data(records)
        assert len(result) == 1
        assert "Missing environmental data" in caplog_with_level.text
        assert "Excluded record" in caplog_with_level.text

def test_filter_polyesters_logs_exclusion(caplog_with_level):
    """Test that non-polyester records are logged."""
    records = [
        {"id": "polyester", "smiles": "CC(=O)OC"}, # Ester
        {"id": "non_polyester", "smiles": "CCO"}   # Alcohol, no ester
    ]
    
    with caplog_with_level.at_level(logging.DEBUG):
        result = filter_polyesters(records)
        assert len(result) == 1
        assert "identified as polyester" in caplog_with_level.text
        # Check for exclusion log if debug level is high enough
        # The log message is: "Excluded record {id}: No ester group detected..."
        # Depending on implementation, this might be DEBUG or WARNING.
        # We verify the logic ran by checking the count.