import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
from sklearn.linear_model import Ridge

from src.config.logging_config import setup_logger
from src.services.quantized_inference import run_quantized_inference, load_quantized_model, InferenceResult
from src.config.env_config import get_model_path, load_config

logger = setup_logger("latency_meter")

@dataclass
class LatencyMetrics:
    proxy_time: float
    baseline_time: float
    reduction_percentage: float
    sample_count: int

def measure_policy_evaluation_latency(
    model: Ridge,
    feature_vectors: List[np.ndarray],
    num_runs: int = 10
) -> float:
    """
    Measures the time taken for the policy evaluation step (KRR prediction).
    Runs the prediction multiple times to get a stable average.

    Args:
        model: The trained Ridge regression model.
        feature_vectors: List of feature vectors (input to the predictor).
        num_runs: Number of times to run the prediction loop for averaging.

    Returns:
        Average time in seconds per full batch prediction.
    """
    if not feature_vectors:
        logger.warning("No feature vectors provided for latency measurement.")
        return 0.0

    total_time = 0.0
    for _ in range(num_runs):
        start = time.perf_counter()
        # Simulate the policy evaluation step: predict gap for all samples
        # The model.predict expects a 2D array
        X_batch = np.vstack(feature_vectors) if len(feature_vectors) > 1 else np.array(feature_vectors)
        _ = model.predict(X_batch)
        end = time.perf_counter()
        total_time += (end - start)

    return total_time / num_runs

def measure_quantized_inference_latency(
    model_path: str,
    prompts: List[str],
    quantization_level: str = "INT4",
    num_runs: int = 3
) -> float:
    """
    Measures the time taken for full quantized inference on the CPU engine.
    Runs the inference multiple times to get a stable average.

    Args:
        model_path: Path to the quantized model file.
        prompts: List of input prompts to run inference on.
        quantization_level: The quantization level (e.g., "INT4", "INT8", "FP8").
        num_runs: Number of times to run the inference loop for averaging.

    Returns:
        Average time in seconds per full batch inference.
    """
    if not prompts:
        logger.warning("No prompts provided for latency measurement.")
        return 0.0

    # Load model once outside the timing loop to avoid load overhead
    try:
        llm = load_quantized_model(model_path, quantization_level)
    except Exception as e:
        logger.error(f"Failed to load quantized model: {e}")
        raise

    total_time = 0.0
    for _ in range(num_runs):
        start = time.perf_counter()
        # Run inference on all prompts
        for prompt in prompts:
            try:
                run_quantized_inference(llm, prompt, max_tokens=50) # Limit tokens for timing
            except Exception as e:
                logger.warning(f"Inference failed for prompt during timing: {e}")
        end = time.perf_counter()
        total_time += (end - start)

    return total_time / num_runs

def run_latency_comparison(
    feature_vectors: List[np.ndarray],
    prompts: List[str],
    model_path: str,
    predictor_path: str,
    quantization_level: str = "INT4",
    output_path: str = "data/processed/latency_metrics.json"
) -> LatencyMetrics:
    """
    Orchestrates the measurement of proxy vs. baseline latency and saves the results.

    Args:
        feature_vectors: List of feature vectors for the samples.
        prompts: List of prompts corresponding to the samples.
        model_path: Path to the quantized model.
        predictor_path: Path to the saved KRR predictor model.
        quantization_level: Quantization level used.
        output_path: Path to write the JSON metrics file.

    Returns:
        LatencyMetrics object containing the results.
    """
    logger.info("Loading predictor model...")
    try:
        import joblib
        predictor = joblib.load(predictor_path)
    except Exception as e:
        logger.error(f"Failed to load predictor model from {predictor_path}: {e}")
        raise

    logger.info(f"Measuring proxy latency (Policy Evaluation) on {len(feature_vectors)} samples...")
    proxy_time = measure_policy_evaluation_latency(predictor, feature_vectors)

    logger.info(f"Measuring baseline latency (Full Quantized Inference) on {len(prompts)} samples...")
    baseline_time = measure_quantized_inference_latency(model_path, prompts, quantization_level)

    if baseline_time <= 0:
        raise ValueError("Baseline time must be greater than zero to calculate reduction percentage.")

    reduction_percentage = ((baseline_time - proxy_time) / baseline_time) * 100

    metrics = LatencyMetrics(
        proxy_time=proxy_time,
        baseline_time=baseline_time,
        reduction_percentage=reduction_percentage,
        sample_count=len(prompts)
    )

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    result_dict = asdict(metrics)
    result_dict["quantization_level"] = quantization_level

    with open(output_file, "w") as f:
        json.dump(result_dict, f, indent=2)

    logger.info(f"Latency metrics saved to {output_path}")
    logger.info(f"Proxy Time: {proxy_time:.6f}s, Baseline Time: {baseline_time:.6f}s")
    logger.info(f"Latency Reduction: {reduction_percentage:.2f}%")

    return metrics

