import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

import networkx as nx

# Add project root to path to allow imports from utils
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.metrics import (
    calculate_assortativity,
    calculate_average_path_length,
    calculate_clustering_coefficient,
    calculate_structural_metrics
)
from utils.checksums import calculate_sha256


def load_network_from_file(file_path: str) -> nx.Graph:
    """
    Load a NetworkX graph from a GraphML file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Network file not found: {file_path}")
    
    # Determine file type based on extension
    if path.suffix.lower() == '.graphml':
        return nx.read_graphml(str(path))
    elif path.suffix.lower() == '.gml':
        return nx.read_gml(str(path))
    elif path.suffix.lower() == '.gpickle':
        return nx.read_gpickle(str(path))
    else:
        # Try GraphML by default as it's the most common for this project
        try:
            return nx.read_graphml(str(path))
        except Exception:
            raise ValueError(f"Unsupported file format: {path.suffix}. Supported: .graphml, .gml, .gpickle")


def calculate_metrics_for_network(graph: nx.Graph, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate structural metrics for a single network instance.
    
    Returns a dictionary containing:
    - seed: The random seed used to generate the network
    - topology: The type of network (er, ba, ws)
    - n_nodes: Number of nodes
    - n_edges: Number of edges
    - density: Graph density
    - assortativity: Degree assortativity coefficient
    - average_path_length: Average shortest path length (or -1 if disconnected)
    - clustering_coefficient: Global clustering coefficient
    - is_connected: Boolean indicating if the graph is connected
    - largest_component_ratio: Ratio of nodes in the largest connected component
    """
    metrics = {
        "seed": seed,
        "n_nodes": graph.number_of_nodes(),
        "n_edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "is_connected": nx.is_connected(graph) if graph.number_of_nodes() > 0 else False
    }
    
    # Add assortativity
    try:
        metrics["assortativity"] = calculate_assortativity(graph)
    except Exception as e:
        metrics["assortativity"] = None
        metrics["assortativity_error"] = str(e)
    
    # Add average path length (handle disconnected graphs)
    try:
        if metrics["is_connected"]:
            metrics["average_path_length"] = calculate_average_path_length(graph)
        else:
            # For disconnected graphs, calculate for the largest connected component
            largest_cc = max(nx.connected_components(graph), key=len)
            subgraph = graph.subgraph(largest_cc)
            metrics["average_path_length"] = calculate_average_path_length(subgraph)
            metrics["largest_component_ratio"] = len(largest_cc) / graph.number_of_nodes()
    except Exception as e:
        metrics["average_path_length"] = None
        metrics["average_path_length_error"] = str(e)
    
    # Add clustering coefficient
    try:
        metrics["clustering_coefficient"] = calculate_clustering_coefficient(graph)
    except Exception as e:
        metrics["clustering_coefficient"] = None
        metrics["clustering_error"] = str(e)
    
    # Add full structural metrics dict if available
    try:
        full_metrics = calculate_structural_metrics(graph)
        metrics.update(full_metrics)
    except Exception:
        pass  # We already have individual metrics, this is just a fallback
    
    return metrics


