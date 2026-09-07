"""
Validate dependency graphs by performing topological sort and cycle detection.

This module provides utilities to:
1. Detect cycles in directed dependency graphs
2. Perform topological sorting of acyclic graphs
3. Validate that dependency graphs from the synthetic dataset are acyclic

Usage:
    python code/data/validate_dependencies.py
    
This script reads dependency graphs from data/processed/dependency_graphs.json
(if it exists) and validates them. It outputs validation results to
data/artifacts/validation_results.json.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.common import (
    get_logger,
    ValidationError,
    read_json,
    write_json,
    ensure_dir,
)

logger = get_logger(__name__)


def detect_cycle(graph: Dict[str, List[str]]) -> Tuple[bool, Optional[List[str]]]:
    """
    Detect if a directed graph contains a cycle using DFS.
    
    Args:
        graph: Dictionary mapping node IDs to lists of dependent node IDs.
               Example: {"A": ["B", "C"], "B": ["C"], "C": []}
    
    Returns:
        Tuple of (has_cycle, cycle_path)
        - has_cycle: True if a cycle exists
        - cycle_path: List of node IDs forming the cycle (if detected), None otherwise
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {node: WHITE for node in graph}
    parent: Dict[str, Optional[str]] = {node: None for node in graph}
    
    def dfs(node: str, path: List[str]) -> Optional[List[str]]:
        color[node] = GRAY
        
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                # Neighbor not in graph keys, skip or treat as leaf
                continue
                
            if color[neighbor] == GRAY:
                # Found a back edge - cycle detected
                cycle_start_idx = path.index(neighbor) if neighbor in path else -1
                if cycle_start_idx >= 0:
                    return path[cycle_start_idx:] + [neighbor]
                return path + [neighbor]
                
            if color[neighbor] == WHITE:
                parent[neighbor] = node
                result = dfs(neighbor, path + [neighbor])
                if result is not None:
                    return result
        
        color[node] = BLACK
        return None
    
    for node in graph:
        if color[node] == WHITE:
            cycle = dfs(node, [node])
            if cycle is not None:
                return True, cycle
    
    return False, None


