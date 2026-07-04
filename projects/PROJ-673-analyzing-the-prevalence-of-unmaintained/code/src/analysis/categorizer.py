"""
Category classifier for NPM packages using metadata keywords and graph topology.

Implements FR-007: Mandatory fallback using dependency graph topology when
keywords are missing or noisy.
"""
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import re

# Keyword mappings for common NPM package categories
CATEGORY_KEYWORDS = {
    "framework": ["framework", "react", "vue", "angular", "svelte", "next", "nuxt", "express", "koa", "fastify"],
    "ui": ["ui", "component", "design", "style", "css", "tailwind", "bootstrap", "material", "ant"],
    "data": ["data", "json", "csv", "xml", "parser", "serializer", "query", "database", "sql", "orm", "mongoose"],
    "network": ["http", "tcp", "udp", "socket", "web", "api", "rest", "graphql", "rpc", "client", "server"],
    "security": ["security", "auth", "crypto", "encrypt", "hash", "jwt", "oauth", "permission", "acl"],
    "utility": ["util", "helper", "tool", "misc", "common", "shared", "base"],
    "testing": ["test", "mock", "stub", "fixture", "assert", "coverage", "jest", "mocha", "chai"],
    "dev-tool": ["build", "compile", "bundle", "transpile", "lint", "format", "dev", "tooling", "webpack", "vite"],
    "storage": ["storage", "cache", "redis", "memory", "disk", "file", "fs", "blob"],
    "logging": ["log", "logger", "trace", "debug", "monitor", "alert", "telemetry"],
}

# Fallback category names for graph-based classification
TOPOLOGY_CATEGORIES = [
    "core-infrastructure",
    "application-layer",
    "domain-specific",
    "utility-libraries"
]

def _normalize_keyword(keyword: str) -> str:
    """Normalize a keyword for comparison."""
    return re.sub(r'[^a-z0-9]', '', keyword.lower())

def _get_keyword_score(keywords: List[str], category: str) -> float:
    """Calculate how well keywords match a category."""
    if not keywords:
        return 0.0
    
    normalized_keywords = [_normalize_keyword(k) for k in keywords]
    category_terms = [_normalize_keyword(t) for t in CATEGORY_KEYWORDS.get(category, [])]
    
    if not category_terms:
        return 0.0
    
    matches = sum(1 for kw in normalized_keywords if any(term in kw or kw in term for term in category_terms))
    return matches / len(category_terms)

def classify_by_keywords(keywords: List[str]) -> Optional[str]:
    """
    Classify a package based on its keywords.
    
    Args:
        keywords: List of keywords from package metadata.
        
    Returns:
        Category name or None if no strong match found.
    """
    if not keywords:
        return None
    
    scores = {
        cat: _get_keyword_score(keywords, cat)
        for cat in CATEGORY_KEYWORDS
    }
    
    # Require at least 0.5 match score to be confident
    best_category = max(scores, key=scores.get)
    if scores[best_category] >= 0.5:
        return best_category
    
    return None

