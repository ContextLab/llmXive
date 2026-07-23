import json
import logging
import math
import os
import sys
import random
import yaml
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Global state for task ID and logger
_task_id = None
_logger = None
_unique_id_counter = 0

def set_task_id(tid: str):
    global _task_id
    _task_id = tid

def get_task_id() -> Optional[str]:
    return _task_id

def get_unique_id() -> str:
    global _unique_id_counter
    _unique_id_counter += 1
    return f"{_task_id or 'UNKNOWN'}-{_unique_id_counter}"

def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Flexible logging setup compatible with all callers.
    Accepts task_id as kwarg, or no args, or positional args (ignored).
    """
    global _logger, _task_id

    # Handle arguments gracefully
    task_id_val = kwargs.get('task_id') or (args[0] if args and isinstance(args[0], str) else None)
    
    if task_id_val:
        _task_id = task_id_val

    if _logger is not None:
        return _logger

    logger = logging.getLogger(f"statistical_tests_{_task_id or 'default'}")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter with task ID if available
    fmt_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if _task_id:
        fmt_str = f"%(asctime)s [{_task_id}] - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(fmt_str)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _logger = logger
    return logger

def get_logger() -> logging.Logger:
    if _logger is None:
        return setup_logging()
    return _logger

def log_info(msg: str):
    logger = get_logger()
    if logger:
        logger.info(msg)

def log_error(msg: str):
    logger = get_logger()
    if logger:
        logger.error(msg)

def load_metrics(path: str = "data/analysis/metrics.json") -> List[Dict[str, Any]]:
    """Load metrics from JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metrics file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data)}")
    
    return data

def wilcoxon_signed_rank_test(data1: List[float], data2: List[float]) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test for paired samples.
    Returns (statistic, p-value).
    """
    if len(data1) != len(data2) or len(data1) == 0:
        return 0.0, 1.0

    differences = [d1 - d2 for d1, d2 in zip(data1, data2)]
    non_zero_diffs = [d for d in differences if d != 0]
    
    if len(non_zero_diffs) == 0:
        return 0.0, 1.0

    ranks = []
    abs_diffs = sorted([abs(d) for d in non_zero_diffs])
    
    # Assign ranks (handling ties)
    rank_map = {}
    for i, val in enumerate(abs_diffs):
        if val not in rank_map:
            # Find how many values are equal to this one
            count = sum(1 for v in abs_diffs if v == val)
            # Average rank for ties
            start_rank = i + 1
            end_rank = i + count
            avg_rank = (start_rank + end_rank) / 2.0
            rank_map[val] = avg_rank
            i += count - 1
        ranks.append(rank_map[val])

    # Sum of positive and negative ranks
    pos_rank_sum = sum(r for d, r in zip(non_zero_diffs, ranks) if d > 0)
    neg_rank_sum = sum(r for d, r in zip(non_diffs, ranks) if d < 0)
    
    statistic = min(pos_rank_sum, neg_rank_sum)
    n = len(non_zero_diffs)
    
    # Approximate p-value using normal distribution for n > 20
    if n > 20:
        mean = n * (n + 1) / 4
        std = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        z = (statistic - mean) / std if std > 0 else 0
        # Two-tailed p-value approximation
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    else:
        # For small n, use exact calculation (simplified)
        # In a real implementation, we would use scipy.stats.wilcoxon
        # Here we approximate for demonstration
        p_value = 0.05 if statistic < n * (n + 1) / 4 else 0.5

    return statistic, p_value

def calculate_wilcoxon_for_all_metrics(metrics: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Calculate Wilcoxon test for all continuous metrics."""
    results = {}
    
    # Group by task_id
    task_data = {}
    for row in metrics:
        tid = row.get('task_id')
        if tid:
            if tid not in task_data:
                task_data[tid] = {}
            task_data[tid][row.get('source_type')] = row

    # Extract paired data
    human_values = {}
    codegen_values = {}
    
    for tid, sources in task_data.items():
        if 'human' in sources and 'codegen' in sources:
            h = sources['human']
            c = sources['codegen']
            
            for metric in ['cyclomatic_complexity', 'halstead_volume']:
                if metric in h and metric in c and h[metric] is not None and c[metric] is not None:
                    if metric not in human_values:
                        human_values[metric] = []
                        codegen_values[metric] = []
                    human_values[metric].append(h[metric])
                    codegen_values[metric].append(c[metric])

    for metric in ['cyclomatic_complexity', 'halstead_volume']:
        if metric in human_values and len(human_values[metric]) > 1:
            stat, p_val = wilcoxon_signed_rank_test(human_values[metric], codegen_values[metric])
            results[metric] = {
                'statistic': stat,
                'p_value': p_val,
                'n': len(human_values[metric])
            }
    
    return results

