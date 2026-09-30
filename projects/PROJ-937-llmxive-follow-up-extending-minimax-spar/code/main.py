import os
import sys
import argparse
import logging
import gc
import json
import signal
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

# Project imports based on API surface
from utils.config import Config, get_default_config, enforce_cpu, set_random_seed
from utils.logger import setup_logger, get_structured_logger, get_logger_for_task
from utils.resource_monitor import start_monitor, stop_monitor, MemoryGuard
from data.loader import download_and_verify_ruler, verify_ruler_data_integrity
from data.preprocess import split_context, check_memory_usage, exit_on_memory_exceeded
from heuristics.base import HeuristicSelector
from heuristics.block_entropy import BlockEntropyHeuristic
from heuristics.gradient import GradientMagnitudeHeuristic
from heuristics.recency import RecencyBiasHeuristic
from heuristics.fallback import FallbackHeuristicWrapper
from eval.baseline_runner import DenseAttentionRunner, run_baseline_experiment
from eval.metrics import calculate_metrics, calculate_perplexity
from eval.statistical import run_paired_ttest, run_wilcoxon_test, apply_holm_bonferroni, calculate_false_positive_rate, run_sensitivity_sweep
from eval.report_generator import generate_final_report
from eval.report_verifier import verify_report
from models.mini_max_wrapper import create_minimax_wrapper, MiniMaxConfig

# --- Timeout Guard Implementation (Task T041) ---
class TimeoutError(Exception):
    """Custom exception raised when the 6-hour timeout is exceeded."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout. Raises TimeoutError to terminate gracefully."""
    raise TimeoutError("Execution exceeded the 6-hour (21600s) timeout limit.")

def setup_timeout_guard(timeout_seconds: int = 21600):
    """
    Sets up a signal-based timeout guard.
    Only works on Unix-like systems where SIGALRM is available.
    On Windows, this is a no-op (graceful degradation).
    """
    if sys.platform != 'win32':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        logging.info(f"Timeout guard set to {timeout_seconds} seconds (6 hours).")
    else:
        logging.warning("SIGALRM not available on Windows. Timeout guard disabled.")

def cancel_timeout_guard():
    """Cancels the active timeout guard."""
    if sys.platform != 'win32':
        signal.alarm(0)
        logging.info("Timeout guard cancelled.")

# --- Heuristic Logic ---
def get_heuristic_instance(heuristic_name: str) -> HeuristicSelector:
    """Factory to instantiate the correct heuristic based on name."""
    if heuristic_name == "block_entropy":
        return BlockEntropyHeuristic()
    elif heuristic_name == "gradient_magnitude":
        return GradientMagnitudeHeuristic()
    elif heuristic_name == "recency_bias":
        return RecencyBiasHeuristic()
    elif heuristic_name == "fallback":
        return FallbackHeuristicWrapper()
    else:
        raise ValueError(f"Unknown heuristic: {heuristic_name}")

def run_single_task(
    model,
    task_data: Dict[str, Any],
    heuristic_name: str,
    config: Config
) -> Dict[str, Any]:
    """
    Executes a single RULER task with the specified heuristic.
    Returns a dictionary of metrics.
    """
    logger = get_logger_for_task("main")
    logger.info(f"Running task with heuristic: {heuristic_name}")

    # 1. Prepare context
    context = task_data.get("context", "")
    target = task_data.get("target", "")
    chunks = list(split_context(context, chunk_size=config.chunk_size))

    # 2. Select blocks using heuristic
    heuristic = get_heuristic_instance(heuristic_name)
    selected_blocks = heuristic.select_blocks(chunks, model)

    # 3. Run inference on selected blocks
    # (Simplified logic for the runner; actual implementation would feed blocks to model)
    # Assuming model has an inference method compatible with the blocks
    # For this implementation, we assume the model returns a prediction string
    # In a real scenario, this would be the actual model call
    prediction = model.infer(selected_blocks) 

    # 4. Calculate metrics
    metrics = calculate_metrics(prediction, target)
    metrics["heuristic"] = heuristic_name
    metrics["task_id"] = task_data.get("id", "unknown")
    
    return metrics

def run_sensitivity_analysis(
    model,
    dataset: List[Dict[str, Any]],
    config: Config
) -> List[Dict[str, Any]]:
    """
    Runs sensitivity analysis across different thresholds.
    Returns a list of results for each threshold.
    """
    logger = get_logger_for_task("main")
    thresholds = config.sensitivity_range
    results = []

    for threshold in thresholds:
        logger.info(f"Running sensitivity sweep at threshold: {threshold}")
        config.current_threshold = threshold
        # Re-run specific heuristics or the whole pipeline with new threshold
        # This is a placeholder for the actual sweep logic
        batch_results = []
        for sample in dataset:
            res = run_single_task(model, sample, "block_entropy", config)
            batch_results.append(res)
        results.append({
            "threshold": threshold,
            "results": batch_results
        })
    return results

