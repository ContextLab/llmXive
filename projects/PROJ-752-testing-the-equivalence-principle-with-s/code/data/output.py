import os
import json
import hashlib
import shutil
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logging import get_logger, AnalysisError
from models.estimator import OrbitSolution, extract_joint_parameters
from analysis.eotvos import EotvosResult, run_eotvos_analysis

logger = get_logger(__name__)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """Save cleaned SLR data to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def record_checksum(file_path: str, checksums_path: str) -> None:
    """Record SHA256 checksum for a file in a JSON registry."""
    os.makedirs(os.path.dirname(checksums_path), exist_ok=True)
    checksum = compute_sha256(file_path)
    
    registry = {}
    if os.path.exists(checksums_path):
        with open(checksums_path, 'r') as f:
            registry = json.load(f)
    
    registry[os.path.basename(file_path)] = {
        "file": os.path.basename(file_path),
        "sha256": checksum,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open(checksums_path, 'w') as f:
        json.dump(registry, f, indent=2)
    logger.info(f"Recorded checksum for {file_path}")

def ensure_raw_data_preserved(raw_dir: str) -> None:
    """Ensure raw data directory exists and is preserved."""
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir, exist_ok=True)
        logger.info(f"Created raw data directory: {raw_dir}")
    else:
        logger.info(f"Raw data directory already exists: {raw_dir}")

def save_orbit_solution(solution: OrbitSolution, output_path: str) -> None:
    """
    Save OrbitSolution object to JSON.
    Converts the solution and its covariance to a JSON-serializable format.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Extract parameters using the defined interface from estimator.py
    # This ensures we get the joint solution values as required by T025
    params = extract_joint_parameters(solution)
    
    # Convert numpy types to Python native types for JSON serialization
    serializable_data = {
        "ac": float(params['ac']),
        "g": float(params['g']),
        "covariance": params['covariance'].tolist(),
        "converged": solution.converged,
        "residuals_norm": float(solution.residuals_norm),
        "iterations": solution.iterations,
        "timestamp": datetime.utcnow().isoformat(),
        "satellites": solution.satellites if hasattr(solution, 'satellites') else ["LAGEOS-1", "LAGEOS-2", "Etalon-1", "Etalon-2", "Starlette"]
    }
    
    with open(output_path, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    
    logger.info(f"Saved orbit solution to {output_path}")

def save_eotvos_metrics(eotvos_result: EotvosResult, output_path: str) -> None:
    """
    Save EotvosResult object to JSON.
    Converts the result and its confidence interval to a JSON-serializable format.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Ensure the result is computed if not already
    if eotvos_result.eta is None:
        # Fallback: compute from solution if available
        # This assumes eotvos_result contains a reference to the solution
        if hasattr(eotvos_result, 'solution') and eotvos_result.solution:
            params = extract_joint_parameters(eotvos_result.solution)
            eta = abs(params['ac']) / params['g']
            eotvos_result.eta = eta
        else:
            raise AnalysisError("Cannot save EotvosResult: eta is None and no solution available")
    
    serializable_data = {
        "eta": float(eotvos_result.eta),
        "eta_std": float(eotvos_result.eta_std) if eotvos_result.eta_std is not None else None,
        "ci_95_lower": float(eotvos_result.ci_95_lower) if eotvos_result.ci_95_lower is not None else None,
        "ci_95_upper": float(eotvos_result.ci_95_upper) if eotvos_result.ci_95_upper is not None else None,
        "ac": float(eotvos_result.ac) if eotvos_result.ac is not None else None,
        "g": float(eotvos_result.g) if eotvos_result.g is not None else None,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    
    logger.info(f"Saved Eotvos metrics to {output_path}")

def run_output_pipeline(
    solution: Optional[OrbitSolution] = None,
    eotvos_result: Optional[EotvosResult] = None,
    output_dir: str = "data/results"
) -> Dict[str, str]:
    """
    Run the full output pipeline: save orbit solutions and Eotvos metrics.
    Returns a dictionary of output file paths.
    """
    results = {}
    
    if solution is not None:
        orbit_path = os.path.join(output_dir, "orbit_solutions.json")
        save_orbit_solution(solution, orbit_path)
        results["orbit_solutions"] = orbit_path
        
        # Record checksum for orbit solutions
        checksums_path = os.path.join(output_dir, ".checksums.json")
        record_checksum(orbit_path, checksums_path)
    
    if eotvos_result is not None:
        eotvos_path = os.path.join(output_dir, "eotvos_metrics.json")
        save_eotvos_metrics(eotvos_result, eotvos_path)
        results["eotvos_metrics"] = eotvos_path
        
        # Record checksum for Eotvos metrics
        checksums_path = os.path.join(output_dir, ".checksums.json")
        record_checksum(eotvos_path, checksums_path)
    
    return results
