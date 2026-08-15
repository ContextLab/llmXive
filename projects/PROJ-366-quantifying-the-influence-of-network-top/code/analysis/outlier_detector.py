import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Set
import numpy as np

from config import get_config, get_paths

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_graph_metrics(graph_dir: Path) -> Dict[str, Any]:
    """
    Load topology metrics for all graphs in the directory.
    Expects metrics files (e.g., from topology_extractor) or graph pickles containing metrics.
    For this implementation, we assume graph pickle files contain a 'metrics' key with node degrees.
    """
    metrics_data = {}
    graph_files = list(graph_dir.glob("*.pkl"))
    
    if not graph_files:
        logger.warning(f"No graph files found in {graph_dir}")
        return metrics_data

    for file_path in graph_files:
        try:
            with open(file_path, 'rb') as f:
                graph_data = pickle.load(f)
            
            sample_id = file_path.stem
            # Extract node degrees. Assuming graph_data has 'node_degrees' or 'metrics'['node_degrees']
            node_degrees = []
            if 'node_degrees' in graph_data:
                node_degrees = graph_data['node_degrees']
            elif 'metrics' in graph_data and 'node_degrees' in graph_data['metrics']:
                node_degrees = graph_data['metrics']['node_degrees']
            else:
                logger.warning(f"Could not find node_degrees in {file_path}, skipping.")
                continue

            metrics_data[sample_id] = {
                "path": str(file_path),
                "node_degrees": node_degrees
            }
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            continue

    return metrics_data

def extract_node_degrees(metrics_data: Dict[str, Any]) -> Dict[str, List[int]]:
    """Extract just the node degree lists keyed by sample ID."""
    return {sid: data["node_degrees"] for sid, data in metrics_data.items()}

def calculate_defect_ratio(node_degrees: List[int], min_coord: int = 3, max_coord: int = 6) -> float:
    """
    Calculate the ratio of atoms with coordination < min_coord or > max_coord.
    """
    if not node_degrees:
        return 0.0
    
    defect_count = sum(1 for d in node_degrees if d < min_coord or d > max_coord)
    return defect_count / len(node_degrees)

def detect_outliers(
    metrics_data: Dict[str, Any], 
    threshold: float = 0.15, 
    min_coord: int = 3, 
    max_coord: int = 6
) -> Set[str]:
    """
    Identify samples where > threshold% of atoms are defects (coord < min_coord or > max_coord).
    Returns a set of sample IDs that are outliers.
    """
    outlier_ids = set()
    
    for sample_id, data in metrics_data.items():
        node_degrees = data["node_degrees"]
        ratio = calculate_defect_ratio(node_degrees, min_coord, max_coord)
        
        if ratio > threshold:
            outlier_ids.add(sample_id)
            logger.info(f"Sample {sample_id} flagged as outlier: defect ratio {ratio:.2%} > {threshold:.2%}")
    
    return outlier_ids

def write_excluded_samples(outlier_ids: Set[str], output_path: Path) -> None:
    """
    Write the list of excluded sample IDs to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "excluded_samples": list(outlier_ids),
        "count": len(outlier_ids),
        "reason": "Topological defect ratio > 15% (coord < 3 or > 6)"
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Written excluded samples to {output_path}")

def main():
    """
    Main entry point for the outlier detection pipeline.
    Reads config, loads graphs, detects outliers, and writes exclusion list if enabled.
    """
    config = get_config()
    paths = get_paths()
    
    graph_dir = paths.get("graphs_dir", paths["data_processed"] / "graphs")
    output_file = paths["data_processed"] / "graphs" / "excluded_samples.json"
    
    enforce_exclusion = config.get("enforce_exclusion", False)
    threshold = config.get("outlier_defect_threshold", 0.15)
    min_coord = config.get("min_valid_coordination", 3)
    max_coord = config.get("max_valid_coordination", 6)

    if not enforce_exclusion:
        logger.warning("Configuration 'enforce_exclusion' is False. Skipping outlier detection and exclusion file generation.")
        return

    logger.info(f"Loading graph metrics from {graph_dir}")
    metrics_data = load_graph_metrics(Path(graph_dir))
    
    if not metrics_data:
        logger.warning("No metrics data loaded. Cannot detect outliers.")
        return

    logger.info(f"Detecting outliers with threshold {threshold} (coord < {min_coord} or > {max_coord})")
    outlier_ids = detect_outliers(metrics_data, threshold, min_coord, max_coord)
    
    if not outlier_ids:
        logger.info("No outliers detected.")
        # Still write an empty file to indicate the check was performed if enforce_exclusion is true?
        # The task says "write excluded IDs ... IF flag is true". An empty list is valid.
        write_excluded_samples(set(), output_file)
    else:
        write_excluded_samples(outlier_ids, output_file)

    logger.info("Outlier detection complete.")

if __name__ == "__main__":
    main()
