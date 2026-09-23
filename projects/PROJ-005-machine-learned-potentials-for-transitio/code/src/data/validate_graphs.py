import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import logging

# Import logging setup from utils if available, otherwise fallback
try:
    from src.utils.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

class GraphValidationError(Exception):
    """Custom exception for graph validation failures."""
    pass

def get_project_root() -> Path:
    """Returns the project root directory (assumed to be 3 levels up from this file)."""
    return Path(__file__).resolve().parent.parent.parent.parent

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads the dataset graph schema from a YAML/JSON file.
    Defaults to contracts/dataset_graph.schema.yaml if not provided.
    """
    if schema_path is None:
        project_root = get_project_root()
        schema_path = project_root / "contracts" / "dataset_graph.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    # Support both YAML (via json if simple) or direct JSON. 
    # The task implies a yaml file, but to avoid adding pyyaml dependency here if not strictly needed,
    # we check extension. However, standard practice is to use yaml for schemas.
    # Since T006 exists for config loading which likely uses yaml, we assume yaml support.
    # To be safe and robust without assuming extra imports beyond standard+project, we try json first, then yaml.
    
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_node_attributes(df_nodes: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates node attributes against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_nodes = schema.get("nodes", {}).get("required_attributes", [])
    types = schema.get("nodes", {}).get("types", {})
    
    if "nodes" not in df_nodes.columns:
        # If the dataframe is a flat representation where node data is columns, adjust logic
        # Based on typical parquet storage for graphs, we might have a 'nodes' column containing dicts or a separate table.
        # Assuming a flat table with prefix or a column named 'nodes' containing list of dicts.
        # Let's assume the input df has a 'nodes' column with a list of dicts per row, OR
        # the function is called on a DataFrame that IS the node table.
        
        # Strategy: If 'nodes' column exists and is object type, expand it. 
        # If not, assume this df IS the node table.
        if "nodes" in df_nodes.columns:
            # This is a graph table where each row is a graph, and 'nodes' is a column of lists
            # We need to validate the structure of the lists inside.
            # However, schema validation usually happens on the flattened node table or the structure of the node objects.
            # Let's assume we receive a DataFrame where each row is a node, or we need to check the structure of the node column.
            pass
        else:
            # Assume this is the node table
            for attr in required_nodes:
                if attr not in df_nodes.columns:
                    errors.append(f"Missing required node attribute: {attr}")
        
        # Check types if we have a node table
        if "nodes" not in df_nodes.columns:
            for col, expected_type in types.items():
                if col in df_nodes.columns:
                    if expected_type == "int" and not np.issubdtype(df_nodes[col].dtype, np.integer):
                        errors.append(f"Node attribute {col} should be integer, got {df_nodes[col].dtype}")
                    elif expected_type == "float" and not np.issubdtype(df_nodes.dtype, np.floating):
                         errors.append(f"Node attribute {col} should be float, got {df_nodes[col].dtype}")
    else:
        # Handling the case where 'nodes' is a column of lists/dicts in a graph-level dataframe
        # We iterate and check the first non-null entry to validate structure
        sample_node = None
        for _, row in df_nodes.iterrows():
            if isinstance(row['nodes'], list) and len(row['nodes']) > 0:
                sample_node = row['nodes'][0]
                break
        
        if sample_node is None:
            errors.append("No valid node data found in 'nodes' column")
        else:
            for attr in required_nodes:
                if attr not in sample_node:
                    errors.append(f"Missing required node attribute '{attr}' in graph data")

    return len(errors) == 0, errors

def validate_edge_attributes(df_edges: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates edge attributes against the schema.
    """
    errors = []
    required_edges = schema.get("edges", {}).get("required_attributes", [])
    
    # Similar logic to nodes: check if 'edges' column exists or if this is the edge table
    if "edges" not in df_edges.columns:
        for attr in required_edges:
            if attr not in df_edges.columns:
                errors.append(f"Missing required edge attribute: {attr}")
    else:
        # Check structure in the edges column
        sample_edge = None
        for _, row in df_edges.iterrows():
            if isinstance(row['edges'], list) and len(row['edges']) > 0:
                sample_edge = row['edges'][0]
                break
        
        if sample_edge is None:
            errors.append("No valid edge data found in 'edges' column")
        else:
            for attr in required_edges:
                if attr not in sample_edge:
                    errors.append(f"Missing required edge attribute '{attr}' in graph data")

    return len(errors) == 0, errors

