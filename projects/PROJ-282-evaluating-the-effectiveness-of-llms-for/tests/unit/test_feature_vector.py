"""
Unit tests for FeatureVector model.
Verifies creation, serialization, and schema compliance.
"""
import pytest
import json
from src.models.feature_vector import FeatureVector, create_feature_vector

class TestFeatureVectorCreation:
    def test_create_default_vector(self):
        """Test creation with default values."""
        vector = FeatureVector()
        assert vector.id is not None
        assert vector.ast_depth == 0
        assert vector.cyclomatic_complexity == 0
        assert vector.node_count == 0
        assert vector.taint_api_count == 0
        assert vector.sanitization_present is False
        assert vector.embedding_similarity_score == 0.0
        assert vector.created_at is not None

    def test_create_vector_with_values(self):
        """Test creation with specific feature values."""
        vector = FeatureVector(
            snippet_id="test-snippet-123",
            ast_depth=5,
            cyclomatic_complexity=12,
            node_count=45,
            taint_api_count=2,
            sanitization_present=True,
            embedding_similarity_score=0.85
        )
        assert vector.snippet_id == "test-snippet-123"
        assert vector.ast_depth == 5
        assert vector.cyclomatic_complexity == 12
        assert vector.node_count == 45
        assert vector.taint_api_count == 2
        assert vector.sanitization_present is True
        assert abs(vector.embedding_similarity_score - 0.85) < 0.001

class TestCreateFeatureVectorFactory:
    def test_factory_creates_instance(self):
        """Test the factory function creates a valid instance."""
        vector = create_feature_vector(
            snippet_id="factory-test",
            ast_depth=3,
            cyclomatic_complexity=5
        )
        assert isinstance(vector, FeatureVector)
        assert vector.snippet_id == "factory-test"
        assert vector.ast_depth == 3
        assert vector.cyclomatic_complexity == 5

class TestFeatureVectorUniqueness:
    def test_unique_ids(self):
        """Ensure every instance gets a unique ID."""
        v1 = FeatureVector()
        v2 = FeatureVector()
        assert v1.id != v2.id

class TestFeatureVectorSerialization:
    def test_to_dict(self):
        """Test dictionary serialization."""
        vector = create_feature_vector(snippet_id="s1", ast_depth=2)
        data = vector.to_dict()
        assert "id" in data
        assert data["snippet_id"] == "s1"
        assert data["ast_depth"] == 2
        assert "created_at" in data

    def test_to_json(self):
        """Test JSON string serialization."""
        vector = create_feature_vector(snippet_id="s2", ast_depth=4)
        json_str = vector.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["snippet_id"] == "s2"
        assert parsed["ast_depth"] == 4

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        raw_data = {
            "id": "fixed-id-123",
            "snippet_id": "s3",
            "ast_depth": 10,
            "cyclomatic_complexity": 20,
            "node_count": 100,
            "taint_api_count": 5,
            "sanitization_present": True,
            "embedding_similarity_score": 0.95,
            "created_at": "2023-10-27T10:00:00"
        }
        vector = FeatureVector.from_dict(raw_data)
        assert vector.id == "fixed-id-123"
        assert vector.snippet_id == "s3"
        assert vector.ast_depth == 10
        assert vector.cyclomatic_complexity == 20
        assert vector.node_count == 100
        assert vector.taint_api_count == 5
        assert vector.sanitization_present is True
        assert vector.embedding_similarity_score == 0.95
        assert vector.created_at == "2023-10-27T10:00:00"

class TestFeatureVectorValidation:
    def test_schema_compliance(self):
        """Verify all required fields are present in serialization."""
        vector = create_feature_vector(
            snippet_id="val-test",
            ast_depth=1,
            cyclomatic_complexity=1,
            node_count=1,
            taint_api_count=0,
            sanitization_present=False,
            embedding_similarity_score=0.0
        )
        data = vector.to_dict()
        required_fields = [
            "id", "snippet_id", "ast_depth", "cyclomatic_complexity",
            "node_count", "taint_api_count", "sanitization_present",
            "embedding_similarity_score", "created_at"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"