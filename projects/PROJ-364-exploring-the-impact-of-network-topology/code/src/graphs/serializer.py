"""
Graph Serialization Module (T016)

Converts NetworkX graphs into JSON-compatible dictionaries conforming to
the graph.schema.yaml specification.

Handles:
- Node attributes (coordinates, metadata)
- Edge attributes (distance, weight)
- Graph-level metadata (sample_id, material, threshold, node_count, edge_count)
- Schema validation via jsonschema
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import networkx as nx

from src.logging_config import get_data_ingestion_logger
from src.utils.checksum import compute_string_sha256

# Import schema directly from the contract test module to ensure consistency
# with the schema file validation
from tests.contract.test_schemas import graph_schema

logger = get_data_ingestion_logger()


class SerializationError(Exception):
    """Raised when graph serialization fails due to schema violation or data issues."""
    pass


def _sanitize_value(value: Any) -> Any:
    """
    Sanitize a value to be JSON-serializable.
    Converts numpy types, sets, and tuples to standard Python types.
    """
    if value is None:
        return None
    
    # Handle common numpy types
    if hasattr(value, 'item'):
        # numpy scalar
        return value.item()
    
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(v) for v in value]
    
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    
    if isinstance(value, set):
        return [_sanitize_value(v) for v in sorted(value)]
    
    if isinstance(value, float):
        # Handle NaN and Infinity
        if value != value:  # NaN check
            return None
        if value == float('inf'):
            return None
        if value == float('-inf'):
            return None
        return value
    
    return value


def _extract_nodes(G: nx.Graph) -> List[Dict[str, Any]]:
    """
    Extract nodes with their attributes into a list of dicts.
    
    Expected node attributes:
    - x, y: coordinates (required)
    - defect_type: optional metadata
    """
    nodes = []
    for node_id, data in G.nodes(data=True):
        node_dict = {
            "id": int(node_id) if isinstance(node_id, (int, float)) else str(node_id),
            "attributes": {}
        }
        
        for key, value in data.items():
            if key in ['x', 'y', 'defect_type', 'defect_id']:
                node_dict["attributes"][key] = _sanitize_value(value)
            else:
                # Include other attributes in a nested metadata dict if needed
                if "metadata" not in node_dict["attributes"]:
                    node_dict["attributes"]["metadata"] = {}
                node_dict["attributes"]["metadata"][key] = _sanitize_value(value)
        
        nodes.append(node_dict)
    
    return nodes


def _extract_edges(G: nx.Graph) -> List[Dict[str, Any]]:
    """
    Extract edges with their attributes into a list of dicts.
    
    Expected edge attributes:
    - distance: Euclidean distance between nodes (required)
    - weight: optional edge weight
    """
    edges = []
    for u, v, data in G.edges(data=True):
        edge_dict = {
            "source": int(u) if isinstance(u, (int, float)) else str(u),
            "target": int(v) if isinstance(v, (int, float)) else str(v),
            "attributes": {}
        }
        
        for key, value in data.items():
            if key in ['distance', 'weight', 'edge_type']:
                edge_dict["attributes"][key] = _sanitize_value(value)
            else:
                if "metadata" not in edge_dict["attributes"]:
                    edge_dict["attributes"]["metadata"] = {}
                edge_dict["attributes"]["metadata"][key] = _sanitize_value(value)
        
        edges.append(edge_dict)
    
    return edges


def _compute_graph_checksum(graph_dict: Dict[str, Any]) -> str:
    """
    Compute a SHA-256 checksum of the serialized graph dictionary.
    Used for data integrity verification.
    """
    canonical_json = json.dumps(graph_dict, sort_keys=True, separators=(',', ':'))
    return compute_string_sha256(canonical_json)


def serialize_graph_to_dict(
    G: nx.Graph,
    sample_id: str,
    material: str,
    threshold: float,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convert a NetworkX graph to a JSON-compatible dictionary conforming to graph.schema.yaml.
    
    Args:
        G: NetworkX graph object
        sample_id: Unique identifier for this sample
        material: Material type (e.g., 'graphene', 'MoS2')
        threshold: Distance threshold used for edge creation
        metadata: Optional additional metadata to include
    
    Returns:
        Dictionary conforming to the graph schema
    
    Raises:
        SerializationError: If the graph cannot be serialized or validation fails
    """
    if not isinstance(G, nx.Graph):
        raise SerializationError(f"Expected NetworkX Graph, got {type(G)}")
    
    # Build the graph dictionary
    graph_dict = {
        "sample_id": sample_id,
        "material": material,
        "threshold_nm": float(threshold),
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "nodes": _extract_nodes(G),
        "edges": _extract_edges(G),
        "is_connected": nx.is_connected(G) if G.number_of_nodes() > 0 else True,
    }
    
    # Add optional metadata
    if metadata:
        graph_dict["metadata"] = _sanitize_value(metadata)
    
    # Add checksum for integrity
    graph_dict["checksum"] = _compute_graph_checksum(graph_dict)
    
    # Validate against schema
    try:
        from jsonschema import validate, ValidationError
        validate(instance=graph_dict, schema=graph_schema)
        logger.debug(f"Graph for sample {sample_id} validated against schema successfully")
    except ValidationError as e:
        raise SerializationError(
            f"Graph for sample {sample_id} failed schema validation: {e.message}"
        )
    
    return graph_dict


