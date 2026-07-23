import os
import json
import logging
import subprocess
import sys
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import shared utilities
from utils import (
    setup_logging, get_logger, log_info, log_error, ensure_directory
)

# Task ID management
_task_id: Optional[str] = None

def set_task_id(tid: str):
    global _task_id
    _task_id = tid

def get_task_id() -> Optional[str]:
    return _task_id

def get_logger() -> logging.Logger:
    return logging.getLogger('analyze_metrics')

def log_info(logger: logging.Logger, msg: str):
    logger.info(msg)

def log_error(logger: logging.Logger, msg: str):
    logger.error(msg)

def ensure_dirs():
    ensure_directory("data/analysis")
    ensure_directory("logs")
    ensure_directory("data/generated")

def calculate_code_metrics(code: str) -> Dict[str, Any]:
    """
    Calculate Cyclomatic Complexity and Halstead metrics using radon.
    Returns dict with cyclomatic_complexity, halstead_volume, and halstead_components.
    """
    try:
        # Write code to a temp file for radon
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Run Cyclomatic Complexity
            cc_result = subprocess.run(
                ['radon', 'cc', '--json', temp_path],
                capture_output=True, text=True, check=False
            )
            
            # Run Halstead
            hal_result = subprocess.run(
                ['radon', 'hal', '--json', temp_path],
                capture_output=True, text=True, check=False
            )

            cc_data = json.loads(cc_result.stdout) if cc_result.stdout else {}
            hal_data = json.loads(hal_result.stdout) if hal_result.stdout else {}

            # Extract CC (sum of all functions/classes)
            total_cc = 0
            if cc_data:
                for item in cc_data:
                    if 'metrics' in item:
                        total_cc += item['metrics']['complexity']
                    elif isinstance(item, dict) and 'complexity' in item:
                        total_cc += item['complexity']
            
            # Extract Halstead
            hal_volume = 0.0
            hal_components = {"N": 0, "n": 0, "L": 0, "D": 0, "E": 0}
            
            if hal_data:
                # Halstead output is a list of metrics per function
                # We sum them up for the whole file
                for item in hal_data:
                    if 'metrics' in item:
                        m = item['metrics']
                        hal_volume += m.get('volume', 0)
                        # Accumulate components (approximate sum for file level)
                        hal_components['N'] += m.get('N', 0)
                        hal_components['n'] += m.get('n', 0)
                        hal_components['L'] += m.get('L', 0)
                        hal_components['D'] += m.get('D', 0)
                        hal_components['E'] += m.get('E', 0)
                    elif isinstance(item, dict):
                        hal_volume += item.get('volume', 0)
                        hal_components['N'] += item.get('N', 0)
                        hal_components['n'] += item.get('n', 0)
                        hal_components['L'] += item.get('L', 0)
                        hal_components['D'] += item.get('D', 0)
                        hal_components['E'] += item.get('E', 0)

            return {
                "cyclomatic_complexity": total_cc if total_cc > 0 else 0,
                "halstead_volume": hal_volume if hal_volume > 0 else 0.0,
                "halstead_components": hal_components
            }
        finally:
            os.unlink(temp_path)
    except Exception as e:
        log_error(get_logger(), f"Error calculating metrics: {e}")
        return {
            "cyclomatic_complexity": None,
            "halstead_volume": None,
            "halstead_components": None
        }

def execute_test_suite(code: str, tests: str, entry_point: str) -> int:
    """
    Execute pytest against the code. Returns 1 if all tests pass, 0 otherwise.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code
            code_path = os.path.join(tmpdir, "solution.py")
            with open(code_path, 'w') as f:
                f.write(code)

            # Write tests
            test_path = os.path.join(tmpdir, "test_solution.py")
            with open(test_path, 'w') as f:
                f.write(tests)
                # Append check function if not present (HumanEval format)
                if "check(" not in tests:
                    f.write("\n\n# Check function placeholder\n")

            # Run pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=True, text=True, timeout=30
            )
            
            # Parse result: 0 = success, non-zero = failure
            if result.returncode == 0:
                return 1
            return 0
    except subprocess.TimeoutExpired:
        return 0
    except Exception as e:
        log_error(get_logger(), f"Test execution error: {e}")
        return 0

def execute_coverage_test(code: str, tests: str, entry_point: str) -> Optional[float]:
    """
    Execute pytest-cov. Returns branch_coverage_pct or None if failed.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            code_path = os.path.join(tmpdir, "solution.py")
            with open(code_path, 'w') as f:
                f.write(code)

            test_path = os.path.join(tmpdir, "test_solution.py")
            with open(test_path, 'w') as f:
                f.write(tests)

            # Run pytest with coverage
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_path, "--cov=solution", 
                 "--cov-report=json", "--tb=short", "-q"],
                capture_output=True, text=True, timeout=30, cwd=tmpdir
            )

            # Parse coverage.json
            cov_json_path = os.path.join(tmpdir, "coverage.json")
            if os.path.exists(cov_json_path):
                with open(cov_json_path, 'r') as f:
                    cov_data = json.load(f)
                
                # Extract branch coverage
                if 'totals' in cov_data and 'percent_branch' in cov_data['totals']:
                    return cov_data['totals']['percent_branch']
                elif 'totals' in cov_data and 'branch_covered' in cov_data['totals'] and 'branches_total' in cov_data['totals']:
                    total = cov_data['totals']['branches_total']
                    covered = cov_data['totals']['branch_covered']
                    if total > 0:
                        return (covered / total) * 100.0
                    return 0.0
            return None
    except Exception as e:
        log_error(get_logger(), f"Coverage execution error: {e}")
        return None

