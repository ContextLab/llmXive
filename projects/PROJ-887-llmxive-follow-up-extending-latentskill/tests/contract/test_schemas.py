"""
Contract tests for validating output formats against defined schemas.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import yaml

# Project root setup
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "code"))

from src.utils.config import get_project_root, get_data_path
from src.retrieval.query import generate_query_vector, QueryOutputSchema
from src.retrieval.strategies import load_skill_index
from src.validate.citation_check import verify_sources


class TestQueryOutputSchema:
    """Contract tests for src/retrieval/query.py output format."""

    def test_generate_query_vector_returns_dict(self):
        """Verify that generate_query_vector returns a dictionary."""
        # We mock the embedding model to avoid heavy dependencies in contract tests
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
            mock_model_class.return_value = mock_model

            query_text = "test task description"
            result = generate_query_vector(query_text)

            assert isinstance(result, dict), "Output must be a dictionary"
            assert "vector" in result, "Output must contain 'vector' key"
            assert "latency_ms" in result, "Output must contain 'latency_ms' key"
            assert "query_text" in result, "Output must contain 'query_text' key"
            assert isinstance(result["vector"], np.ndarray), "Vector must be a numpy array"
            assert isinstance(result["latency_ms"], (int, float)), "Latency must be numeric"
            assert result["query_text"] == query_text

    def test_vector_dimensionality(self):
        """Verify that the generated vector has the expected dimensionality (384 for MiniLM)."""
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            expected_dim = 384
            mock_model = MagicMock()
            mock_model.encode.return_value = np.random.rand(expected_dim).astype(np.float32)
            mock_model_class.return_value = mock_model

            result = generate_query_vector("test")
            assert result["vector"].shape == (expected_dim,), f"Vector dimension mismatch: {result['vector'].shape}"

    def test_latency_is_positive(self):
        """Verify that latency is a positive number."""
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
            mock_model_class.return_value = mock_model

            result = generate_query_vector("test")
            assert result["latency_ms"] >= 0, "Latency must be non-negative"


class TestSkillIndexSchema:
    """Contract tests for the skill index structure loaded from vector_db."""

    def test_skill_index_loads_as_dict(self):
        """Verify that the skill index loads as a dictionary with expected keys."""
        # This test assumes T014d has been run and data/processed/skill_index.npz exists.
        # If not, it should fail loudly to indicate missing prerequisite data.
        index_path = get_data_path() / "processed" / "skill_index.npz"
        if not index_path.exists():
            pytest.fail(f"Skill index file not found at {index_path}. Ensure T014d has been executed.")

        data = load_skill_index(index_path)
        assert isinstance(data, dict), "Skill index must be a dictionary"
        assert "vectors" in data, "Skill index must contain 'vectors' key"
        assert "metadata" in data, "Skill index must contain 'metadata' key"
        assert "ids" in data, "Skill index must contain 'ids' key"

    def test_vectors_are_numpy_array(self):
        """Verify that vectors in the skill index are a numpy array."""
        index_path = get_data_path() / "processed" / "skill_index.npz"
        if not index_path.exists():
            pytest.skip("Skill index file missing")

        data = load_skill_index(index_path)
        assert isinstance(data["vectors"], np.ndarray), "Vectors must be a numpy array"
        assert len(data["vectors"].shape) == 2, "Vectors must be 2D (n_samples, n_features)"


class TestCitationVerificationSchema:
    """Contract tests for citation verification output."""

    def test_citation_verification_json_structure(self):
        """Verify the structure of citation_verification.json."""
        # This test assumes T006b has been run.
        verification_path = get_data_path() / "processed" / "citation_verification.json"
        if not verification_path.exists():
            pytest.skip("Citation verification file missing. Run T006b first.")

        with open(verification_path, 'r') as f:
            data = json.load(f)

        assert isinstance(data, dict), "Verification data must be a dictionary"
        assert "sources" in data, "Must contain 'sources' key"
        assert "timestamp" in data, "Must contain 'timestamp' key"
        assert "overall_status" in data, "Must contain 'overall_status' key"

        for source_key, source_data in data["sources"].items():
            assert "url" in source_data, f"Source {source_key} must have 'url'"
            assert "status" in source_data, f"Source {source_key} must have 'status'"
            assert source_data["status"] in ["valid", "invalid", "partial"], f"Source {source_key} has invalid status"