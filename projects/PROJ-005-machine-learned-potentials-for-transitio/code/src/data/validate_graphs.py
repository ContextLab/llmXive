"""
Validation module for TransitionStateGraph structures against the dataset_graph.schema.yaml.
This module ensures that the generated graphs conform to the required schema before saving.
"""
import json
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yaml

# Setup logging
logger = logging.getLogger(__name__)

class GraphValidationError(Exception):
    """Custom exception for graph validation errors."""
    pass

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the schema from the YAML file.
    
    Args:
        schema_path: Path to the schema file. If None, uses default location.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if schema_path is None:
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    return schema

def validate_node_attributes(nodes: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate node attributes against the schema.
    
    Args:
        nodes: Node data (list of dicts, DataFrame, or structured array).
        schema: The loaded schema definition.
        
    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    
    # Convert to DataFrame if necessary for uniform processing
    if isinstance(nodes, list):
        try:
            df = pd.DataFrame(nodes)
        except Exception as e:
            errors.append(f"Failed to convert nodes to DataFrame: {str(e)}")
            return errors
    elif isinstance(nodes, pd.DataFrame):
        df = nodes
    else:
        try:
            df = pd.DataFrame(nodes)
        except Exception as e:
            errors.append(f"Failed to convert nodes to DataFrame: {str(e)}")
            return errors

    # Check required properties from schema
    required_props = schema.get('properties', {}).get('node_attributes', {}).get('items', {}).get('required', [])
    node_schema = schema.get('properties', {}).get('node_attributes', {}).get('items', {}).get('properties', {})
    
    # Check for required columns
    for col in required_props:
        if col not in df.columns:
            errors.append(f"Missing required node attribute: {col}")
    
    # Validate types and constraints
    for col, col_schema in node_schema.items():
        if col not in df.columns:
            continue  # Already handled in required check
        
        # Type checking
        expected_type = col_schema.get('type')
        if expected_type == 'integer':
            if not pd.api.types.is_integer_dtype(df[col]) and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Node attribute '{col}' should be integer, got {df[col].dtype}")
        elif expected_type == 'number':
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Node attribute '{col}' should be number, got {df[col].dtype}")
        elif expected_type == 'boolean':
            if not pd.api.types.is_bool_dtype(df[col]):
                errors.append(f"Node attribute '{col}' should be boolean, got {df[col].dtype}")
        elif expected_type == 'string':
            if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                errors.append(f"Node attribute '{col}' should be string, got {df[col].dtype}")
        
        # Enum validation
        if 'enum' in col_schema:
            valid_values = set(col_schema['enum'])
            invalid_values = set(df[col].dropna().unique()) - valid_values
            if invalid_values:
                errors.append(f"Node attribute '{col}' contains invalid enum values: {invalid_values}")
    
    # Check minItems constraint
    min_items = schema.get('properties', {}).get('node_attributes', {}).get('minItems', 0)
    if len(df) < min_items:
        errors.append(f"Node count ({len(df)}) is less than minimum required ({min_items})")
    
    return errors

def validate_edge_attributes(edges: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate edge attributes against the schema.
    
    Args:
        edges: Edge data (list of dicts, DataFrame, or structured array).
        schema: The loaded schema definition.
        
    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    
    # Convert to DataFrame if necessary
    if isinstance(edges, list):
        try:
            df = pd.DataFrame(edges)
        except Exception as e:
            errors.append(f"Failed to convert edges to DataFrame: {str(e)}")
            return errors
    elif isinstance(edges, pd.DataFrame):
        df = edges
    else:
        try:
            df = pd.DataFrame(edges)
        except Exception as e:
            errors.append(f"Failed to convert edges to DataFrame: {str(e)}")
            return errors

    # Check required properties
    required_props = schema.get('properties', {}).get('edge_attributes', {}).get('items', {}).get('required', [])
    edge_schema = schema.get('properties', {}).get('edge_attributes', {}).get('items', {}).get('properties', {})
    
    for col in required_props:
        if col not in df.columns:
            errors.append(f"Missing required edge attribute: {col}")
    
    # Validate types
    for col, col_schema in edge_schema.items():
        if col not in df.columns:
            continue
        
        expected_type = col_schema.get('type')
        if expected_type == 'integer':
            if not pd.api.types.is_integer_dtype(df[col]) and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Edge attribute '{col}' should be integer, got {df[col].dtype}")
        elif expected_type == 'number':
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Edge attribute '{col}' should be number, got {df[col].dtype}")
        elif expected_type == 'string':
            if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                errors.append(f"Edge attribute '{col}' should be string, got {df[col].dtype}")
        
        # Enum validation
        if 'enum' in col_schema:
            valid_values = set(col_schema['enum'])
            invalid_values = set(df[col].dropna().unique()) - valid_values
            if invalid_values:
                errors.append(f"Edge attribute '{col}' contains invalid enum values: {invalid_values}")
    
    # Check minItems constraint
    min_items = schema.get('properties', {}).get('edge_attributes', {}).get('minItems', 0)
    if len(df) < min_items:
        errors.append(f"Edge count ({len(df)}) is less than minimum required ({min_items})")
    
    # Validate edge indices are within node bounds
    if 'source' in df.columns and 'target' in df.columns:
        if len(df) > 0:
            max_node_idx = len(df)  # This is approximate, need actual node count
            # Note: Actual node count validation requires access to node data
            # which is handled in validate_graph_structure
    
    return errors

def validate_graph_metadata(metadata: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate graph metadata against the schema.
    
    Args:
        metadata: Dictionary of metadata.
        schema: The loaded schema definition.
        
    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    
    if not isinstance(metadata, dict):
        errors.append("Graph metadata must be a dictionary")
        return errors
    
    # Check required properties
    required_props = schema.get('properties', {}).get('graph_metadata', {}).get('required', [])
    meta_schema = schema.get('properties', {}).get('graph_metadata', {}).get('properties', {})
    
    for col in required_props:
        if col not in metadata:
            errors.append(f"Missing required metadata field: {col}")
    
    # Validate types and constraints
    for field, field_schema in meta_schema.items():
        if field not in metadata:
            continue
        
        value = metadata[field]
        expected_type = field_schema.get('type')
        
        if expected_type == 'integer':
            if not isinstance(value, (int, np.integer)):
                errors.append(f"Metadata '{field}' should be integer, got {type(value)}")
        elif expected_type == 'number':
            if not isinstance(value, (int, float, np.number)):
                errors.append(f"Metadata '{field}' should be number, got {type(value)}")
        elif expected_type == 'string':
            if not isinstance(value, str):
                errors.append(f"Metadata '{field}' should be string, got {type(value)}")
        elif expected_type == 'boolean':
            if not isinstance(value, bool):
                errors.append(f"Metadata '{field}' should be boolean, got {type(value)}")
        
        # Enum validation
        if 'enum' in field_schema:
            valid_values = set(field_schema['enum'])
            if value not in valid_values:
                errors.append(f"Metadata '{field}' has invalid enum value: {value}. Valid: {valid_values}")
    
    return errors

def validate_graph_structure(nodes: Any, edges: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate graph structure (consistency between nodes and edges).
    
    Args:
        nodes: Node data.
        edges: Edge data.
        schema: The loaded schema definition.
        
    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    
    # Convert to DataFrames
    if isinstance(nodes, list):
        node_df = pd.DataFrame(nodes)
    elif isinstance(nodes, pd.DataFrame):
        node_df = nodes
    else:
        node_df = pd.DataFrame(nodes)
    
    if isinstance(edges, list):
        edge_df = pd.DataFrame(edges)
    elif isinstance(edges, pd.DataFrame):
        edge_df = edges
    else:
        edge_df = pd.DataFrame(edges) if len(edges) > 0 else pd.DataFrame(columns=['source', 'target'])
    
    num_nodes = len(node_df)
    
    # Check for self-loops
    if 'source' in edge_df.columns and 'target' in edge_df.columns:
        self_loops = edge_df[edge_df['source'] == edge_df['target']]
        if len(self_loops) > 0:
            errors.append(f"Self-loops detected: {len(self_loops)} edges connect a node to itself")
        
        # Check for out-of-bounds indices
        invalid_sources = edge_df[~edge_df['source'].apply(lambda x: isinstance(x, (int, np.integer)) and 0 <= x < num_nodes)]
        invalid_targets = edge_df[~edge_df['target'].apply(lambda x: isinstance(x, (int, np.integer)) and 0 <= x < num_nodes)]
        
        if len(invalid_sources) > 0:
            errors.append(f"Edge source indices out of bounds: {len(invalid_sources)} invalid")
        if len(invalid_targets) > 0:
            errors.append(f"Edge target indices out of bounds: {len(invalid_targets)} invalid")
    
    return errors

def validate_graph(nodes: Any, edges: Any, metadata: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single graph against the schema.
    
    Args:
        nodes: Node data.
        edges: Edge data.
        metadata: Graph metadata.
        schema: The loaded schema definition.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    all_errors = []
    
    # Validate components
    node_errors = validate_node_attributes(nodes, schema)
    edge_errors = validate_edge_attributes(edges, schema)
    meta_errors = validate_graph_metadata(metadata, schema)
    struct_errors = validate_graph_structure(nodes, edges, schema)
    
    all_errors.extend(node_errors)
    all_errors.extend(edge_errors)
    all_errors.extend(meta_errors)
    all_errors.extend(struct_errors)
    
    return len(all_errors) == 0, all_errors

def validate_all_graphs(graphs_path: Path, schema: Dict[str, Any]) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Validate all graphs in a parquet file.
    
    Args:
        graphs_path: Path to the parquet file containing graphs.
        schema: The loaded schema definition.
        
    Returns:
        Tuple of (valid_count, invalid_count, list_of_error_details).
    """
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_path}")
    
    # Load the parquet file
    try:
        df = pd.read_parquet(graphs_path)
    except Exception as e:
        raise GraphValidationError(f"Failed to load parquet file: {str(e)}")
    
    valid_count = 0
    invalid_count = 0
    error_details = []
    
    # Iterate through rows if graph data is stored row-wise
    # Assuming each row represents a graph with node/edge/metadata columns
    # or the file contains a list of graph dictionaries
    
    # Check structure of the DataFrame
    if 'nodes' in df.columns and 'edges' in df.columns and 'metadata' in df.columns:
        # Row-wise graph storage
        for idx, row in df.iterrows():
            nodes = row['nodes']
            edges = row['edges']
            metadata = row['metadata']
            
            is_valid, errors = validate_graph(nodes, edges, metadata, schema)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                error_details.append({
                    'row_index': idx,
                    'errors': errors
                })
    else:
        # Assume the file contains a list of graph dictionaries in a single column or flattened
        # Try to detect the structure
        if len(df.columns) == 1 and 'graph' in df.columns:
            graph_list = df['graph'].tolist()
            for idx, graph_data in enumerate(graph_list):
                nodes = graph_data.get('node_attributes', [])
                edges = graph_data.get('edge_attributes', [])
                metadata = graph_data.get('graph_metadata', {})
                
                is_valid, errors = validate_graph(nodes, edges, metadata, schema)
                
                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
                    error_details.append({
                        'graph_index': idx,
                        'errors': errors
                    })
        else:
            # Fallback: try to interpret as a single graph or raise error
            if len(df) == 1:
                # Single graph
                nodes = df.iloc[0].to_dict() if hasattr(df.iloc[0], 'to_dict') else dict(df.iloc[0])
                # This is a simplification; actual implementation depends on data format
                is_valid, errors = validate_graph(
                    nodes.get('node_attributes', []),
                    nodes.get('edge_attributes', []),
                    nodes.get('graph_metadata', {}),
                    schema
                )
                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
                    error_details.append({
                        'graph_index': 0,
                        'errors': errors
                    })
            else:
                raise GraphValidationError("Unable to determine graph structure in parquet file. Expected columns: 'nodes', 'edges', 'metadata' or a single 'graph' column.")
    
    return valid_count, invalid_count, error_details

def main():
    """Main entry point for graph validation."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = get_project_root()
    graphs_path = project_root / "data" / "processed" / "graphs.parquet"
    
    logger.info(f"Starting graph validation for: {graphs_path}")
    
    try:
        # Load schema
        schema = load_schema()
        logger.info("Schema loaded successfully")
        
        # Validate all graphs
        valid_count, invalid_count, errors = validate_all_graphs(graphs_path, schema)
        
        logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
        
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} invalid graphs:")
            for error_detail in errors[:5]:  # Log first 5 errors
                logger.warning(f"  - Graph {error_detail.get('row_index', error_detail.get('graph_index', 'N/A'))}: {error_detail['errors']}")
            if len(errors) > 5:
                logger.warning(f"  ... and {len(errors) - 5} more errors")
            sys.exit(1)
        else:
            logger.info("All graphs are valid!")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        sys.exit(1)
    except GraphValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
