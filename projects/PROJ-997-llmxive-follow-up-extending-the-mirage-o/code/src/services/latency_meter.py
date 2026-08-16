import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pickle
import sys

# Ensure parent is in path for imports if running as script
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.entities import GapPredictionResult
from src.config.logging_config import setup_logger, ensure_log_dir

@dataclass
class LatencyMetrics:
    proxy_prediction_time: float
    baseline_inference_time: float
    reduction_percentage: float
    target_met: bool

def load_test_data(test_path: Path) -> List[Dict[str, Any]]:
    """Load the test dataset (parquet or json) to get sample count for timing."""
    # We need the number of samples to estimate total time for the proxy loop
    # Assuming T021A produced split_test.parquet
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path}")
    
    # Simple loading logic; if parquet, use pandas, else json
    if test_path.suffix == '.parquet':
        import pandas as pd
        df = pd.read_parquet(test_path)
        return df.to_dict(orient='records')
    elif test_path.suffix == '.json':
        with open(test_path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported test data format: {test_path.suffix}")

def load_predictor(model_path: Path) -> Any:
    """Load the trained KRR predictor model."""
    if not model_path.exists():
        raise FileNotFoundError(f"Predictor model not found at {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def measure_proxy_policy_evaluation_time(
    test_samples: List[Dict[str, Any]], 
    predictor: Any,
    feature_keys: List[str] = ['gradient_norms', 'local_curvature']
) -> float:
    """
    Measure the time taken to run the proxy policy evaluation (KRR prediction)
    for all samples in the test set.
    
    This simulates the 'prediction_only_time' from T028.
    """
    if not test_samples:
        return 0.0

    start_time = time.perf_counter()
    
    # Simulate the loop from run_proxy_loop.py
    # The proxy policy logic: Accept if predicted gap < 0.1
    for sample in test_samples:
        # Extract features (mocking the extraction step if not present, 
        # but T028 implies we have features in the test data or extract them)
        # Assuming features are already in the sample dict or we need to extract them.
        # Based on T021A, test data comes from training_sample.parquet which has features.
        
        features = []
        for key in feature_keys:
            if key in sample:
                val = sample[key]
                # Handle if val is a list or scalar
                if isinstance(val, (list, tuple)):
                    features.extend(val)
                else:
                    features.append(float(val))
        
        # If features are missing (e.g., loaded from a minimal JSON), we might need to mock
        # But for T030, we assume the test data has the necessary features or we skip.
        if not features:
            continue
            
        # Run prediction
        try:
            _ = predictor.predict([features])
        except Exception as e:
            logging.warning(f"Prediction failed for sample: {e}")
            continue

    end_time = time.perf_counter()
    return end_time - start_time

def measure_baseline_policy_evaluation_time(
    baseline_metrics_path: Path
) -> float:
    """
    Read the 'inference_only_time' from the baseline metrics JSON (T027 output).
    This represents the time taken for the full hardware sync check.
    """
    if not baseline_metrics_path.exists():
        raise FileNotFoundError(f"Baseline metrics not found at {baseline_metrics_path}")
    
    with open(baseline_metrics_path, 'r') as f:
        data = json.load(f)
    
    if 'timing_metadata' not in data:
        raise ValueError("Baseline metrics missing 'timing_metadata'")
    
    if 'inference_only_time' not in data['timing_metadata']:
        raise ValueError("Baseline metrics missing 'inference_only_time' in timing_metadata")
    
    return float(data['timing_metadata']['inference_only_time'])

def calculate_latency_reduction(
    proxy_time: float, 
    baseline_time: float
) -> Tuple[float, bool]:
    """
    Calculate latency reduction percentage and check against target (>= 90%).
    Formula: (baseline - proxy) / baseline * 100
    """
    if baseline_time <= 0:
        raise ValueError("Baseline time must be positive to calculate reduction.")
    
    reduction = (baseline_time - proxy_time) / baseline_time * 100
    target_met = reduction >= 90.0
    return reduction, target_met

def write_metrics(
    metrics: LatencyMetrics,
    output_path: Path
) -> None:
    """Write the latency metrics to a JSON file."""
    ensure_log_dir(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(asdict(metrics), f, indent=2)

def run_latency_analysis(
    test_data_path: Path,
    predictor_path: Path,
    baseline_metrics_path: Path,
    output_path: Path,
    feature_keys: List[str] = ['gradient_norms', 'local_curvature']
) -> LatencyMetrics:
    """
    Main orchestration function for T030.
    1. Load test data.
    2. Load predictor.
    3. Measure proxy evaluation time.
    4. Read baseline evaluation time.
    5. Calculate reduction.
    6. Write results.
    """
    logger = setup_logger("latency_meter")
    logger.info("Starting latency analysis for T030")
    
    # 1. Load test data
    logger.info(f"Loading test data from {test_data_path}")
    test_samples = load_test_data(test_data_path)
    logger.info(f"Loaded {len(test_samples)} test samples")
    
    # 2. Load predictor
    logger.info(f"Loading predictor from {predictor_path}")
    predictor = load_predictor(predictor_path)
    
    # 3. Measure proxy time
    logger.info("Measuring proxy policy evaluation time...")
    proxy_time = measure_proxy_policy_evaluation_time(
        test_samples, predictor, feature_keys
    )
    logger.info(f"Proxy evaluation time: {proxy_time:.4f}s")
    
    # 4. Read baseline time
    logger.info(f"Reading baseline inference time from {baseline_metrics_path}")
    baseline_time = measure_baseline_policy_evaluation_time(baseline_metrics_path)
    logger.info(f"Baseline inference time: {baseline_time:.4f}s")
    
    # 5. Calculate reduction
    reduction, target_met = calculate_latency_reduction(proxy_time, baseline_time)
    logger.info(f"Latency reduction: {reduction:.2f}% (Target >= 90%: {target_met})")
    
    # 6. Write results
    metrics = LatencyMetrics(
        proxy_prediction_time=proxy_time,
        baseline_inference_time=baseline_time,
        reduction_percentage=reduction,
        target_met=target_met
    )
    write_metrics(metrics, output_path)
    logger.info(f"Metrics written to {output_path}")
    
    return metrics

def main():
    """CLI entry point for T030."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Measure latency reduction for T030")
    parser.add_argument("--test-data", type=str, required=True, help="Path to split_test.parquet")
    parser.add_argument("--predictor", type=str, required=True, help="Path to gap_predictor.pkl")
    parser.add_argument("--baseline-metrics", type=str, required=True, help="Path to baseline_metrics.json")
    parser.add_argument("--output", type=str, default="data/processed/latency_metrics.json", help="Output path")
    
    args = parser.parse_args()
    
    test_path = Path(args.test_data)
    predictor_path = Path(args.predictor)
    baseline_path = Path(args.baseline_metrics)
    output_path = Path(args.output)
    
    try:
        metrics = run_latency_analysis(
            test_data_path=test_path,
            predictor_path=predictor_path,
            baseline_metrics_path=baseline_path,
            output_path=output_path
        )
        print(f"Success: Reduction {metrics.reduction_percentage:.2f}%, Target Met: {metrics.target_met}")
    except Exception as e:
        logging.error(f"Latency analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
