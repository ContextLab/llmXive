import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional
import networkx as nx

from config import RANDOM_SEED
from metrics import MetricsLogger
from graph_builder import SymbolicGraphBuilder, GraphNode, GraphEdge

# Constants for validation
DEFAULT_GROUND_TRUTH_PATH = "data/schemas/ground_truth_mapping.json"
DEFAULT_OUTPUT_PATH = "data/results/reconstruction_error.json"
METRICS_LOG_PATH = "data/results/metrics_log.json"

def load_ground_truth(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the ground truth schema mapping from the specified JSON file.
    
    Args:
        path: Path to the ground truth JSON file. Defaults to DEFAULT_GROUND_TRUTH_PATH.
        
    Returns:
        Dictionary containing 'nodes', 'edges', and 'predicates' keys.
        
    Raises:
        FileNotFoundError: If the ground truth file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if path is None:
        path = DEFAULT_GROUND_TRUTH_PATH
        
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Validate structure
    required_keys = {'nodes', 'edges', 'predicates'}
    if not required_keys.issubset(data.keys()):
        missing = required_keys - set(data.keys())
        raise ValueError(f"Ground truth file missing required keys: {missing}")
        
    return data

def calculate_reconstruction_error(
    constructed_graph: nx.DiGraph,
    ground_truth: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate reconstruction error by comparing constructed graph against ground truth.
    
    Args:
        constructed_graph: The networkx DiGraph built from traces.
        ground_truth: The ground truth mapping dictionary.
        
    Returns:
        Dictionary containing error metrics:
            - 'node_error_rate': float (0.0 to 1.0)
            - 'edge_error_rate': float (0.0 to 1.0)
            - 'predicate_error_rate': float (0.0 to 1.0)
            - 'total_nodes_constructed': int
            - 'total_nodes_ground_truth': int
            - 'total_edges_constructed': int
            - 'total_edges_ground_truth': int
            - 'mismatched_nodes': list of node details
            - 'mismatched_edges': list of edge details
    """
    # Extract ground truth sets
    gt_nodes = set(ground_truth['nodes'])
    gt_edges = set()
    for edge in ground_truth['edges']:
        gt_edges.add((edge['source'], edge['target'], edge['predicate']))
    gt_predicates = set(ground_truth['predicates'])
    
    # Extract constructed graph sets
    constructed_nodes = set(constructed_graph.nodes())
    constructed_edges = set()
    for u, v, data in constructed_graph.edges(data=True):
        pred = data.get('predicate', 'unknown')
        constructed_edges.add((u, v, pred))
    constructed_predicates = set(data.get('predicate', 'unknown') for _, _, data in constructed_graph.edges(data=True))
    
    # Calculate node errors
    missing_nodes = gt_nodes - constructed_nodes
    extra_nodes = constructed_nodes - gt_nodes
    node_error_count = len(missing_nodes) + len(extra_nodes)
    node_error_rate = node_error_count / max(len(gt_nodes), 1)
    
    # Calculate edge errors
    missing_edges = gt_edges - constructed_edges
    extra_edges = constructed_edges - gt_edges
    edge_error_count = len(missing_edges) + len(extra_edges)
    edge_error_rate = edge_error_count / max(len(gt_edges), 1)
    
    # Calculate predicate errors (edges with wrong predicates)
    # An edge exists in both but with different predicate
    common_edges = gt_edges & constructed_edges
    common_edges_by_location = {}
    for u, v, pred in common_edges:
        key = (u, v)
        if key not in common_edges_by_location:
            common_edges_by_location[key] = {'gt': pred, 'constructed': pred}
        else:
            # If there are multiple edges between same nodes with different predicates, 
            # we need to handle that. For simplicity, we assume single edge per pair or 
            # we count distinct predicates.
            pass
    
    # Better approach: check edges that exist in both but have different predicates
    predicate_mismatches = 0
    total_common_edges = 0
    for u, v, gt_pred in gt_edges:
        # Find if this edge exists in constructed with a different predicate
        matching_constructed = [c_pred for (cu, cv, c_pred) in constructed_edges if cu == u and cv == v]
        if matching_constructed:
            total_common_edges += 1
            # Check if any of the constructed predicates match the ground truth
            if gt_pred not in matching_constructed:
                predicate_mismatches += 1
    
    predicate_error_rate = predicate_mismatches / max(total_common_edges, 1) if total_common_edges > 0 else 0.0
    
    # Compile detailed mismatches
    mismatched_nodes = {
        'missing_in_constructed': list(missing_nodes),
        'extra_in_constructed': list(extra_nodes)
    }
    
    mismatched_edges = []
    for edge in missing_edges:
        mismatched_edges.append({
            'source': edge[0],
            'target': edge[1],
            'predicate': edge[2],
            'status': 'missing_in_constructed'
        })
    for edge in extra_edges:
        mismatched_edges.append({
            'source': edge[0],
            'target': edge[1],
            'predicate': edge[2],
            'status': 'extra_in_constructed'
        })
    
    return {
        'node_error_rate': round(node_error_rate, 6),
        'edge_error_rate': round(edge_error_rate, 6),
        'predicate_error_rate': round(predicate_error_rate, 6),
        'total_nodes_constructed': len(constructed_nodes),
        'total_nodes_ground_truth': len(gt_nodes),
        'total_edges_constructed': len(constructed_edges),
        'total_edges_ground_truth': len(gt_edges),
        'mismatched_nodes': mismatched_nodes,
        'mismatched_edges': mismatched_edges,
        'seed_used': RANDOM_SEED
    }

def validate_graph_from_files(
    graph_file_path: str,
    ground_truth_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load a constructed graph from a JSON file, compare it against ground truth,
    and save the reconstruction error metrics.
    
    Args:
        graph_file_path: Path to the JSON file containing the constructed graph.
        ground_truth_path: Optional path to ground truth JSON. Defaults to DEFAULT_GROUND_TRUTH_PATH.
        output_path: Optional path to save results. Defaults to DEFAULT_OUTPUT_PATH.
        
    Returns:
        The reconstruction error metrics dictionary.
    """
    # Load ground truth
    ground_truth = load_ground_truth(ground_truth_path)
    
    # Load constructed graph from file
    graph_path = Path(graph_file_path)
    if not graph_path.exists():
        raise FileNotFoundError(f"Constructed graph file not found: {graph_path}")
        
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
        
    # Reconstruct networkx graph from JSON
    constructed_graph = nx.DiGraph()
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])
    
    for node in nodes:
        constructed_graph.add_node(node['id'], **node.get('attributes', {}))
        
    for edge in edges:
        constructed_graph.add_edge(
            edge['source'], 
            edge['target'], 
            predicate=edge.get('predicate', 'unknown'),
            **edge.get('attributes', {})
        )
        
    # Calculate error
    error_metrics = calculate_reconstruction_error(constructed_graph, ground_truth)
    
    # Save results
    if output_path is None:
        output_path = DEFAULT_OUTPUT_PATH
        
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(error_metrics, f, indent=2)
        
    # Log to metrics
    logger = MetricsLogger()
    logger.log_success(error_metrics['node_error_rate'] == 0.0 and error_metrics['edge_error_rate'] == 0.0)
    logger.save_report(str(output_file.parent / "metrics_log.json"))
    
    return error_metrics

