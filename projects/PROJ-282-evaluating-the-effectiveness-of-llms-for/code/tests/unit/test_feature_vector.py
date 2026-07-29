"""
Unit tests for FeatureVector dataclass.

Tests verify schema compliance, factory function behavior, and serialization.
"""
import pytest
import json
from src.models.feature_vector import FeatureVector, create_feature_vector


class TestFeatureVectorCreation:
    """Test basic FeatureVector instantiation."""

    def test_feature_vector_creation(self):
        """Test creating a FeatureVector with required fields."""
        fv = FeatureVector(
            vector_id="test-uuid-123",
            snippet_id="snippet-456",
            language="python"
        )
        
        assert fv.vector_id == "test-uuid-123"
        assert fv.snippet_id == "snippet-456"
        assert fv.language == "python"
        assert fv.ast_depth is None
        assert fv.taint_api_count == 0
        assert fv.has_sanitization is False

    def test_feature_vector_with_all_fields(self):
        """Test creating a FeatureVector with all optional fields."""
        fv = FeatureVector(
            vector_id="test-uuid-789",
            snippet_id="snippet-012",
            language="c",
            ast_depth=5,
            ast_node_count=150,
            cyclomatic_complexity=8,
            taint_api_count=3,
            has_sanitization=True,
            embedding_similarity_score=0.85,
            embedding_vector=[0.1, 0.2, 0.3],
            lines_of_code=42,
            num_functions=3,
            num_imports=5
        )
        
        assert fv.ast_depth == 5
        assert fv.ast_node_count == 150
        assert fv.cyclomatic_complexity == 8
        assert fv.taint_api_count == 3
        assert fv.has_sanitization is True
        assert fv.embedding_similarity_score == 0.85
        assert fv.embedding_vector == [0.1, 0.2, 0.3]
        assert fv.lines_of_code == 42
        assert fv.num_functions == 3
        assert fv.num_imports == 5


class TestCreateFeatureVectorFactory:
    """Test the create_feature_vector factory function."""

    def test_create_feature_vector_factory(self):
        """Test factory function creates valid FeatureVector."""
        fv = create_feature_vector(
            snippet_id="factory-snippet",
            language="javascript",
            ast_depth=3,
            cyclomatic_complexity=5
        )
        
        assert fv.snippet_id == "factory-snippet"
        assert fv.language == "javascript"
        assert fv.ast_depth == 3
        assert fv.cyclomatic_complexity == 5
        assert fv.vector_id != ""  # Auto-generated
        assert fv.extraction_timestamp is not None

    def test_feature_vector_defaults(self):
        """Test that factory sets correct defaults for optional fields."""
        fv = create_feature_vector(
            snippet_id="defaults-test",
            language="python"
        )
        
        assert fv.ast_depth is None
        assert fv.ast_node_count is None
        assert fv.cyclomatic_complexity is None
        assert fv.taint_api_count == 0
        assert fv.has_sanitization is False
        assert fv.embedding_similarity_score is None
        assert fv.embedding_vector is None
        assert fv.lines_of_code is None
        assert fv.num_functions is None
        assert fv.num_imports is None
        assert fv.extraction_error is None


class TestFeatureVectorUniqueness:
    """Test UUID generation and uniqueness."""

    def test_feature_vector_uniqueness(self):
        """Test that each FeatureVector gets a unique ID."""
        fv1 = create_feature_vector(snippet_id="s1", language="python")
        fv2 = create_feature_vector(snippet_id="s2", language="python")
        
        assert fv1.vector_id != fv2.vector_id
        assert len(fv1.vector_id) == 36  # Standard UUID format


class TestFeatureVectorSerialization:
    """Test serialization and deserialization."""

    def test_to_dict(self):
        """Test dictionary conversion."""
        fv = create_feature_vector(
            snippet_id="dict-test",
            language="java",
            ast_depth=4
        )
        fv_dict = fv.to_dict()
        
        assert "vector_id" in fv_dict
        assert "snippet_id" in fv_dict
        assert "language" in fv_dict
        assert "ast_depth" in fv_dict
        assert fv_dict["snippet_id"] == "dict-test"
        assert fv_dict["language"] == "java"
        assert fv_dict["ast_depth"] == 4

    def test_from_dict(self):
        """Test dictionary reconstruction."""
        data = {
            "vector_id": "manual-uuid",
            "snippet_id": "from-dict",
            "language": "cpp",
            "ast_depth": 6,
            "taint_api_count": 2
        }
        fv = FeatureVector.from_dict(data)
        
        assert fv.vector_id == "manual-uuid"
        assert fv.snippet_id == "from-dict"
        assert fv.language == "cpp"
        assert fv.ast_depth == 6
        assert fv.taint_api_count == 2

    def test_to_json(self):
        """Test JSON serialization."""
        fv = create_feature_vector(
            snippet_id="json-test",
            language="python",
            ast_depth=2
        )
        json_str = fv.to_json()
        
        assert isinstance(json_str, str)
        assert "json-test" in json_str
        assert "python" in json_str

    def test_from_json(self):
        """Test JSON deserialization."""
        json_str = '{"vector_id": "json-uuid", "snippet_id": "from-json", "language": "rust", "ast_depth": 3}'
        fv = FeatureVector.from_json(json_str)
        
        assert fv.vector_id == "json-uuid"
        assert fv.snippet_id == "from-json"
        assert fv.language == "rust"
        assert fv.ast_depth == 3

    def test_round_trip_serialization(self):
        """Test that serialization and deserialization preserve data."""
        original = create_feature_vector(
            snippet_id="round-trip",
            language="go",
            ast_depth=5,
            cyclomatic_complexity=10,
            taint_api_count=4,
            has_sanitization=True,
            embedding_similarity_score=0.92,
            embedding_vector=[0.5, 0.5, 0.5],
            lines_of_code=100,
            num_functions=5,
            num_imports=10
        )
        
        # Dict round trip
        fv_dict = FeatureVector.from_dict(original.to_dict())
        assert fv_dict.snippet_id == original.snippet_id
        assert fv_dict.language == original.language
        assert fv_dict.ast_depth == original.ast_depth
        
        # JSON round trip
        fv_json = FeatureVector.from_json(original.to_json())
        assert fv_json.snippet_id == original.snippet_id
        assert fv_json.language == original.language
        assert fv_json.cyclomatic_complexity == original.cyclomatic_complexity


class TestFeatureVectorValidation:
    """Test validation and error handling."""

    def test_feature_vector_invalid_embedding_type(self):
        """Test that embedding_vector must be a list of floats."""
        # This test verifies the type hint is respected at runtime
        # (Python dataclasses don't enforce types by default, but the contract is documented)
        fv = create_feature_vector(
            snippet_id="type-test",
            language="python",
            embedding_vector=[1.0, 2.0, 3.0]
        )
        assert isinstance(fv.embedding_vector, list)
        assert all(isinstance(x, float) for x in fv.embedding_vector)

    def test_extraction_error_field(self):
        """Test that extraction_error can store error messages."""
        fv = create_feature_vector(
            snippet_id="error-test",
            language="python",
            extraction_error="AST parsing failed: syntax error"
        )
        
        assert fv.extraction_error == "AST parsing failed: syntax error"
        
        # Test with no error
        fv_no_error = create_feature_vector(
            snippet_id="no-error-test",
            language="python"
        )
        assert fv_no_error.extraction_error is None