def topological_sort(graph: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
    """
    Perform topological sort on a directed acyclic graph (DAG).
    
    Uses Kahn's algorithm for topological sorting.
    
    Args:
        graph: Dictionary mapping node IDs to lists of dependent node IDs.
               Example: {"A": ["B", "C"], "B": ["C"], "C": []}
    
    Returns:
        Tuple of (success, sorted_nodes)
        - success: True if sort succeeded (graph is acyclic)
        - sorted_nodes: List of node IDs in topological order, or partial order if cycle detected
    """
    # Calculate in-degrees
    all_nodes = set(graph.keys())
    for deps in graph.values():
        all_nodes.update(deps)
    
    in_degree: Dict[str, int] = {node: 0 for node in all_nodes}
    
    for node, deps in graph.items():
        for dep in deps:
            if dep in in_degree:
                in_degree[dep] += 1
    
    # Initialize queue with nodes having zero in-degree
    queue = [node for node, degree in in_degree.items() if degree == 0]
    result: List[str] = []
    
    while queue:
        node = queue.pop(0)
        result.append(node)
        
        for dependent in graph.get(node, []):
            if dependent in in_degree:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
    
    # Check if all nodes were processed
    if len(result) != len(all_nodes):
        return False, result
    
    return True, result


def validate_graph(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single dependency graph.
    
    Args:
        graph_data: Dictionary containing graph information.
                   Expected keys: 'id', 'nodes', 'edges' or 'graph'
    
    Returns:
        Dictionary with validation results
    """
    graph_id = graph_data.get('id', 'unknown')
    
    # Extract graph structure
    if 'graph' in graph_data:
        graph = graph_data['graph']
    elif 'nodes' in graph_data and 'edges' in graph_data:
        # Convert nodes/edges format to adjacency list
        graph: Dict[str, List[str]] = {}
        for node in graph_data.get('nodes', []):
            graph[node] = []
        for edge in graph_data.get('edges', []):
            src = edge.get('source')
            dst = edge.get('target')
            if src and dst:
                if src not in graph:
                    graph[src] = []
                graph[src].append(dst)
    else:
        raise ValidationError(f"Invalid graph format for id {graph_id}")
    
    # Detect cycles
    has_cycle, cycle_path = detect_cycle(graph)
    
    if has_cycle:
        return {
            'id': graph_id,
            'valid': False,
            'has_cycle': True,
            'cycle_path': cycle_path,
            'topological_sort_success': False,
            'topological_order': [],
            'error': f"Cycle detected: {' -> '.join(cycle_path)}"
        }
    
    # Perform topological sort
    sort_success, sorted_nodes = topological_sort(graph)
    
    return {
        'id': graph_id,
        'valid': sort_success,
        'has_cycle': False,
        'cycle_path': None,
        'topological_sort_success': sort_success,
        'topological_order': sorted_nodes,
        'node_count': len(graph),
        'edge_count': sum(len(deps) for deps in graph.values())
    }


def validate_all_graphs(graphs_file: Path) -> Dict[str, Any]:
    """
    Validate all dependency graphs from a JSON file.
    
    Args:
        graphs_file: Path to JSON file containing dependency graphs
    
    Returns:
        Dictionary with overall validation results
    """
    logger.info(f"Loading dependency graphs from {graphs_file}")
    
    if not graphs_file.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_file}")
    
    try:
        data = read_json(graphs_file)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {graphs_file}: {e}")
    
    # Handle both single graph and list of graphs
    if isinstance(data, dict):
        graphs = [data]
    elif isinstance(data, list):
        graphs = data
    else:
        raise ValidationError(f"Expected dict or list, got {type(data)}")
    
    results = []
    valid_count = 0
    invalid_count = 0
    total_graphs = len(graphs)
    
    for i, graph_data in enumerate(graphs):
        try:
            result = validate_graph(graph_data)
            results.append(result)
            
            if result['valid']:
                valid_count += 1
            else:
                invalid_count += 1
                logger.warning(f"Graph {result['id']} is invalid: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error validating graph {i}: {e}")
            results.append({
                'id': graph_data.get('id', f'unknown_{i}'),
                'valid': False,
                'error': str(e),
                'exception_type': type(e).__name__
            })
            invalid_count += 1
    
    summary = {
        'total_graphs': total_graphs,
        'valid_graphs': valid_count,
        'invalid_graphs': invalid_count,
        'validation_rate': valid_count / total_graphs if total_graphs > 0 else 0.0,
        'all_valid': invalid_count == 0
    }
    
    return {
        'summary': summary,
        'results': results
    }


def main():
    """Main entry point for dependency validation."""
    logger.info("Starting dependency graph validation")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    graphs_file = project_root / "data" / "processed" / "dependency_graphs.json"
    output_dir = project_root / "data" / "artifacts"
    output_file = output_dir / "validation_results.json"
    
    # Ensure output directory exists
    ensure_dir(output_dir)
    
    try:
        # Validate graphs
        validation_results = validate_all_graphs(graphs_file)
        
        # Write results
        write_json(output_file, validation_results)
        
        # Log summary
        summary = validation_results['summary']
        logger.info(f"Validation complete: {summary['valid_graphs']}/{summary['total_graphs']} graphs valid")
        logger.info(f"Validation rate: {summary['validation_rate']:.2%}")
        
        if not summary['all_valid']:
            logger.warning(f"{summary['invalid_graphs']} graphs failed validation")
            logger.warning(f"Results written to {output_file}")
            sys.exit(1)
        
        logger.info("All dependency graphs are valid (acyclic)")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.info("No graphs file found. This is expected if the dataset hasn't been generated yet.")
        # Write empty results
        empty_results = {
            'summary': {
                'total_graphs': 0,
                'valid_graphs': 0,
                'invalid_graphs': 0,
                'validation_rate': 0.0,
                'all_valid': True
            },
            'results': [],
            'note': 'No graphs file found - validation skipped'
        }
        write_json(output_file, empty_results)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
