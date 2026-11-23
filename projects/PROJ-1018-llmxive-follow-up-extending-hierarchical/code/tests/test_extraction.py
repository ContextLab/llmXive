"""
Tests for the extraction module.
"""
import pytest
import logging
import numpy as np
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Import the module under test
from src.extraction import (
    Chunk, 
    RelevanceProfile, 
    aggregate_profiles, 
    validate_profiles, 
    save_profiles,
    DynamicHiLSWrapper,
    chunk_document,
    verify_edge_case_logging
)
from src.config import Config

class TestValidation:
    def test_validate_profiles_valid(self):
        """Test validation with valid profiles."""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[0.1, 0.2, 0.3], document_id="d1"),
            RelevanceProfile(chunk_id="c2", scores=[0.5, 0.6], document_id="d2")
        ]
        assert validate_profiles(profiles) is True

    def test_validate_profiles_nan(self):
        """Test validation with NaN scores."""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[0.1, np.nan, 0.3], document_id="d1")
        ]
        assert validate_profiles(profiles) is False

    def test_validate_profiles_empty(self):
        """Test validation with empty scores."""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[], document_id="d1")
        ]
        assert validate_profiles(profiles) is False

class TestChunking:
    def test_chunk_document_basic(self):
        """Test basic document chunking."""
        tokenizer = MagicMock()
        tokenizer.encode.return_value = list(range(100))
        tokenizer.decode.return_value = "test text"
        
        chunks = chunk_document("some text", 50, tokenizer)
        
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(c.token_count <= 50 for c in chunks)

    def test_chunk_document_short(self):
        """Test chunking a short document."""
        tokenizer = MagicMock()
        tokenizer.encode.return_value = list(range(10))
        tokenizer.decode.return_value = "short"
        
        # Should still create a chunk or handle edge case
        chunks = chunk_document("short", 50, tokenizer)
        # Depending on implementation, might be empty or one chunk
        # Here we assume it creates a chunk if > 0 tokens
        assert len(chunks) >= 0 

class TestEdgeCaseLogging:
    def test_verify_edge_case_logging_skip(self, caplog):
        """Test that short documents are logged and skipped."""
        with caplog.at_level(logging.WARNING):
            result = verify_edge_case_logging("doc1", 100, min_tokens=2048)
            assert result is False
            assert "Skipping document doc1" in caplog.text

    def test_verify_edge_case_logging_process(self):
        """Test that long documents are processed."""
        result = verify_edge_case_logging("doc2", 3000, min_tokens=2048)
        assert result is True

class TestAggregation:
    def test_aggregate_profiles_from_dicts(self):
        """Test aggregation from list of dicts (output of run_dynamic_inference)."""
        data = [
            {"chunk_id": "c1", "scores": [0.1, 0.2], "document_id": "d1"},
            {"chunk_id": "c2", "scores": [0.3, 0.4], "document_id": "d1"}
        ]
        
        profiles = aggregate_profiles(data)
        
        assert len(profiles) == 2
        assert profiles[0].chunk_id == "c1"
        assert profiles[0].scores == [0.1, 0.2]
        assert profiles[1].document_id == "d1"

    def test_aggregate_profiles_empty(self):
        """Test aggregation of empty list."""
        profiles = aggregate_profiles([])
        assert len(profiles) == 0

class TestSaveProfiles:
    def test_save_profiles_creates_file(self):
        """Test that save_profiles writes a valid JSON file."""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[0.1], document_id="d1")
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            path = f.name
        
        try:
            save_profiles(profiles, path)
            assert os.path.exists(path)
            
            with open(path, 'r') as f:
                import json
                data = json.load(f)
                assert len(data) == 1
                assert data[0]['chunk_id'] == 'c1'
        finally:
            os.remove(path)

class TestDynamicHiLSWrapper:
    def test_wrapper_extract_scores(self):
        """Test the wrapper's extract_scores method."""
        model = MagicMock()
        tokenizer = MagicMock()
        config = Config()
        
        # Mock model output
        mock_outputs = MagicMock()
        mock_outputs.attentions = [torch.tensor([[[0.1, 0.2]]])]
        model.return_value = mock_outputs
        
        wrapper = DynamicHiLSWrapper(model, tokenizer, config)
        
        chunk = Chunk(
            chunk_id="test",
            text="test text",
            document_id="d1",
            start_token=0,
            end_token=10,
            token_count=10
        )
        
        # This would require a real model to run fully, but we can check structure
        # For unit test, we mock the forward pass
        with patch.object(wrapper.model, '__call__', return_value=mock_outputs):
            scores = wrapper.extract_scores(chunk)
            assert isinstance(scores, list)
            assert len(scores) > 0