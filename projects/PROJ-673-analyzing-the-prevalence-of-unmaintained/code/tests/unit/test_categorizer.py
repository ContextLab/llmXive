"""
Unit tests for the category classifier.

Tests FR-007: Mandatory fallback using dependency graph topology.
"""
import pytest
from src.analysis.categorizer import (
    classify_package,
    classify_by_keywords,
    classify_batch,
    build_dependency_graph,
    get_category_distribution,
    _calculate_graph_metrics,
    _classify_by_topology
)

def test_classify_by_keywords_framework():
    """Test keyword classification for framework packages."""
    keywords = ["react", "component", "ui", "framework"]
    result = classify_by_keywords(keywords)
    assert result == "framework"

def test_classify_by_keywords_data():
    """Test keyword classification for data packages."""
    keywords = ["data", "json", "parser", "csv"]
    result = classify_by_keywords(keywords)
    assert result == "data"

def test_classify_by_keywords_no_match():
    """Test that empty keywords return None."""
    result = classify_by_keywords([])
    assert result is None

def test_classify_by_keywords_weak_match():
    """Test that weak keyword matches return None."""
    # Very few matches, below threshold
    keywords = ["random", "unique", "xyz"]
    result = classify_by_keywords(keywords)
    assert result is None

def test_classify_package_with_keywords():
    """Test full package classification with keywords."""
    package_data = {
        "name": "test-framework",
        "keywords": ["react", "vue", "framework"]
    }
    result = classify_package(package_data)
    assert result == "framework"

def test_classify_package_fallback_to_topology():
    """Test that missing keywords trigger topology fallback."""
    package_data = {
        "name": "unknown-pkg",
        "keywords": []
    }
    # With no graph, should default to utility-libraries
    result = classify_package(package_data, dependency_graph=None)
    assert result == "utility-libraries"

def test_classify_package_with_topology():
    """Test topology-based classification."""
    package_data = {
        "name": "core-lib",
        "keywords": [],
        "dependencies": ["dep1", "dep2", "dep3", "dep4", "dep5", "dep6"]
    }
    # Create a graph where this package has high in-degree
    graph = {
        "core-lib": ["dep1", "dep2"],
        "other1": ["core-lib"],
        "other2": ["core-lib"],
        "other3": ["core-lib"],
        "other4": ["core-lib"],
        "other5": ["core-lib"],
        "other6": ["core-lib"],
        "other7": ["core-lib"],
        "other8": ["core-lib"],
        "other9": ["core-lib"],
        "other10": ["core-lib"],
        "other11": ["core-lib"],
        "other12": ["core-lib"],
        "other13": ["core_lib"],
        "other14": ["core-lib"],
        "other15": ["core-lib"],
        "other16": ["core-lib"],
        "other17": ["core-lib"],
        "other18": ["core-lib"],
        "other19": ["core-lib"],
        "other20": ["core-lib"],
        "other21": ["core-lib"],
    }
    result = classify_package(package_data, dependency_graph=graph)
    # High in-degree should trigger core-infrastructure
    assert result == "core-infrastructure"

def test_classify_batch():
    """Test batch classification."""
    packages = [
        {"name": "pkg1", "keywords": ["react", "framework"]},
        {"name": "pkg2", "keywords": ["data", "json"]},
        {"name": "pkg3", "keywords": []},
    ]
    results = classify_batch(packages)
    
    assert len(results) == 3
    assert results[0]["category"] == "framework"
    assert results[1]["category"] == "data"
    assert results[2]["category"] == "utility-libraries"  # fallback

def test_build_dependency_graph():
    """Test building a dependency graph."""
    packages = [
        {"name": "pkg1", "dependencies": {"dep1": "^1.0.0", "dep2": "^2.0.0"}},
        {"name": "pkg2", "dependencies": ["dep3", "dep4"]},
        {"name": "pkg3", "dependencies": {}},
    ]
    graph = build_dependency_graph(packages)
    
    assert "pkg1" in graph
    assert set(graph["pkg1"]) == {"dep1", "dep2"}
    assert set(graph["pkg2"]) == {"dep3", "dep4"}
    assert graph["pkg3"] == []

def test_get_category_distribution():
    """Test category distribution calculation."""
    packages = [
        {"name": "pkg1", "keywords": ["react", "framework"]},
        {"name": "pkg2", "keywords": ["react", "framework"]},
        {"name": "pkg3", "keywords": ["data", "json"]},
        {"name": "pkg4", "keywords": []},
    ]
    distribution = get_category_distribution(packages)
    
    assert distribution.get("framework", 0) == 2
    assert distribution.get("data", 0) == 1
    assert distribution.get("utility-libraries", 0) == 1

def test_classify_package_with_missing_keywords():
    """Test classification when keywords are missing entirely."""
    package_data = {
        "name": "no-keywords-pkg",
        # No keywords field
    }
    result = classify_package(package_data)
    assert result == "utility-libraries"

def test_classify_package_with_noisy_keywords():
    """Test classification with noisy/irrelevant keywords."""
    package_data = {
        "name": "noisy-pkg",
        "keywords": ["asdf", "qwer", "zxcv", "random"]
    }
    result = classify_package(package_data)
    # Should fall back to utility-libraries
    assert result == "utility-libraries"

def test_graph_metrics_calculation():
    """Test graph metrics calculation."""
    graph = {
        "a": ["b", "c"],
        "b": ["c"],
        "c": [],
        "d": []
    }
    metrics = _calculate_graph_metrics(graph)
    
    assert metrics["avg_degree"] == 0.75  # (2+1+0+0)/4
    assert metrics["max_degree"] == 2
    assert metrics["isolated_ratio"] == 0.5  # 2/4

def test_topology_classification_isolated():
    """Test topology classification for isolated package."""
    graph = {
        "isolated": []
    }
    result = _classify_by_topology(
        {"avg_degree": 0.0, "max_degree": 0, "isolated_ratio": 1.0},
        "isolated",
        graph
    )
    assert result == "utility-libraries"

def test_topology_classification_high_degree():
    """Test topology classification for high degree package."""
    graph = {
        "hub": ["dep" + str(i) for i in range(15)],
        **{f"dep{i}": [] for i in range(15)}
    }
    result = _classify_by_topology(
        {"avg_degree": 1.0, "max_degree": 15, "isolated_ratio": 0.9},
        "hub",
        graph
    )
    assert result == "core-infrastructure"