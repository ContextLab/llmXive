import os
import sys
import logging
import json
import time
from typing import Dict, List, Optional, Tuple

import torch
from torch_geometric.data import Data, HeteroData
from torch_geometric.loader import DataLoader

# Project imports based on provided API surface
from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, log_metric, get_logger

def setup_script_logging():
    """Initialize logging for the serialization script."""
    logger = setup_logging("serialization")
    return logger

def load_intermediate_graphs(file_path: str) -> List[Data]:
    """
    Load the intermediate graphs from the PyTorch Geometric format (.pt).
    
    Args:
        file_path: Path to the intermediate graphs file.
        
    Returns:
        List of Data objects.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Intermediate graphs file not found: {file_path}")
    
    logger = get_logger("serialization")
    logger.info(f"Loading intermediate graphs from {file_path}")
    
    # Load the list of Data objects
    graphs = torch.load(file_path, weights_only=False)
    
    if not isinstance(graphs, list):
        raise TypeError(f"Expected list of Data objects, got {type(graphs)}")
    
    logger.info(f"Loaded {len(graphs)} graphs from intermediate file")
    return graphs

def load_split_indices(split_dir: str) -> Tuple[List[int], List[int], List[int]]:
    """
    Load the train, validation, and test indices from the split files.
    
    Args:
        split_dir: Directory containing the split index files.
        
    Returns:
        Tuple of (train_indices, val_indices, test_indices).
    """
    train_path = os.path.join(split_dir, "train_indices.pt")
    val_path = os.path.join(split_dir, "val_indices.pt")
    test_path = os.path.join(split_dir, "test_indices.pt")
    
    logger = get_logger("serialization")
    
    # Verify all files exist
    for path in [train_path, val_path, test_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Split index file not found: {path}")
    
    logger.info("Loading split indices...")
    
    train_indices = torch.load(train_path, weights_only=False)
    val_indices = torch.load(val_path, weights_only=False)
    test_indices = torch.load(test_path, weights_only=False)
    
    # Convert to lists if they are tensors
    if isinstance(train_indices, torch.Tensor):
        train_indices = train_indices.tolist()
    if isinstance(val_indices, torch.Tensor):
        val_indices = val_indices.tolist()
    if isinstance(test_indices, torch.Tensor):
        test_indices = test_indices.tolist()
    
    logger.info(f"Loaded {len(train_indices)} train, {len(val_indices)} val, {len(test_indices)} test indices")
    
    return train_indices, val_indices, test_indices

def filter_graphs_by_indices(graphs: List[Data], indices: List[int]) -> List[Data]:
    """
    Filter the list of graphs to only include those at the specified indices.
    
    Args:
        graphs: Full list of Data objects.
        indices: List of indices to keep.
        
    Returns:
        Filtered list of Data objects.
    """
    logger = get_logger("serialization")
    logger.info(f"Filtering graphs to {len(indices)} indices...")
    
    # Validate indices
    if not indices:
        logger.warning("Empty indices list provided")
        return []
    
    if max(indices) >= len(graphs):
        raise IndexError(f"Index {max(indices)} out of range for {len(graphs)} graphs")
    
    filtered = [graphs[i] for i in indices]
    logger.info(f"Filtered to {len(filtered)} graphs")
    
    return filtered

def validate_graph_schema(graph: Data) -> bool:
    """
    Validate that a graph object has the expected schema.
    
    Args:
        graph: A Data object to validate.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    logger = get_logger("serialization")
    
    # Check for required attributes
    required_attrs = ['x', 'edge_index', 'y']
    for attr in required_attrs:
        if not hasattr(graph, attr):
            raise ValueError(f"Graph missing required attribute: {attr}")
    
    # Validate edge_index shape
    if graph.edge_index.dim() != 2 or graph.edge_index.size(0) != 2:
        raise ValueError(f"edge_index must be 2D with size [2, E], got {graph.edge_index.shape}")
    
    logger.debug(f"Graph schema validated: {len(graph.x)} nodes, {graph.edge_index.size(1)} edges")
    return True

