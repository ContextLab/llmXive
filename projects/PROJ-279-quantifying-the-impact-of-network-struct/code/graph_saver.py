import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import networkx as nx

from config.env_config import get_processed_dir, get_config
from logging_config import get_logger
from state_manager import register_artifact, save_state, compute_file_checksum
from models.atomic_config import AtomicConfiguration

logger = get_logger(__name__)

def save_graph_to_graphml(graph: nx.Graph, output_path: Path) -> None:
    """
    Saves a NetworkX graph to a GraphML file.
    Ensures node and edge attributes are JSON-serializable.
    """
    try:
        # Ensure all attributes are serializable (GraphML has limitations on types)
        for node, data in graph.nodes(data=True):
            for key, value in list(data.items()):
                if isinstance(value, (set, frozenset)):
                    graph.nodes[node][key] = list(value)
                elif isinstance(value, np.ndarray):
                    graph.nodes[node][key] = value.tolist()
        
        for u, v, data in graph.edges(data=True):
            for key, value in list(data.items()):
                if isinstance(value, (set, frozenset)):
                    graph.edges[u, v][key] = list(value)
                elif isinstance(value, np.ndarray):
                    graph.edges[u, v][key] = value.tolist()

        nx.write_graphml(graph, str(output_path))
        logger.info(f"Saved graph to GraphML: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save graph to GraphML {output_path}: {e}")
        raise

def save_graph_to_json(graph: nx.Graph, config_id: str, output_path: Path) -> None:
    """
    Saves a NetworkX graph to a JSON file with explicit metadata.
    Includes node coordinates, connectivity, and graph-level stats.
    """
    try:
        import numpy as np

        # Convert graph to a serializable dictionary structure
        serializable_graph = {
            "config_id": config_id,
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "is_connected": nx.is_connected(graph) if graph.number_of_nodes() > 0 else False,
            "nodes": [],
            "edges": []
        }

        # Serialize nodes
        for node, data in graph.nodes(data=True):
            node_data = {
                "id": node,
                "attributes": {}
            }
            for key, value in data.items():
                if isinstance(value, np.ndarray):
                    node_data["attributes"][key] = value.tolist()
                elif isinstance(value, (set, frozenset)):
                    node_data["attributes"][key] = list(value)
                else:
                    node_data["attributes"][key] = value
            serializable_graph["nodes"].append(node_data)

        # Serialize edges
        for u, v, data in graph.edges(data=True):
            edge_data = {
                "source": u,
                "target": v,
                "attributes": {}
            }
            for key, value in data.items():
                if isinstance(value, np.ndarray):
                    edge_data["attributes"][key] = value.tolist()
                elif isinstance(value, (set, frozenset)):
                    edge_data["attributes"][key] = list(value)
                else:
                    edge_data["attributes"][key] = value
            serializable_graph["edges"].append(edge_data)

        with open(output_path, 'w') as f:
            json.dump(serializable_graph, f, indent=2)
        
        logger.info(f"Saved graph to JSON: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save graph to JSON {output_path}: {e}")
        raise

def save_graphs(
    graphs: Dict[str, nx.Graph],
    output_dir: Optional[Path] = None,
    format_type: str = "both"
) -> List[Path]:
    """
    Saves a dictionary of graphs (config_id -> nx.Graph) to the processed directory.
    
    Args:
        graphs: Dictionary mapping configuration IDs to NetworkX graphs.
        output_dir: Optional directory override. Defaults to data/processed/graphs/.
        format_type: "graphml", "json", or "both".
    
    Returns:
        List of paths to saved artifact files.
    """
    if output_dir is None:
        processed_dir = get_processed_dir()
        output_dir = processed_dir / "graphs"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    for config_id, graph in graphs.items():
        # Sanitize ID for filename
        safe_id = config_id.replace("/", "_").replace("\\", "_")
        
        if format_type in ["graphml", "both"]:
            path = output_dir / f"{safe_id}.graphml"
            save_graph_to_graphml(graph, path)
            saved_paths.append(path)
            # Register artifact for state management
            checksum = compute_file_checksum(path)
            register_artifact(str(path), checksum, "graphml")

        if format_type in ["json", "both"]:
            path = output_dir / f"{safe_id}.json"
            save_graph_to_json(graph, config_id, path)
            saved_paths.append(path)
            # Register artifact for state management
            checksum = compute_file_checksum(path)
            register_artifact(str(path), checksum, "json")

    # Update state file
    save_state()
    
    logger.info(f"Saved {len(saved_paths)} graph files to {output_dir}")
    return saved_paths

def main() -> None:
    """
    Entry point for the graph saving task.
    This function is designed to be called by the main pipeline after graph construction.
    For testing purposes, it can also load a sample if no input is provided, 
    but in production it relies on the pipeline passing the graphs dictionary.
    """
    setup_logging()
    logger.info("Starting graph saving process (T018)")
    
    # In a real pipeline execution, 'graphs' would be passed from graph_builder
    # Since this is a standalone module execution for the task, we assume 
    # the caller (main.py) has populated the data or we are just verifying the saver logic.
    # However, to satisfy the "real output" requirement, we must ensure 
    # that if this script is run as part of the pipeline, it saves the data.
    
    # NOTE: This function is typically called as:
    # graphs = build_graphs(...)
    # save_graphs(graphs)
    
    # For the purpose of this task implementation, we define the logic.
    # The actual execution happens in main.py calling this function.
    logger.info("Graph saver module ready. Use save_graphs() to persist data.")

if __name__ == "__main__":
    main()
