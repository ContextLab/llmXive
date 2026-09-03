import os
import sys
import argparse
import logging
import gc
import json
import time
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Local imports matching provided API surface
from utils.config import Config, get_default_config, create_config_with_overrides, enforce_cpu, set_random_seed, get_heuristic_thresholds, get_sensitivity_range
from utils.logger import setup_logger, get_structured_logger, get_current_resource_snapshot
from utils.resource_monitor import start_monitor, stop_monitor, get_max_memory_usage_gb, MemoryGuard
from data.loader import download_and_verify_ruler, verify_ruler_data_integrity
from data.preprocess import split_context, check_memory_usage, reduce_context_window, reduce_batch_size, exit_on_memory_exceeded, PreprocessConfig
from heuristics.base import HeuristicSelector
from heuristics.entropy import BlockEntropyHeuristic
from heuristics.gradient import GradientMagnitudeHeuristic
from heuristics.recency import RecencyBiasHeuristic
from heuristics.fallback import FallbackHeuristicWrapper
from eval.metrics import calculate_metrics, calculate_perplexity, evaluate_predictions
from eval.baseline_runner import DenseAttentionRunner, run_baseline_experiment
from eval.statistical import run_paired_ttest, run_wilcoxon_test, apply_holm_bonferroni, run_sensitivity_sweep, calculate_false_positive_rate, generate_statistical_report
from eval.report_generator import load_baseline_metrics, load_heuristic_results, compute_statistical_significance, generate_sensitivity_analysis, generate_final_report
from eval.exclusion_logger import validate_needle_presence, log_exclusion, scan_dataset_for_exclusions
from eval.report_verifier import verify_report

# Timeout handling
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out after 6 hours (21600 seconds)")

def setup_timeout_guard(seconds: int = 21600):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout_guard():
    signal.alarm(0)

def get_heuristic_instance(name: str, config: Config) -> HeuristicSelector:
    """Factory to instantiate heuristics based on config name."""
    thresholds = get_heuristic_thresholds(config)
    if name == "entropy":
        return BlockEntropyHeuristic(threshold=thresholds.get("entropy_threshold", 0.5))
    elif name == "gradient":
        return GradientMagnitudeHeuristic(threshold=thresholds.get("gradient_threshold", 0.5))
    elif name == "recency":
        return RecencyBiasHeuristic(threshold=thresholds.get("recency_threshold", 0.5))
    else:
        raise ValueError(f"Unknown heuristic: {name}")

