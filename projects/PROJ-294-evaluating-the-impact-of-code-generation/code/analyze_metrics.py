import os
import sys
import json
import logging
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
import re

# Logging state
_task_id = None
_timestamp = None
_unique_id = None
_logger = None

def set_task_id(task_id: str) -> None:
    global _task_id
    _task_id = task_id

def get_task_id() -> Optional[str]:
    return _task_id

def get_timestamp() -> str:
    global _timestamp
    if _timestamp is None:
        _timestamp = datetime.now().isoformat()
    return _timestamp

def get_unique_id() -> str:
    global _unique_id
    if _unique_id is None:
        import uuid
        _unique_id = str(uuid.uuid4())
    return _unique_id

def setup_logging(task_id: Optional[str] = None, level=logging.INFO):
    """
    Configures logging with optional task_id context.
    Accepts: setup_logging(), setup_logging(task_id="T015"), setup_logging(task_id=TASK_ID), setup_logging(level=logging.INFO)
    """
    global _logger, _task_id
    
    if task_id is not None:
        _task_id = task_id
    
    if _logger is not None:
        return _logger

    logger = logging.getLogger(f"T015_{_task_id or 'default'}")
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    _logger = logger
    return logger

def get_logger() -> Optional[logging.Logger]:
    return _logger

def log_info(msg: str) -> None:
    if _logger:
        _logger.info(msg)
    else:
        print(f"[INFO] {msg}")

def log_error(msg: str) -> None:
    if _logger:
        _logger.error(msg)
    else:
        print(f"[ERROR] {msg}")

def log_warning(msg: str) -> None:
    if _logger:
        _logger.warning(msg)
    else:
        print(f"[WARNING] {msg}")

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        'data/analysis',
        'data/generated',
        'data/raw'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_human_reference_data(filepath: str = "data/generated/human_samples.json") -> List[Dict[str, Any]]:
    """Load human reference code samples."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Human reference data not found: {filepath}")
    samples = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples

def load_generated_code_data(filepath: str = "data/generated/codegen_samples.json") -> List[Dict[str, Any]]:
    """Load generated code samples."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Generated code data not found: {filepath}")
    samples = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples

def load_intermediate_metrics(filepath: str = "data/analysis/intermediate_metrics.json") -> Dict[str, Any]:
    """Load intermediate metrics."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Intermediate metrics not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_intermediate_metrics(metrics: Dict[str, Any], filepath: str = "data/analysis/intermediate_metrics.json") -> None:
    """Save intermediate metrics."""
    ensure_dirs()
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)

# --- Sandbox Integration ---
def run_test_suite_in_sandbox(code: str, test_code: str, entry_point: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute code against its test suite using the sandbox context manager.
    Returns dict with 'passed', 'total', 'result' (0/1).
    """
    # Import sandbox here to avoid circular issues if sandbox.py is updated separately
    # We assume sandbox.py provides 'sandbox_context' and 'run_test_suite'
    try:
        from sandbox import sandbox_context, run_test_suite
    except ImportError:
        log_error("Sandbox module not found. Cannot execute tests.")
        return {'passed': 0, 'total': 0, 'result': 0, 'error': 'Sandbox not available'}

    try:
        with sandbox_context():
            result = run_test_suite(code, test_code, entry_point, timeout=timeout)
            return result
    except Exception as e:
        log_error(f"Sandbox execution failed: {e}")
        return {'passed': 0, 'total': 0, 'result': 0, 'error': str(e)}

