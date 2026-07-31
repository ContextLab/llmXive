"""
Unit tests for the FeatureVector model generated from contracts/feature.schema.yaml.
"""
import pytest
import json
from src.models.feature_vector import FeatureVector, create_feature_vector


class TestFeatureVectorCreation:
    """Test basic creation of FeatureVector instances."""

    def test_create_with_all_fields(self):
        """Test creating a FeatureVector with all required fields."""
        fv = FeatureVector(
            snippet_id="test-123",
            ast_depth=5,
            cyclomatic_complexity=3,
            node_count=42,
            taint_api_count=1,
            sanitization_present=True,
            embedding_similarity_score=0.85
        )
        
        assert fv.snippet_id == "test-123"
        assert fv.ast_depth == 5
        assert fv.cyclomatic_complexity == 3
        assert fv.node_count == 42
        assert fv.taint_api_count == 1
        assert fv.sanitization_present is True
        assert fv.embedding_similarity_score == 0.85
        assert fv.label_missing is False  # Default value

    def test_create_with_label_missing(self):
        """Test creating a FeatureVector with label_missing flag."""
        fv = FeatureVector(
            snippet_id="test-124",
            ast_depth=3,
            cyclomatic_complexity=2,
            node_count=20,
            taint_api_count=0,
            sanitization_present=False,
            embedding_similarity_score=0.5,
            label_missing=True
        )
        
        assert fv.label_missing is True

    def test_create_with_minimum_values(self):
        """Test creating a FeatureVector with minimum valid values."""
        fv = FeatureVector(
            snippet_id="test-125",
            ast_depth=0,
            cyclomatic_complexity=1,
            node_count=0,
            taint_api_count=0,
            sanitization_present=False,
            embedding_similarity_score=0.0
        )
        
        assert fv.ast_depth == 0
        assert fv.cyclomatic_complexity == 1
        assert fv.embedding_similarity_score == 0.0


class TestCreateFeatureVectorFactory:
    """Test the factory method create_feature_vector."""

    def test_factory_with_explicit_id(self):
        """Test factory method with explicit snippet_id."""
        fv = create_feature_vector(
            snippet_id="factory-test-1",
            ast_depth=4,
            cyclomatic_complexity=2,
            node_count=30,
            taint_api_count=1,
            sanitization_present=True,
            embedding_similarity_score=0.75
        )
        
        assert fv.snippet_id == "factory-test-1"
        assert fv.ast_depth == 4

    def test_factory_generates_uuid(self):
        """Test that factory generates a UUID if snippet_id is not provided."""
        fv = create_feature_vector(
            ast_depth=2,
            cyclomatic_complexity=1,
            node_count=10,
            taint_api_count=0,
            sanitization_present=False,
            embedding_similarity_score=0.1
        )
        
        assert fv.snippet_id is not None
        assert len(fv.snippet_id) > 0
        # Basic UUID format check (8-4-4-4-12 hex chars)
        parts = fv.snippet_id.split('-')
        assert len(parts) == 5
        assert all(len(p) > 0 for p in parts)


class TestFeatureVectorUniqueness:
    """Test uniqueness constraints."""

    def test_multiple_instances_different_ids(self):
        """Test that multiple instances can have different IDs."""
        fv1 = create_feature_vector(ast_depth=1)
        fv2 = create_feature_vector(ast_depth=2)
        
        assert fv1.snippet_id != fv2.snippet_id