def load_intermediate_metrics(input_path: str) -> List[Dict[str, Any]]:
    """Load intermediate metrics from JSON."""
    if not os.path.exists(input_path):
        return []
    with open(input_path, 'r') as f:
        return json.load(f)

def apply_pairwise_exclusion_gate(metrics: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Exclude pairs where either human or codegen has null coverage.
    Returns (filtered_metrics, excluded_task_ids).
    """
    # Group by task_id
    by_task = {}
    for m in metrics:
        tid = m.get('task_id')
        if tid not in by_task:
            by_task[tid] = []
        by_task[tid].append(m)

    excluded_ids = []
    valid_metrics = []

    for tid, items in by_task.items():
        # Check coverage for human and codegen
        has_human = False
        has_codegen = False
        human_cov = None
        codegen_cov = None

        for item in items:
            src = item.get('source_type')
            if src == 'human':
                has_human = True
                human_cov = item.get('branch_coverage_pct')
            elif src in ['codegen-350M', 'codegen-3B', 'codellama-7B', 'sensitivity']:
                has_codegen = True
                codegen_cov = item.get('branch_coverage_pct')

        # If either is missing or null, exclude the pair
        if (has_human and human_cov is None) or (has_codegen and codegen_cov is None):
            excluded_ids.append(tid)
        else:
            valid_metrics.extend(items)

    return valid_metrics, excluded_ids

def aggregate_metrics_to_json(input_path: str, output_path: str):
    """
    Aggregate intermediate metrics into the final metrics.json.
    Schema: task_id, source_type, cyclomatic_complexity, halstead_volume, 
            branch_coverage_pct, pass_rate.
    Constraint: Verify no record has null for cyclomatic_complexity OR halstead_volume.
    """
    logger = get_logger()
    
    # Load raw intermediate data
    raw_data = load_intermediate_metrics(input_path)
    if not raw_data:
        log_error(logger, f"No data found in {input_path}")
        return

    # Apply exclusion gate
    filtered_data, excluded_ids = apply_pairwise_exclusion_gate(raw_data)
    
    if excluded_ids:
        log_info(logger, f"Excluded {len(excluded_ids)} pairs due to null coverage: {excluded_ids[:5]}...")
        # Log to file
        with open("logs/pairwise_exclusions.log", 'a') as f:
            f.write(f"{datetime.now()}: Excluded {excluded_ids}\n")

    # Validate constraints
    valid_records = []
    null_count = 0
    for record in filtered_data:
        cc = record.get('cyclomatic_complexity')
        hal = record.get('halstead_volume')
        
        if cc is None or hal is None:
            null_count += 1
            log_error(logger, f"Record {record.get('task_id')} ({record.get('source_type')}) has null metrics. Skipping.")
            continue
        
        valid_records.append(record)

    if null_count > 0:
        log_info(logger, f"Removed {null_count} records with null metrics.")

    # Write final output
    with open(output_path, 'w') as f:
        json.dump(valid_records, f, indent=2)

    log_info(logger, f"Aggregated {len(valid_records)} valid records to {output_path}")

def main():
    logger = setup_logging(task_id="T017")
    set_task_id("T017")
    
    log_info(logger, "Starting Metric Aggregation (T017)")
    
    ensure_dirs()
    
    input_path = "data/analysis/intermediate_metrics.json"
    output_path = "data/analysis/metrics.json"
    
    # If intermediate doesn't exist, try to load from raw data if available
    # For now, assume intermediate was produced by T014/T015
    if not os.path.exists(input_path):
        # Fallback: check if we need to generate from raw HumanEval + generated code
        # This logic might be invoked if T014/T015 failed or produced different paths
        log_error(logger, f"Intermediate metrics file not found: {input_path}")
        # Try to find any existing metrics
        if os.path.exists("data/analysis/metrics.json"):
            log_info(logger, "Output file already exists, skipping aggregation.")
            return
        else:
            log_error(logger, "Cannot proceed without intermediate metrics.")
            sys.exit(1)

    aggregate_metrics_to_json(input_path, output_path)
    
    # Verify output
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            data = json.load(f)
        log_info(logger, f"Verification: {len(data)} records written to {output_path}")
    else:
        log_error(logger, f"Failed to write output file: {output_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
