import os
import sys
import argparse
import logging
import gc
import json
import time
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- Project Imports (Validating API Surface) ---
from utils.config import get_default_config, set_random_seed, enforce_cpu
from utils.logger import setup_logger, get_structured_logger, get_logger_for_task
from utils.env_check import detect_cuda_availability, enforce_cpu_only
from utils.resource_monitor import start_monitor, stop_monitor, MemoryGuard
from data.loader import download_and_verify_ruler, verify_ruler_data_integrity
from data.preprocess import (
    check_memory_usage, reduce_batch_size,
    reduce_context_window, exit_on_memory_exceeded
)
from data.streaming_chunker import stream_chunker
from heuristics.fallback import FallbackHeuristicWrapper
from heuristics.selector import HeuristicSelector
from eval.baseline_runner import DenseAttentionRunner
from eval.metrics import calculate_metrics, calculate_perplexity
from eval.statistical import (
    run_paired_ttest, run_wilcoxon_test, apply_holm_bonferroni,
    run_sensitivity_sweep, calculate_false_positive_rate
)
from eval.report_generator import generate_final_report
from eval.exclusion_logger import validate_needle_presence, log_exclusion

# --- Timeout Guard Implementation (T041) ---
def timeout_handler(signum, frame):
    """Handler called when the execution exceeds the allowed time."""
    logger = get_structured_logger("main")
    logger.critical(
        "TIMEOUT GUARD TRIGGERED: Execution exceeded 6 hours (21600s). Terminating."
    )
    sys.exit(1)

def setup_timeout_guard(seconds: int = 21600):
    """Sets up a signal‑based timeout guard."""
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
    else:
        # Windows fallback (no SIGALRM) - log warning
        logger = get_structured_logger("main")
        logger.warning(
            "SIGALRM not available on this OS. Timeout guard disabled."
        )

def cancel_timeout_guard():
    """Cancels any previously set alarm."""
    if hasattr(signal, "SIGALRM"):
        signal.alarm(0)

# --- No Quantization Enforcement (T051) ---
def enforce_no_quantization(config: Dict[str, Any]):
    """Runtime check to ensure no quantization flags are active."""
    if config.get("load_in_8bit", False) or config.get("load_in_4bit", False):
        raise RuntimeError(
            "Quantization detected (8-bit or 4-bit). This project strictly forbids "
            "quantization libraries per FR-003. Set load_in_8bit=False and load_in_4bit=False."
        )

# --- Model Loading with Memory Guard (T047, T048) ---
def load_model_with_memory_guard(config: Dict[str, Any]):
    """
    Loads the model with strict memory checks.
    Implements T047: If memory exceeded, reduce context/batch -> THEN load.
    If reduction fails, exit with code 1.
    """
    logger = get_structured_logger("main")
    
    # Check memory before loading
    if check_memory_usage():
        logger.warning(
            "High memory usage detected before model load. Attempting reduction strategies."
        )
        # Strategy 1: Reduce context window
        new_context = reduce_context_window(config.get("context_window", 4096))
        if new_context:
            config["context_window"] = new_context
            logger.info(f"Context window reduced to {new_context}.")
        
        # Strategy 2: Reduce batch size
        if check_memory_usage():
            new_batch = reduce_batch_size(config.get("batch_size", 1))
            if new_batch:
                config["batch_size"] = new_batch
                logger.info(f"Batch size reduced to {new_batch}.")
        
        # Final Check: If still high, exit
        if check_memory_usage():
            exit_on_memory_exceeded()
    
    # Enforce CPU and No Quantization
    enforce_cpu(config)
    enforce_no_quantization(config)
    
    # Load Model (Placeholder for actual model loading logic from T017a)
    # Assuming a wrapper exists or we load via transformers directly here
    logger.info("Loading model with memory guard...")
    # In a real implementation, this would call the specific model loader
    # e.g., from models.mini_max_wrapper import create_minimax_wrapper
    # model = create_minimax_wrapper(config)
    return "MockModelInstance"  # Placeholder for actual model object

