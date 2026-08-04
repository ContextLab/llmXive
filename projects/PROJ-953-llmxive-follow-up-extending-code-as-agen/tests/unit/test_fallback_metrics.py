import pytest
from scripts.extract_features import calculate_semantic_complexity_score, extract_graph_and_metrics

# Code with no semantic nodes (no functions, classes, or calls)
NO_SEMANTIC_CODE = """
x = 1
y = 2
z = x + y
"""

def test_fallback_logic():
    """Test that fallback metrics are calculated when semantic nodes are missing."""
    score = calculate_semantic_complexity_score(NO_SEMANTIC_CODE)
    assert score is None, "Semantic score should be None for code without semantic nodes"

    graph, metrics = extract_graph_and_metrics(NO_SEMANTIC_CODE)
    
    # Verify fallback flag
    assert graph["metadata"]["fallback_active"] == True
    assert graph["metadata"]["has_semantic_nodes"] == False
    
    # Verify fallback metrics are present and valid
    assert metrics["lines_of_code"] > 0
    assert metrics["dependency_depth"] >= 0
    assert metrics["cyclomatic_complexity"] >= 1.0
    assert metrics["semantic_complexity_score"] is None