"""
Category classifier for NPM packages.

Classifies packages based on metadata keywords with a mandatory fallback
to dependency graph topology (centrality metrics) when keywords are missing or noisy.

Implements FR-007: MANDATORY FALLBACK to topology classification.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import re
import networkx as nx
import logging

logger = logging.getLogger(__name__)

# Keyword mappings for category classification
KEYWORD_CATEGORIES = {
    'framework': ['framework', 'lib', 'library', 'sdk', 'kit'],
    'data': ['data', 'database', 'db', 'orm', 'query', 'store', 'cache'],
    'utility': ['util', 'utility', 'helper', 'tool', 'tools', 'common'],
    'security': ['security', 'auth', 'crypto', 'encrypt', 'decrypt', 'password', 'oauth'],
    'ui': ['ui', 'user interface', 'component', 'react', 'vue', 'angular', 'dom', 'css'],
    'testing': ['test', 'testing', 'mock', 'stub', 'assertion', 'coverage'],
    'build': ['build', 'bundling', 'webpack', 'vite', 'rollup', 'esbuild', 'compile'],
    'network': ['http', 'network', 'socket', 'websockets', 'rest', 'api', 'client', 'server'],
    'devops': ['devops', 'deploy', 'ci', 'cd', 'docker', 'kubernetes', 'cloud'],
    'core': ['core', 'essential', 'foundation', 'base'],
    'infrastructure': ['infrastructure', 'infra', 'platform', 'middleware']
}

# Thresholds for topology-based classification
DEGREE_CENTRALITY_THRESHOLD = 0.8
BETWEENNESS_CENTRALITY_THRESHOLD = 0.5


def classify_by_keywords(package_data: Dict[str, Any]) -> Optional[str]:
    """
    Classify a package based on its metadata keywords.
    
    Args:
        package_data: Dictionary containing package metadata (keywords, description, name)
        
    Returns:
        Category string if a strong match is found, None otherwise
    """
    if not package_data:
        return None
        
    # Extract keywords and description
    keywords = package_data.get('keywords', []) or []
    description = package_data.get('description', '') or ''
    name = package_data.get('name', '') or ''
    
    # Combine all text for matching
    all_text = ' '.join(keywords + [description, name]).lower()
    
    # Count matches for each category
    category_scores = {}
    
    for category, category_keywords in KEYWORD_CATEGORIES.items():
        score = 0
        for kw in category_keywords:
            # Check if keyword appears in text
            if re.search(r'\b' + re.escape(kw) + r'\b', all_text):
                score += 1
        category_scores[category] = score
    
    # Find the best category
    if not category_scores:
        return None
        
    best_category = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_category]
    
    # Only return a category if we have at least one strong match
    # (at least 2 keyword matches for the category, or 1 match for high-confidence categories)
    if best_score >= 2 or (best_score == 1 and best_category in ['security', 'testing', 'devops']):
        logger.debug(f"Keyword classification: {package_data.get('name', 'unknown')} -> {best_category} (score: {best_score})")
        return best_category
        
    return None


def build_dependency_graph(dependencies: List[Dict[str, Any]]) -> nx.Graph:
    """
    Build a dependency graph from a list of dependency relationships.
    
    Args:
        dependencies: List of dicts with 'from' and 'to' package names
        
    Returns:
        NetworkX Graph object
    """
    G = nx.Graph()
    
    for dep in dependencies:
        from_pkg = dep.get('from')
        to_pkg = dep.get('to')
        
        if from_pkg and to_pkg:
            G.add_edge(from_pkg, to_pkg)
    
    logger.info(f"Built dependency graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G


def classify_by_topology(package_name: str, graph: nx.Graph) -> str:
    """
    Classify a package based on its position in the dependency graph.
    
    Uses centrality metrics as per FR-007:
    - degree_centrality > 0.8 -> 'core'
    - betweenness_centrality > 0.5 -> 'infrastructure'
    - otherwise -> 'other'
    
    Args:
        package_name: Name of the package to classify
        graph: NetworkX Graph of dependencies
        
    Returns:
        Category string based on topology
    """
    if package_name not in graph:
        logger.warning(f"Package {package_name} not found in dependency graph, defaulting to 'other'")
        return 'other'
    
    # Calculate centrality metrics
    try:
        degree_centrality = nx.degree_centrality(graph)
        betweenness_centrality = nx.betweenness_centrality(graph)
    except Exception as e:
        logger.error(f"Error calculating centrality metrics: {e}")
        return 'other'
    
    deg_cent = degree_centrality.get(package_name, 0)
    betw_cent = betweenness_centrality.get(package_name, 0)
    
    logger.debug(f"Topology metrics for {package_name}: degree={deg_cent:.4f}, betweenness={betw_cent:.4f}")
    
    # Apply thresholds
    if deg_cent > DEGREE_CENTRALITY_THRESHOLD:
        return 'core'
    elif betw_cent > BETWEENNESS_CENTRALITY_THRESHOLD:
        return 'infrastructure'
    else:
        return 'other'


def classify_package(package_data: Dict[str, Any], dependency_graph: Optional[nx.Graph] = None) -> str:
    """
    Main classification function with fallback logic.
    
    First tries keyword-based classification. If keywords are missing, noisy,
    or no strong match is found, falls back to topology-based classification
    if a dependency graph is provided.
    
    Args:
        package_data: Package metadata dictionary
        dependency_graph: Optional NetworkX graph for topology fallback
        
    Returns:
        Category string
    """
    package_name = package_data.get('name', 'unknown')
    
    # Step 1: Try keyword classification
    category = classify_by_keywords(package_data)
    
    # Step 2: Fallback to topology if keyword classification failed
    if category is None:
        if dependency_graph is not None:
            logger.info(f"Keyword classification failed for {package_name}, falling back to topology")
            category = classify_by_topology(package_name, dependency_graph)
        else:
            # No graph available, default to 'other'
            logger.warning(f"No keyword match and no dependency graph for {package_name}, defaulting to 'other'")
            category = 'other'
    
    return category


def classify_batch(packages: List[Dict[str, Any]], dependency_graph: Optional[nx.Graph] = None) -> List[Dict[str, str]]:
    """
    Classify a batch of packages.
    
    Args:
        packages: List of package metadata dictionaries
        dependency_graph: Optional NetworkX graph for topology fallback
        
    Returns:
        List of dicts with 'name' and 'category'
    """
    results = []
    for pkg in packages:
        category = classify_package(pkg, dependency_graph)
        results.append({
            'name': pkg.get('name', 'unknown'),
            'category': category
        })
    return results


def get_category_distribution(classifications: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Calculate the distribution of categories.
    
    Args:
        classifications: List of dicts with 'name' and 'category'
        
    Returns:
        Dictionary mapping category to count
    """
    counter = Counter(item['category'] for item in classifications)
    return dict(counter)