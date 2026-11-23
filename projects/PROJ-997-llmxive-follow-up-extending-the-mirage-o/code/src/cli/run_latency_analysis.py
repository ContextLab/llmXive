import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
import pandas as pd
import pickle

from src.services.latency_meter import (
    LatencyMetrics, load_test_data, measure_proxy_policy_evaluation_time,
    measure_baseline_policy_evaluation_time, calculate_latency_reduction,
    write_metrics, run_latency_analysis
)
from src.config.logging_config import setup_logger

logger = logging.getLogger(__name__)

def main():
    """
    CLI entry point for latency analysis.
    Measures the time for proxy vs baseline policy evaluation steps.
    """
    parser = argparse.ArgumentParser(description="Run latency analysis.")
    parser.add_argument("--test-data", type=Path, required=True, help="Path to split_test.parquet")
    parser.add_argument("--predictor", type=Path, required=True, help="Path to gap_predictor.pkl")
    parser.add_argument("--baseline-model", type=Path, required=True, help="Path to quantized model for baseline")
    parser.add_argument("--output", type=Path, default=Path("data/processed/latency_metrics.json"), help="Output path")
    args = parser.parse_args()

    # Setup logger
    setup_logger("latency_analysis", log_file="logs/latency_analysis.log")

    logger.info(f"Loading test data from {args.test_data}")
    test_data = load_test_data(args.test_data)

    logger.info(f"Loading predictor from {args.predictor}")
    with open(args.predictor, 'rb') as f:
        predictor = pickle.load(f)

    logger.info(f"Running latency analysis...")
    metrics = run_latency_analysis(
        test_data=test_data,
        predictor=predictor,
        baseline_model_path=args.baseline_model
    )

    logger.info(f"Writing metrics to {args.output}")
    write_metrics(metrics, args.output)

    logger.info(f"Latency analysis complete. Reduction: {metrics.reduction_percentage:.2f}%")

if __name__ == "__main__":
    import argparse
    main()
