"""
Outlier detection for extreme topological defects in amorphous silicon graphs.

Identifies samples where >15% of atoms have coordination number < 3 or > 6.
Excludes such samples and logs warnings.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Set
import numpy as np

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_graph_metrics(graphs_dir: Path) -> Dict[str, Any]:
    """
    Load graph metrics from processed graphs directory.
    
    Args:
        graphs_dir: Path to directory containing graph pickle files
        
    Returns:
        Dictionary mapping sample_id to graph data
    """
    graphs = {}
    graphs_path = Path(graphs_dir)
    
    if not graphs_path.exists():
        logger.error(f"Graphs directory not found: {graphs_path}")
        return graphs
        
    for pickle_file in graphs_path.glob("*.pkl"):
        try:
            with open(pickle_file, 'rb') as f:
                graph_data = pickle.load(f)
                sample_id = graph_data.get('graph_id', pickle_file.stem)
                graphs[sample_id] = graph_data
                logger.info(f"Loaded graph: {sample_id}")
        except Exception as e:
            logger.error(f"Failed to load {pickle_file}: {e}")
            
    return graphs

def extract_node_degrees(graph_data: Dict[str, Any]) -> List[int]:
    """
    Extract node degrees from graph data.
    
    Args:
        graph_data: Dictionary containing graph structure with 'nodes' list
        
    Returns:
        List of node degrees
    """
    nodes = graph_data.get('nodes', [])
    degrees = [node.get('degree', 0) for node in nodes]
    return degrees

def calculate_defect_ratio(degrees: List[int], min_coord: int = 3, max_coord: int = 6) -> float:
    """
    Calculate the ratio of defective atoms (coord < min_coord or coord > max_coord).
    
    Args:
        degrees: List of node coordination numbers
        min_coord: Minimum acceptable coordination number (default: 3)
        max_coord: Maximum acceptable coordination number (default: 6)
        
    Returns:
        Ratio of defective atoms (float between 0 and 1)
    """
    if not degrees:
        return 0.0
        
    defective_count = sum(1 for d in degrees if d < min_coord or d > max_coord)
    return defective_count / len(degrees)

def detect_outliers(
    graphs: Dict[str, Any],
    defect_threshold: float = 0.15,
    min_coord: int = 3,
    max_coord: int = 6
) -> Set[str]:
    """
    Detect outlier samples with excessive topological defects.
    
    A sample is considered an outlier if more than `defect_threshold` (default 15%)
    of its atoms have coordination < min_coord or > max_coord.
    
    Args:
        graphs: Dictionary of sample_id -> graph_data
        defect_threshold: Maximum allowed defect ratio (default: 0.15)
        min_coord: Minimum acceptable coordination number
        max_coord: Maximum acceptable coordination number
        
    Returns:
        Set of sample_ids that are outliers
    """
    outliers = set()
    
    for sample_id, graph_data in graphs.items():
        degrees = extract_node_degrees(graph_data)
        defect_ratio = calculate_defect_ratio(degrees, min_coord, max_coord)
        
        if defect_ratio > defect_threshold:
            outliers.add(sample_id)
            logger.warning(
                f"OUTLIER DETECTED: Sample '{sample_id}' has {defect_ratio:.2%} "
                f"defective atoms (coord < {min_coord} or > {max_coord}). "
                f"Threshold: {defect_threshold:.2%}"
            )
            
    return outliers

def write_excluded_samples(
    excluded_ids: Set[str],
    output_path: Path,
    defect_log_path: Path
) -> None:
    """
    Write excluded sample IDs to JSON and log warnings.
    
    Args:
        excluded_ids: Set of sample IDs to exclude
        output_path: Path to write excluded_samples.json
        defect_log_path: Path to write defect_log.txt
    """
    # Ensure parent directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    defect_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write excluded samples JSON
    excluded_data = {
        "excluded_samples": list(excluded_ids),
        "count": len(excluded_ids),
        "reason": "Extreme topological defects (>15% atoms with coordination < 3 or > 6)"
    }
    
    with open(output_path, 'w') as f:
        json.dump(excluded_data, f, indent=2)
    logger.info(f"Written excluded samples to: {output_path}")
    
    # Write defect log
    with open(defect_log_path, 'w') as f:
        f.write("Topological Defect Log\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total excluded samples: {len(excluded_ids)}\n")
        f.write(f"Exclusion criteria: >15% atoms with coordination < 3 or > 6\n\n")
        
        for sample_id in sorted(excluded_ids):
            f.write(f"Sample ID: {sample_id}\n")
            f.write(f"  Status: EXCLUDED\n")
            f.write(f"  Reason: Extreme topological defects detected\n")
            f.write("-" * 30 + "\n")
            
    logger.info(f"Written defect log to: {defect_log_path}")

def main():
    """Main entry point for outlier detection."""
    config = get_config()
    paths = get_paths()
    
    graphs_dir = paths.get('processed_graphs', paths['data'] / 'processed' / 'graphs')
    output_dir = paths['data'] / 'processed' / 'graphs'
    
    excluded_samples_path = output_dir / 'excluded_samples.json'
    defect_log_path = output_dir / 'defect_log.txt'
    
    # Get configuration parameters
    defect_threshold = config.get('outlier_detection', {}).get('defect_threshold', 0.15)
    min_coord = config.get('outlier_detection', {}).get('min_coordination', 3)
    max_coord = config.get('outlier_detection', {}).get('max_coordination', 6)
    
    logger.info(f"Starting outlier detection with threshold: {defect_threshold:.2%}")
    logger.info(f"Coordination range: [{min_coord}, {max_coord}]")
    
    # Load graph metrics
    graphs = load_graph_metrics(graphs_dir)
    if not graphs:
        logger.warning("No graphs found to process")
        # Write empty excluded list
        write_excluded_samples(set(), excluded_samples_path, defect_log_path)
        return
        
    logger.info(f"Loaded {len(graphs)} graphs for analysis")
    
    # Detect outliers
    excluded_ids = detect_outliers(
        graphs,
        defect_threshold=defect_threshold,
        min_coord=min_coord,
        max_coord=max_coord
    )
    
    logger.info(f"Detected {len(excluded_ids)} outlier samples")
    
    # Write results
    write_excluded_samples(excluded_ids, excluded_samples_path, defect_log_path)
    
    logger.info("Outlier detection complete")

if __name__ == '__main__':
    main()