def run_single_task(
    task_id: str,
    sample: Dict[str, Any],
    heuristic_name: str,
    config: Config,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run a single RULER task with a specific heuristic.
    Returns a result dictionary containing metrics and selection info.
    """
    set_random_seed(config.seed)
    start_time = time.time()
    
    # Memory check before processing
    if check_memory_usage():
        reduce_context_window(config)
        reduce_batch_size(config)
        if check_memory_usage():
            exit_on_memory_exceeded()

    # Validate needle presence
    if not validate_needle_presence(sample):
        log_exclusion(task_id, "Missing needle string", logger)
        return None

    # Initialize heuristic
    heuristic = get_heuristic_instance(heuristic_name, config)
    
    # Run inference (simplified logic for T023c context)
    # In a full implementation, this would call the model wrapper and heuristic logic
    # For T023c, we structure the output format expected by T024
    
    # Placeholder for actual inference result
    # In real execution, this would come from the model wrapper
    result = {
        "task_id": task_id,
        "heuristic": heuristic_name,
        "selection_set": heuristic.select_blocks(sample, config),
        "metrics": {
            "exact_match": 0.0, # Calculated by eval.metrics in real run
            "f1": 0.0,
            "perplexity": 0.0
        },
        "timing": time.time() - start_time
    }
    
    return result

def run_sensitivity_analysis(
    config: Config,
    baseline_results: List[Dict],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across thresholds and calculate false positive rates.
    """
    thresholds = get_sensitivity_range(config) # {0.01, 0.05, 0.1}
    sensitivity_table = []
    
    logger.info(f"Starting sensitivity analysis with thresholds: {thresholds}")
    
    for thresh in thresholds:
        # Update config threshold
        config.heuristic_threshold = thresh
        
        # Run heuristics with this threshold
        # (In real execution, this loops through dataset samples)
        heuristic_results = [] 
        
        # Calculate false positive rate against baseline
        # FPR = (Heuristic Selection - Baseline Selection) / Total Baseline Selection
        fpr = calculate_false_positive_rate(heuristic_results, baseline_results)
        
        # Mock accuracy for structure (real run calculates this)
        acc = 0.0 
        
        sensitivity_table.append({
            "threshold": thresh,
            "accuracy": acc,
            "false_positive_rate": fpr
        })
        
        gc.collect()
    
    return {
        "sensitivity_table": sensitivity_table,
        "thresholds_tested": thresholds
    }

def format_results_for_aggregation(
    heuristic_results: List[Dict],
    baseline_results: List[Dict],
    sensitivity_data: Dict,
    config: Config,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    T023c: Implement output formatting in code/main.py to structure results for T024.
    Aggregates raw run results into the schema required by T024 (benchmark_report.json).
    """
    logger.info("Formatting results for aggregation...")
    
    # 1. Aggregate Metrics (T021/T021b)
    # Average F1 across runs
    total_f1 = sum(r.get("metrics", {}).get("f1", 0.0) for r in heuristic_results if r)
    count = len([r for r in heuristic_results if r])
    avg_f1 = total_f1 / count if count > 0 else 0.0
    
    # 2. Statistical Significance (T027/T027b)
    # Run paired t-test and Wilcoxon
    ttest_p, ttest_stat = run_paired_ttest(heuristic_results, baseline_results)
    wilcoxon_p, wilcoxon_stat = run_wilcoxon_test(heuristic_results, baseline_results)
    
    # Apply Holm-Bonferroni if multiple comparisons (simplified here)
    corrected_p = apply_holm_bonferroni([ttest_p, wilcoxon_p])
    
    # Determine significance statement
    significance_statement = f"p < 0.05" if corrected_p[0] < 0.05 else "p >= 0.05"
    
    # 3. Sensitivity Analysis (T028/T029/T032a/T032b)
    # Use pre-calculated sensitivity data
    sensitivity_table = sensitivity_data.get("sensitivity_table", [])
    
    # 4. Construct Final Report
    report = {
        "f1_score": avg_f1,
        "p_value": corrected_p[0], # Primary t-test p-value
        "false_positive_rate": sensitivity_table[0]["false_positive_rate"] if sensitivity_table else 0.0,
        "sensitivity_table": sensitivity_table,
        "ttest_stat": ttest_stat,
        "wilcoxon_stat": wilcoxon_stat,
        "significance_statement": significance_statement,
        "metadata": {
            "heuristic": config.heuristic_name,
            "thresholds_tested": sensitivity_data.get("thresholds_tested", []),
            "samples_processed": count,
            "seed": config.seed
        }
    }
    
    return report

def main():
    parser = argparse.ArgumentParser(description="LLMXive Sparse Attention Pipeline")
    parser.add_argument("--config", type=str, default="default", help="Config profile")
    parser.add_argument("--heuristic", type=str, default="entropy", help="Heuristic to run")
    parser.add_argument("--output", type=str, default="results/benchmark_report.json", help="Output path")
    args = parser.parse_args()

    # Setup
    enforce_cpu()
    logger = setup_logger("main", level=logging.INFO)
    config = create_config_with_overrides(args.config, {"heuristic_name": args.heuristic})
    
    # Memory Guard
    guard = MemoryGuard(max_gb=6.5, logger=logger)
    guard.start()

    # Setup Timeout
    setup_timeout_guard(21600)

    try:
        # 1. Load Data (T006/T037)
        # In real execution, this downloads/verifies RULER
        # dataset = download_and_verify_ruler() 
        logger.info("Data loading step skipped in T023c formatting task (assumed loaded).")
        
        # 2. Run Baseline (T022c)
        # baseline_results = run_baseline_experiment(dataset, config, logger)
        baseline_results = [] # Placeholder for real run
        logger.info("Baseline execution skipped in T023c formatting task.")

        # 3. Run Heuristics (T023a/T023b)
        # heuristic_results = [run_single_task(...) for ...]
        heuristic_results = []
        logger.info("Heuristic execution skipped in T023c formatting task.")

        # 4. Run Sensitivity Analysis (T028/T029)
        sensitivity_data = run_sensitivity_analysis(config, baseline_results, logger)

        # 5. Format Results (T023c - THIS TASK)
        final_report = format_results_for_aggregation(
            heuristic_results,
            baseline_results,
            sensitivity_data,
            config,
            logger
        )

        # 6. Write Output (T024)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Report written to {output_path}")

        # 7. Verify Report (T036)
        verify_report(output_path)

    except TimeoutError:
        logger.error("Pipeline timed out.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    finally:
        guard.stop()
        cancel_timeout_guard()
        stop_monitor()

if __name__ == "__main__":
    main()