def serialize_graphs_to_file(
    graphs_data: List[Tuple[nx.Graph, str, str, float, Optional[Dict[str, Any]]]],
    output_path: str | Path,
    overwrite: bool = False
) -> List[str]:
    """
    Serialize multiple graphs to a JSON file.
    
    Args:
        graphs_data: List of tuples (graph, sample_id, material, threshold, metadata)
        output_path: Path to the output JSON file
        overwrite: Whether to overwrite existing file
    
    Returns:
        List of sample_ids that were successfully serialized
    
    Raises:
        SerializationError: If any graph fails serialization or file write fails
        FileExistsError: If file exists and overwrite=False
    """
    output_path = Path(output_path)
    
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output file {output_path} already exists. Set overwrite=True to replace.")
    
    logger.info(f"Serializing {len(graphs_data)} graphs to {output_path}")
    
    serialized_graphs = []
    successful_samples = []
    
    for i, (G, sample_id, material, threshold, metadata) in enumerate(graphs_data):
        try:
            graph_dict = serialize_graph_to_dict(G, sample_id, material, threshold, metadata)
            serialized_graphs.append(graph_dict)
            successful_samples.append(sample_id)
            logger.debug(f"Serialized graph {i+1}/{len(graphs_data)}: {sample_id}")
        except SerializationError as e:
            logger.error(f"Failed to serialize graph {i+1}/{len(graphs_data)}: {e}")
            raise
    
    # Write to file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serialized_graphs, f, indent=2)
        
        logger.info(f"Successfully wrote {len(serialized_graphs)} graphs to {output_path}")
        
        # Generate checksum manifest
        manifest_path = output_path.with_suffix('.json.sha256')
        manifest = {
            "file": str(output_path),
            "checksum": compute_string_sha256(json.dumps(serialized_graphs, sort_keys=True)),
            "graph_count": len(serialized_graphs),
            "samples": successful_samples
        }
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        return successful_samples
        
    except IOError as e:
        raise SerializationError(f"Failed to write output file {output_path}: {e}")


def export_graph_to_dict(
    G: nx.Graph,
    sample_id: str,
    material: str,
    threshold: float,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Alias for serialize_graph_to_dict for backward compatibility.
    
    This function is exported from src.graphs.constructor but implemented here
    to maintain separation of concerns.
    """
    return serialize_graph_to_dict(G, sample_id, material, threshold, metadata)