def _calculate_graph_metrics(dependency_graph: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Calculate basic graph metrics for topology-based classification.
    
    Args:
        dependency_graph: Dict mapping package name to list of dependencies.
        
    Returns:
        Dict with graph metrics.
    """
    if not dependency_graph:
        return {"avg_degree": 0.0, "max_degree": 0, "isolated_ratio": 1.0}
    
    degrees = [len(deps) for deps in dependency_graph.values()]
    total_nodes = len(dependency_graph)
    
    # Count isolated nodes (no dependencies)
    isolated = sum(1 for d in degrees if d == 0)
    
    return {
        "avg_degree": sum(degrees) / len(degrees) if degrees else 0.0,
        "max_degree": max(degrees) if degrees else 0,
        "isolated_ratio": isolated / total_nodes if total_nodes > 0 else 1.0,
        "total_edges": sum(degrees)
    }

def _classify_by_topology(graph_metrics: Dict[str, float], package_name: str, 
                          dependency_graph: Dict[str, List[str]]) -> str:
    """
    Classify a package based on dependency graph topology.
    
    This is the mandatory fallback when keyword classification fails.
    
    Args:
        graph_metrics: Pre-calculated graph metrics.
        package_name: The name of the package to classify.
        dependency_graph: The full dependency graph.
        
    Returns:
        One of the TOPOLOGY_CATEGORIES.
    """
    if not dependency_graph:
        return "utility-libraries"
    
    deps = dependency_graph.get(package_name, [])
    degree = len(deps)
    
    # Calculate in-degree (how many packages depend on this one)
    in_degree = sum(1 for d in dependency_graph.values() if package_name in d)
    
    # Classification logic based on topology
    if degree == 0 and in_degree == 0:
        # Isolated package
        return "utility-libraries"
    elif degree > 10 or in_degree > 20:
        # Highly connected - likely core infrastructure
        return "core-infrastructure"
    elif degree > 5 or in_degree > 10:
        # Moderately connected - application layer
        return "application-layer"
    elif degree > 0 and in_degree == 0:
        # Depends on others but no one depends on it - domain specific
        return "domain-specific"
    else:
        # Default fallback
        return "utility-libraries"

def classify_package(package_data: Dict[str, Any], 
                    dependency_graph: Optional[Dict[str, List[str]]] = None) -> str:
    """
    Classify a package using keywords first, then topology fallback.
    
    Implements FR-007: Mandatory fallback using dependency graph topology.
    
    Args:
        package_data: Dict containing package metadata including 'keywords'.
        dependency_graph: Optional full dependency graph for topology analysis.
        
    Returns:
        Category string.
    """
    keywords = package_data.get("keywords", [])
    package_name = package_data.get("name", "unknown")
    
    # Try keyword-based classification first
    category = classify_by_keywords(keywords)
    
    if category:
        return category
    
    # Fallback to topology-based classification
    if dependency_graph is not None:
        # Ensure the package exists in the graph
        if package_name not in dependency_graph:
            dependency_graph[package_name] = package_data.get("dependencies", [])
        
        graph_metrics = _calculate_graph_metrics(dependency_graph)
        category = _classify_by_topology(graph_metrics, package_name, dependency_graph)
    else:
        # Ultimate fallback if no graph data available
        category = "utility-libraries"
    
    return category

def classify_batch(packages: List[Dict[str, Any]], 
                  dependency_graph: Optional[Dict[str, List[str]]] = None) -> List[Dict[str, str]]:
    """
    Classify multiple packages.
    
    Args:
        packages: List of package metadata dicts.
        dependency_graph: Optional full dependency graph.
        
    Returns:
        List of dicts with package name and assigned category.
    """
    results = []
    for pkg in packages:
        name = pkg.get("name", "unknown")
        category = classify_package(pkg, dependency_graph)
        results.append({
            "name": name,
            "category": category
        })
    return results

def build_dependency_graph(packages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Build a dependency graph from a list of packages.
    
    Args:
        packages: List of package metadata dicts with 'dependencies' field.
        
    Returns:
        Dict mapping package name to list of dependency names.
    """
    graph = {}
    for pkg in packages:
        name = pkg.get("name", "unknown")
        deps = pkg.get("dependencies", [])
        # Extract just the package names from dependency specs
        if isinstance(deps, dict):
            deps = list(deps.keys())
        graph[name] = deps
    return graph

def get_category_distribution(packages: List[Dict[str, Any]], 
                             dependency_graph: Optional[Dict[str, List[str]]] = None) -> Dict[str, int]:
    """
    Get the distribution of categories across packages.
    
    Args:
        packages: List of package metadata dicts.
        dependency_graph: Optional full dependency graph.
        
    Returns:
        Dict mapping category to count.
    """
    distribution = Counter()
    for pkg in packages:
        category = classify_package(pkg, dependency_graph)
        distribution[category] += 1
    return dict(distribution)
