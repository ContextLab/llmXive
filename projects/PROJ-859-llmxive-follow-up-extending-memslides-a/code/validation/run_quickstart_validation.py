"""
Quickstart Validation Module

This module implements the validation logic for the llmXive pipeline as defined in quickstart.md.
It executes each step in the strict order, verifies artifact generation, and reports pass/fail status.
"""

import sys
import os
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)


class QuickstartValidationError(Exception):
    """Custom exception for quickstart validation failures."""
    pass


def log_step(message: str) -> None:
    """Log a step message."""
    logger.info(f"STEP: {message}")


def log_success(message: str) -> None:
    """Log a success message."""
    logger.info(f"✓ SUCCESS: {message}")


def log_error(message: str) -> None:
    """Log an error message."""
    logger.error(f"✗ ERROR: {message}")


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    path = Path(file_path)
    exists = path.exists()
    if exists:
        log_success(f"File exists: {file_path}")
    else:
        log_error(f"File missing: {file_path}")
    return exists


def check_file_not_empty(file_path: str) -> bool:
    """Check if a file is not empty."""
    path = Path(file_path)
    if not path.exists():
        log_error(f"Cannot check empty: file missing {file_path}")
        return False
    
    size = path.stat().st_size
    if size > 0:
        log_success(f"File not empty ({size} bytes): {file_path}")
        return True
    else:
        log_error(f"File is empty: {file_path}")
        return False


def validate_json_structure(file_path: str, required_keys: Optional[List[str]] = None) -> bool:
    """Validate JSON structure."""
    if not check_file_exists(file_path):
        return False
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if required_keys:
            missing = [k for k in required_keys if k not in data]
            if missing:
                log_error(f"Missing required keys in {file_path}: {missing}")
                return False
            else:
                log_success(f"JSON structure valid: {file_path}")
                return True
        else:
            log_success(f"JSON file valid: {file_path}")
            return True
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in {file_path}: {e}")
        return False


def validate_csv_structure(file_path: str, required_columns: Optional[List[str]] = None) -> bool:
    """Validate CSV structure."""
    if not check_file_exists(file_path):
        return False
    
    try:
        import csv
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                log_error(f"CSV has no headers: {file_path}")
                return False
            
            if required_columns:
                missing = [c for c in required_columns if c not in headers]
                if missing:
                    log_error(f"Missing required columns in {file_path}: {missing}")
                    return False
                else:
                    log_success(f"CSV structure valid: {file_path}")
                    return True
            else:
                log_success(f"CSV file valid: {file_path}")
                return True
    except Exception as e:
        log_error(f"Error validating CSV {file_path}: {e}")
        return False


