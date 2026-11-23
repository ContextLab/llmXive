"""
Unit tests for the Semantic Similarity Merging module (T040).
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from pathlib import Path

# Mock the heavy sentence-transformers dependency for unit tests
# to avoid downloading the model during test execution
@pytest.fixture(autouse=True)
def mock_sentence_transformers(monkeypatch):
    class MockModel:
        def encode(self, texts, show_progress_bar=False):
            # Return deterministic embeddings based on text content for testing
            # Just map 'A' -> [1,0], 'B' -> [0,1], 'SimilarA' -> [0.9, 0.1] etc.
            # For the specific test case: 'Math' vs 'Mathematics'
            embeddings = []
            for t in texts:
                if t == "Math":
                    embeddings.append([1.0, 0.0])
                elif t == "Mathematics":
                    # Very similar to Math
                    embeddings.append([0.95, 0.05])
                elif t == "Science":
                    embeddings.append([0.0, 1.0])
                elif t == "Biology":
                    # Similar to Science
                    embeddings.append([0.1, 0.95])
                else:
                    embeddings.append([0.0, 0.0])
            return np.array(embeddings)

    monkeypatch.setattr("merger.SentenceTransformer", lambda name: MockModel())

from merger import merge_similar_categories, build_merge_map, compute_pairwise_distances
from config import ProjectConfig

def test_merge_similar_categories_basic():
    """
    Test that categories with high similarity are merged.
    """
    config = ProjectConfig()
    # Override threshold to ensure Math and Mathematics merge
    config.SEMANTIC_SIMILARITY_THRESHOLD = 0.9

    data = {
        "user_id": [1, 2],
        "session_id": ["s1", "s2"],
        "recommended_categories": [
            ["Math", "Science"],
            ["Mathematics", "Biology"]
        ],
        "enrolled_categories": [
            ["Physics"],
            ["Chemistry"]
        ]
    }
    df = pd.DataFrame(data)

    result_df = merge_similar_categories(df, config, category_col="recommended_categories")

    # Check that the new column exists
    assert "recommended_categories_merged" in result_df.columns

    # Row 0: Math and Science. Math should merge to itself or Math (since Math < Mathematics).
    # Row 1: Mathematics and Biology. Mathematics should merge to Math. Biology should merge to Science.
    # Expected:
    # Row 0: ["Math", "Science"]
    # Row 1: ["Math", "Science"] (Mathematics -> Math, Biology -> Science)

    row_0 = result_df.iloc[0]["recommended_categories_merged"]
    row_1 = result_df.iloc[1]["recommended_categories_merged"]

    # Verify Math and Science are present in row 0
    assert set(row_0) == {"Math", "Science"}

    # Verify Math and Science are present in row 1 (merged)
    assert set(row_1) == {"Math", "Science"}

def test_merge_map_determinism():
    """
    Test that the merge map is deterministic and consistent.
    """
    categories = ["Math", "Mathematics", "Science", "Biology"]
    # Simulate pairs: (Math, Mathematics) and (Science, Biology)
    # Indices: 0=Math, 1=Mathematics, 2=Science, 3=Biology
    pairs = [
        (0, 1, 0.95),
        (2, 3, 0.95)
    ]

    merge_map = build_merge_map(categories, pairs)

    # Math < Mathematics, so Mathematics -> Math
    assert merge_map["Mathematics"] == "Math"
    assert merge_map["Math"] == "Math"

    # Science < Biology, so Biology -> Science
    assert merge_map["Biology"] == "Science"
    assert merge_map["Science"] == "Science"

def test_no_merge_below_threshold():
    """
    Test that categories are NOT merged if similarity is below threshold.
    """
    config = ProjectConfig()
    config.SEMANTIC_SIMILARITY_THRESHOLD = 0.99 # Very high threshold

    data = {
        "user_id": [1],
        "session_id": ["s1"],
        "recommended_categories": [["Math", "Science"]],
        "enrolled_categories": [["Physics"]]
    }
    df = pd.DataFrame(data)

    # Mock embeddings such that Math and Science are not similar
    # In the mock fixture, Math=[1,0], Science=[0,1]. Cosine sim = 0.
    # 0 is not > 0.99, so no merge.
    result_df = merge_similar_categories(df, config, category_col="recommended_categories")

    row_0 = result_df.iloc[0]["recommended_categories_merged"]
    # Should remain unchanged (order might be preserved or sorted, but set should be same)
    assert set(row_0) == {"Math", "Science"}

def test_empty_categories():
    """
    Test handling of empty category lists.
    """
    config = ProjectConfig()
    data = {
        "user_id": [1],
        "session_id": ["s1"],
        "recommended_categories": [[]],
        "enrolled_categories": [["Physics"]]
    }
    df = pd.DataFrame(data)

    result_df = merge_similar_categories(df, config, category_col="recommended_categories")
    row_0 = result_df.iloc[0]["recommended_categories_merged"]
    assert row_0 == []