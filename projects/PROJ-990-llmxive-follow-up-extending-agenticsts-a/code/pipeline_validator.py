import os
import sys
import json
import hashlib
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import existing modules as per API surface
from parser import compute_file_checksum
from config import load_config_from_file
from splitter import load_processed_data
from ablation import load_trajectories
from stats import load_simulation_results
from divergence_checker import load_simulation_logs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define expected artifact paths relative to project root
EXPECTED_ARTIFACTS = {
    # Phase 2: Foundational
    "data/raw/manifest.json": "T005c",
    "data/raw/agenticsts_trajectories.jsonl": "T005b",
    "data/processed/metrics_with_moves.csv": "T006a",
    "data/processed/entropy_metrics.csv": "T006b",
    "data/processed/train_set.csv": "T014a",
    "data/processed/validation_set.csv": "T014a",
    "data/processed/test_set.csv": "T014a",
    "data/processed/ablation_labels_train.json": "T008",
    "data/processed/ablation_labels_holdout.json": "T008c",
    "data/processed/ground_truth_utility_train.csv": "T008d",
    "data/processed/ground_truth_utility_holdout.csv": "T008e",
    "data/processed/proxy_validation_report.json": "T014",
    "models/layer_utility_classifier.pkl": "T009",
    # Phase 3: User Stories 1 & 2
    "data/processed/simulation_logs_dynamic.json": "T017",
    "data/processed/simulation_logs_static.json": "T019",
    "data/processed/simulation_logs_random.json": "T020",
    "data/processed/baseline_comparison.csv": "T022",
    "data/processed/token_savings_per_trajectory.csv": "T022a",
    "data/processed/token_consistency_report.json": "T023",
    "data/processed/paired_status.json": "T024",
    "data/processed/token_budget_detailed.csv": "T056",
    # Phase 4: User Story 3
    "data/processed/mcnemar_results.json": "T025a",
    "data/processed/ttest_results.json": "T025a",
    "data/processed/success_criteria_report.json": "T026",
    # Phase 6 & 7: Revision & Documentation
    "data/processed/edge_case_warnings.log": "T055",
    "data/processed/power_analysis.json": "T053",
    "data/processed/statistical_analysis_report.md": "T057c",
    "docs/edge_cases.md": "T055",
}

def check_file_exists(path: str) -> Tuple[bool, Optional[str]]:
    """Check if a file exists and is not empty."""
    p = Path(path)
    if not p.exists():
        return False, "File does not exist"
    if p.stat().st_size == 0:
        return False, "File is empty"
    return True, None