def run_script(script_path: str, expected_outputs: List[str]) -> bool:
    """Run a Python script and verify expected outputs are generated."""
    log_step(f"Executing: {script_path}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            log_error(f"Script failed with exit code {result.returncode}")
            log_error(f"STDOUT: {result.stdout}")
            log_error(f"STDERR: {result.stderr}")
            return False
        
        log_success(f"Script completed in {elapsed:.2f}s")
        
        # Verify expected outputs
        all_outputs_exist = True
        for output in expected_outputs:
            if not check_file_exists(output):
                all_outputs_exist = False
            elif not check_file_not_empty(output):
                all_outputs_exist = False
        
        if all_outputs_exist:
            log_success(f"All expected outputs generated for {script_path}")
            return True
        else:
            log_error(f"Some expected outputs missing for {script_path}")
            return False
            
    except subprocess.TimeoutExpired:
        log_error(f"Script timed out: {script_path}")
        return False
    except Exception as e:
        log_error(f"Error running script {script_path}: {e}")
        return False


def validate_pipeline_artifacts() -> Dict[str, Any]:
    """Validate all artifacts produced by the pipeline."""
    results = {
        'training_data': False,
        'held_out_data': False,
        'feature_matrix': False,
        'global_rules': False,
        'per_trace_scores': False,
        'benchmark_results': False,
        'statistical_analysis': False,
        'sensitivity_sweep': False
    }
    
    # Check training data
    training_dir = Path('data/training')
    if training_dir.exists() and any(training_dir.glob('session_*.json')):
        results['training_data'] = True
        log_success("Training data present")
    else:
        log_error("Training data missing")
    
    # Check held-out data
    held_out_dir = Path('data/held_out')
    if held_out_dir.exists() and any(held_out_dir.glob('session_*.json')):
        results['held_out_data'] = True
        log_success("Held-out data present")
    else:
        log_error("Held-out data missing")
    
    # Check feature matrix
    feature_matrix = 'data/processed/feature_matrix.csv'
    if validate_csv_structure(feature_matrix, ['trace_id', 'sequence_entropy', 'tool_repetition_freq', 'arg_semantic_variance']):
        results['feature_matrix'] = True
    else:
        log_error("Feature matrix invalid or missing")
    
    # Check global rules
    global_rules = 'data/processed/rules/global_rules.json'
    if validate_json_structure(global_rules):
        results['global_rules'] = True
    else:
        log_error("Global rules invalid or missing")
    
    # Check per-trace scores
    per_trace_scores = 'data/processed/per_trace_scores.csv'
    if validate_csv_structure(per_trace_scores, ['trace_id', 'rule_count', 'fidelity', 'compressibility_score']):
        results['per_trace_scores'] = True
    else:
        log_error("Per-trace scores invalid or missing")
    
    # Check benchmark results
    benchmark_results = 'data/processed/benchmark_results.json'
    if validate_json_structure(benchmark_results):
        results['benchmark_results'] = True
    else:
        log_error("Benchmark results invalid or missing")
    
    # Check statistical analysis
    stats_analysis = 'data/processed/statistical_analysis.json'
    if validate_json_structure(stats_analysis):
        results['statistical_analysis'] = True
    else:
        log_error("Statistical analysis invalid or missing")
    
    # Check sensitivity sweep
    sensitivity_sweep = 'data/processed/sensitivity_sweep.csv'
    if validate_csv_structure(sensitivity_sweep, ['threshold', 'fidelity_rate', 'latency', 'rule_count']):
        results['sensitivity_sweep'] = True
    else:
        log_error("Sensitivity sweep invalid or missing")
    
    return results


def run_quickstart_validation() -> Tuple[bool, Dict[str, Any]]:
    """
    Execute the full quickstart validation pipeline.
    
    Returns:
        Tuple of (success: bool, results: Dict)
    """
    log_step("Starting Quickstart Validation")
    
    # Define the execution order from quickstart.md
    pipeline_steps = [
        {
            'name': 'Synthetic Trace Generation',
            'script': 'code/generators/run_generation.py',
            'outputs': []  # Multiple session files, checked by directory scan
        },
        {
            'name': 'Metric Extraction',
            'script': 'code/metrics/extract.py',
            'outputs': ['data/processed/feature_matrix.csv']
        },
        {
            'name': 'Rule Induction',
            'script': 'code/models/rule_induction.py',
            'outputs': [
                'data/processed/rules/global_rules.json',
                'data/processed/per_trace_scores.csv',
                'data/processed/aggregate_model_summary.json'
            ]
        },
        {
            'name': 'Delta Calculation',
            'script': 'code/evaluation/calculate_deltas.py',
            'outputs': ['data/processed/accuracy_deltas.csv']
        },
        {
            'name': 'Benchmark Execution',
            'script': 'code/evaluation/benchmark.py',
            'outputs': ['data/processed/benchmark_results.json']
        },
        {
            'name': 'Statistical Analysis',
            'script': 'code/evaluation/stats.py',
            'outputs': ['data/processed/statistical_analysis.json']
        },
        {
            'name': 'Sensitivity Sweep',
            'script': 'code/evaluation/sensitivity_sweep.py',
            'outputs': ['data/processed/sensitivity_sweep.csv']
        }
    ]
    
    all_passed = True
    step_results = {}
    
    for step in pipeline_steps:
        log_step(f"Running: {step['name']}")
        success = run_script(step['script'], step['outputs'])
        step_results[step['name']] = success
        
        if not success:
            all_passed = False
            log_error(f"Pipeline failed at step: {step['name']}")
            break
        else:
            log_success(f"Step completed: {step['name']}")
    
    # Final artifact validation
    log_step("Validating Pipeline Artifacts")
    artifact_results = validate_pipeline_artifacts()
    
    # Summary
    log_step("Validation Summary")
    if all_passed and all(artifact_results.values()):
        log_success("Quickstart validation PASSED")
        return True, {
            'step_results': step_results,
            'artifact_results': artifact_results,
            'overall_status': 'PASSED'
        }
    else:
        log_error("Quickstart validation FAILED")
        return False, {
            'step_results': step_results,
            'artifact_results': artifact_results,
            'overall_status': 'FAILED'
        }


def main():
    """Main entry point for quickstart validation."""
    print("=" * 60)
    print("LLMXive Quickstart Validation")
    print("=" * 60)
    
    try:
        success, results = run_quickstart_validation()
        
        # Write results to file
        results_file = Path('data/quickstart_validation_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        log_success(f"Results saved to {results_file}")
        
        if success:
            print("\n" + "=" * 60)
            print("VALIDATION PASSED")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("VALIDATION FAILED")
            print("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Validation crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
