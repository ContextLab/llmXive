"""
Metric Aggregation and Analysis Pipeline (T017).
Aggregates intermediate metrics, applies exclusion gates, and produces the final metrics.json.
"""
import os
import sys
import json
import logging
import subprocess
import tempfile
from datetime import datetime
import uuid

# --- Shared Utility Contract (MUST match utils.py and other callers) ---
_task_id = None
_unique_id = None
_timestamp = None

def set_task_id(tid):
    global _task_id, _unique_id, _timestamp
    _task_id = tid
    _unique_id = str(uuid.uuid4())
    _timestamp = datetime.now().isoformat()

def get_task_id():
    return _task_id

def get_unique_id():
    return _unique_id

def get_timestamp():
    return _timestamp

def setup_logging(*args, **kwargs):
    """
    Universal logging setup compatible with all callers in the project.
    Accepts:
      - setup_logging()
      - setup_logging(task_id="T017")
      - setup_logging(task_id=TASK_ID)
      - setup_logging(level=logging.INFO)
    """
    global _task_id, _unique_id, _timestamp

    # Handle keyword arguments
    if 'task_id' in kwargs:
        tid = kwargs.pop('task_id')
        set_task_id(tid)

    if 'level' in kwargs:
        level = kwargs.pop('level')
    else:
        level = logging.INFO

    # Configure root logger if not already configured
    if not logging.getLogger().handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(level)

    logger = logging.getLogger(get_task_id() or "ROOT")
    return logger

def get_logger():
    return logging.getLogger(get_task_id() or "ROOT")

def log_info(msg):
    get_logger().info(msg)

def log_error(msg):
    get_logger().error(msg)

# --- File I/O Helpers ---

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        "data/raw",
        "data/generated",
        "data/analysis",
        "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_intermediate_metrics(path="data/analysis/intermediate_metrics.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Intermediate metrics file not found: {path}")
    return load_json_file(path)

def save_intermediate_metrics(data, path="data/analysis/intermediate_metrics.json"):
    save_json_file(path, data)

# --- Metric Parsing & Calculation ---

def parse_radon_output(raw_output):
    """
    Parse raw radon output (JSON string or dict) into structured metrics.
    Expected keys: cyclomatic_complexity, halstead_volume, halstead_components.
    """
    if isinstance(raw_output, str):
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            return {}
    else:
        data = raw_output

    metrics = {}
    if 'cc' in data:
        # radon cc output structure varies; usually a list or dict per file
        # We assume a simplified structure or extract the first valid entry
        if isinstance(data['cc'], list) and len(data['cc']) > 0:
            metrics['cyclomatic_complexity'] = data['cc'][0].get('complexity', 0)
        elif isinstance(data['cc'], dict):
            metrics['cyclomatic_complexity'] = data['cc'].get('complexity', 0)

    if 'hal' in data:
        if isinstance(data['hal'], list) and len(data['hal']) > 0:
            vol = data['hal'][0].get('volume', 0)
            metrics['halstead_volume'] = vol
            metrics['halstead_components'] = data['hal'][0].get('components', {})
        elif isinstance(data['hal'], dict):
            vol = data['hal'].get('volume', 0)
            metrics['halstead_volume'] = vol
            metrics['halstead_components'] = data['hal'].get('components', {})

    return metrics

def calculate_code_metrics(source_code):
    """
    Calculate static metrics (CC, Halstead) for a given source code string.
    Uses radon via subprocess.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(source_code)
        tmp_path = tmp.name

    try:
        # Run radon cc
        cc_result = subprocess.run(
            ['radon', 'cc', '--json', tmp_path],
            capture_output=True, text=True, timeout=30
        )
        cc_data = json.loads(cc_result.stdout) if cc_result.stdout.strip() else {}

        # Run radon hal
        hal_result = subprocess.run(
            ['radon', 'hal', '--json', tmp_path],
            capture_output=True, text=True, timeout=30
        )
        hal_data = json.loads(hal_result.stdout) if hal_result.stdout.strip() else {}

        combined = {'cc': cc_data, 'hal': hal_data}
        return parse_radon_output(combined)
    except Exception as e:
        log_error(f"Error calculating metrics: {e}")
        return {'cyclomatic_complexity': None, 'halstead_volume': None}
    finally:
        os.unlink(tmp_path)

def calculate_branch_coverage(source_code, test_code):
    """
    Calculate branch coverage using coverage.py.
    Returns a percentage (0-100).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = os.path.join(tmpdir, "sample.py")
        test_file = os.path.join(tmpdir, "test_sample.py")
        conf_file = os.path.join(tmpdir, ".coveragerc")

        with open(code_file, 'w') as f:
            f.write(source_code)
        with open(test_file, 'w') as f:
            f.write(test_code)
        with open(conf_file, 'w') as f:
            f.write("[run]\nbranch=True\n")

        try:
            # Run coverage
            subprocess.run(
                ['coverage', 'run', '--source', code_file, test_file],
                cwd=tmpdir, capture_output=True, timeout=60
            )
            result = subprocess.run(
                ['coverage', 'report', '--json'],
                cwd=tmpdir, capture_output=True, text=True, timeout=30
            )
            data = json.loads(result.stdout)
            # Extract total branch coverage
            totals = data.get('totals', {})
            return totals.get('branch_pct', 0.0)
        except Exception as e:
            log_error(f"Coverage calculation failed: {e}")
            return 0.0