def process_single_network(input_path: str, output_dir: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Process a single network file: calculate metrics and save to JSON.
    
    Args:
        input_path: Path to the input network file (GraphML, GML, etc.)
        output_dir: Directory to save the metrics JSON file
        seed: Optional seed to record in the metrics (if not in filename)
    
    Returns:
        Dictionary containing the metrics and output path
    """
    # Load the network
    graph = load_network_from_file(input_path)
    
    # Extract seed from filename if not provided
    if seed is None:
        filename = Path(input_path).stem
        # Try to extract seed from filename pattern like "network_seed_123.graphml"
        parts = filename.split('_')
        for i, part in enumerate(parts):
            if part == 'seed' and i + 1 < len(parts):
                try:
                    seed = int(parts[i + 1])
                    break
                except ValueError:
                    pass
        # If still no seed, use a placeholder
        if seed is None:
            seed = -1
    
    # Determine topology from filename if possible
    topology = "unknown"
    filename = Path(input_path).stem.lower()
    if "er" in filename or "erdos" in filename:
        topology = "erdos_renyi"
    elif "ba" in filename or "barabasi" in filename:
        topology = "barabasi_albert"
    elif "ws" in filename or "watts" in filename:
        topology = "watts_strogatz"
    
    # Calculate metrics
    metrics = calculate_metrics_for_network(graph, seed)
    metrics["topology"] = topology
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save metrics to JSON
    output_file = output_path / f"metrics_{seed}.json"
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Generate checksum for the metrics file
    checksum = calculate_sha256(str(output_file))
    metrics["checksum"] = checksum
    
    # Update the saved file with checksum
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return {
        "seed": seed,
        "topology": topology,
        "input_file": input_path,
        "output_file": str(output_file),
        "checksum": checksum,
        "metrics": metrics
    }


def process_networks_directory(networks_dir: str, output_dir: str, topology_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Process all network files in a directory, calculate metrics, and save to JSON.
    
    Args:
        networks_dir: Directory containing network files
        output_dir: Directory to save metrics JSON files
        topology_filter: Optional filter for topology type (e.g., 'erdos_renyi')
    
    Returns:
        List of dictionaries containing processing results for each network
    """
    results = []
    networks_path = Path(networks_dir)
    
    if not networks_path.exists():
        raise FileNotFoundError(f"Networks directory not found: {networks_dir}")
    
    # Find all network files
    network_files = list(networks_path.glob("*.graphml")) + \
                   list(networks_path.glob("*.gml")) + \
                   list(networks_path.glob("*.gpickle"))
    
    for network_file in network_files:
        try:
            # Extract seed from filename
            filename = network_file.stem
            seed = None
            parts = filename.split('_')
            for i, part in enumerate(parts):
                if part == 'seed' and i + 1 < len(parts):
                    try:
                        seed = int(parts[i + 1])
                        break
                    except ValueError:
                        pass
            
            # Determine topology
            topology = "unknown"
            filename_lower = filename.lower()
            if "er" in filename_lower or "erdos" in filename_lower:
                topology = "erdos_renyi"
            elif "ba" in filename_lower or "barabasi" in filename_lower:
                topology = "barabasi_albert"
            elif "ws" in filename_lower or "watts" in filename_lower:
                topology = "watts_strogatz"
            
            # Apply topology filter if specified
            if topology_filter and topology != topology_filter:
                continue
            
            # Process the network
            result = process_single_network(str(network_file), output_dir, seed)
            results.append(result)
            
        except Exception as e:
            print(f"Error processing {network_file}: {e}", file=sys.stderr)
            results.append({
                "seed": None,
                "topology": "unknown",
                "input_file": str(network_file),
                "error": str(e)
            })
    
    return results


def main():
    """
    Main entry point for the network metrics calculation script.
    """
    parser = argparse.ArgumentParser(description="Calculate and store structural metrics for generated networks")
    parser.add_argument("--networks-dir", type=str, default="data/raw/networks",
                      help="Directory containing network files (default: data/raw/networks)")
    parser.add_argument("--output-dir", type=str, default="data/raw/networks",
                      help="Directory to save metrics JSON files (default: data/raw/networks)")
    parser.add_argument("--topology", type=str, choices=["erdos_renyi", "barabasi_albert", "watts_strogatz"],
                      help="Filter by topology type")
    parser.add_argument("--single", type=str, help="Process a single network file instead of a directory")
    parser.add_argument("--seed", type=int, help="Seed value for single file processing")
    
    args = parser.parse_args()
    
    if args.single:
        # Process a single file
        result = process_single_network(args.single, args.output_dir, args.seed)
        print(f"Processed single network: {result['output_file']}")
        print(f"Metrics: {json.dumps(result['metrics'], indent=2)}")
    else:
        # Process directory
        results = process_networks_directory(args.networks_dir, args.output_dir, args.topology)
        
        print(f"Processed {len(results)} networks")
        for result in results:
            if "error" in result:
                print(f"  ERROR: {result['input_file']} - {result['error']}")
            else:
                print(f"  OK: {result['output_file']} (seed={result['seed']}, topology={result['topology']})")
        
        # Save summary
        summary_file = Path(args.output_dir) / "metrics_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Summary saved to: {summary_file}")


if __name__ == "__main__":
    main()