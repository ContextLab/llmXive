"""
Validation module for TransitionStateGraph data against the dataset schema.

This module validates the generated parquet graphs against the schema defined
in code/contracts/dataset_graph.schema.yaml to ensure data integrity before
downstream processing.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import yaml

# Attempt to import jsonschema for robust validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema not installed. Using basic validation only.")

# Attempt to import pyarrow for parquet handling
try:
    import pyarrow.parquet as pq
except ImportError:
    raise ImportError("pyarrow is required for parquet handling. Install via requirements.txt.")


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_node_attributes(nodes: Any, schema_def: Dict) -> List[str]:
    """
    Validate the node_attributes structure.
    
    Args:
        nodes: The node data (list of dicts or DataFrame).
        schema_def: The schema definition for node_attributes.
        
    Returns:
        List of error messages.
    """
    errors = []
    
    # Handle DataFrame case (common when loading from parquet)
    if isinstance(nodes, pd.DataFrame):
        required_cols = ['atomic_number', 'x', 'y', 'z']
        for col in required_cols:
            if col not in nodes.columns:
                errors.append(f"Missing required node column: {col}")
        
        if 'atomic_number' in nodes.columns:
            if not pd.api.types.is_integer_dtype(nodes['atomic_number']):
                errors.append("atomic_number must be integer type")
        
        if 'is_metal' in nodes.columns:
            if not pd.api.types.is_bool_dtype(nodes['is_metal']):
                errors.append("is_metal must be boolean type")
                
        if 'ligand_class' in nodes.columns:
            valid_classes = ['Group_13', 'Conventional']
            invalid = nodes[~nodes['ligand_class'].isin(valid_classes)]['ligand_class'].unique()
            if len(invalid) > 0:
                errors.append(f"Invalid ligand_class values found: {invalid}")
                
    elif isinstance(nodes, list):
        if not nodes:
            errors.append("node_attributes list is empty")
        else:
            # Check first item for required keys
            first_node = nodes[0]
            required_keys = ['atomic_number', 'x', 'y', 'z']
            for key in required_keys:
                if key not in first_node:
                    errors.append(f"Missing required node key: {key}")
            
            if 'ligand_class' in first_node:
                valid_classes = ['Group_13', 'Conventional']
                for i, node in enumerate(nodes):
                    if node.get('ligand_class') and node['ligand_class'] not in valid_classes:
                        errors.append(f"Invalid ligand_class at node {i}: {node['ligand_class']}")
    else:
        errors.append("node_attributes must be a list or DataFrame")
        
    return errors


def validate_edge_attributes(edges: Any, schema_def: Dict) -> List[str]:
    """
    Validate the edge_attributes structure.
    
    Args:
        edges: The edge data.
        schema_def: The schema definition for edge_attributes.
        
    Returns:
        List of error messages.
    """
    errors = []
    
    if isinstance(edges, pd.DataFrame):
        required_cols = ['source', 'target', 'distance']
        for col in required_cols:
            if col not in edges.columns:
                errors.append(f"Missing required edge column: {col}")
                
        if 'source' in edges.columns and not pd.api.types.is_integer_dtype(edges['source']):
            errors.append("edge source must be integer type")
            
        if 'target' in edges.columns and not pd.api.types.is_integer_dtype(edges['target']):
            errors.append("edge target must be integer type")
            
        if 'distance' in edges.columns:
            if edges['distance'].isna().any():
                errors.append("edge distance contains NaN values")
                
    elif isinstance(edges, list):
        if edges:
            first_edge = edges[0]
            required_keys = ['source', 'target', 'distance']
            for key in required_keys:
                if key not in first_edge:
                    errors.append(f"Missing required edge key: {key}")
    else:
        errors.append("edge_attributes must be a list or DataFrame")
        
    return errors


def validate_graph_metadata(meta: Dict, schema_def: Dict) -> List[str]:
    """
    Validate the graph_metadata structure.
    
    Args:
        meta: The metadata dictionary.
        schema_def: The schema definition for graph_metadata.
        
    Returns:
        List of error messages.
    """
    errors = []
    
    if not isinstance(meta, dict):
        errors.append("graph_metadata must be a dictionary")
        return errors
        
    required_keys = ['energy_dft', 'barrier_height', 'metal_center', 'reaction_id']
    for key in required_keys:
        if key not in meta:
            errors.append(f"Missing required metadata key: {key}")
            
    if 'ligand_class' in meta:
        valid_classes = ['Group_13', 'Conventional']
        if meta['ligand_class'] not in valid_classes:
            errors.append(f"Invalid global ligand_class: {meta['ligand_class']}")
            
    if 'is_outlier' in meta:
        if not isinstance(meta['is_outlier'], bool):
            errors.append("is_outlier must be boolean")
            
    if 'cutoff_used' in meta:
        if not isinstance(meta['cutoff_used'], (int, float)):
            errors.append("cutoff_used must be numeric")
            
    return errors


def validate_graph(graph_data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single graph structure against the schema.
    
    Args:
        graph_data: Dictionary containing 'node_attributes', 'edge_attributes', 'graph_metadata'.
        schema: The loaded YAML schema.
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check top level keys
    if 'node_attributes' not in graph_data:
        errors.append("Missing 'node_attributes' in graph data")
    else:
        errors.extend(validate_node_attributes(graph_data['node_attributes'], schema.get('properties', {}).get('node_attributes', {})))
        
    if 'edge_attributes' not in graph_data:
        errors.append("Missing 'edge_attributes' in graph data")
    else:
        errors.extend(validate_edge_attributes(graph_data['edge_attributes'], schema.get('properties', {}).get('edge_attributes', {})))
        
    if 'graph_metadata' not in graph_data:
        errors.append("Missing 'graph_metadata' in graph data")
    else:
        errors.extend(validate_graph_metadata(graph_data['graph_metadata'], schema.get('properties', {}).get('graph_metadata', {})))
        
    return len(errors) == 0, errors


def run_validation(graphs_path: Path, schema_path: Path) -> Dict[str, Any]:
    """
    Run validation on the entire parquet file.
    
    Args:
        graphs_path: Path to the graphs.parquet file.
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary with validation results summary.
    """
    results = {
        "total_graphs": 0,
        "valid_graphs": 0,
        "invalid_graphs": 0,
        "errors_by_graph": [],
        "status": "unknown"
    }
    
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_path}")
        
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    logging.info(f"Loading schema from {schema_path}")
    schema = load_schema(schema_path)
    
    logging.info(f"Loading graphs from {graphs_path}")
    try:
        # Load as PyArrow table to iterate efficiently
        table = pq.read_table(graphs_path)
        df = table.to_pandas()
    except Exception as e:
        raise RuntimeError(f"Failed to read parquet file: {e}")
        
    results["total_graphs"] = len(df)
    
    # The parquet file likely stores nodes and edges as serialized JSON strings or lists
    # We need to iterate and validate each row (graph)
    # Assuming the columns are 'nodes', 'edges', 'metadata' or similar based on typical serialization
    # If the schema expects specific column names, we map them.
    # Based on the schema, we expect a structure like:
    # { "node_attributes": [...], "edge_attributes": [...], "graph_metadata": {...} }
    # If the parquet stores them as separate columns, we need to reconstruct this dict per row.
    
    # Common serialization patterns in parquet for graphs:
    # 1. Single column 'data' containing the dict
    # 2. Separate columns 'nodes', 'edges', 'metadata'
    # 3. Separate columns for each attribute (flat)
    
    # Let's check columns
    cols = df.columns.tolist()
    logging.info(f"Parquet columns: {cols}")
    
    # Strategy: If 'data' column exists, use it. Else if 'nodes', 'edges', 'metadata' exist, reconstruct.
    # Else assume flat structure is invalid for this specific schema validation without more info.
    # Given the task context, we assume the file was saved with the structure:
    # nodes (json string or list), edges (json string or list), metadata (dict or json string)
    
    # Helper to parse JSON if string
    def parse_if_str(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except:
                return val
        return val

    valid_count = 0
    invalid_count = 0
    
    for idx, row in df.iterrows():
        graph_dict = {}
        
        # Map expected keys from row
        # Try to find the columns that match the schema structure
        if 'data' in cols:
            graph_dict = parse_if_str(row['data'])
        elif 'nodes' in cols and 'edges' in cols and 'metadata' in cols:
            graph_dict = {
                'node_attributes': parse_if_str(row['nodes']),
                'edge_attributes': parse_if_str(row['edges']),
                'graph_metadata': parse_if_str(row['metadata'])
            }
        elif 'node_attributes' in cols and 'edge_attributes' in cols and 'graph_metadata' in cols:
            # Already in the right format
            graph_dict = {
                'node_attributes': parse_if_str(row['node_attributes']),
                'edge_attributes': parse_if_str(row['edge_attributes']),
                'graph_metadata': parse_if_str(row['graph_metadata'])
            }
        else:
            # Fallback: try to construct from available columns if they look like metadata
            # This is a best-effort attempt if the file structure is slightly different
            # but we expect the specific keys from the schema.
            # If we can't find the keys, we fail the graph.
            graph_dict = {
                'node_attributes': row.get('nodes', row.get('node_attributes', [])),
                'edge_attributes': row.get('edges', row.get('edge_attributes', [])),
                'graph_metadata': row.get('metadata', row.get('graph_metadata', {}))
            }
            # Ensure they are parsed if strings
            if isinstance(graph_dict['node_attributes'], str):
                graph_dict['node_attributes'] = json.loads(graph_dict['node_attributes'])
            if isinstance(graph_dict['edge_attributes'], str):
                graph_dict['edge_attributes'] = json.loads(graph_dict['edge_attributes'])
            if isinstance(graph_dict['graph_metadata'], str):
                graph_dict['graph_metadata'] = json.loads(graph_dict['graph_metadata'])
        
        is_valid, errors = validate_graph(graph_dict, schema)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            results["errors_by_graph"].append({
                "index": idx,
                "errors": errors
            })
            # Limit error reporting to first 10 errors to avoid huge logs
            if len(results["errors_by_graph"]) > 10:
                break
    
    results["valid_graphs"] = valid_count
    results["invalid_graphs"] = invalid_count
    results["status"] = "PASS" if invalid_count == 0 else "FAIL"
    
    return results


def save_validation_results(results: Dict[str, Any], output_path: Path):
    """Save validation results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logging.info(f"Validation results saved to {output_path}")


def main():
    """Main entry point for validation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = get_project_root()
    graphs_path = project_root / "data" / "processed" / "graphs.parquet"
    schema_path = project_root / "contracts" / "dataset_graph.schema.yaml"
    output_path = project_root / "data" / "results" / "validation_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logging.info(f"Starting validation of {graphs_path}")
        results = run_validation(graphs_path, schema_path)
        
        save_validation_results(results, output_path)
        
        if results["status"] == "PASS":
            logging.info(f"Validation PASSED. {results['valid_graphs']} graphs validated.")
            sys.exit(0)
        else:
            logging.warning(f"Validation FAILED. {results['invalid_graphs']} graphs failed.")
            logging.warning(f"See {output_path} for details.")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