def main():
    """
    Main entry point for the validator script.
    
    Usage:
        python code/validator.py [--graph-file <path>] [--ground-truth <path>] [--output <path>]
        
    Defaults:
        --graph-file: data/results/constructed_graph.json (or first found graph file in data/processed/)
        --ground-truth: data/schemas/ground_truth_mapping.json
        --output: data/results/reconstruction_error.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate constructed graph against ground truth')
    parser.add_argument('--graph-file', type=str, help='Path to constructed graph JSON file')
    parser.add_argument('--ground-truth', type=str, default=DEFAULT_GROUND_TRUTH_PATH, 
                      help='Path to ground truth JSON file')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_PATH,
                      help='Path to save reconstruction error results')
                      
    args = parser.parse_args()
    
    # If no graph file specified, try to find one
    graph_file = args.graph_file
    if graph_file is None:
        # Look in data/processed/ for graph files
        processed_dir = Path('data/processed')
        if processed_dir.exists():
            graph_files = list(processed_dir.glob('*.json'))
            if graph_files:
                graph_file = str(graph_files[0])
                print(f"No graph file specified, using first found: {graph_file}")
            else:
                raise FileNotFoundError(
                    "No graph file specified and no graph files found in data/processed/. "
                    "Please specify --graph-file or ensure a graph file exists."
                )
        else:
            raise FileNotFoundError(
                "No graph file specified and data/processed/ directory does not exist. "
                "Please specify --graph-file."
            )
    
    try:
        print(f"Loading ground truth from: {args.ground_truth}")
        print(f"Validating graph from: {graph_file}")
        print(f"Saving results to: {args.output}")
        
        metrics = validate_graph_from_files(graph_file, args.ground_truth, args.output)
        
        print("\n=== Reconstruction Error Metrics ===")
        print(f"Node Error Rate: {metrics['node_error_rate']:.4f}")
        print(f"Edge Error Rate: {metrics['edge_error_rate']:.4f}")
        print(f"Predicate Error Rate: {metrics['predicate_error_rate']:.4f}")
        print(f"Total Nodes (Constructed): {metrics['total_nodes_constructed']}")
        print(f"Total Nodes (Ground Truth): {metrics['total_nodes_ground_truth']}")
        print(f"Total Edges (Constructed): {metrics['total_edges_constructed']}")
        print(f"Total Edges (Ground Truth): {metrics['total_edges_ground_truth']}")
        print(f"\nResults saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"Validation failed: {str(e)}", file=sys.stderr)
        raise

if __name__ == "__main__":
    sys.exit(main())
