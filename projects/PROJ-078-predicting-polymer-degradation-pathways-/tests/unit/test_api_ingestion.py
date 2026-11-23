"""
Unit tests for API ingestion logic.
"""
import pytest
from ingest import filter_records_with_degradation_labels
from data_models import PolymerRecord

def test_filter_degradation_labels_valid(sample_polymer_record_dict):
    """Test filtering of records with valid degradation labels."""
    record = PolymerRecord(**sample_polymer_record_dict)
    filtered = filter_records_with_degradation_labels([record])
    assert len(filtered) == 1

def test_filter_degradation_labels_missing_label(sample_polymer_record_missing_label):
    """Test filtering of records with missing degradation labels."""
    record = PolymerRecord(**sample_polymer_record_missing_label)
    filtered = filter_records_with_degradation_labels([record])
    assert len(filtered) == 0