# --- Data Loading & Merging ---

def load_sensitivity_samples(path="data/generated/sensitivity_samples.json"):
    if not os.path.exists(path):
        return []
    return load_json_file(path)

def merge_sensitivity_with_base(base_metrics, sensitivity_samples):
    """
    Merge sensitivity analysis results into the base metrics.
    Adds 'source_type' and ensures all task_ids are accounted for.
    """
    merged = []
    base_map = {m['task_id']: m for m in base_metrics}

    for sample in sensitivity_samples:
        tid = sample.get('task_id')
        if tid in base_map:
            entry = base_map[tid].copy()
            entry['source_type'] = 'sensitivity-model'
            # Override metrics with sensitivity sample if available
            if 'metrics' in sample:
                entry.update(sample['metrics'])
            merged.append(entry)
            del base_map[tid] # Remove from base to avoid duplication if logic differs

    # Add remaining base samples (codegen-350m)
    for tid, entry in base_map.items():
        entry['source_type'] = 'codegen-350m'
        merged.append(entry)

    return merged

def perform_pairwise_exclusion_gate(data, exclusion_log="logs/pairwise_exclusions.log"):
    """
    Identify and exclude pairs where either Human or LLM sample has null coverage.
    Writes excluded pairs to exclusion_log.
    Returns filtered data.
    """
    excluded = []
    filtered = []

    # Group by task_id to check pairs
    task_map = {}
    for entry in data:
        tid = entry['task_id']
        if tid not in task_map:
            task_map[tid] = []
        task_map[tid].append(entry)

    for tid, entries in task_map.items():
        # Check if we have both human and generated samples
        has_human = any(e.get('source_type') == 'human' for e in entries)
        has_generated = any(e.get('source_type') in ['codegen-350m', 'sensitivity-model'] for e in entries)

        if not (has_human and has_generated):
            excluded.append({"task_id": tid, "reason": "Missing pair (human or generated)"})
            continue

        # Check for null coverage
        has_null_coverage = False
        for e in entries:
            if e.get('branch_coverage_pct') is None:
                has_null_coverage = True
                break

        if has_null_coverage:
            excluded.append({"task_id": tid, "reason": "Null coverage in pair"})
        else:
            filtered.extend(entries)

    # Log exclusions
    os.makedirs(os.path.dirname(exclusion_log), exist_ok=True)
    with open(exclusion_log, 'w') as f:
        json.dump(excluded, f, indent=2)

    total_pairs = len(task_map)
    excluded_count = len(excluded)
    if excluded_count > 0:
        log_info(f"Excluded {excluded_count}/{total_pairs} pairs due to coverage issues.")
        if total_pairs - excluded_count < 30:
            log_error(f"WARNING: Remaining sample size ({total_pairs - excluded_count}) < 30. Power analysis may be invalid.")
        if excluded_count / total_pairs > 0.5:
            log_error("CRITICAL: >50% of pairs excluded. Systematic failure detected.")
            sys.exit(1)

    return filtered

# --- Aggregation (T017 Main Logic) ---

def aggregate_metrics_to_json():
    """
    Main aggregation function for T017.
    1. Loads intermediate metrics.
    2. Merges sensitivity data.
    3. Performs exclusion gate.
    4. Validates schema.
    5. Saves to data/analysis/metrics.json.
    """
    log_info("Starting Metric Aggregation (T017)")

    # 1. Load Intermediate Metrics
    try:
        intermediate_data = load_intermediate_metrics()
    except FileNotFoundError as e:
        log_error(str(e))
        raise

    # 2. Merge Sensitivity Samples
    sensitivity_samples = load_sensitivity_samples()
    merged_data = merge_sensitivity_with_base(intermediate_data, sensitivity_samples)

    # 3. Pairwise Exclusion Gate
    final_data = perform_pairwise_exclusion_gate(merged_data)

    # 4. Validation: Ensure no nulls in critical fields
    required_fields = ['cyclomatic_complexity', 'halstead_volume', 'mutation_score']
    valid_records = []
    for record in final_data:
        is_valid = True
        for field in required_fields:
            if record.get(field) is None:
                log_error(f"Record {record.get('task_id')} missing {field}. Excluding.")
                is_valid = False
                break
        if is_valid:
            valid_records.append(record)

    if len(valid_records) < len(final_data):
        log_info(f"Filtered {len(final_data) - len(valid_records)} records with null critical metrics.")

    # 5. Save Final Output
    output_path = "data/analysis/metrics.json"
    save_json_file(output_path, valid_records)
    log_info(f"Aggregation complete. Saved {len(valid_records)} records to {output_path}")

    return valid_records

def main():
    set_task_id("T017")
    ensure_dirs()
    try:
        aggregate_metrics_to_json()
    except Exception as e:
        log_error(f"Aggregation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()