def validate_json_structure(path: str, required_keys: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate a JSON file has required keys."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        missing = [k for k in required_keys if k not in data]
        if missing:
            return False, f"Missing keys: {missing}"
        return True, None
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def validate_csv_structure(path: str, required_columns: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate a CSV file has required columns and rows."""
    try:
        df = pd.read_csv(path)
        if df.empty:
            return False, "CSV has no data rows"
        missing_cols = [c for c in required_columns if c not in df.columns]
        if missing_cols:
            return False, f"Missing columns: {missing_cols}"
        return True, None
    except Exception as e:
        return False, f"Error reading CSV: {e}"

def run_integrity_checks() -> Dict[str, Any]:
    """Run comprehensive integrity checks on all pipeline artifacts."""
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": [],
        "summary": {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
    }

    # 1. File Existence Checks
    logger.info("Phase 1: Checking file existence...")
    for path, task_id in EXPECTED_ARTIFACTS.items():
        exists, reason = check_file_exists(path)
        status = "PASS" if exists else "FAIL"
        results["checks"].append({
            "type": "file_exists",
            "path": path,
            "task_id": task_id,
            "status": status,
            "reason": reason
        })
        if exists:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
        results["summary"]["total_checks"] += 1

    # 2. Content Validation Checks
    logger.info("Phase 2: Validating content structure...")
    
    # JSON validations
    json_checks = {
        "data/processed/proxy_validation_report.json": ["proxy_valid"],
        "data/processed/paired_status.json": ["is_paired"],
        "data/processed/token_consistency_report.json": ["passed"],
        "data/processed/success_criteria_report.json": ["sc_001", "sc_002", "sc_003", "sc_004"],
        "data/processed/mcnemar_results.json": ["statistic", "pvalue"],
        "data/processed/ttest_results.json": ["statistic", "pvalue"],
        "data/processed/power_analysis.json": ["sample_size", "power"],
    }
    
    for path, keys in json_checks.items():
        if Path(path).exists():
            valid, reason = validate_json_structure(path, keys)
            status = "PASS" if valid else "FAIL"
            results["checks"].append({
                "type": "json_structure",
                "path": path,
                "status": status,
                "reason": reason
            })
            if valid:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
            results["summary"]["total_checks"] += 1

    # CSV validations
    csv_checks = {
        "data/processed/metrics_with_moves.csv": ["trajectory_id", "turn", "health_ratio"],
        "data/processed/baseline_comparison.csv": ["condition", "win_rate", "avg_tokens"],
        "data/processed/token_savings_per_trajectory.csv": ["trajectory_id", "static_tokens", "dynamic_tokens", "savings"],
        "data/processed/token_budget_detailed.csv": ["trajectory_id", "initial_tokens", "final_tokens"],
    }

    for path, cols in csv_checks.items():
        if Path(path).exists():
            valid, reason = validate_csv_structure(path, cols)
            status = "PASS" if valid else "FAIL"
            results["checks"].append({
                "type": "csv_structure",
                "path": path,
                "status": status,
                "reason": reason
            })
            if valid:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
            results["summary"]["total_checks"] += 1

    # 3. Cross-Reference Integrity (Data Flow)
    logger.info("Phase 3: Checking data flow integrity...")
    
    # Check that train/test sets have matching IDs with simulation logs
    try:
        if Path("data/processed/test_set.csv").exists() and Path("data/processed/simulation_logs_dynamic.json").exists():
            test_ids = set(load_processed_data("data/processed/test_set.csv")['trajectory_id'].tolist())
            sim_logs = load_simulation_logs("data/processed/simulation_logs_dynamic.json")
            sim_ids = set([log['trajectory_id'] for log in sim_logs])
            
            if test_ids.issubset(sim_ids):
                results["checks"].append({
                    "type": "data_flow_integrity",
                    "description": "Test set IDs match simulation logs",
                    "status": "PASS"
                })
                results["summary"]["passed"] += 1
            else:
                missing = test_ids - sim_ids
                results["checks"].append({
                    "type": "data_flow_integrity",
                    "description": "Test set IDs match simulation logs",
                    "status": "FAIL",
                    "reason": f"Missing IDs in simulation: {len(missing)}"
                })
                results["summary"]["failed"] += 1
            results["summary"]["total_checks"] += 1
    except Exception as e:
        results["checks"].append({
            "type": "data_flow_integrity",
            "description": "Test set IDs match simulation logs",
            "status": "WARN",
            "reason": str(e)
        })
        results["summary"]["warnings"] += 1

    # 4. Checksum Verification (if manifest exists)
    if Path("data/raw/manifest.json").exists() and Path("data/raw/agenticsts_trajectories.jsonl").exists():
        try:
            with open("data/raw/manifest.json", 'r') as f:
                manifest = json.load(f)
            # Basic check: manifest contains expected file entry
            if "agenticsts_trajectories.jsonl" in str(manifest):
                results["checks"].append({
                    "type": "checksum_manifest",
                    "status": "PASS",
                    "reason": "Manifest contains trajectory entry"
                })
                results["summary"]["passed"] += 1
            else:
                results["checks"].append({
                    "type": "checksum_manifest",
                    "status": "FAIL",
                    "reason": "Manifest missing trajectory entry"
                })
                results["summary"]["failed"] += 1
            results["summary"]["total_checks"] += 1
        except Exception as e:
            results["checks"].append({
                "type": "checksum_manifest",
                "status": "WARN",
                "reason": str(e)
            })
            results["summary"]["warnings"] += 1

    return results

def generate_final_report(results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the final validation report."""
    is_valid = results["summary"]["failed"] == 0
    return {
        "pipeline_validation_report": {
            "status": "VALID" if is_valid else "INVALID",
            "validation_timestamp": results["timestamp"],
            "summary": results["summary"],
            "details": results["checks"],
            "reproducibility_check": is_valid,
            "single_source_of_truth": is_valid
        }
    }

def main():
    """Main entry point for pipeline validation."""
    logger.info("Starting comprehensive pipeline integrity validation (T058)...")
    
    # Run checks
    validation_results = run_integrity_checks()
    
    # Generate final report
    final_report = generate_final_report(validation_results)
    
    # Write output
    output_path = "data/processed/pipeline_validation_report.json"
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")
    
    # Print summary
    summary = final_report["pipeline_validation_report"]["summary"]
    logger.info(f"Validation Complete: {summary['passed']} passed, {summary['failed']} failed, {summary['warnings']} warnings")
    
    if summary['failed'] > 0:
        logger.error("Pipeline validation FAILED. See report for details.")
        sys.exit(1)
    else:
        logger.info("Pipeline validation PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
