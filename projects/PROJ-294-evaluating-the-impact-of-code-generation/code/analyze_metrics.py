import os
import sys
import json
import logging
import subprocess
import tempfile
import random
from typing import Dict, List, Any, Optional, Tuple

# --- Task ID & Logging Setup (Shared Contract) ---
_TASK_ID = None

def set_task_id(task_id: Optional[str] = None) -> None:
    global _TASK_ID
    _TASK_ID = task_id

def get_task_id() -> Optional[str]:
    return _TASK_ID

def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Robust logging setup compatible with all call sites:
    - setup_logging()
    - setup_logging(task_id="...")
    - setup_logging(task_id=TASK_ID)
    - setup_logging(level=logging.INFO)
    """
    global _TASK_ID
    if task_id is not None:
        _TASK_ID = task_id

    logger_name = f"T042" if _TASK_ID is None else f"{_TASK_ID}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        f"%(asctime)s [{logger_name}] [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_logger() -> logging.Logger:
    return setup_logging()

def log_info(msg: str) -> None:
    get_logger().info(msg)

def log_error(msg: str) -> None:
    get_logger().error(msg)

def log_warning(msg: str) -> None:
    get_logger().warning(msg)

# --- Radon Parsing Utilities ---

def parse_radon_cc_output(radon_output: str) -> List[Dict[str, Any]]:
    """
    Parse radon cc --json output.
    Returns a list of dicts with 'filename', 'name', 'cyclomatic_complexity'.
    """
    try:
        data = json.loads(radon_output)
        results = []
        for file_key, file_data in data.items():
            for entry in file_data:
                results.append({
                    'filename': file_key,
                    'name': entry.get('name', ''),
                    'cyclomatic_complexity': entry.get('cc', {}).get('value', 0)
                })
        return results
    except json.JSONDecodeError:
        log_error(f"Failed to parse radon cc output: {radon_output}")
        return []

def parse_radon_hal_output(radon_output: str) -> List[Dict[str, Any]]:
    """
    Parse radon hal --json output.
    Returns a list of dicts with 'filename', 'name', 'halstead_volume', and components.
    """
    try:
        data = json.loads(radon_output)
        results = []
        for file_key, file_data in data.items():
            for entry in file_data:
                vol = entry.get('hal', {}).get('volume', 0)
                results.append({
                    'filename': file_key,
                    'name': entry.get('name', ''),
                    'halstead_volume': vol,
                    'hal_components': entry.get('hal', {})
                })
        return results
    except json.JSONDecodeError:
        log_error(f"Failed to parse radon hal output: {radon_output}")
        return []

def calculate_halstead_volume(n1: float, n2: float, N1: float, N2: float) -> float:
    """
    Calculate Halstead Volume: V = N * log2(n)
    where N = N1 + N2, n = n1 + n2
    """
    N = N1 + N2
    n = n1 + n2
    if n == 0:
        return 0.0
    return N * (math.log2(n) if n > 1 else 0)

import math

# --- Data Loading Utilities ---

def load_human_reference_data(path: str) -> List[Dict[str, Any]]:
    """Load human reference samples from JSONL."""
    if not os.path.exists(path):
        log_error(f"Human reference file not found: {path}")
        return []
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_generated_code_data(path: str) -> List[Dict[str, Any]]:
    """Load generated code samples from JSONL."""
    if not os.path.exists(path):
        log_error(f"Generated code file not found: {path}")
        return []
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

# --- Metric Calculation & Aggregation ---

def calculate_code_metrics(code: str) -> Dict[str, Any]:
    """
    Run radon cc and radon hal on a code string.
    Returns metrics dict.
    """
    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        # Run radon cc
        cc_proc = subprocess.run(
            ['radon', 'cc', '--json', tmp_path],
            capture_output=True, text=True, timeout=30
        )
        cc_data = parse_radon_cc_output(cc_proc.stdout)

        # Run radon hal
        hal_proc = subprocess.run(
            ['radon', 'hal', '--json', tmp_path],
            capture_output=True, text=True, timeout=30
        )
        hal_data = parse_radon_hal_output(hal_proc.stdout)

        # Aggregate (take max complexity, avg volume if multiple functions)
        max_cc = 0
        total_vol = 0
        count = 0

        for item in cc_data:
            if item.get('cyclomatic_complexity', 0) > max_cc:
                max_cc = item['cyclomatic_complexity']

        for item in hal_data:
            total_vol += item.get('halstead_volume', 0)
            count += 1

        avg_vol = total_vol / count if count > 0 else 0

        return {
            'cyclomatic_complexity': max_cc,
            'halstead_volume': avg_vol
        }
    except Exception as e:
        log_error(f"Error calculating metrics: {e}")
        return {'cyclomatic_complexity': None, 'halstead_volume': None}
    finally:
        os.unlink(tmp_path)

def aggregate_metrics_from_radon_samples(human_samples: List[Dict], codegen_samples: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate metrics for all samples.
    Returns a dict keyed by task_id with metrics for 'human' and 'codegen'.
    """
    results = {}

    # Process Human
    for sample in human_samples:
        task_id = sample.get('task_id')
        code = sample.get('canonical_solution') or sample.get('prompt') # Fallback logic
        if not code:
            continue
        metrics = calculate_code_metrics(code)
        if task_id not in results:
            results[task_id] = {}
        results[task_id]['human'] = metrics

    # Process CodeGen
    for sample in codegen_samples:
        task_id = sample.get('task_id')
        code = sample.get('generated_code')
        if not code:
            continue
        metrics = calculate_code_metrics(code)
        if task_id not in results:
            results[task_id] = {}
        results[task_id]['codegen'] = metrics

    return results

