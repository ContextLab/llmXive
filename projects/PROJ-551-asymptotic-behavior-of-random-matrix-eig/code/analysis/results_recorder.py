import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import from existing API surface
from utils.config import get_project_paths, load_config
from data_models import SimulationRun

logger = logging.getLogger(__name__)

def load_single_run_results(path: Path) -> Dict[str, Any]:
    """Load existing single run results if present."""
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_single_run_results(data: Dict[str, Any], path: Path) -> None:
    """Save results to the specified JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Results saved to {path}")

def create_result_record(
    run_id: str,
    N: int,
    theta: float,
    seed: int,
    eigenvalues: List[float],
    outlier_flag: bool,
    traceability: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a result record matching the schema:
    {"run_id": str, "N": int, "theta": float, "seed": int, "eigenvalues": list, "outlier_flag": bool}
    """
    record = {
        "run_id": run_id,
        "N": N,
        "theta": theta,
        "seed": seed,
        "eigenvalues": eigenvalues,
        "outlier_flag": outlier_flag
    }
    if traceability:
        record["traceability"] = traceability
    return record

def run_single_run_recorder(
    run_id: str,
    N: int,
    theta: float,
    seed: int,
    eigenvalues: List[float],
    outlier_flag: bool,
    traceability: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Record simulation results to data/processed/single_run_results.json.
    
    This function satisfies Constitution Principle III (Data Hygiene) by
    persisting the full state of a simulation run including eigenvalues,
    perturbation parameters, and traceability information.
    """
    if output_path is None:
        config = load_config()
        paths = get_project_paths()
        output_path = paths["processed"] / "single_run_results.json"
    
    # Create the result record
    record = create_result_record(
        run_id=run_id,
        N=N,
        theta=theta,
        seed=seed,
        eigenvalues=eigenvalues,
        outlier_flag=outlier_flag,
        traceability=traceability
    )
    
    # Save to disk
    save_single_run_results(record, output_path)
    
    return record

def main():
    """CLI entry point for T015: results recording."""
    parser = argparse.ArgumentParser(description="Record simulation results to JSON")
    parser.add_argument("--run-id", type=str, required=True, help="Unique run identifier")
    parser.add_argument("--N", type=int, required=True, help="Matrix dimension")
    parser.add_argument("--theta", type=float, required=True, help="Perturbation norm")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--eigenvalues", type=str, required=True, 
                      help="Comma-separated list of eigenvalues")
    parser.add_argument("--outlier-flag", type=bool, default=False,
                      help="Whether an outlier was detected")
    parser.add_argument("--traceability", type=str, default=None,
                      help="JSON string of traceability info")
    parser.add_argument("--output", type=str, default=None,
                      help="Output file path (default: data/processed/single_run_results.json)")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse eigenvalues
    eigenvalues = [float(x.strip()) for x in args.eigenvalues.split(',')]
    
    # Parse traceability if provided
    traceability = None
    if args.traceability:
        try:
            traceability = json.loads(args.traceability)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse traceability JSON: {e}")
            sys.exit(1)
    
    # Determine output path
    output_path = Path(args.output) if args.output else None
    
    # Record results
    record = run_single_run_recorder(
        run_id=args.run_id,
        N=args.N,
        theta=args.theta,
        seed=args.seed,
        eigenvalues=eigenvalues,
        outlier_flag=args.outlier_flag,
        traceability=traceability,
        output_path=output_path
    )
    
    logger.info(f"Recorded run {record['run_id']} with {len(record['eigenvalues'])} eigenvalues")
    logger.info(f"Outlier flag: {record['outlier_flag']}")

if __name__ == "__main__":
    main()