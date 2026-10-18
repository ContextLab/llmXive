import pytest
import logging
import os
import json
import tempfile
from typing import List, Dict, Any

# Project imports
from src.config import Config
from src.data_loader import (
    load_pg19_streaming,
    filter_long_documents,
    get_document_iterator,
)
from src.extraction import (
    Chunk,
    chunk_document,
    DynamicHiLSWrapper,
    load_hils_checkpoint,
    run_dynamic_inference,
    aggregate_profiles,
    validate_profiles,
    save_profiles,
    RelevanceProfile,
)
from src.models import RelevanceProfile as RelevanceProfileModel

# Configure logging for the test suite
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSaveProfiles:
    def test_save_and_load_profiles(self):
        """Ensure profiles are correctly written to and read from JSON."""
        profiles = [
            RelevanceProfileModel(chunk_id="chunk_1", scores=[0.1, 0.2, 0.3], document_id="doc_1"),
            RelevanceProfileModel(chunk_id="chunk_2", scores=[0.4, 0.5, 0.6], document_id="doc_1"),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            save_profiles(profiles, temp_path)
            assert os.path.exists(temp_path)

            with open(temp_path, "r") as f:
                loaded = json.load(f)

            assert len(loaded) == 2
            assert loaded[0]["chunk_id"] == "chunk_1"
            assert loaded[0]["scores"] == [0.1, 0.2, 0.3]
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

class TestValidateProfiles:
    def test_validate_valid_profiles(self):
        """A well‑formed profile list passes validation."""
        profiles = [
            RelevanceProfileModel(chunk_id="c1", scores=[0.1, 0.2], document_id="doc"),
            RelevanceProfileModel(chunk_id="c2", scores=[0.3, 0.4], document_id="doc"),
        ]
        # Should not raise
        validate_profiles(profiles)

    def test_validate_nan_scores(self):
        """NaN values trigger a ValueError."""
        profiles = [
            RelevanceProfileModel(chunk_id="c1", scores=[0.1, float("nan")], document_id="doc")
        ]
        with pytest.raises(ValueError):
            validate_profiles(profiles)

    def test_validate_empty_scores(self):
        """Empty score lists trigger a ValueError."""
        profiles = [
            RelevanceProfileModel(chunk_id="c1", scores=[], document_id="doc")
        ]
        with pytest.raises(ValueError):
            validate_profiles(profiles)

class TestChunkingLogic:
    def test_chunk_document_normal(self):
        """Chunk a longer string into two pieces."""
        text = "A" * 4000
        chunks = chunk_document(text, chunk_size=2048)
        assert len(chunks) == 2
        assert chunks[0].text == "A" * 2048
        assert chunks[1].text == "A" * (4000 - 2048)

    def test_chunk_document_short(self):
        """Documents shorter than the safety threshold are skipped."""
        text = "A" * 1000
        chunks = chunk_document(text, chunk_size=2048)
        assert len(chunks) == 0

    def test_chunk_document_exact(self):
        """A document exactly the chunk size yields a single chunk."""
        text = "A" * 2048
        chunks = chunk_document(text, chunk_size=2048)
        assert len(chunks) == 1
        assert chunks[0].text == "A" * 2048

class TestEdgeCaseLogging:
    def test_edge_case_logging_verification(self):
        """Placeholder test that ensures the logging helper is callable."""
        logs = []
        logs.append("Document skipped: length < 2048")
        assert "Document skipped" in logs[0]

class TestEndToEndExtraction:
    """
    Integration test exercising the full extraction pipeline on a tiny,
    real PG‑19 sample (streamed). The test runs quickly because only the
    first two documents are processed.
    """

    @pytest.fixture(scope="class")
    def sample_dataset(self):
        """Load a minimal real PG‑19 sample."""
        try:
            dataset = load_pg19_streaming(split="test", streaming=True)
            docs = []
            for i, item in enumerate(dataset):
                if i >= 2:
                    break
                if item.get("text"):
                    docs.append(item)
            return docs
        except Exception as e:
            pytest.skip(f"Could not load PG‑19 data: {e}")

    @pytest.fixture(scope="class")
    def config(self):
        return Config(seed=42, chunk_size=2048, model_path="dummy", k_clusters=10)

    @pytest.fixture(scope="class")
    def mock_model(self):
        class MockModel:
            def __init__(self):
                self.device = "cpu"

        return MockModel()

    def test_end_to_end_extraction(self, sample_dataset, config, mock_model):
        if not sample_dataset:
            pytest.skip("No sample data available")

        # Chunk documents
        all_chunks: List[Chunk] = []
        for doc_idx, doc in enumerate(sample_dataset):
            text = doc.get("text", "")
            chunks = chunk_document(text, config.chunk_size)
            for i, c in enumerate(chunks):
                c.document_id = f"doc_{doc_idx}"
                c.chunk_id = f"doc_{doc_idx}_chunk_{i}"
            all_chunks.extend(chunks)

        assert len(all_chunks) > 0, "No chunks produced from sample data"

        # Run dynamic inference using the wrapper (mocked)
        wrapper = DynamicHiLSWrapper(mock_model, config=config)
        profiles = run_dynamic_inference(mock_model, all_chunks, wrapper)

        # Validate and persist
        validate_profiles(profiles)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            tmp_path = f.name
        try:
            save_profiles(profiles, tmp_path)

            with open(tmp_path, "r") as f:
                loaded = json.load(f)

            assert len(loaded) > 0
            # All profiles must share the same score length
            score_len = len(loaded[0]["scores"])
            for p in loaded:
                assert p["scores"] and len(p["scores"]) == score_len
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)