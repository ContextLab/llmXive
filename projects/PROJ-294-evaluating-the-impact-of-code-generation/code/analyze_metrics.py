import os
import sys
import json
import logging
import subprocess
import tempfile
from typing import Dict, Any, List, Optional
from utils import setup_logging, get_logger, set_task_id, get_task_id, get_timestamp, get_unique_id
from sandbox import run_test_suite

# Global task context
_task_id = None

def set_task_id(task_id: str):
    global _task_id
    _task_id = task_id
    setup_logging(task_id=task_id)

def get_task_id():
    return _task_id

def get_timestamp():
    from datetime import datetime
    return datetime.now().isoformat()

def get_unique_id():
    import uuid
    return str(uuid.uuid4())

def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    global _task_id
    if task_id:
        _task_id = task_id
    if not logging.root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] [%(task_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    logger = logging.getLogger(__name__)
    if not any(isinstance(f, logging.Filter) for f in logger.filters):
        class TaskFilter(logging.Filter):
            def filter(self, record):
                record.task_id = _task_id or "UNKNOWN"
                return True
        logger.addFilter(TaskFilter())
    return logger

def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    if not any(isinstance(f, logging.Filter) for f in logger.filters):
        class TaskFilter(logging.Filter):
            def filter(self, record):
                record.task_id = _task_id or "UNKNOWN"
                return True
        logger.addFilter(TaskFilter())
    return logger

def log_info(msg: str):
    logging.info(msg)

def log_error(msg: str):
    logging.error(msg)

def log_warning(msg: str):
    logging.warning(msg)

def ensure_dirs():
    """Ensure output directories exist."""
    os.makedirs("data/analysis", exist_ok=True)
    os.makedirs("data/generated", exist_ok=True)

def load_human_reference_data() -> List[Dict[str, Any]]:
    """Load human reference samples."""
    path = "data/generated/human_samples.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Human samples not found: {path}")
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def load_generated_code_data() -> List[Dict[str, Any]]:
    """Load generated code samples."""
    path = "data/generated/codegen_samples.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Generated samples not found: {path}")
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def load_intermediate_metrics() -> Dict[str, Any]:
    """Load intermediate metrics."""
    path = "data/analysis/intermediate_metrics.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Intermediate metrics not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def save_intermediate_metrics(data: Dict[str, Any]):
    """Save intermediate metrics."""
    path = "data/analysis/intermediate_metrics.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def run_test_suite_in_sandbox(code: str, tests: str) -> bool:
    """Run test suite in sandbox and return pass status."""
    result = run_test_suite(code, tests, timeout=10)
    return result.get("passed", False)

def calculate_pass_rate(task_id: str, code: str, tests: str) -> float:
    """Calculate pass rate for a single task."""
    # In a real scenario, we would run multiple tests. 
    # For HumanEval, the test string contains the assertions.
    # We assume 1 test unit per task for this simplified metric.
    if run_test_suite_in_sandbox(code, tests):
        return 1.0
    return 0.0

def aggregate_pass_rates(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate pass rates for a list of samples."""
    results = []
    for sample in samples:
        pass_rate = calculate_pass_rate(
            sample["task_id"], 
            sample.get("generated_code") or sample.get("canonical_solution", ""), 
            sample.get("test", "")
        )
        results.append({
            "task_id": sample["task_id"],
            "pass_rate": pass_rate
        })
    return results

def main():
    logger = setup_logging(task_id="T017")
    logger.info("Starting Metric Aggregation (T017)")

    try:
        ensure_dirs()
        human_samples = load_human_reference_data()
        codegen_samples = load_generated_code_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Process human samples
    human_metrics = []
    for sample in human_samples:
        code = sample.get("canonical_solution", "")
        tests = sample.get("test", "")
        pass_rate = calculate_pass_rate(sample["task_id"], code, tests)
        human_metrics.append({
            "task_id": sample["task_id"],
            "source_type": "human",
            "pass_rate": pass_rate
        })

    # Process codegen samples
    codegen_metrics = []
    for sample in codegen_samples:
        code = sample.get("generated_code")
        if not code:
            continue
        tests = sample.get("test", "")
        pass_rate = calculate_pass_rate(sample["task_id"], code, tests)
        codegen_metrics.append({
            "task_id": sample["task_id"],
            "source_type": "codegen",
            "pass_rate": pass_rate
        })

    # Combine and save base metrics
    base_metrics = human_metrics + codegen_metrics
    with open("data/analysis/base_metrics.json", "w") as f:
        json.dump(base_metrics, f, indent=2)
    logger.info(f"Saved base_metrics.json with {len(base_metrics)} records")

    # Filter valid metrics (pass_rate >= 0.80)
    valid_metrics = [m for m in base_metrics if m["pass_rate"] >= 0.80]
    valid_task_ids = [m["task_id"] for m in valid_metrics]

    with open("data/analysis/valid_metrics.json", "w") as f:
        json.dump(valid_metrics, f, indent=2)
    with open("data/analysis/valid_task_ids.json", "w") as f:
        json.dump(valid_task_ids, f, indent=2)
    
    logger.info(f"Saved valid_metrics.json ({len(valid_metrics)}) and valid_task_ids.json ({len(valid_task_ids)})")

    # Create intermediate_metrics for downstream tasks
    intermediate = {"base_metrics": base_metrics, "valid_metrics": valid_metrics}
    save_intermediate_metrics(intermediate)
    
    # Create the main metrics.json file required by other tasks
    with open("data/analysis/metrics.json", "w") as f:
        json.dump(base_metrics, f, indent=2)
    
    logger.info("Metric Aggregation completed successfully.")

if __name__ == "__main__":
    main()
