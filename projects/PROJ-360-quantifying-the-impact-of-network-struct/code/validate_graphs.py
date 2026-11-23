import os
import sys
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path if needed (robustness)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config

def setup_validation_logger(log_file: str = "results/validation.log") -> logging.Logger:
    """
    Sets up a dedicated logger for graph validation tasks.
    """
    logger = logging.getLogger("graph_validator")
    logger.setLevel(logging.DEBUG)

    # File handler
    log_path = Path("results") / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def load_graphs_from_directory(directory: str) -> List[Tuple[str, Any]]:
    """
    Loads all pickle files from the specified directory.
    Returns a list of tuples: (filename, graph_object).
    """
    graphs = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    for file_path in dir_path.glob("*.pkl"):
        try:
            with open(file_path, 'rb') as f:
                graph = pickle.load(f)
                graphs.append((file_path.name, graph))
        except Exception as e:
            logging.error(f"Failed to load {file_path}: {e}")
    
    return graphs

def validate_graph(graph: Any, material_id: str) -> Tuple[bool, str]:
    """
    Validates a single graph object.
    Returns (is_valid, reason).
    
    Criteria:
    - Must have >= 2 nodes
    - Must have >= 1 edge
    """
    if graph is None:
        return False, "Graph is None"

    # Check nodes
    try:
        num_nodes = graph.number_of_nodes()
    except AttributeError:
        return False, "Object is not a networkx Graph (missing number_of_nodes)"

    if num_nodes < 2:
        return False, f"Insufficient nodes: {num_nodes} (requires >= 2)"

    # Check edges
    try:
        num_edges = graph.number_of_edges()
    except AttributeError:
        return False, "Object is not a networkx Graph (missing number_of_edges)"

    if num_edges < 1:
        return False, f"Insufficient edges: {num_edges} (requires >= 1)"

    return True, "Valid"

def validate_all_graphs(input_dir: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Validates all graphs in the input directory.
    Logs skipped/invalid graphs.
    Optionally saves a summary report.
    """
    logger = setup_validation_logger()
    logger.info(f"Starting validation for graphs in: {input_dir}")

    graphs = load_graphs_from_directory(input_dir)
    
    total_count = len(graphs)
    valid_count = 0
    invalid_count = 0
    invalid_details = []

    if total_count == 0:
        logger.warning("No graphs found to validate.")
        return {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "details": []
        }

    for filename, graph in graphs:
        # Extract material_id from filename if possible (e.g., mp-123.pkl -> mp-123)
        material_id = filename.replace(".pkl", "")
        
        is_valid, reason = validate_graph(graph, material_id)
        
        if is_valid:
            valid_count += 1
            logger.debug(f"VALID: {material_id} ({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)")
        else:
            invalid_count += 1
            invalid_details.append({
                "material_id": material_id,
                "filename": filename,
                "reason": reason
            })
            logger.warning(f"SKIPPED: {material_id} - Reason: {reason}")

    summary = {
        "total": total_count,
        "valid": valid_count,
        "invalid": invalid_count,
        "details": invalid_details
    }

    logger.info(f"Validation Complete: {valid_count}/{total_count} valid.")
    
    # Save summary report if output_dir is provided
    if output_dir:
        output_path = Path(output_dir) / "validation_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Validation report saved to: {output_path}")

    return summary

def main():
    """
    Entry point for CLI execution.
    Usage: python code/validate_graphs.py
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate network graphs from US1.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/networks",
        help="Directory containing .pkl graph files."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Directory to save validation report JSON."
    )
    
    args = parser.parse_args()
    
    # Ensure input directory exists
    if not Path(args.input).exists():
        print(f"Error: Input directory '{args.input}' does not exist.")
        sys.exit(1)

    summary = validate_all_graphs(args.input, args.output)
    
    # Exit with error if validation failed for any critical reason (e.g. all invalid)
    if summary["total"] > 0 and summary["valid"] == 0:
        print("CRITICAL: No valid graphs found. Pipeline cannot proceed.")
        sys.exit(1)
        
    print(f"Validation finished. Valid: {summary['valid']}, Invalid: {summary['invalid']}")

if __name__ == "__main__":
    main()