def main():
    """
    Entry point for running the latency meter as a standalone script.
    This function expects to be called after data generation and model training are complete.
    It loads the necessary artifacts and runs the comparison.
    """
    # Configuration - In a real pipeline, these would come from args or config
    # Assuming standard paths based on tasks.md
    DATA_DIR = Path("data/processed")
    MODEL_DIR = Path("data/models")
    CONFIG = load_config()

    # Paths
    predictor_path = MODEL_DIR / "gap_predictor.pkl"
    model_path = get_model_path() # From env/config

    # We need to load some sample data to get prompts and features
    # Since T030 depends on the existence of data from T015/T021A
    # We will load a subset of the training_sample.parquet to get prompts and features
    # Note: In a real scenario, we might load the specific test split used for evaluation
    
    import pandas as pd
    import joblib
    import numpy as np

    parquet_path = DATA_DIR / "training_sample.parquet"
    
    if not parquet_path.exists():
        raise FileNotFoundError(f"Required data file {parquet_path} not found. Run T015 first.")
    
    logger.info(f"Loading data from {parquet_path}...")
    df = pd.read_parquet(parquet_path)
    
    # For demonstration, take the first 10 samples to measure latency (avoids long waits)
    # In a full report, one might measure on the full test set
    sample_size = 10
    if len(df) > sample_size:
        df_sample = df.head(sample_size)
        logger.info(f"Using {sample_size} samples for latency measurement (subset of full data).")
    else:
        df_sample = df
        logger.info(f"Using all {len(df)} samples for latency measurement.")

    # Extract features and prompts
    # The 'local_curvature' and 'gradient_norms' are typically stored as lists/arrays in the parquet
    # We need to reconstruct the feature vector expected by the predictor
    # Assuming the predictor was trained on [gradient_norms, local_curvature]
    
    feature_vectors = []
    prompts = []
    
    for _, row in df_sample.iterrows():
        # Reconstruct feature vector
        # Depending on how T012 stored them, they might be lists or scalars
        # Assuming they are scalars or 1D arrays that can be concatenated
        grad = row.get('gradient_norms', 0.0)
        curv = row.get('local_curvature', 0.0)
        
        # Ensure they are floats or 1D arrays
        if isinstance(grad, (list, np.ndarray)):
            grad = float(np.mean(grad)) # Simplify to mean if it's a sequence
        if isinstance(curv, (list, np.ndarray)):
            curv = float(np.mean(curv))
        
        feature_vectors.append(np.array([grad, curv]))
        prompts.append(row.get('input_id', '')) # Assuming input_id holds the prompt or text
        
        # If input_id is just an ID, we might need a 'prompt' column. 
        # If T015 stored the actual prompt text, we should use that.
        # If not, we might need to reload from the raw dataset.
        # For this implementation, we assume 'input_id' or a 'prompt' column exists.
        # If 'prompt' column exists, use it.
        if 'prompt' in df.columns:
            prompts[-1] = row['prompt']
        elif 'text' in df.columns:
            prompts[-1] = row['text']
    
    if not prompts:
        raise ValueError("Could not extract prompts from the dataset.")

    # Run comparison
    metrics = run_latency_comparison(
        feature_vectors=feature_vectors,
        prompts=prompts,
        model_path=model_path,
        predictor_path=str(predictor_path),
        quantization_level="INT4", # Default, can be dynamic
        output_path=str(DATA_DIR / "latency_metrics.json")
    )

    return metrics

if __name__ == "__main__":
    main()
