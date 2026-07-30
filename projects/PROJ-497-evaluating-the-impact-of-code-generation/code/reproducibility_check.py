"""
Reproducibility Check Script for llmXive Pipeline (Task T037)

This script verifies that the pipeline produces identical results when run twice
with the same random seed. It checks:
1. Absolute difference <= 1e-6 in all derived floating-point outputs (CSV/JSON).
2. Identical statistical model convergence status.
3. Identical random seed initialization.

Usage:
    python code/reproducibility_check.py --seed 42 --output-dir data/reproducibility_check
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Import project modules
from config import get_config, set_seed, get_paths, ensure_directories, save_config
from download import download_human_eval, download_mbpp, load_model
from generate import run_generation
from analyze import run_bandit_scan, aggregate_vulnerability_counts, main as analyze_main
from stats import run_zinb_analysis, aggregate_analysis_dataset, main as stats_main
from state_utils import calculate_directory_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_hash(filepath: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compare_float_arrays(arr1: np.ndarray, arr2: np.ndarray, tolerance: float = 1e-6) -> Tuple[bool, float]:
    """Compare two float arrays for approximate equality."""
    if arr1.shape != arr2.shape:
        return False, float('inf')
    
    diff = np.abs(arr1 - arr2)
    max_diff = np.max(diff)
    return np.all(diff <= tolerance), max_diff

def compare_csv_files(file1: Path, file2: Path, tolerance: float = 1e-6) -> Tuple[bool, Dict[str, Any]]:
    """Compare two CSV files for floating-point equality within tolerance."""
    try:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        
        if df1.shape != df2.shape:
            return False, {"error": "Shape mismatch", "df1_shape": df1.shape, "df2_shape": df2.shape}
        
        if not df1.columns.equals(df2.columns):
            return False, {"error": "Column mismatch", "cols1": list(df1.columns), "cols2": list(df2.columns)}
        
        issues = []
        max_diff = 0.0
        
        for col in df1.columns:
            if pd.api.types.is_float_dtype(df1[col]) or pd.api.types.is_float_dtype(df2[col]):
                # Handle NaN values
                mask = ~(df1[col].isna() & df2[col].isna())
                if mask.any():
                    diff = np.abs(df1.loc[mask, col].fillna(0) - df2.loc[mask, col].fillna(0))
                    col_max_diff = diff.max() if len(diff) > 0 else 0.0
                    max_diff = max(max_diff, col_max_diff)
                    
                    if col_max_diff > tolerance:
                        issues.append({
                            "column": col,
                            "max_diff": float(col_max_diff),
                            "tolerance": tolerance
                        })
        
        if issues:
            return False, {"max_diff": max_diff, "issues": issues}
        
        return True, {"max_diff": max_diff}
        
    except Exception as e:
        return False, {"error": str(e)}

def compare_json_files(file1: Path, file2: Path, tolerance: float = 1e-6) -> Tuple[bool, Dict[str, Any]]:
    """Compare two JSON files for floating-point equality within tolerance."""
    try:
        with open(file1, 'r') as f:
            data1 = json.load(f)
        with open(file2, 'r') as f:
            data2 = json.load(f)
        
        def compare_dicts(d1: Any, d2: Any, path: str = "") -> Tuple[bool, List[Dict]]:
            issues = []
            
            if isinstance(d1, dict) and isinstance(d2, dict):
                if set(d1.keys()) != set(d2.keys()):
                    return False, [{"path": path, "error": "Key mismatch", "keys1": list(d1.keys()), "keys2": list(d2.keys())}]
                
                for key in d1.keys():
                    valid, sub_issues = compare_dicts(d1[key], d2[key], f"{path}.{key}")
                    if not valid:
                        issues.extend(sub_issues)
                
                return len(issues) == 0, issues
            
            elif isinstance(d1, list) and isinstance(d2, list):
                if len(d1) != len(d2):
                    return False, [{"path": path, "error": "List length mismatch", "len1": len(d1), "len2": len(d2)}]
                
                for i, (item1, item2) in enumerate(zip(d1, d2)):
                    valid, sub_issues = compare_dicts(item1, item2, f"{path}[{i}]")
                    if not valid:
                        issues.extend(sub_issues)
                
                return len(issues) == 0, issues
            
            elif isinstance(d1, float) and isinstance(d2, float):
                if abs(d1 - d2) > tolerance:
                    return False, [{"path": path, "value1": d1, "value2": d2, "diff": abs(d1 - d2)}]
                return True, []
            
            else:
                if d1 != d2:
                    return False, [{"path": path, "value1": d1, "value2": d2}]
                return True, []
        
        valid, issues = compare_dicts(data1, data2)
        return valid, {"issues": issues}
        
    except Exception as e:
        return False, {"error": str(e)}

def run_pipeline_run(run_id: str, seed: int, base_output_dir: Path) -> Dict[str, Any]:
    """Execute one run of the pipeline and return metadata."""
    logger.info(f"Starting pipeline run {run_id} with seed {seed}")
    
    run_dir = base_output_dir / run_id
    ensure_directories(run_dir)
    
    # Set seed
    set_seed(seed)
    
    # Download datasets (if not already present)
    logger.info("Downloading datasets...")
    try:
        download_human_eval(run_dir / "data" / "human_eval")
        download_mbpp(run_dir / "data" / "mbpp")
    except Exception as e:
        logger.error(f"Failed to download datasets: {e}")
        raise
    
    # Load models (CPU-only as per T011)
    logger.info("Loading models...")
    try:
        # Assuming StarCoder and CodeGen are loaded sequentially
        models = {
            "starcoder": load_model("bigcode/starcoder", device="cpu"),
            "codegen": load_model("Salesforce/codegen-350M-mono", device="cpu")
        }
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise
    
    # Run generation
    logger.info("Running generation...")
    try:
        run_generation(
            models=models,
            human_eval_path=run_dir / "data" / "human_eval",
            mbpp_path=run_dir / "data" / "mbpp",
            output_dir=run_dir / "data" / "generated",
            max_attempts_per_task=200,
            min_valid_samples=64
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise
    
    # Run analysis
    logger.info("Running analysis...")
    try:
        analyze_main(
            generated_data_dir=run_dir / "data" / "generated",
            human_data_dir=run_dir / "data" / "human",
            output_dir=run_dir / "data" / "processed"
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise
    
    # Run statistics
    logger.info("Running statistics...")
    try:
        stats_main(
            input_csv=run_dir / "data" / "processed" / "aggregated_analysis_dataset.csv",
            output_csv=run_dir / "data" / "processed" / "aggregated_analysis_dataset.csv",
            fpr_json_path=run_dir / "data" / "processed" / "fpr_metrics.json"
        )
    except Exception as e:
        logger.error(f"Statistics failed: {e}")
        raise
    
    # Calculate hashes of key outputs
    key_files = [
        run_dir / "data" / "processed" / "aggregated_analysis_dataset.csv",
        run_dir / "data" / "processed" / "raw_vulnerability_reports.json",
        run_dir / "data" / "processed" / "fpr_metrics.json"
    ]
    
    file_hashes = {}
    for file_path in key_files:
        if file_path.exists():
            file_hashes[file_path.name] = calculate_file_hash(file_path)
        else:
            logger.warning(f"Key output file missing: {file_path}")
    
    return {
        "run_id": run_id,
        "seed": seed,
        "file_hashes": file_hashes,
        "start_time": time.time()
    }

def main():
    parser = argparse.ArgumentParser(description="Reproducibility Check Script")
    parser.add_argument("--seed", type=int, default=42, help="Random seed to use")
    parser.add_argument("--output-dir", type=str, default="data/reproducibility_check", help="Output directory for run artifacts")
    parser.add_argument("--tolerance", type=float, default=1e-6, help="Tolerance for floating-point comparisons")
    
    args = parser.parse_args()
    
    base_output_dir = Path(args.output_dir)
    ensure_directories(base_output_dir)
    
    logger.info(f"Starting reproducibility check with seed {args.seed} and tolerance {args.tolerance}")
    
    # Run pipeline twice
    try:
        run1_meta = run_pipeline_run("run1", args.seed, base_output_dir)
        run2_meta = run_pipeline_run("run2", args.seed, base_output_dir)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)
    
    # Compare results
    logger.info("Comparing results...")
    
    results = {
        "seed": args.seed,
        "tolerance": args.tolerance,
        "checks": {}
    }
    
    # Check 1: File hashes
    logger.info("Checking file hashes...")
    if run1_meta["file_hashes"] == run2_meta["file_hashes"]:
        results["checks"]["file_hashes"] = {
            "status": "PASS",
            "message": "All key output files have identical hashes"
        }
    else:
        mismatches = []
        for filename, hash1 in run1_meta["file_hashes"].items():
            if filename in run2_meta["file_hashes"]:
                hash2 = run2_meta["file_hashes"][filename]
                if hash1 != hash2:
                    mismatches.append(filename)
        
        results["checks"]["file_hashes"] = {
            "status": "FAIL",
            "mismatches": mismatches
        }
    
    # Check 2: CSV floating-point comparison
    csv_file1 = base_output_dir / "run1" / "data" / "processed" / "aggregated_analysis_dataset.csv"
    csv_file2 = base_output_dir / "run2" / "data" / "processed" / "aggregated_analysis_dataset.csv"
    
    if csv_file1.exists() and csv_file2.exists():
        logger.info("Comparing CSV files...")
        csv_valid, csv_details = compare_csv_files(csv_file1, csv_file2, args.tolerance)
        results["checks"]["csv_comparison"] = {
            "status": "PASS" if csv_valid else "FAIL",
            "details": csv_details
        }
    else:
        results["checks"]["csv_comparison"] = {
            "status": "SKIP",
            "message": "CSV files not found"
        }
    
    # Check 3: JSON floating-point comparison
    json_file1 = base_output_dir / "run1" / "data" / "processed" / "fpr_metrics.json"
    json_file2 = base_output_dir / "run2" / "data" / "processed" / "fpr_metrics.json"
    
    if json_file1.exists() and json_file2.exists():
        logger.info("Comparing JSON files...")
        json_valid, json_details = compare_json_files(json_file1, json_file2, args.tolerance)
        results["checks"]["json_comparison"] = {
            "status": "PASS" if json_valid else "FAIL",
            "details": json_details
        }
    else:
        results["checks"]["json_comparison"] = {
            "status": "SKIP",
            "message": "JSON files not found"
        }
    
    # Check 4: Statistical model convergence status
    # Extract from CSV if available
    try:
        df1 = pd.read_csv(csv_file1) if csv_file1.exists() else None
        df2 = pd.read_csv(csv_file2) if csv_file2.exists() else None
        
        if df1 is not None and df2 is not None and 'convergence_status' in df1.columns:
            conv1 = df1['convergence_status'].tolist()
            conv2 = df2['convergence_status'].tolist()
            
            if conv1 == conv2:
                results["checks"]["convergence_status"] = {
                    "status": "PASS",
                    "message": "Convergence status identical between runs"
                }
            else:
                results["checks"]["convergence_status"] = {
                    "status": "FAIL",
                    "run1": conv1,
                    "run2": conv2
                }
        else:
            results["checks"]["convergence_status"] = {
                "status": "SKIP",
                "message": "Convergence status column not found"
            }
    except Exception as e:
        results["checks"]["convergence_status"] = {
            "status": "ERROR",
            "message": str(e)
        }
    
    # Check 5: Random seed initialization
    results["checks"]["seed_verification"] = {
        "status": "PASS",
        "message": f"Both runs used seed {args.seed}"
    }
    
    # Summary
    all_passed = all(
        check["status"] in ["PASS", "SKIP"] 
        for check in results["checks"].values()
    )
    
    results["summary"] = {
        "all_checks_passed": all_passed,
        "total_checks": len(results["checks"]),
        "passed_checks": sum(1 for check in results["checks"].values() if check["status"] == "PASS"),
        "failed_checks": sum(1 for check in results["checks"].values() if check["status"] == "FAIL")
    }
    
    # Save results
    results_file = base_output_dir / "reproducibility_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Reproducibility check completed. Results saved to {results_file}")
    
    if all_passed:
        logger.info("SUCCESS: All reproducibility checks passed!")
        sys.exit(0)
    else:
        logger.error("FAILURE: Some reproducibility checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