def serialize_graphs(graphs: List[Data], output_path: str) -> None:
    """
    Serialize the filtered graphs to a PyTorch Geometric format file.
    
    Args:
        graphs: List of Data objects to serialize.
        output_path: Path to write the output file.
    """
    logger = get_logger("serialization")
    
    # Validate all graphs before serialization
    logger.info("Validating graph schemas...")
    for i, graph in enumerate(graphs):
        try:
            validate_graph_schema(graph)
        except ValueError as e:
            raise ValueError(f"Validation failed for graph at index {i}: {e}")
    
    logger.info(f"Serializing {len(graphs)} graphs to {output_path}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the list of graphs
    torch.save(graphs, output_path)
    
    # Verify the file was created and is non-empty
    if not os.path.exists(output_path):
        raise RuntimeError(f"Failed to create output file: {output_path}")
    
    file_size = os.path.getsize(output_path)
    if file_size == 0:
        raise RuntimeError(f"Output file is empty: {output_path}")
    
    logger.info(f"Successfully serialized {len(graphs)} graphs ({file_size} bytes)")

def write_derivation_log(
    input_file: str,
    split_files: Dict[str, str],
    output_file: str,
    counts: Dict[str, int]
) -> None:
    """
    Write a derivation log documenting the serialization process.
    
    Args:
        input_file: Path to the intermediate graphs file.
        split_files: Dictionary of split names to file paths.
        output_file: Path to the final output file.
        counts: Dictionary of split names to counts.
    """
    logger = get_logger("serialization")
    log_path = output_file.replace(".pt", "_derivation.json")
    
    log_data = {
        "input_file": input_file,
        "split_files": split_files,
        "output_file": output_file,
        "counts": counts,
        "total_graphs": sum(counts.values()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "process": "T016_serialization"
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Derivation log written to {log_path}")

def main():
    """Main entry point for the serialization task."""
    logger = setup_script_logging()
    logger.info("Starting T016: Serialization of preprocessed graphs")
    
    try:
        config = get_config()
        ensure_directories()
        
        # Define paths
        intermediate_path = config.get("paths", {}).get("graphs_intermediate", 
                             os.path.join("data", "processed", "graphs_intermediate.pt"))
        split_dir = config.get("paths", {}).get("splits_dir", 
                             os.path.join("data", "processed", "splits"))
        output_path = config.get("paths", {}).get("graphs_final", 
                             os.path.join("data", "processed", "graphs.pt"))
        
        logger.info(f"Intermediate graphs: {intermediate_path}")
        logger.info(f"Split directory: {split_dir}")
        logger.info(f"Output path: {output_path}")
        
        # Load intermediate graphs
        graphs = load_intermediate_graphs(intermediate_path)
        logger.info(f"Total graphs loaded: {len(graphs)}")
        
        # Load split indices
        train_indices, val_indices, test_indices = load_split_indices(split_dir)
        
        # Filter graphs by split indices
        train_graphs = filter_graphs_by_indices(graphs, train_indices)
        val_graphs = filter_graphs_by_indices(graphs, val_indices)
        test_graphs = filter_graphs_by_indices(graphs, test_indices)
        
        # Combine all filtered graphs
        final_graphs = train_graphs + val_graphs + test_graphs
        
        # Validate total count
        expected_total = len(train_indices) + len(val_indices) + len(test_indices)
        if len(final_graphs) != expected_total:
            logger.warning(f"Graph count mismatch: expected {expected_total}, got {len(final_graphs)}")
        
        # Serialize to final output
        serialize_graphs(final_graphs, output_path)
        
        # Write derivation log
        split_files = {
            "train": os.path.join(split_dir, "train_indices.pt"),
            "val": os.path.join(split_dir, "val_indices.pt"),
            "test": os.path.join(split_dir, "test_indices.pt")
        }
        counts = {
            "train": len(train_indices),
            "val": len(val_indices),
            "test": len(test_indices)
        }
        write_derivation_log(intermediate_path, split_files, output_path, counts)
        
        # Log metrics
        log_metric("total_graphs", len(final_graphs))
        log_metric("train_graphs", len(train_graphs))
        log_metric("val_graphs", len(val_graphs))
        log_metric("test_graphs", len(test_graphs))
        
        logger.info("T016 Serialization completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
