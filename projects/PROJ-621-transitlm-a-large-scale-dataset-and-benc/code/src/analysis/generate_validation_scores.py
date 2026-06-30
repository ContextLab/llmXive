import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
from src.cli.run_benchmark import load_test_od_pairs, run_benchmark
from src.models.validation import validate_route_sequence, ValidationResult
from src.lib.text_utils import parse_llm_route_output, strip_conversational_filler
from src.lib.config import get_logger, set_seed
from src.contracts.models import ValidationResult as ValidationResultContract

def generate_validation_scores(
    od_pairs_path: Path,
    graph_path: Path,
    output_path: Path,
    model_output_path: Optional[Path] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generates validation scores for the held-out set.
    
    If model_output_path is provided, it loads pre-generated model outputs.
    Otherwise, it runs the benchmark to generate outputs first.
    
    Returns a dictionary of validation results keyed by O-D pair ID.
    """
    set_seed(seed)
    logger = get_logger(__name__)
    
    # Load O-D pairs
    logger.info(f"Loading O-D pairs from {od_pairs_path}")
    od_pairs = load_test_od_pairs(od_pairs_path)
    
    if not od_pairs:
        logger.error("No O-D pairs found in the input file.")
        return {}
    
    # If no pre-generated outputs, run the benchmark
    if model_output_path is None:
        logger.info("No model output path provided. Running benchmark to generate outputs...")
        # We need to generate outputs first. Since run_benchmark expects an output path,
        # we'll use a temporary one or assume it writes to a standard location.
        # For this task, we assume run_benchmark writes to data/results/model_outputs.json
        temp_output = od_pairs_path.parent / "model_outputs.json"
        run_benchmark(od_pairs_path, temp_output, graph_path, n_samples=len(od_pairs))
        model_output_path = temp_output
    
    # Load model outputs
    logger.info(f"Loading model outputs from {model_output_path}")
    with open(model_output_path, 'r') as f:
        model_outputs = json.load(f)
    
    # Load graph for validation
    from src.lib.splitter import load_graph_from_file
    logger.info(f"Loading graph from {graph_path}")
    graph_data = load_graph_from_file(graph_path)
    
    validation_results = {}
    
    for i, od_pair in enumerate(od_pairs):
        od_id = od_pair.get('id', f'od_{i}')
        origin = od_pair['origin']
        destination = od_pair['destination']
        
        # Get model output for this pair
        model_output = model_outputs.get(od_id, "")
        
        # Parse the LLM output
        cleaned_text = strip_conversational_filler(model_output)
        stations = parse_llm_route_output(cleaned_text)
        
        if not stations:
            logger.warning(f"No stations extracted for {od_id}. Marking as invalid.")
            validation_results[od_id] = {
                "origin": origin,
                "destination": destination,
                "predicted_sequence": [],
                "is_valid": False,
                "exact_match_score": 0.0,
                "connectivity_valid": False,
                "has_infinite_loop": False,
                "has_hallucinated_station": False,
                "error": "No stations extracted"
            }
            continue
        
        # Validate the sequence
        result = validate_route_sequence(
            graph=graph_data,
            origin=origin,
            destination=destination,
            predicted_sequence=stations
        )
        
        validation_results[od_id] = {
            "origin": origin,
            "destination": destination,
            "predicted_sequence": stations,
            "is_valid": result.is_valid,
            "exact_match_score": result.exact_match_score,
            "connectivity_valid": result.connectivity_valid,
            "has_infinite_loop": result.has_infinite_loop,
            "has_hallucinated_station": result.has_hallucinated_station,
            "error": result.error_message if result.error_message else None
        }
        
        logger.debug(f"Validated {od_id}: valid={result.is_valid}, score={result.exact_match_score}")
    
    # Calculate summary statistics
    total = len(validation_results)
    valid_count = sum(1 for v in validation_results.values() if v['is_valid'])
    avg_score = sum(v['exact_match_score'] for v in validation_results.values()) / total if total > 0 else 0.0
    
    summary = {
        "total_samples": total,
        "valid_routes": valid_count,
        "invalid_routes": total - valid_count,
        "validity_rate": valid_count / total if total > 0 else 0.0,
        "average_exact_match_score": avg_score
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    output_data = {
        "summary": summary,
        "results": validation_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Validation scores written to {output_path}")
    logger.info(f"Summary: {summary}")
    
    return output_data

def main():
    """
    Entry point for generating validation scores.
    
    Usage:
    python -m src.analysis.generate_validation_scores
    """
    logger = get_logger(__name__)
    
    # Default paths
    project_root = Path(__file__).resolve().parent.parent.parent
    od_pairs_path = project_root / "data" / "processed" / "test_od_pairs.json"
    graph_path = project_root / "data" / "processed" / "gtfs_graph.json"
    output_path = project_root / "data" / "results" / "validation_scores.json"
    
    # Parse arguments if provided
    if len(sys.argv) > 1:
        od_pairs_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        graph_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])
    
    if not od_pairs_path.exists():
        logger.error(f"O-D pairs file not found: {od_pairs_path}")
        sys.exit(1)
    
    if not graph_path.exists():
        logger.error(f"Graph file not found: {graph_path}")
        sys.exit(1)
    
    try:
        generate_validation_scores(od_pairs_path, graph_path, output_path)
    except Exception as e:
        logger.exception(f"Failed to generate validation scores: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