def validate_graph_metadata(df_graphs: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates graph-level metadata (e.g., energy_dft, barrier_height).
    """
    errors = []
    required_meta = schema.get("metadata", {}).get("required_attributes", [])
    
    for attr in required_meta:
        if attr not in df_graphs.columns:
            errors.append(f"Missing required metadata attribute: {attr}")
    
    # Check for nulls in critical fields
    if "energy_dft" in df_graphs.columns:
        if df_graphs["energy_dft"].isnull().any():
            errors.append("Found null values in 'energy_dft'")
    
    return len(errors) == 0, errors

def validate_graph_structure(df_graphs: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates structural integrity (e.g., no self loops, consistent node counts).
    """
    errors = []
    
    # Check for self-loops if edge data is present
    if "edges" in df_graphs.columns:
        for idx, row in df_graphs.iterrows():
            edges = row['edges']
            if isinstance(edges, list):
                for edge in edges:
                    if isinstance(edge, dict):
                        src = edge.get('source')
                        tgt = edge.get('target')
                        if src is not None and tgt is not None and src == tgt:
                            errors.append(f"Graph {idx} contains a self-loop at node {src}")
                            break # One error per graph is enough for this check
    
    return len(errors) == 0, errors

def validate_graph(df_graphs: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Runs all validation checks on a DataFrame of graphs.
    """
    all_errors = []
    
    # 1. Validate Nodes
    valid, errors = validate_node_attributes(df_graphs, schema)
    if not valid:
        all_errors.extend(errors)
    
    # 2. Validate Edges
    valid, errors = validate_edge_attributes(df_graphs, schema)
    if not valid:
        all_errors.extend(errors)
    
    # 3. Validate Metadata
    valid, errors = validate_graph_metadata(df_graphs, schema)
    if not valid:
        all_errors.extend(errors)
    
    # 4. Validate Structure
    valid, errors = validate_graph_structure(df_graphs)
    if not valid:
        all_errors.extend(errors)
    
    return len(all_errors) == 0, all_errors

def validate_all_graphs(input_path: Path, schema_path: Optional[Path] = None) -> bool:
    """
    Loads graphs from a parquet file and validates them against the schema.
    Returns True if valid, raises GraphValidationError if not.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input graphs file not found: {input_path}")
    
    logger.info(f"Loading graphs from {input_path}...")
    df = pd.read_parquet(input_path)
    
    logger.info(f"Loaded {len(df)} graphs. Validating against schema...")
    schema = load_schema(schema_path)
    
    is_valid, errors = validate_graph(df, schema)
    
    if not is_valid:
        error_msg = "\n".join(errors)
        logger.error(f"Validation failed with {len(errors)} errors:\n{error_msg}")
        raise GraphValidationError(f"Graph validation failed:\n{error_msg}")
    
    logger.info("Validation successful. All graphs conform to schema.")
    return True

def main():
    """
    CLI entry point for validating the processed graphs.
    """
    project_root = get_project_root()
    input_file = project_root / "data" / "processed" / "graphs.parquet"
    schema_file = project_root / "contracts" / "dataset_graph.schema.yaml"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        validate_all_graphs(input_file, schema_file)
        logger.info("T019: Graph validation completed successfully.")
    except GraphValidationError as e:
        logger.error(f"T019: Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"T019: Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
