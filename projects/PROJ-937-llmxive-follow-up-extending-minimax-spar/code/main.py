import os
import sys
import argparse
import logging
import gc
import json
import signal
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Local imports based on API surface
from utils.config import Config, get_default_config, enforce_cpu, set_random_seed
from utils.logger import setup_logger, get_structured_logger, log_resource_usage
from utils.resource_monitor import start_monitor, stop_monitor, MemoryGuard
from data.loader import download_and_verify_ruler
from data.preprocess import preprocess_and_save, PreprocessConfig
from heuristics.entropy import BlockEntropyHeuristic
from heuristics.gradient import GradientMagnitudeHeuristic
from heuristics.recency import RecencyBiasHeuristic
from heuristics.fallback import FallbackHeuristicWrapper
from eval.baseline_runner import DenseAttentionRunner, run_baseline_experiment
from eval.metrics import calculate_metrics
from eval.aggregator import run_aggregation
from eval.report_generator import generate_final_report
from models.mini_max_wrapper import create_minimax_wrapper

# Global timeout limit for CI compliance (in seconds)
# Default: 3 hours (10800 seconds) as per typical CI limits, configurable via env
CI_TIMEOUT_SECONDS = int(os.getenv("CI_TIMEOUT_SECONDS", "10800"))

# Global variable to track start time for timeout checks
_experiment_start_time: Optional[float] = None

def _timeout_handler(signum, frame):
    """Signal handler for timeout. Raises an exception to break the loop."""
    raise TimeoutError(
        f"Experiment exceeded the time limit of {CI_TIMEOUT_SECONDS} seconds. "
        "Terminating execution to respect CI constraints."
    )

def _check_timeout():
    """Check if the experiment has exceeded the timeout limit."""
    if _experiment_start_time is None:
        return
    elapsed = time.time() - _experiment_start_time
    if elapsed > CI_TIMEOUT_SECONDS:
        raise TimeoutError(
            f"Experiment exceeded the time limit of {CI_TIMEOUT_SECONDS} seconds "
            f"(elapsed: {elapsed:.2f}s). Terminating."
        )

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Sparse Attention Heuristic Evaluation")
    parser.add_argument("--config", type=str, default=None, help="Path to config JSON")
    parser.add_argument("--heuristic", type=str, choices=["entropy", "gradient", "recency"], default="entropy")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run on (cpu)")
    parser.add_argument("--timeout", type=int, default=CI_TIMEOUT_SECONDS, help="Timeout in seconds")
    parser.add_argument("--subset-size", type=int, default=10, help="Number of samples to process for quick run")
    parser.add_argument("--run-baseline", action="store_true", help="Run dense attention baseline")
    parser.add_argument("--run-statistics", action="store_true", help="Run statistical analysis after experiments")
    return parser.parse_args()

def get_heuristic_instance(name: str, config: Config):
    if name == "entropy":
        return BlockEntropyHeuristic(config)
    elif name == "gradient":
        return GradientMagnitudeHeuristic(config)
    elif name == "recency":
        return RecencyBiasHeuristic(config)
    else:
        raise ValueError(f"Unknown heuristic: {name}")

def run_single_task(heuristic_name: str, config: Config, logger: logging.Logger, subset_size: int):
    """
    Runs a single heuristic experiment on the RULER dataset subset.
    Includes timeout checks at critical points.
    """
    global _experiment_start_time
    _experiment_start_time = time.time()

    logger.info(f"Starting experiment for heuristic: {heuristic_name}")

    # 1. Download and verify data
    logger.info("Downloading RULER dataset...")
    data_path = download_and_verify_ruler(subset_size=subset_size)
    
    # Check timeout after download
    _check_timeout()

    # 2. Preprocess data
    logger.info("Preprocessing data...")
    preprocess_config = PreprocessConfig(
        input_path=data_path,
        output_path=Path("data/processed/preprocessed_ruler.json"),
        chunk_size=4096,
        max_batch_size=1
    )
    processed_data_path = preprocess_and_save(preprocess_config, logger)

    # Check timeout after preprocess
    _check_timeout()

    # 3. Initialize Model
    logger.info("Initializing MiniMax model wrapper...")
    model_wrapper = create_minimax_wrapper(config, device=config.device)

    # 4. Initialize Heuristic
    heuristic = get_heuristic_instance(heuristic_name, config)
    wrapped_heuristic = FallbackHeuristicWrapper(heuristic, config)

    # 5. Run Inference Loop
    logger.info("Running heuristic inference loop...")
    results = []
    
    try:
        for idx, sample in enumerate(model_wrapper.stream_dataset(processed_data_path)):
            # Periodic timeout check inside the loop
            if idx % 5 == 0:
                _check_timeout()

            # Run heuristic selection
            selected_blocks = wrapped_heuristic.select_blocks(sample, model_wrapper)
            
            # Run inference with selected blocks
            prediction = model_wrapper.inference_with_sparse_attention(sample, selected_blocks)
            
            results.append({
                "sample_id": idx,
                "prediction": prediction,
                "selected_blocks": selected_blocks,
                "heuristic": heuristic_name
            })
            
            # Cleanup to prevent memory bloat in long runs
            if idx % 10 == 0:
                gc.collect()
                log_resource_usage(logger)

    except TimeoutError as e:
        logger.error(f"Timeout during inference loop: {e}")
        raise

    # Save results
    output_file = Path(f"results/{heuristic_name}_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return results

def main():
    args = parse_args()
    
    # Set global timeout based on argument
    global CI_TIMEOUT_SECONDS
    CI_TIMEOUT_SECONDS = args.timeout

    # Setup logging
    logger = setup_logger("main", level=logging.INFO)
    
    # Load config
    config = get_default_config()
    if args.config:
        config = Config.from_json(args.config)
    
    # Enforce constraints
    enforce_cpu()
    set_random_seed(config.seed)
    
    logger.info(f"Starting llmXive pipeline with timeout: {CI_TIMEOUT_SECONDS}s")
    
    # Start Resource Monitor (T040)
    start_monitor(logger)

    # Set up signal handler for SIGALRM (Unix) or manual check (Windows fallback)
    # Note: signal.SIGALRM is not available on Windows. We rely on _check_timeout() for cross-platform safety.
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(CI_TIMEOUT_SECONDS)
        logger.info("SIGALRM timeout guard installed.")
    else:
        logger.warning("SIGALRM not available (Windows). Relying on periodic manual timeout checks.")

    try:
        all_results = {}

        # Run Baseline if requested
        if args.run_baseline:
            logger.info("Running Dense Attention Baseline...")
            baseline_results = run_baseline_experiment(args.subset_size, config, logger)
            all_results["baseline"] = baseline_results
            _check_timeout()

        # Run Heuristic
        logger.info(f"Running {args.heuristic} heuristic...")
        heuristic_results = run_single_task(args.heuristic, config, logger, args.subset_size)
        all_results[args.heuristic] = heuristic_results
        _check_timeout()

        # Run Aggregation and Report
        if args.run_statistics:
            logger.info("Running statistical analysis and report generation...")
            run_aggregation(config, logger)
            generate_final_report(config, logger)
        
        logger.info("Pipeline completed successfully.")

    except TimeoutError as e:
        logger.critical(f"Pipeline terminated due to timeout: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Stop resource monitor
        stop_monitor()
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel the alarm

if __name__ == "__main__":
    main()