import os
import sys
import json
import logging
from typing import List, Dict, Any, Tuple
from generate.validate_distinctness import validate_distinctness, validate_explanation_pair

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_explanation_pairs(
    symbolic_dir: str,
    neuro_symbolic_dir: str
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Find pairs of symbolic and neuro-symbolic explanations for the same problem.
    
    Args:
        symbolic_dir: Directory containing symbolic explanation JSON files
        neuro_symbolic_dir: Directory containing neuro-symbolic explanation JSON files
    
    Returns:
        List of tuples (symbolic_explanation, neuro_symbolic_explanation)
    """
    pairs = []
    
    if not os.path.exists(symbolic_dir) or not os.path.exists(neuro_symbolic_dir):
        logger.error(f"Directories not found: {symbolic_dir} or {neuro_symbolic_dir}")
        return pairs
    
    # Get all JSON files
    symbolic_files = [f for f in os.listdir(symbolic_dir) if f.endswith('.json')]
    neuro_symbolic_files = [f for f in os.listdir(neuro_symbolic_dir) if f.endswith('.json')]
    
    # Create mapping by problem_id
    symbolic_map = {}
    for filename in symbolic_files:
        filepath = os.path.join(symbolic_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                problem_id = data.get('problem_id')
                if problem_id:
                    symbolic_map[problem_id] = data
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
    
    neuro_symbolic_map = {}
    for filename in neuro_symbolic_files:
        filepath = os.path.join(neuro_symbolic_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                problem_id = data.get('problem_id')
                if problem_id:
                    neuro_symbolic_map[problem_id] = data
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
    
    # Find common problem IDs
    common_ids = set(symbolic_map.keys()) & set(neuro_symbolic_map.keys())
    
    for problem_id in common_ids:
        pairs.append((symbolic_map[problem_id], neuro_symbolic_map[problem_id]))
    
    logger.info(f"Found {len(pairs)} explanation pairs")
    return pairs

def run_batch_validation(
    pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    threshold: float = 0.3,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run distinctness validation on a batch of explanation pairs.
    
    Args:
        pairs: List of (symbolic, neuro_symbolic) explanation pairs
        threshold: Maximum allowed Jaccard similarity
        output_path: Optional path to save results JSON
    
    Returns:
        Validation report dictionary
    """
    results = {
        "total_pairs": len(pairs),
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for i, (symbolic, neuro_symbolic) in enumerate(pairs):
        problem_id = symbolic.get('problem_id', f'unknown_{i}')
        is_valid, report = validate_explanation_pair(symbolic, neuro_symbolic, threshold)
        
        result_entry = {
            "problem_id": problem_id,
            "is_valid": is_valid,
            "checks": report['checks']
        }
        
        results["details"].append(result_entry)
        
        if is_valid:
            results["passed"] += 1
        else:
            results["failed"] += 1
            logger.warning(f"Validation failed for {problem_id}")
    
    results["pass_rate"] = results["passed"] / results["total_pairs"] if results["total_pairs"] > 0 else 0.0
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation results saved to {output_path}")
    
    return results

def main():
    """
    Main entry point for running distinctness validation.
    
    Usage:
        python code/generate/run_distinctness_validation.py
    
    Expected directory structure:
        data/explanations/symbolic/
        data/explanations/neuro_symbolic/
    
    Output:
        data/validation/distinctness_report.json
    """
    logger.info("Starting batch distinctness validation")
    
    # Define paths
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    symbolic_dir = os.path.join(project_root, "data", "explanations", "symbolic")
    neuro_symbolic_dir = os.path.join(project_root, "data", "explanations", "neuro_symbolic")
    output_path = os.path.join(project_root, "data", "validation", "distinctness_report.json")
    
    # Find pairs
    pairs = find_explanation_pairs(symbolic_dir, neuro_symbolic_dir)
    
    if not pairs:
        logger.warning("No explanation pairs found. Validation cannot proceed.")
        return 1
    
    # Run validation
    results = run_batch_validation(pairs, threshold=0.3, output_path=output_path)
    
    # Print summary
    print(json.dumps({
        "total": results["total_pairs"],
        "passed": results["passed"],
        "failed": results["failed"],
        "pass_rate": results["pass_rate"]
    }, indent=2))
    
    if results["failed"] > 0:
        logger.error(f"Validation failed for {results['failed']} pairs")
        return 1
    
    logger.info("All validations passed")
    return 0

if __name__ == "__main__":
    exit(main())
