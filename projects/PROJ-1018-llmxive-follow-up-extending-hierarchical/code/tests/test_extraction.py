"""
Tests for the extraction module.
"""

import pytest
import logging
import numpy as np
import os
import sys
import tempfile

# Add src to path if running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extraction import (
    validate_profiles, 
    RelevanceProfile, 
    Chunk, 
    chunk_document,
    verify_edge_case_logging
)
from src.config import Config


class TestValidation:
    """Tests for the validate_profiles function."""

    def test_validate_profiles_valid(self):
        """Test validation with valid profiles."""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[0.1, 0.2, 0.3], document_id="d1"),
            RelevanceProfile(chunk_id="c2", scores=[0.4, 0.5], document_id="d2")
        ]
        config = Config(seed=42, chunk_size=512, model_path="", k_clusters=10)
        
        result = validate_profiles(profiles, config)
        assert result is True

    def test_validate_profiles_null_scores(self):
        """Test validation fails on null scores."""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=None, document_id="d1")
        ]
        config = Config(seed=42, chunk_size=512, model_path="", k_clusters=10)
        
        with pytest.raises(ValueError, match="Validation failed"):
            validate_profiles(profiles, config)

    def test_validate_profiles_nan_scores(self):
        """Test validation fails on NaN scores."""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[0.1, np.nan, 0.3], document_id="d1")
        ]
        config = Config(seed=42, chunk_size=512, model_path="", k_clusters=10)
        
        with pytest.raises(ValueError, match="Validation failed"):
            validate_profiles(profiles, config)

    def test_validate_profiles_empty_list(self):
        """Test validation with empty list returns True."""
        profiles = []
        config = Config(seed=42, chunk_size=512, model_path="", k_clusters=10)
        
        result = validate_profiles(profiles, config)
        assert result is True


class TestChunking:
    """Tests for chunk_document function."""

    def test_chunk_document_short(self):
        """Test that short documents are skipped."""
        short_text = "This is a very short text."
        chunks = chunk_document(short_text, chunk_size=512, doc_id="short_doc")
        assert len(chunks) == 0

    def test_chunk_document_long(self):
        """Test that long documents are chunked."""
        # Create a text long enough to be > 2048 tokens (approx 8192 chars)
        long_text = "word " * 10000
        chunks = chunk_document(long_text, chunk_size=512, doc_id="long_doc")
        
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(c.document_id == "long_doc" for c in chunks)


class TestEdgeCaseLogging:
    """Tests for verify_edge_case_logging."""

    def test_verify_edge_case_logging_found(self):
        """Test detection of short document warnings."""
        logs = [
            "INFO: Starting process",
            "WARNING: Document doc1 too short (100 tokens). Skipping.",
            "INFO: Finished"
        ]
        assert verify_edge_case_logging(logs) is True

    def test_verify_edge_case_logging_not_found(self):
        """Test when no warnings are found."""
        logs = [
            "INFO: Starting process",
            "INFO: Processing done",
        ]
        assert verify_edge_case_logging(logs) is False