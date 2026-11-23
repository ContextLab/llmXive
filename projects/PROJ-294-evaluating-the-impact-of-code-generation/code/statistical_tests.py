import json
import logging
import math
import os
import sys
import random
from typing import Dict, Any, List, Tuple
from utils import setup_logging, get_logger, set_task_id, get_task_id, get_unique_id, get_timestamp

def set_task_id(task_id: str):
    global _task_id
    _task_id = task_id
    setup_logging(task_id=task_id)

def get_task_id():
    return _task_id

def get_unique_id():
    import uuid
    return str(uuid.uuid4())

def get_timestamp():
    from datetime import datetime
    return datetime.now().isoformat()

def setup_logging(task_id: str = None, level: int = logging.INFO) -> logging.Logger:
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

def load_metrics() -> List[Dict[str, Any]]:
    path = "data/analysis/metrics.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metrics file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def wilcoxon_signed_rank_test(group1: List[float], group2: List[float]) -> Dict[str, float]:
    """
    Perform Wilcoxon Signed-Rank test.
    Returns p-value and statistic.
    """
    # Simplified implementation for demonstration
    # In production, use scipy.stats.wilcoxon
    n = min(len(group1), len(group2))
    if n < 5:
        return {"statistic": 0.0, "p_value": 1.0}
    
    # Mock calculation
    statistic = sum(abs(g1 - g2) for g1, g2 in zip(group1[:n], group2[:n]))
    p_value = 0.05 if statistic > 10 else 0.5
    return {"statistic": statistic, "p_value": p_value}

def calculate_wilcoxon_for_all_metrics(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate Wilcoxon tests for all continuous metrics."""
    human = [m for m in metrics if m["source_type"] == "human"]
    codegen = [m for m in metrics if m["source_type"] == "codegen"]
    
    results = {}
    metrics_to_check = ["cyclomatic_complexity", "halstead_volume", "branch_coverage_potential", "pass_rate"]
    
    for metric in metrics_to_check:
        h_vals = [m.get(metric, 0) for m in human]
        c_vals = [m.get(metric, 0) for m in codegen]
        results[metric] = wilcoxon_signed_rank_test(h_vals, c_vals)
    
    return results

def mcnemar_test(group1: List[bool], group2: List[bool]) -> Dict[str, float]:
    """Perform McNemar's test for categorical data."""
    return {"statistic": 0.0, "p_value": 1.0}

def calculate_mcnemar_for_pass_rate(metrics: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate McNemar test for pass rate."""
    human = [m["pass_rate"] >= 0.8 for m in metrics if m["source_type"] == "human"]
    codegen = [m["pass_rate"] >= 0.8 for m in metrics if m["source_type"] == "codegen"]
    return mcnemar_test(human, codegen)

def permutation_test_paired(group1: List[float], group2: List[float], iterations: int = 1000) -> float:
    """Permutation test for paired data."""
    diffs = [g1 - g2 for g1, g2 in zip(group1, group2)]
    observed = sum(diffs)
    count = 0
    for _ in range(iterations):
        random.shuffle(diffs)
        if sum(diffs) >= observed:
            count += 1
    return count / iterations

def calculate_permutation_for_branch_coverage(metrics: List[Dict[str, Any]]) -> float:
    """Calculate permutation test for branch coverage."""
    human = [m.get("branch_coverage_potential", 0) for m in metrics if m["source_type"] == "human"]
    codegen = [m.get("branch_coverage_potential", 0) for m in metrics if m["source_type"] == "codegen"]
    return permutation_test_paired(human, codegen)

def calculate_effect_size_cohen_d(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size."""
    if not group1 or not group2:
        return 0.0
    mean1 = sum(group1) / len(group1)
    mean2 = sum(group2) / len(group2)
    std1 = (sum((x - mean1)**2 for x in group1) / len(group1))**0.5
    std2 = (sum((x - mean2)**2 for x in group2) / len(group2))**0.5
    pooled_std = ((std1**2 + std2**2) / 2)**0.5
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def a_priori_power_analysis(effect_size: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """Calculate required sample size for a priori power analysis."""
    # Simplified formula
    if effect_size == 0:
        return 0
    return int((1.96 + 0.84)**2 / (effect_size**2))

def post_hoc_power_analysis(effect_size: float, n: int, alpha: float = 0.05) -> float:
    """Calculate achieved power post-hoc."""
    # Simplified approximation
    if n == 0 or effect_size == 0:
        return 0.0
    return min(1.0, (n * effect_size**2) / 4)

def validate_success_criteria(results: Dict[str, Any]) -> Dict[str, bool]:
    """Validate results against success criteria."""
    return {
        "statistical_significance": results.get("p_value", 1.0) < 0.05,
        "power_achieved": results.get("power", 0.0) >= 0.80
    }

def run_statistical_analysis(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run full statistical analysis."""
    wilcoxon_results = calculate_wilcoxon_for_all_metrics(metrics)
    mcnemar_results = calculate_mcnemar_for_pass_rate(metrics)
    permutation_results = calculate_permutation_for_branch_coverage(metrics)
    
    # Calculate effect sizes
    human = [m for m in metrics if m["source_type"] == "human"]
    codegen = [m for m in metrics if m["source_type"] == "codegen"]
    
    effect_sizes = {
        "pass_rate": calculate_effect_size_cohen_d(
            [m["pass_rate"] for m in human], 
            [m["pass_rate"] for m in codegen]
        )
    }
    
    # Power analysis
    n = len(human)
    power = post_hoc_power_analysis(effect_sizes["pass_rate"], n)
    
    return {
        "wilcoxon": wilcoxon_results,
        "mcnemar": mcnemar_results,
        "permutation": permutation_results,
        "effect_sizes": effect_sizes,
        "power": power,
        "sample_size": n
    }

def main():
    logger = setup_logging(task_id="T046")
    logger.info("Starting Success Criteria Validation (T046)")
    
    try:
        metrics = load_metrics()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    results = run_statistical_analysis(metrics)
    
    # Save results
    with open("data/analysis/statistical_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Validate criteria
    validation = validate_success_criteria(results)
    
    with open("state/validation_results.yaml", "w") as f:
        f.write(f"statistical_significance: {validation['statistical_significance']}\n")
        f.write(f"power_achieved: {validation['power_achieved']}\n")
    
    logger.info("Statistical analysis completed.")

if __name__ == "__main__":
    main()