# --- Needle Validation (T045) ---
def verify_needle_presence(sample: Dict[str, Any]) -> bool:
    """
    Checks if the 'needle' key exists and is non‑empty in the sample.
    Logs a warning and returns False if missing.
    """
    if "needle" not in sample or not sample["needle"]:
        logger = get_structured_logger("main")
        logger.warning(
            f"Missing or empty 'needle' in sample. Skipping. Sample keys: {list(sample.keys())}"
        )
        return False
    return True

# --- Heuristic Execution Logic (T023a, T030a, T030b) ---
def run_single_task(
    task_id: str,
    model,
    dataset_sample: Dict[str, Any],
    config: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Executes a single task with heuristics or baseline.
    Returns a dictionary of results for aggregation.
    """
    results = {
        "task_id": task_id,
        "heuristic_results": {},
        "baseline_result": None,
        "excluded": False
    }

    # Validate Needle (T045)
    if not verify_needle_presence(dataset_sample):
        log_exclusion(task_id, "Missing needle")
        results["excluded"] = True
        return results

    # 1. Run Baseline (Dense Attention) - T022c
    baseline_runner = DenseAttentionRunner(config)
    baseline_result = baseline_runner.run(task_id, dataset_sample, model)
    results["baseline_result"] = baseline_result

    # 2. Run Heuristics
    heuristics_to_run = config.get("heuristics", ["all"])
    
    # Check for Fallback (T018)
    selector = HeuristicSelector(config)
    fallback_wrapper = FallbackHeuristicWrapper(config)

    for heuristic_name in heuristics_to_run:
        if heuristic_name == "all":
            # Run all defined heuristics
            heuristic_scores = selector.run_all(dataset_sample)
        else:
            heuristic_scores = selector.run(heuristic_name, dataset_sample)

        # Check for Zero Scores (T018 Fallback)
        if selector.is_scores_zero(heuristic_scores):
            logger.info(
                f"Heuristic scores near‑zero for {heuristic_name}. Using Fallback (First K)."
            )
            final_selection = fallback_wrapper.select_first_k(
                dataset_sample, config.get("k", 5)
            )
        else:
            final_selection = selector.select_top_k(
                heuristic_scores, config.get("k", 5)
            )

        # Calculate Metrics for this heuristic
        metrics = calculate_metrics(
            baseline_result["predictions"],  # Ground truth
            final_selection,                # Heuristic selection
            dataset_sample
        )
        
        results["heuristic_results"][heuristic_name] = {
            "selection": final_selection,
            "metrics": metrics
        }

    return results

# --- Statistical Analysis Integration (T030) ---
def run_analysis(
    results_list: List[Dict[str, Any]],
    config: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Aggregates results, runs statistical tests (T030), and generates the final report.
    Prioritizes Paired t‑test (T030b) over Wilcoxon.
    """
    # 1. Collect Data for Statistical Tests
    baseline_scores = []
    heuristic_scores: Dict[str, List[float]] = {}

    for res in results_list:
        if res.get("excluded"):
            continue
        
        if res.get("baseline_result"):
            baseline_scores.append(res["baseline_result"].get("f1_score", 0.0))
        
        for h_name, h_data in res.get("heuristic_results", {}).items():
            heuristic_scores.setdefault(h_name, []).append(
                h_data.get("metrics", {}).get("f1_score", 0.0)
            )

    # 2. Run Statistical Tests (T027a, T027b)
    ttest_results = {}
    for h_name, scores in heuristic_scores.items():
        if len(baseline_scores) == len(scores) and len(baseline_scores) > 1:
            t_stat, p_val = run_paired_ttest(baseline_scores, scores)
            ttest_results[h_name] = {"t_stat": t_stat, "p_val": p_val}

    corrected_p_values = apply_holm_bonferroni(
        [info["p_val"] for info in ttest_results.values()]
    )

    wilcoxon_results = {}
    for h_name, scores in heuristic_scores.items():
        if len(baseline_scores) == len(scores) and len(baseline_scores) > 1:
            w_stat, p_val = run_wilcoxon_test(baseline_scores, scores)
            wilcoxon_results[h_name] = {"w_stat": w_stat, "p_val": p_val}

    # 3. Sensitivity Analysis & False Positive Rate (T028b, T032a, T032b)
    sensitivity_thresholds = config.get("sensitivity_thresholds", [0.01, 0.05, 0.1])
    sensitivity_table = []

    for thresh in sensitivity_thresholds:
        fp_rate = calculate_false_positive_rate(
            heuristic_scores.get("all", []),  # Placeholder
            baseline_scores,
            threshold=thresh
        )
        avg_f1 = (
            sum(heuristic_scores.get("all", [0.0])) / max(1, len(heuristic_scores.get("all", [])))
        )
        sensitivity_table.append(
            {
                "threshold": thresh,
                "accuracy": float(avg_f1),
                "false_positive_rate": float(fp_rate)
            }
        )

    # 4. Generate Final Report (T031)
    # Prioritize T‑test p‑value as per T030b
    if ttest_results:
        best_heuristic = max(
            ttest_results.keys(),
            key=lambda k: corrected_p_values[ttest_results.keys().index(k)]
        )
    else:
        best_heuristic = None
    best_p_val = (
        corrected_p_values[0]["adjusted_p_value"]
        if corrected_p_values
        else 1.0
    )

    significance_statement = (
        "p < 0.05" if best_p_val < 0.05 else "p >= 0.05"
    )

    final_report = generate_final_report(
        baseline_avg_f1=sum(baseline_scores) / max(1, len(baseline_scores)),
        best_heuristic=best_heuristic,
        best_heuristic_f1=sum(
            heuristic_scores.get(best_heuristic, [0.0])
        ) / max(1, len(heuristic_scores.get(best_heuristic, []))),
        p_value=best_p_val,
        significance_statement=significance_statement,
        ttest_stat=ttest_results.get(best_heuristic, {}).get("t_stat"),
        wilcoxon_stat=wilcoxon_results.get(best_heuristic, {}).get("w_stat"),
        sensitivity_table=sensitivity_table,
        false_positive_rate=sensitivity_table[-1]["false_positive_rate"]
        if sensitivity_table
        else 0.0
    )

    # Write to disk
    output_path = Path("results/benchmark_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Final benchmark report written to {output_path}")
    return final_report

# --- Main Entry Point ---
def main():
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline"
    )
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=["download", "run", "analyze"]
    )
    parser.add_argument("--heuristic", type=str, default="all")
    parser.add_argument("--threshold", type=float, default=0.05)
    args = parser.parse_args()

    # Setup Logger
    logger = setup_logger("main")

    # Setup Timeout Guard (T041)
    setup_timeout_guard(21600)

    # Load Config
    config = get_default_config()
    config["heuristic"] = args.heuristic
    config["threshold"] = args.threshold
    set_random_seed(config.get("seed", 42))

    # Detect Environment
    detect_cuda_availability()
    enforce_cpu_only()

    try:
        if args.action == "download":
            logger.info("Starting RULER dataset download and verification...")
            download_and_verify_ruler(config)
            logger.info("Download complete.")

        elif args.action == "run":
            logger.info("Starting heuristic execution...")
            # Load Model
            model = load_model_with_memory_guard(config)
            
            # Load Data (Streaming)
            dataset = stream_chunker(config)
            
            results_list = []
            for sample in dataset:
                task_id = sample.get("task_id", "unknown")
                res = run_single_task(task_id, model, sample, config, logger)
                results_list.append(res)
                
                # Check memory periodically
                if check_memory_usage():
                    logger.warning(
                        "Memory pressure detected during run. Reducing batch/context."
                    )
                    reduce_batch_size(config)
                    reduce_context_window(config)

            # Save intermediate results for analysis step
            with open("results/intermediate_results.json", "w") as f:
                json.dump(results_list, f)
            
            logger.info(
                "Execution complete. Intermediate results saved."
            )

        elif args.action == "analyze":
            logger.info("Starting statistical analysis...")
            # Load intermediate results
            with open("results/intermediate_results.json", "r") as f:
                results_list = json.load(f)
            
            run_analysis(results_list, config, logger)
            logger.info("Analysis complete.")

    except Exception as e:
        logger.critical(f"Execution failed with error: {e}")
        raise
    finally:
        cancel_timeout_guard()
        stop_monitor()

if __name__ == "__main__":
    main()