def format_results_for_aggregation(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Formats individual task results into the aggregation structure."""
    return {
        "tasks": results,
        "summary": {
            "count": len(results),
            "avg_f1": sum(r.get("f1_score", 0) for r in results) / len(results) if results else 0
        }
    }

def main():
    """Main entry point for the RULER evaluation pipeline."""
    # Setup logging
    logger = setup_logger("main", level=logging.INFO)
    logger.info("Starting llmXive Sparse Attention Evaluation Pipeline")

    # Parse arguments
    parser = argparse.ArgumentParser(description="Run Sparse Attention Heuristics on RULER")
    parser.add_argument("--heuristic", type=str, default="block_entropy", help="Heuristic to use")
    parser.add_argument("--timeout", type=int, default=21600, help="Timeout in seconds (default 6 hours)")
    parser.add_argument("--sensitivity", action="store_true", help="Run sensitivity analysis")
    args = parser.parse_args()

    # 1. Setup Timeout Guard (T041)
    setup_timeout_guard(args.timeout)

    try:
        # 2. Load Configuration
        config = get_default_config()
        enforce_cpu()
        set_random_seed(config.seed)

        # 3. Resource Monitoring (T040)
        start_monitor()
        memory_guard = MemoryGuard(threshold_gb=6.5)
        
        # 4. Data Loading (T006, T037)
        logger.info("Loading RULER dataset...")
        # Assuming download_and_verify_ruler handles the fetch and checksum
        dataset = download_and_verify_ruler()
        
        # 5. Model Loading (T048, T017a)
        logger.info("Loading MiniMax-M3 model...")
        model_config = MiniMaxConfig(device="cpu")
        model = create_minimax_wrapper(model_config)

        # 6. Baseline Execution (T022c)
        logger.info("Running Dense Attention Baseline...")
        baseline_results = run_baseline_experiment(model, dataset, config)

        # 7. Heuristic Execution
        logger.info(f"Running Heuristic: {args.heuristic}")
        heuristic_results = []
        
        # Check memory before heavy lifting
        if check_memory_usage():
            logger.warning("Memory usage high. Attempting reduction...")
            exit_on_memory_exceeded()

        for sample in dataset:
            res = run_single_task(model, sample, args.heuristic, config)
            heuristic_results.append(res)

        # 8. Sensitivity Analysis (if requested)
        if args.sensitivity:
            logger.info("Running Sensitivity Analysis...")
            sensitivity_data = run_sensitivity_analysis(model, dataset, config)
            # Flatten sensitivity data for report
            for sweep in sensitivity_data:
                for r in sweep["results"]:
                    r["sensitivity_threshold"] = sweep["threshold"]

        # 9. Statistical Analysis (T027, T030)
        logger.info("Running Statistical Analysis...")
        # Compare heuristic vs baseline
        # Note: In a real scenario, we align results by task_id
        ttest_stat, ttest_p = run_paired_ttest(heuristic_results, baseline_results)
        wilcoxon_stat, wilcoxon_p = run_wilcoxon_test(heuristic_results, baseline_results)
        
        # Holm-Bonferroni correction
        corrected_p = apply_holm_bonferroni([ttest_p, wilcoxon_p])

        # 10. Generate Report (T024, T031)
        report = generate_final_report(
            baseline=baseline_results,
            heuristics=heuristic_results,
            ttest_stat=ttest_stat,
            ttest_p=ttest_p,
            wilcoxon_stat=wilcoxon_stat,
            wilcoxon_p=wilcoxon_p,
            corrected_p=corrected_p,
            sensitivity_data=sensitivity_data if args.sensitivity else None
        )

        # 11. Verify Report (T036)
        verify_report(report)

        # Save report
        output_path = Path("results/benchmark_report.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {output_path}")

    except TimeoutError as e:
        logger.critical(str(e))
        logger.error("Process terminated due to timeout. Check logs for partial results.")
        sys.exit(1)
    except RuntimeError as e:
        if "Memory constraint exceeded" in str(e):
            logger.critical(str(e))
            sys.exit(1)
        raise
    finally:
        # 12. Cleanup
        cancel_timeout_guard()
        stop_monitor()
        gc.collect()
        logger.info("Pipeline finished.")

if __name__ == "__main__":
    main()