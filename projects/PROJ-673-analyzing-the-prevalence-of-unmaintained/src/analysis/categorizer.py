"""
Package categorization module for analyzing unmaintained dependencies.

Implements keyword-based classification with a mandatory fallback to
dependency graph topology analysis when keywords are missing or noisy.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import re

# Keyword mappings for category classification
CATEGORY_KEYWORDS = {
    'framework': ['framework', 'react', 'vue', 'angular', 'svelte', 'next', 'nuxt', 'ember', 'meteor'],
    'data': ['data', 'database', 'db', 'sql', 'nosql', 'redis', 'mongo', 'postgres', 'mysql'],
    'utility': ['util', 'utility', 'helper', 'tool', 'tools', 'common', 'shared'],
    'testing': ['test', 'jest', 'mocha', 'chai', 'cypress', 'playwright', 'vitest', 'ava', 'tape'],
    'build': ['build', 'webpack', 'vite', 'rollup', 'esbuild', 'parcel', 'babel', 'typescript', 'eslint', 'prettier'],
    'security': ['security', 'auth', 'authentication', 'authorization', 'crypto', 'encryption', 'jwt', 'oauth'],
    'networking': ['http', 'fetch', 'axios', 'socket', 'websocket', 'rpc', 'grpc', 'rest', 'api'],
    'ui': ['ui', 'component', 'design', 'style', 'css', 'tailwind', 'bootstrap', 'material', 'icon'],
    'cli': ['cli', 'command', 'terminal', 'shell', 'node', 'bin'],
    'devops': ['docker', 'kubernetes', 'ci', 'cd', 'deploy', 'pipeline', 'aws', 'azure', 'gcp']
}

# Topology-based heuristics
DEGREE_THRESHOLDS = {
    'framework': 15,      # High in-degree (many depend on it)
    'utility': 8,         # Moderate in-degree
    'data': 10,           # Moderate-high in-degree
    'security': 12,       # High importance, moderate in-degree
    'build': 6,           # Moderate in-degree
    'testing': 7,         # Moderate in-degree
    'networking': 9,      # Moderate-high in-degree
    'ui': 5,              # Variable in-degree
    'cli': 3,             # Lower in-degree
    'devops': 4           # Lower in-degree
}

def build_dependency_graph(dependencies: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build a dependency graph structure from the list of dependencies.
    
    Args:
        dependencies: List of dependency dictionaries with at least 'name' key
    
    Returns:
        Dictionary mapping package names to their graph metrics
    """
    graph = {}
    
    # Initialize all nodes
    for dep in dependencies:
        name = dep.get('name', '')
        if name and name not in graph:
            graph[name] = {
                'in_degree': 0,
                'out_degree': 0,
                'dependents': [],
                'dependencies': dep.get('dependencies', [])
            }
    
    # Calculate edges
    for dep in dependencies:
        name = dep.get('name', '')
        deps = dep.get('dependencies', [])
        
        if name in graph:
            graph[name]['out_degree'] = len(deps)
            for dependent in deps:
                if dependent in graph:
                    graph[dependent]['in_degree'] += 1
                    graph[dependent]['dependents'].append(name)
    
    return graph

def classify_by_keywords(name: str, keywords: Optional[List[str]] = None) -> Optional[str]:
    """
    Classify a package based on its name and associated keywords.
    
    Args:
        name: Package name
        keywords: Optional list of keywords from package metadata
    
    Returns:
        Category string or None if no match found
    """
    # Normalize inputs
    search_terms = [name.lower()]
    if keywords:
        search_terms.extend([k.lower() for k in keywords if isinstance(k, str)])
    
    search_text = ' '.join(search_terms)
    
    # Score each category
    best_category = None
    best_score = 0
    
    for category, category_keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in category_keywords:
            if keyword in search_text:
                score += 1
                # Boost for exact matches in name
                if keyword in name.lower():
                    score += 2
        
        if score > best_score:
            best_score = score
            best_category = category
    
    # Only return if we have a meaningful match
    return best_category if best_score >= 2 else None

def classify_by_topology(package_name: str, graph: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """
    Classify a package based on its position in the dependency graph.
    
    Args:
        package_name: Name of the package to classify
        graph: Dependency graph from build_dependency_graph()
    
    Returns:
        Category string or None if topology doesn't provide clear classification
    """
    if package_name not in graph:
        return None
    
    node = graph[package_name]
    in_degree = node['in_degree']
    out_degree = node['out_degree']
    
    # Calculate a "centrality" score
    # High in-degree suggests foundational packages (frameworks, utilities)
    # High out-degree suggests application-level packages
    
    # Heuristic scoring
    scores = {}
    for category, threshold in DEGREE_THRESHOLDS.items():
        if in_degree >= threshold:
            scores[category] = (in_degree - threshold) / max(threshold, 1)
    
    if not scores:
        return None
    
    # Return category with highest score
    return max(scores, key=scores.get)

def classify_package(package: Dict[str, Any], graph: Optional[Dict[str, Dict[str, Any]]] = None) -> str:
    """
    Classify a single package using keywords first, then topology fallback.
    
    Args:
        package: Package dictionary with 'name' and optionally 'keywords'
        graph: Optional dependency graph for topology-based fallback
    
    Returns:
        Category string (never None, falls back to 'uncategorized')
    """
    name = package.get('name', '')
    keywords = package.get('keywords', [])
    
    # Try keyword classification first
    category = classify_by_keywords(name, keywords)
    
    # If keywords failed and we have a graph, try topology
    if category is None and graph is not None:
        category = classify_by_topology(name, graph)
    
    # Final fallback
    if category is None:
        category = 'uncategorized'
    
    return category

def classify_batch(
    dependencies: List[Dict[str, Any]],
    use_topology: bool = True
) -> List[Dict[str, Any]]:
    """
    Classify a batch of packages with optional topology-based fallback.
    
    Args:
        dependencies: List of package dictionaries
        use_topology: Whether to use graph topology as fallback
    
    Returns:
        List of dictionaries with added 'category' field
    """
    graph = None
    if use_topology:
        graph = build_dependency_graph(dependencies)
    
    results = []
    for dep in dependencies:
        classified = dep.copy()
        classified['category'] = classify_package(dep, graph)
        results.append(classified)
    
    return results

def get_category_distribution(dependencies: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get the distribution of categories in a list of dependencies.
    
    Args:
        dependencies: List of classified package dictionaries
    
    Returns:
        Dictionary mapping category names to counts
    """
    categories = [dep.get('category', 'uncategorized') for dep in dependencies]
    return dict(Counter(categories))

def build_dependency_graph_from_resolved(resolved_deps: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build dependency graph from resolved dependency data (from T015).
    
    This function extracts the dependency structure from the resolved
    dependency tree and builds a graph for topology-based classification.
    
    Args:
        resolved_deps: List of resolved dependencies with 'dependencies' field
    
    Returns:
        Dependency graph structure
    """
    return build_dependency_graph(resolved_deps)