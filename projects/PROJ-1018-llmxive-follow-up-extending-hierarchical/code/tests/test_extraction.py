import pytest
import logging
import numpy as np
from code.src.extraction import chunk_document, Chunk, validate_profiles
from code.src.models import RelevanceProfile
from code.src.config import Config

logger = logging.getLogger(__name__)

class TestChunkingLogic:
    def test_chunk_document_basic(self):
        text = "A" * 4096
        chunks = chunk_document(text, 1024)
        assert len(chunks) == 4
        assert all(len(c.text) == 1024 for c in chunks)
        assert chunks[0].chunk_id.startswith("doc_")
    
    def test_chunk_document_short(self):
        text = "Short"
        chunks = chunk_document(text, 1024)
        assert len(chunks) == 0
    
    def test_chunk_document_padding(self):
        text = "A" * 1025
        chunks = chunk_document(text, 1024)
        # First chunk 1024, second chunk 1 char padded to 1024
        assert len(chunks) == 2
        assert len(chunks[0].text) == 1024
        assert len(chunks[1].text) == 1024

class TestValidateProfiles:
    def test_validate_valid_profiles(self):
        config = Config(seed=42, chunk_size=1024, model_path="", k_clusters=10)
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[0.1] * 10, document_id="d1"),
            RelevanceProfile(chunk_id="c2", scores=[0.2] * 10, document_id="d1")
        ]
        assert validate_profiles(profiles, config) is True

    def test_validate_none_scores(self):
        config = Config(seed=42, chunk_size=1024, model_path="", k_clusters=10)
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=None, document_id="d1")
        ]
        with pytest.raises(ValueError, match="has None scores"):
            validate_profiles(profiles, config)

    def test_validate_nan_scores(self):
        config = Config(seed=42, chunk_size=1024, model_path="", k_clusters=10)
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[0.1, np.nan, 0.3], document_id="d1")
        ]
        with pytest.raises(ValueError, match="NaN/Inf score"):
            validate_profiles(profiles, config)

    def test_validate_wrong_dimension(self):
        config = Config(seed=42, chunk_size=1024, model_path="", k_clusters=10)
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[0.1] * 5, document_id="d1")
        ]
        with pytest.raises(ValueError, match="expected 10"):
            validate_profiles(profiles, config)

    def test_validate_empty_list(self):
        config = Config(seed=42, chunk_size=1024, model_path="", k_clusters=10)
        assert validate_profiles([], config) is True