def calculate_pass_rate(sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate pass_rate for a single sample.
    Input: sample dict with 'code', 'test', 'entry_point'.
    Output: dict with 'pass_rate' (float), 'passed', 'total'.
    """
    code = sample.get('code') or sample.get('generated_code') or sample.get('canonical_solution')
    test_code = sample.get('test')
    entry_point = sample.get('entry_point')

    if not code or not test_code or not entry_point:
        log_warning(f"Missing code, test, or entry_point for task {sample.get('task_id')}")
        return {'pass_rate': 0.0, 'passed': 0, 'total': 0, 'status': 'missing_fields'}

    result = run_test_suite_in_sandbox(code, test_code, entry_point)
    
    if 'error' in result and result['error'] == 'Sandbox not available':
        # Fallback: if sandbox is missing, we cannot calculate pass_rate. 
        # Per constraints, we must fail loudly or return 0 if execution is impossible.
        # Here we return 0.0 to indicate failure to execute.
        return {'pass_rate': 0.0, 'passed': 0, 'total': 0, 'status': 'sandbox_failed'}

    passed = result.get('passed', 0)
    total = result.get('total', 0)
    
    if total == 0:
        pass_rate = 0.0
    else:
        pass_rate = float(passed) / float(total)

    return {
        'pass_rate': pass_rate,
        'passed': passed,
        'total': total,
        'status': 'completed'
    }

def aggregate_pass_rates(samples: List[Dict[str, Any]], source_type: str) -> List[Dict[str, Any]]:
    """
    Calculate pass_rate for all samples and return enriched list.
    """
    results = []
    for sample in samples:
        task_id = sample.get('task_id', 'unknown')
        log_info(f"Calculating pass_rate for {source_type} task {task_id}")
        
        metrics = calculate_pass_rate(sample)
        
        enriched = {
            'task_id': task_id,
            'source_type': source_type,
            'pass_rate': metrics['pass_rate'],
            'passed_tests': metrics['passed'],
            'total_tests': metrics['total'],
            'status': metrics['status']
        }
        results.append(enriched)
    return results

def main():
    """
    Main entry point for T015: Execute test suites and calculate pass_rate.
    Dependencies: T011 (human_samples.json), T012 (codegen_samples.json), T015a (sandbox).
    Output: data/analysis/intermediate_metrics.json (updated with pass_rate) OR creates new pass_rate file.
    Note: T015 specifically asks for Intermediate JSON with pass_rate. 
    We will update the intermediate_metrics.json if it exists, or create a pass_rate specific file if not.
    However, T017 expects to aggregate everything. Let's create a dedicated pass_rate intermediate file 
    and also update the main intermediate_metrics if it exists.
    """
    set_task_id("T015")
    logger = setup_logging(task_id="T015")
    log_info("Starting T015: Pass Rate Calculation")

    ensure_dirs()

    # Load inputs
    try:
        human_samples = load_human_reference_data()
        log_info(f"Loaded {len(human_samples)} human samples")
    except FileNotFoundError as e:
        log_error(str(e))
        sys.exit(1)

    try:
        gen_samples = load_generated_code_data()
        log_info(f"Loaded {len(gen_samples)} generated samples")
    except FileNotFoundError as e:
        log_error(str(e))
        sys.exit(1)

    # Calculate pass rates
    human_pass_rates = aggregate_pass_rates(human_samples, 'human')
    gen_pass_rates = aggregate_pass_rates(gen_samples, 'codegen')

    # Combine results
    all_pass_rates = human_pass_rates + gen_pass_rates

    # Save intermediate pass rate results
    pass_rate_file = "data/analysis/pass_rate_metrics.json"
    with open(pass_rate_file, 'w') as f:
        json.dump(all_pass_rates, f, indent=2)
    log_info(f"Saved pass rate metrics to {pass_rate_file}")

    # Update intermediate_metrics.json if it exists (for T017 consumption)
    # If T014a hasn't run, this file might not exist. We handle that gracefully.
    intermediate_file = "data/analysis/intermediate_metrics.json"
    if os.path.exists(intermediate_file):
        try:
            with open(intermediate_file, 'r') as f:
                intermediate_data = json.load(f)
            
            # Merge pass_rate into existing metrics
            # Structure: list of dicts per task_id
            existing_map = {item['task_id']: item for item in intermediate_data}
            
            for pr in all_pass_rates:
                tid = pr['task_id']
                if tid in existing_map:
                    existing_map[tid].update({
                        'pass_rate': pr['pass_rate'],
                        'passed_tests': pr['passed_tests'],
                        'total_tests': pr['total_tests']
                    })
                else:
                    # New entry
                    existing_map[tid] = {
                        'task_id': tid,
                        'source_type': pr['source_type'],
                        'pass_rate': pr['pass_rate'],
                        'passed_tests': pr['passed_tests'],
                        'total_tests': pr['total_tests']
                    }
            
            # Convert back to list
            updated_list = list(existing_map.values())
            
            with open(intermediate_file, 'w') as f:
                json.dump(updated_list, f, indent=2)
            log_info(f"Updated {intermediate_file} with pass_rate")
        except Exception as e:
            log_error(f"Failed to update intermediate_metrics.json: {e}")
    else:
        log_warning(f"Intermediate metrics file {intermediate_file} not found. Created separate pass_rate file.")

    log_info("T015 completed successfully.")

if __name__ == "__main__":
    main()