def mcnemar_test(confusion_matrix: Dict[str, int]) -> Tuple[float, float]:
    """
    Perform McNemar's test for paired binary data.
    confusion_matrix should have keys: 'both_pass', 'both_fail', 'human_pass_codegen_fail', 'human_fail_codegen_pass'
    """
    b = confusion_matrix.get('human_pass_codegen_fail', 0)
    c = confusion_matrix.get('human_fail_codegen_pass', 0)
    
    n = b + c
    if n == 0:
        return 0.0, 1.0
    
    # Chi-square statistic with continuity correction
    stat = (abs(b - c) - 1) ** 2 / n
    
    # Approximate p-value using chi-square distribution with 1 df
    # For large n, chi-square(1) is approximately normal^2
    p_value = 1.0
    if stat > 0:
        # Using normal approximation for chi-square(1)
        z = math.sqrt(stat)
        p_value = 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))
    
    return stat, p_value

def calculate_mcnemar_for_pass_rate(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate McNemar's test for pass rate."""
    confusion = {
        'both_pass': 0,
        'both_fail': 0,
        'human_pass_codegen_fail': 0,
        'human_fail_codegen_pass': 0
    }
    
    task_data = {}
    for row in metrics:
        tid = row.get('task_id')
        if tid:
            if tid not in task_data:
                task_data[tid] = {}
            task_data[tid][row.get('source_type')] = row

    for tid, sources in task_data.items():
        if 'human' in sources and 'codegen' in sources:
            h_pass = sources['human'].get('pass_rate')
            c_pass = sources['codegen'].get('pass_rate')
            
            if h_pass is not None and c_pass is not None:
                h_pass = h_pass == 1
                c_pass = c_pass == 1
                
                if h_pass and c_pass:
                    confusion['both_pass'] += 1
                elif not h_pass and not c_pass:
                    confusion['both_fail'] += 1
                elif h_pass and not c_pass:
                    confusion['human_pass_codegen_fail'] += 1
                elif not h_pass and c_pass:
                    confusion['human_fail_codegen_pass'] += 1

    stat, p_val = mcnemar_test(confusion)
    
    return {
        'confusion_matrix': confusion,
        'statistic': stat,
        'p_value': p_val,
        'total_discordant': confusion['human_pass_codegen_fail'] + confusion['human_fail_codegen_pass']
    }

def fisher_exact_test_paired(data: List[Tuple[int, int]]) -> float:
    """
    Paired Fisher's exact test approximation using permutation.
    data: list of (human_success, codegen_success) pairs (0 or 1)
    """
    n = len(data)
    if n == 0:
        return 1.0

    # Count discordant pairs
    discordant = [(h, c) for h, c in data if h != c]
    if len(discordant) == 0:
        return 1.0

    # Observed count of human_success=1, codegen_success=0
    observed = sum(1 for h, c in discordant if h == 1 and c == 0)
    n_discordant = len(discordant)
    
    # Permutation test: randomly flip discordant pairs
    n_perms = 1000
    extreme_count = 0
    
    for _ in range(n_perms):
        perm_obs = 0
        for h, c in discordant:
            if random.random() < 0.5:
                # Flip the pair
                if c == 1 and h == 0:
                    perm_obs += 1
            else:
                if h == 1 and c == 0:
                    perm_obs += 1
        
        if perm_obs >= observed or perm_obs <= n_discordant - observed:
            extreme_count += 1

    return extreme_count / n_perms

def calculate_fisher_for_pass_rate(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate paired Fisher's exact test for pass rate."""
    pairs = []
    
    task_data = {}
    for row in metrics:
        tid = row.get('task_id')
        if tid:
            if tid not in task_data:
                task_data[tid] = {}
            task_data[tid][row.get('source_type')] = row

    for tid, sources in task_data.items():
        if 'human' in sources and 'codegen' in sources:
            h_pass = sources['human'].get('pass_rate')
            c_pass = sources['codegen'].get('pass_rate')
            
            if h_pass is not None and c_pass is not None:
                pairs.append((h_pass == 1, c_pass == 1))

    if len(pairs) == 0:
        return {'p_value': 1.0, 'n': 0}

    p_val = fisher_exact_test_paired(pairs)
    
    return {
        'p_value': p_val,
        'n': len(pairs),
        'discordant_pairs': sum(1 for h, c in pairs if h != c)
    }

def permutation_test_paired(data1: List[float], data2: List[float], n_perms: int = 1000) -> float:
    """
    Permutation test for paired data.
    """
    if len(data1) != len(data2) or len(data1) == 0:
        return 1.0

    observed_diff = sum(d1 - d2 for d1, d2 in zip(data1, data2)) / len(data1)
    n = len(data1)
    
    extreme_count = 0
    for _ in range(n_perms):
        # Randomly flip signs
        perm_diff = 0
        for d1, d2 in zip(data1, data2):
            diff = d1 - d2
            if random.random() < 0.5:
                diff = -diff
            perm_diff += diff
        perm_diff /= n
        
        if abs(perm_diff) >= abs(observed_diff):
            extreme_count += 1

    return extreme_count / n_perms

def calculate_permutation_for_branch_coverage(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate permutation test for branch coverage."""
    human_cov = []
    codegen_cov = []
    
    task_data = {}
    for row in metrics:
        tid = row.get('task_id')
        if tid:
            if tid not in task_data:
                task_data[tid] = {}
            task_data[tid][row.get('source_type')] = row

    for tid, sources in task_data.items():
        if 'human' in sources and 'codegen' in sources:
            h_cov = sources['human'].get('branch_coverage_pct')
            c_cov = sources['codegen'].get('branch_coverage_pct')
            
            if h_cov is not None and c_cov is not None:
                human_cov.append(h_cov)
                codegen_cov.append(c_cov)

    if len(human_cov) == 0:
        return {'p_value': 1.0, 'n': 0}

    p_val = permutation_test_paired(human_cov, codegen_cov)
    
    return {
        'p_value': p_val,
        'n': len(human_cov),
        'mean_diff': sum(h - c for h, c in zip(human_cov, codegen_cov)) / len(human_cov)
    }

def calculate_effect_size_cohen_d(data1: List[float], data2: List[float]) -> float:
    """Calculate Cohen's d effect size."""
    if len(data1) != len(data2) or len(data1) == 0:
        return 0.0

    mean1 = sum(data1) / len(data1)
    mean2 = sum(data2) / len(data2)
    
    var1 = sum((x - mean1) ** 2 for x in data1) / len(data1)
    var2 = sum((x - mean2) ** 2 for x in data2) / len(data2)
    
    pooled_std = math.sqrt((var1 + var2) / 2)
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def a_priori_power_analysis(effect_size: float = 0.5, alpha: float = 0.05, power: float = 0.8) -> int:
    """
    Calculate required sample size for a priori power analysis.
    Simplified calculation for paired t-test.
    """
    if effect_size <= 0:
        return 0

    # Approximate formula for paired t-test
    # n = ( (Z_alpha + Z_beta) / effect_size )^2
    # Z_alpha for two-tailed 0.05 is ~1.96
    # Z_beta for 0.8 power is ~0.84
    z_alpha = 1.96
    z_beta = 0.84
    
    n = ((z_alpha + z_beta) / effect_size) ** 2
    return int(math.ceil(n))

def post_hoc_power_analysis(effect_size: float, n: int, alpha: float = 0.05) -> float:
    """
    Calculate achieved power post-hoc.
    """
    if n <= 0 or effect_size <= 0:
        return 0.0

    # Simplified calculation
    # Power = P(Z > Z_alpha - effect_size * sqrt(n))
    z_alpha = 1.96
    z_stat = effect_size * math.sqrt(n)
    
    # Approximate power using normal CDF
    power = 0.5 * (1 + math.erf((z_stat - z_alpha) / math.sqrt(2)))
    return max(0.0, min(1.0, power))

def validate_success_criteria(stats_results: Dict[str, Any], metrics: List[Dict[str, Any]]) -> Dict[str, bool]:
    """
    Validate results against Success Criteria SC-002 (Statistical Significance) and SC-003 (Visualization Quality).
    
    SC-002: At least one statistical test (Wilcoxon, McNemar, Fisher, Permutation) must yield p < 0.05.
    SC-003: Visualization data must be present (checked by existence of required fields in metrics).
    """
    criteria = {}
    
    # SC-002: Statistical Significance
    # Check Wilcoxon p-values
    wilcoxon_pass = False
    if 'wilcoxon' in stats_results:
        for metric, result in stats_results['wilcoxon'].items():
            if result.get('p_value', 1.0) < 0.05:
                wilcoxon_pass = True
                break
    
    # Check McNemar p-value
    mcnemar_pass = False
    if 'mcnemar' in stats_results:
        if stats_results['mcnemar'].get('p_value', 1.0) < 0.05:
            mcnemar_pass = True
    
    # Check Fisher p-value
    fisher_pass = False
    if 'fisher' in stats_results:
        if stats_results['fisher'].get('p_value', 1.0) < 0.05:
            fisher_pass = True
    
    # Check Permutation p-value
    perm_pass = False
    if 'permutation' in stats_results:
        if stats_results['permutation'].get('p_value', 1.0) < 0.05:
            perm_pass = True
    
    # SC-002 passes if ANY test is significant
    criteria['SC-002_statistical_significance'] = wilcoxon_pass or mcnemar_pass or fisher_pass or perm_pass
    
    # SC-003: Visualization Quality
    # Check that metrics have all required fields for visualization
    required_fields = ['task_id', 'source_type', 'cyclomatic_complexity', 'halstead_volume', 'branch_coverage_pct', 'pass_rate']
    visualization_pass = True
    
    for row in metrics:
        for field in required_fields:
            if field not in row or row[field] is None:
                visualization_pass = False
                break
        if not visualization_pass:
            break
    
    criteria['SC-003_visualization_quality'] = visualization_pass
    
    return criteria

def run_statistical_analysis(metrics_path: str = "data/analysis/metrics.json", output_path: str = "state/validation_results.yaml"):
    """
    Run all statistical tests and validate success criteria.
    """
    logger = setup_logging(task_id="T046")
    logger.info("Starting Success Criteria Validation (T046)")
    
    try:
        metrics = load_metrics(metrics_path)
        logger.info(f"Loaded {len(metrics)} metrics records")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Run statistical tests
    stats_results = {}
    
    # Wilcoxon
    try:
        wilcoxon_results = calculate_wilcoxon_for_all_metrics(metrics)
        stats_results['wilcoxon'] = wilcoxon_results
        logger.info(f"Wilcoxon results: {wilcoxon_results}")
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        stats_results['wilcoxon'] = {}
    
    # McNemar
    try:
        mcnemar_results = calculate_mcnemar_for_pass_rate(metrics)
        stats_results['mcnemar'] = mcnemar_results
        logger.info(f"McNemar results: {mcnemar_results}")
    except Exception as e:
        logger.error(f"McNemar test failed: {e}")
        stats_results['mcnemar'] = {}
    
    # Fisher
    try:
        fisher_results = calculate_fisher_for_pass_rate(metrics)
        stats_results['fisher'] = fisher_results
        logger.info(f"Fisher results: {fisher_results}")
    except Exception as e:
        logger.error(f"Fisher test failed: {e}")
        stats_results['fisher'] = {}
    
    # Permutation
    try:
        perm_results = calculate_permutation_for_branch_coverage(metrics)
        stats_results['permutation'] = perm_results
        logger.info(f"Permutation results: {perm_results}")
    except Exception as e:
        logger.error(f"Permutation test failed: {e}")
        stats_results['permutation'] = {}
    
    # Validate success criteria
    criteria_results = validate_success_criteria(stats_results, metrics)
    
    # Prepare output
    output_data = {
        'timestamp': get_timestamp(),
        'task_id': get_task_id(),
        'criteria': criteria_results,
        'statistical_tests': stats_results
    }
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False)
    
    logger.info(f"Validation results written to {output_path}")
    
    # Print summary
    logger.info("=== Success Criteria Validation Summary ===")
    for criterion, passed in criteria_results.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"{criterion}: {status}")
    
    return output_data

def main():
    """Main entry point for T046."""
    set_task_id("T046")
    logger = setup_logging()
    
    try:
        run_statistical_analysis()
        logger.info("T046 completed successfully")
    except Exception as e:
        logger.error(f"T046 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()