# --- File I/O for Intermediate Metrics ---

def save_intermediate_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save intermediate metrics (including coverage/pass_rate) to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    log_info(f"Saved intermediate metrics to {output_path}")

def load_intermediate_metrics(input_path: str) -> Dict[str, Any]:
    """Load intermediate metrics from JSON."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Intermediate metrics file not found: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_dirs(*paths: str) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)

# --- T042: Pairwise Exclusion Gate Implementation ---

def apply_pairwise_exclusion_gate(metrics_data: Dict[str, Dict], output_path: str) -> List[str]:
    """
    T042 Logic:
    1. Identify task IDs where EITHER human OR codegen has null coverage (or null metrics).
    2. Filter to valid pairs (both have non-null metrics).
    3. If n < 30, generate a simple random subset of 30 task IDs (seed=42).
    4. If n >= 30, use all valid pairs.
    5. Save valid_task_ids.json.
    6. Return the list of valid task IDs.
    """
    valid_task_ids = []
    invalid_task_ids = []

    for task_id, sources in metrics_data.items():
        human_metrics = sources.get('human', {})
        codegen_metrics = sources.get('codegen', {})

        # Check for null coverage or null metrics in either
        # Assuming 'branch_coverage_pct' is added later, but we check for existence of metrics first
        # If a source is missing or has None for critical metrics, it's invalid.
        human_valid = (
            human_metrics and
            human_metrics.get('cyclomatic_complexity') is not None and
            human_metrics.get('halstead_volume') is not None
        )
        codegen_valid = (
            codegen_metrics and
            codegen_metrics.get('cyclomatic_complexity') is not None and
            codegen_metrics.get('halstead_volume') is not None
        )

        # Note: T016 adds coverage. If coverage is null, it's invalid.
        # We assume intermediate_metrics includes coverage if T016 ran.
        # For safety, we check if the key exists and is not None.
        # If T016 hasn't run yet, coverage might be missing entirely.
        # The task says: "either the human reference OR the LLM sample has null coverage"
        # We assume the input 'metrics_data' here already includes coverage from T016.
        
        # Check coverage if present
        if human_valid and human_metrics.get('branch_coverage_pct') is None:
            human_valid = False
        if codegen_valid and codegen_metrics.get('branch_coverage_pct') is None:
            codegen_valid = False

        if human_valid and codegen_valid:
            valid_task_ids.append(task_id)
        else:
            invalid_task_ids.append(task_id)

    log_info(f"Valid pairs: {len(valid_task_ids)}, Invalid pairs: {len(invalid_task_ids)}")

    final_task_ids = valid_task_ids
    if len(valid_task_ids) < 30:
        log_warning(f"Valid pairs ({len(valid_task_ids)}) < 30. Generating random subset of 30 from original 164.")
        # We need the original 164. If we don't have them here, we assume the input dict keys are a subset.
        # Ideally, we should load the full list of task IDs from the raw data.
        # However, the task says "from the original 164".
        # Since we are in the gate, we assume we have access to the full set or the input contains all.
        # If input only contains valid/invalid processed, we can't reconstruct the 164.
        # Assumption: metrics_data contains ALL tasks processed so far (including invalid ones).
        # If not, we fallback to the valid set if we can't get 30, but the requirement is strict.
        # Let's assume the input 'metrics_data' has all 164 keys.
        
        all_task_ids = list(metrics_data.keys())
        if len(all_task_ids) < 30:
            log_error(f"Not enough total tasks ({len(all_task_ids)}) to form a subset of 30.")
            # Fallback to all available if absolutely necessary, but log error
            final_task_ids = all_task_ids
        else:
            random.seed(42)
            final_task_ids = random.sample(all_task_ids, 30)
            log_info(f"Selected 30 random task IDs: {final_task_ids}")
    else:
        log_info(f"Valid pairs ({len(valid_task_ids)}) >= 30. Using all valid pairs.")

    # Save valid_task_ids.json
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_task_ids, f, indent=2)
    
    return final_task_ids

# --- Main Entry Point ---

def main():
    """
    Main entry point for T042 (Pairwise Exclusion Gate) and T017 (Aggregation).
    This function orchestrates:
    1. Load intermediate metrics (from T014a, T015, T016).
    2. Apply T042 exclusion gate.
    3. Aggregate final metrics (T017) for valid pairs.
    4. Save data/analysis/metrics.json.
    """
    logger = setup_logging(task_id="T042")
    
    # Paths
    intermediate_path = "data/analysis/intermediate_metrics.json"
    valid_ids_path = "data/analysis/valid_task_ids.json"
    final_metrics_path = "data/analysis/metrics.json"

    # Ensure directories
    ensure_dirs("data/analysis")

    # 1. Load Intermediate Metrics
    try:
        metrics_data = load_intermediate_metrics(intermediate_path)
        logger.info(f"Loaded intermediate metrics with {len(metrics_data)} tasks.")
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Cannot proceed without intermediate metrics. Ensure T014a, T015, T016 have run.")
        sys.exit(1)

    # 2. Apply T042: Pairwise Exclusion Gate
    valid_task_ids = apply_pairwise_exclusion_gate(metrics_data, valid_ids_path)

    if not valid_task_ids:
        logger.error("No valid pairs found. Pipeline cannot proceed.")
        sys.exit(1)

    # 3. T017: Aggregate Final Metrics for Valid Pairs
    final_records = []
    for task_id in valid_task_ids:
        sources = metrics_data.get(task_id, {})
        
        # Human
        if 'human' in sources:
            h_metrics = sources['human']
            final_records.append({
                'task_id': task_id,
                'source_type': 'human',
                'cyclomatic_complexity': h_metrics.get('cyclomatic_complexity'),
                'halstead_volume': h_metrics.get('halstead_volume'),
                'branch_coverage_pct': h_metrics.get('branch_coverage_pct'),
                'pass_rate': h_metrics.get('pass_rate')
            })

        # CodeGen
        if 'codegen' in sources:
            c_metrics = sources['codegen']
            final_records.append({
                'task_id': task_id,
                'source_type': 'codegen',
                'cyclomatic_complexity': c_metrics.get('cyclomatic_complexity'),
                'halstead_volume': c_metrics.get('halstead_volume'),
                'branch_coverage_pct': c_metrics.get('branch_coverage_pct'),
                'pass_rate': c_metrics.get('pass_rate')
            })

    # 4. Save Final Metrics
    save_intermediate_metrics(final_records, final_metrics_path)
    logger.info(f"Final metrics saved to {final_metrics_path} with {len(final_records)} records.")
    
    # Verification
    for record in final_records:
        if record.get('cyclomatic_complexity') is None or record.get('halstead_volume') is None:
            logger.warning(f"Record {record['task_id']} ({record['source_type']}) has null metrics.")

    return 0

if __name__ == "__main__":
    sys.exit(main())