class TestFeatureVectorSerialization:
    """Test serialization and deserialization."""

    def test_to_dict(self):
        """Test converting FeatureVector to dictionary."""
        fv = FeatureVector(
            snippet_id="dict-test",
            ast_depth=3,
            cyclomatic_complexity=2,
            node_count=15,
            taint_api_count=1,
            sanitization_present=True,
            embedding_similarity_score=0.9
        )
        
        data = fv.to_dict()
        
        assert data["snippet_id"] == "dict-test"
        assert data["ast_depth"] == 3
        assert data["cyclomatic_complexity"] == 2
        assert data["node_count"] == 15
        assert data["taint_api_count"] == 1
        assert data["sanitization_present"] is True
        assert data["embedding_similarity_score"] == 0.9

    def test_to_json(self):
        """Test converting FeatureVector to JSON string."""
        fv = FeatureVector(
            snippet_id="json-test",
            ast_depth=4,
            cyclomatic_complexity=3,
            node_count=25,
            taint_api_count=2,
            sanitization_present=False,
            embedding_similarity_score=0.6
        )
        
        json_str = fv.to_json()
        data = json.loads(json_str)
        
        assert data["snippet_id"] == "json-test"
        assert data["ast_depth"] == 4

    def test_from_dict(self):
        """Test creating FeatureVector from dictionary."""
        data = {
            "snippet_id": "from-dict-test",
            "ast_depth": 5,
            "cyclomatic_complexity": 4,
            "node_count": 50,
            "taint_api_count": 3,
            "sanitization_present": True,
            "embedding_similarity_score": 0.95
        }
        
        fv = FeatureVector.from_dict(data)
        
        assert fv.snippet_id == "from-dict-test"
        assert fv.ast_depth == 5

    def test_from_json(self):
        """Test creating FeatureVector from JSON string."""
        json_str = json.dumps({
            "snippet_id": "from-json-test",
            "ast_depth": 6,
            "cyclomatic_complexity": 5,
            "node_count": 60,
            "taint_api_count": 4,
            "sanitization_present": False,
            "embedding_similarity_score": 0.4
        })
        
        fv = FeatureVector.from_json(json_str)
        
        assert fv.snippet_id == "from-json-test"
        assert fv.ast_depth == 6

    def test_round_trip(self):
        """Test that serialization and deserialization preserve data."""
        original = FeatureVector(
            snippet_id="round-trip-test",
            ast_depth=7,
            cyclomatic_complexity=6,
            node_count=70,
            taint_api_count=5,
            sanitization_present=True,
            embedding_similarity_score=0.88,
            label_missing=True
        )
        
        # Dict round trip
        data = original.to_dict()
        restored_dict = FeatureVector.from_dict(data)
        assert restored_dict == original

        # JSON round trip
        json_str = original.to_json()
        restored_json = FeatureVector.from_json(json_str)
        assert restored_json == original


class TestFeatureVectorValidation:
    """Test validation constraints."""

    def test_negative_ast_depth_fails(self):
        """Test that negative ast_depth raises validation error."""
        with pytest.raises(Exception):
            FeatureVector(
                snippet_id="invalid-1",
                ast_depth=-1,
                cyclomatic_complexity=1,
                node_count=10,
                taint_api_count=0,
                sanitization_present=False,
                embedding_similarity_score=0.5
            )

    def test_complexity_zero_fails(self):
        """Test that cyclomatic_complexity of 0 raises validation error."""
        with pytest.raises(Exception):
            FeatureVector(
                snippet_id="invalid-2",
                ast_depth=1,
                cyclomatic_complexity=0,
                node_count=10,
                taint_api_count=0,
                sanitization_present=False,
                embedding_similarity_score=0.5
            )

    def test_embedding_score_above_one_fails(self):
        """Test that embedding_similarity_score > 1.0 raises validation error."""
        with pytest.raises(Exception):
            FeatureVector(
                snippet_id="invalid-3",
                ast_depth=1,
                cyclomatic_complexity=1,
                node_count=10,
                taint_api_count=0,
                sanitization_present=False,
                embedding_similarity_score=1.5
            )

    def test_embedding_score_below_zero_fails(self):
        """Test that embedding_similarity_score < 0.0 raises validation error."""
        with pytest.raises(Exception):
            FeatureVector(
                snippet_id="invalid-4",
                ast_depth=1,
                cyclomatic_complexity=1,
                node_count=10,
                taint_api_count=0,
                sanitization_present=False,
                embedding_similarity_score=-0.1
            )

    def test_missing_required_field_fails(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(Exception):
            FeatureVector(
                snippet_id="invalid-5",
                # Missing ast_depth
                cyclomatic_complexity=1,
                node_count=10,
                taint_api_count=0,
                sanitization_present=False,
                embedding_similarity_score=0.5
            )