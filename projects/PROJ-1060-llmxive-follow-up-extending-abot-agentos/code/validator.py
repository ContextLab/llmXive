import json
import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

# Ensure code directory is in path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

logger = logging.getLogger(__name__)

def load_ground_truth(schema_path: str = "data/schemas/ground_truth_mapping.json") -> Dict[str, Any]:
    """Load ground truth schema from JSON file."""
    filepath = Path(schema_path)
    if not filepath.exists():
        logger.warning(f"Ground truth schema not found at {schema_path}, returning empty.")
        return {"nodes": [], "edges": [], "predicates": []}
    
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_reconstruction_error(
    constructed_graph: Any, 
    ground_truth: Dict[str, Any], 
    output_path: str = "data/results/reconstruction_error.json"
) -> Dict[str, float]:
    """
    Calculate reconstruction error between constructed graph and ground truth.
    Writes result to output_path and warnings to validation_warnings.log.
    """
    warnings_log = Path("data/results/validation_warnings.log")
    warnings_log.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract nodes and edges from constructed graph
    if hasattr(constructed_graph, 'nodes'):
        c_nodes = set(constructed_graph.nodes)
        c_edges = set((u, v, d.get('predicate', '')) for u, v, d in constructed_graph.edges(data=True))
    else:
        c_nodes = set()
        c_edges = set()
        
    gt_nodes = set(ground_truth.get("nodes", []))
    gt_edges = set()
    for edge in ground_truth.get("edges", []):
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        pred = edge.get("predicate", "")
        gt_edges.add((src, tgt, pred))
    
    # Calculate errors
    missing_nodes = gt_nodes - c_nodes
    extra_nodes = c_nodes - gt_nodes
    missing_edges = gt_edges - c_edges
    extra_edges = c_edges - gt_edges
    
    total_gt = len(gt_nodes) + len(gt_edges)
    if total_gt == 0:
        error_rate = 0.0
    else:
        error_count = len(missing_nodes) + len(missing_edges)
        error_rate = error_count / total_gt
    
    result = {
        "missing_nodes": list(missing_nodes),
        "extra_nodes": list(extra_nodes),
        "missing_edges": [{"source": s, "target": t, "predicate": p} for s, t, p in missing_edges],
        "extra_edges": [{"source": s, "target": t, "predicate": p} for s, t, p in extra_edges],
        "error_rate": error_rate,
        "total_gt_entities": total_gt,
        "total_constructed_entities": len(c_nodes) + len(c_edges)
    }
    
    # Write warnings if any
    if missing_nodes or missing_edges:
        with open(warnings_log, 'a') as f:
            for node in missing_nodes:
                f.write(f"Missing node: {node}\n")
            for edge in missing_edges:
                f.write(f"Missing edge: {edge['source']} -> {edge['target']} ({edge['predicate']})\n")
    
    # Write result
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

def validate_graph_from_files(graph_path: str, schema_path: str) -> bool:
    """Validate a saved graph against schema."""
    with open(graph_path, 'r') as f:
        graph_data = json.load(f)
    ground_truth = load_ground_truth(schema_path)
    
    allowed_predicates = set(ground_truth.get("predicates", []))
    
    for edge in graph_data.get("edges", []):
        if edge.get("predicate") not in allowed_predicates:
            logger.warning(f"Invalid predicate {edge.get('predicate')} in graph.")
            return False
    return True

def main():
    """CLI entry point for validator."""
    import argparse
    parser = argparse.ArgumentParser(description="Validator Utilities")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    args = parser.parse_args()
    
    if args.demo:
        # Demo
        gt = {"nodes": ["cup", "table"], "edges": [{"source": "cup", "target": "table", "predicate": "on_top_of"}], "predicates": ["on_top_of"]}
        result = calculate_reconstruction_error(None, gt)
        print(f"Error rate: {result['error_rate']}")

if __name__ == "__main__":
    main()