"""
Unit tests for the ingestion scaffolding.
"""
import pytest
import os
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion.aggregator import LiteratureAggregator
from ingestion.cleaner import DataCleaner
from ingestion.validator import DataValidator
from ingestion.citation_tracker import CitationTracker, get_tracker, reset_tracker


def test_literature_aggregator_init():
    """Test that LiteratureAggregator initializes correctly."""
    aggregator = LiteratureAggregator()
    assert aggregator is not None
    assert "openalloy" in aggregator.sources
    assert "literature_csv" in aggregator.sources


def test_citation_tracker_singleton():
    """Test that CitationTracker returns a singleton."""
    tracker1 = get_tracker()
    tracker2 = get_tracker()
    assert tracker1 is tracker2
    reset_tracker()
    tracker3 = get_tracker()
    assert tracker1 is not tracker3


def test_citation_tracker_add():
    """Test adding a citation."""
    reset_tracker()
    tracker = get_tracker()
    tracker.add_citation("Test Source", "http://example.com", "Test Description")
    citations = tracker.get_citations()
    assert len(citations) == 1
    assert citations[0]["source"] == "Test Source"