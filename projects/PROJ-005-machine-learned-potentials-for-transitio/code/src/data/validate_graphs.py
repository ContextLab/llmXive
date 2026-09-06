import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import logging

from src.utils.config import get_project_root
from src.utils.logging import setup_logger

# Configure logging
logger = setup_logger("validate_graphs")

class GraphValidationError(Exception):
    """Custom exception for graph validation failures."""
    pass

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load the graph schema from a YAML/JSON file.
    Expects a dictionary with 'nodes', 'edges', and 'metadata' definitions.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Try loading as JSON first, then YAML if needed (though tasks.md says .yaml)
    # Since we need to support .yaml without external yaml lib if not strictly needed,
    # but requirements.txt has pyyaml. Let's assume standard yaml loading.
    try:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed, attempting JSON fallback for schema.")
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Schema file is not valid JSON or YAML.")
    
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary.")
    
    return schema

def validate_node_attributes(df_nodes: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate node attributes against the schema.
    Returns a list of error messages.
    """
    errors = []
    node_schema = schema.get('nodes', {})
    
    required_attrs = node_schema.get('required', [])
    type_schema = node_schema.get('types', {})
    
    existing_cols = set(df_nodes.columns)
    
    # Check required attributes
    missing = set(required_attrs) - existing_cols
    if missing:
        errors.append(f"Missing required node attributes: {missing}")
    
    # Check types
    for col, expected_type in type_schema.items():
        if col in existing_cols:
            actual_type = str(df_nodes[col].dtype)
            # Map pandas types to generic python types for comparison if needed
            # For now, just log if there's a gross mismatch if we can detect it
            if expected_type == 'int' and not np.issubdtype(df_nodes[col].dtype, np.integer):
                errors.append(f"Node attribute '{col}' expected int, got {actual_type}")
            elif expected_type == 'float' and not np.issubdtype(df_nodes[col].dtype, np.floating):
                errors.append(f"Node attribute '{col}' expected float, got {actual_type}")
    
    return errors

def validate_edge_attributes(df_edges: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate edge attributes against the schema.
    Returns a list of error messages.
    """
    errors = []
    edge_schema = schema.get('edges', {})
    
    required_attrs = edge_schema.get('required', [])
    type_schema = edge_schema.get('types', {})
    
    existing_cols = set(df_edges.columns)
    
    # Check required attributes
    missing = set(required_attrs) - existing_cols
    if missing:
        errors.append(f"Missing required edge attributes: {missing}")
    
    # Check types
    for col, expected_type in type_schema.items():
        if col in existing_cols:
            actual_type = str(df_edges[col].dtype)
            if expected_type == 'int' and not np.issubdtype(df_edges[col].dtype, np.integer):
                errors.append(f"Edge attribute '{col}' expected int, got {actual_type}")
            elif expected_type == 'float' and not np.issubdtype(df_edges[col].dtype, np.floating):
                errors.append(f"Edge attribute '{col}' expected float, got {actual_type}")
    
    return errors

def validate_graph_metadata(metadata: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate graph metadata against the schema.
    Returns a list of error messages.
    """
    errors = []
    meta_schema = schema.get('metadata', {})
    
    required_fields = meta_schema.get('required', [])
    type_schema = meta_schema.get('types', {})
    
    # Check required fields
    missing = set(required_fields) - set(metadata.keys())
    if missing:
        errors.append(f"Missing required metadata fields: {missing}")
    
    # Check types
    for field, expected_type in type_schema.items():
        if field in metadata:
            val = metadata[field]
            if expected_type == 'int' and not isinstance(val, int):
                errors.append(f"Metadata field '{field}' expected int, got {type(val).__name__}")
            elif expected_type == 'float' and not isinstance(val, (int, float)):
                errors.append(f"Metadata field '{field}' expected float, got {type(val).__name__}")
            elif expected_type == 'str' and not isinstance(val, str):
                errors.append(f"Metadata field '{field}' expected str, got {type(val).__name__}")
    
    return errors

def validate_graph_structure(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> List[str]:
    """
    Validate basic graph structure (e.g., no self-loops if disallowed, consistent IDs).
    Returns a list of error messages.
    """
    errors = []
    
    if 'node_id' in nodes_df.columns and 'source' in edges_df.columns and 'target' in edges_df.columns:
        node_ids = set(nodes_df['node_id'])
        edge_sources = set(edges_df['source'])
        edge_targets = set(edges_df['target'])
        
        # Check if all edge endpoints exist in nodes
        invalid_sources = edge_sources - node_ids
        invalid_targets = edge_targets - node_ids
        
        if invalid_sources:
            errors.append(f"Edge sources {invalid_sources} not found in nodes.")
        if invalid_targets:
            errors.append(f"Edge targets {invalid_targets} not found in nodes.")
        
        # Check for self-loops if schema disallows them (assumption: disallowed by default unless specified)
        # This is a basic check; specific schema rules might vary.
        if 'source' in edges_df.columns and 'target' in edges_df.columns:
            self_loops = edges_df[edges_df['source'] == edges_df['target']]
            if not self_loops.empty:
                # Count unique self-loops
                count = len(self_loops)
                errors.append(f"Found {count} self-loops. Self-loops are typically disallowed in this schema.")
    
    return errors

def validate_graph(nodes_df: pd.DataFrame, edges_df: pd.DataFrame, metadata: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Perform full validation on a single graph instance.
    Returns (is_valid, list_of_errors).
    """
    all_errors = []
    
    all_errors.extend(validate_node_attributes(nodes_df, schema))
    all_errors.extend(validate_edge_attributes(edges_df, schema))
    all_errors.extend(validate_graph_metadata(metadata, schema))
    all_errors.extend(validate_graph_structure(nodes_df, edges_df))
    
    return len(all_errors) == 0, all_errors

def validate_all_graphs(graphs_df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a batch of graphs stored in a parquet-like dataframe structure.
    Assumes the dataframe has columns: 'graph_id', 'nodes' (list of dicts or serialized), 'edges' (list of dicts), 'metadata'.
    Or, if nodes/edges are already exploded into separate DataFrames with a 'graph_id' foreign key.
    
    For this implementation, we assume the input `graphs_df` is a summary or the output of a loader that 
    has parsed nodes/edges into lists per graph_id, OR we iterate if the schema implies a specific format.
    
    Given the context of `src/data/graph_construction.py` saving to parquet, it likely saves a row per graph 
    with nodes/edges as complex types or separate files. 
    However, `validate_graphs` is usually run on the saved Parquet file.
    Parquet with nested structures is supported by pandas/pyarrow.
    
    Let's assume the input `graphs_df` has columns:
    - graph_id
    - nodes (list of dicts or similar)
    - edges (list of dicts or similar)
    - metadata (dict)
    
    If the data is flat (one row per node), we would need to group by graph_id.
    Based on `graph_construction.py` saving to parquet, it likely saves a list of graphs.
    We will assume a structure where we can reconstruct node/edge DFs per graph.
    """
    results = {
        "total_graphs": 0,
        "valid_graphs": 0,
        "invalid_graphs": 0,
        "errors": []
    }
    
    results["total_graphs"] = len(graphs_df)
    
    for idx, row in graphs_df.iterrows():
        graph_id = row.get('graph_id', idx)
        try:
            # Handle potential serialization formats
            nodes_data = row.get('nodes', [])
            edges_data = row.get('edges', [])
            metadata = row.get('metadata', {})
            
            # Convert to DataFrames for validation functions
            nodes_df = pd.DataFrame(nodes_data) if nodes_data else pd.DataFrame()
            edges_df = pd.DataFrame(edges_data) if edges_data else pd.DataFrame()
            
            is_valid, errors = validate_graph(nodes_df, edges_df, metadata, schema)
            
            if is_valid:
                results["valid_graphs"] += 1
            else:
                results["invalid_graphs"] += 1
                results["errors"].append({
                    "graph_id": str(graph_id),
                    "errors": errors
                })
                
        except Exception as e:
            results["invalid_graphs"] += 1
            results["errors"].append({
                "graph_id": str(graph_id),
                "errors": [f"Exception during validation: {str(e)}"]
            })
    
    return results

def main():
    """
    Main entry point to validate graphs against the schema.
    Loads graphs from data/processed/graphs.parquet and schema from contracts/dataset_graph.schema.yaml.
    """
    project_root = get_project_root()
    schema_path = project_root / "contracts" / "dataset_graph.schema.yaml"
    graphs_path = project_root / "data" / "processed" / "graphs.parquet"
    output_path = project_root / "data" / "results" / "validation_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting graph validation. Schema: {schema_path}, Data: {graphs_path}")
    
    try:
        # Load Schema
        schema = load_schema(schema_path)
        logger.info("Schema loaded successfully.")
        
        # Load Graphs
        if not graphs_path.exists():
            raise FileNotFoundError(f"Graphs file not found: {graphs_path}")
        
        graphs_df = pd.read_parquet(graphs_path)
        logger.info(f"Loaded {len(graphs_df)} graphs from {graphs_path}")
        
        # Validate
        validation_results = validate_all_graphs(graphs_df, schema)
        
        # Save Results
        with open(output_path, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        logger.info(f"Validation complete. Report saved to {output_path}")
        logger.info(f"Valid: {validation_results['valid_graphs']}, Invalid: {validation_results['invalid_graphs']}")
        
        if validation_results['invalid_graphs'] > 0:
            logger.warning("Some graphs failed validation. Check the report for details.")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
