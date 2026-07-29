import pytest
import json
from src.models.feature_vector import FeatureVector, create_feature_vector


class TestFeatureVectorCreation:
    def test_create_vector_minimal(self):
        vector = create_feature_vector(snippet_id="123")
        assert vector.snippet_id == "123"
        assert vector.ast_depth is None
        assert vector.embedding_similarity_score is None

    def test_create_vector_full(self):
        vector = create_feature_vector(
            snippet_id="123",
            ast_depth=5,
            cyclomatic_complexity=10,
            embedding_similarity_score=0.85
        )
        assert vector.ast_depth == 5
        assert vector.cyclomatic_complexity == 10
        assert vector.embedding_similarity_score == 0.85

class TestCreateFeatureVectorFactory:
    def test_vector_uniqueness(self):
        v1 = create_feature_vector("1")
        v2 = create_feature_vector("2")
        assert v1.vector_id != v2.vector_id

class TestFeatureVectorUniqueness:
    def test_vector_id_generation(self):
        vectors = [create_feature_vector(str(i)) for i in range(10)]
        ids = [v.vector_id for v in vectors]
        assert len(ids) == len(set(ids))

class TestFeatureVectorSerialization:
    def test_to_dict(self):
        vector = create_feature_vector("1", ast_depth=3)
        data = vector.to_dict()
        assert data["snippet_id"] == "1"
        assert data["ast_depth"] == 3

    def test_from_dict(self):
        data = {
            "snippet_id": "1",
            "ast_depth": 4,
            "cyclomatic_complexity": 5
        }
        vector = FeatureVector.from_dict(data)
        assert vector.snippet_id == "1"
        assert vector.ast_depth == 4

class TestFeatureVectorValidation:
    def test_negative_complexity(self):
        with pytest.raises(ValueError):
            create_feature_vector("1", cyclomatic_complexity=-1)

    def test_embedding_score_bounds(self):
        # 0.0 to 1.0
        create_feature_vector("1", embedding_similarity_score=0.0)
        create_feature_vector("1", embedding_similarity_score=1.0)
        with pytest.raises(ValueError):
            create_feature_vector("1", embedding_similarity_score=1.1)
