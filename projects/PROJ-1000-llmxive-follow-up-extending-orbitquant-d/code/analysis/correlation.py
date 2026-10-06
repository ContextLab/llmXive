"""
Correlation analysis module for OrbitQuant.

This module computes the correlation between prompt semantic entropy
and DiT activation variance using a streaming/chunked approach to
handle large datasets (e.g., MS-COCO) without exceeding memory limits.
"""
import os
import json
import logging
import csv
import numpy as np
from scipy import stats
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Generator, Any
from config import Config
from utils.data_streaming import DataLoader
from analysis.entropy_proxy import EntropyProxy
from models.dit_wrapper import DiTWrapper, ActivationCapture
from models.flux_wan_loader import ModelLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
CHUNK_SIZE = 50
CONFIG = Config()

def load_entropy_scores(entropy_path: str) -> Dict[str, float]:
    """Load pre-computed entropy scores from a CSV file."""
    scores = {}
    path = Path(entropy_path)
    if not path.exists():
        raise FileNotFoundError(f"Entropy scores file not found: {entropy_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompt_id = row.get('id') or row.get('prompt_id')
            entropy = float(row['entropy'])
            scores[prompt_id] = entropy
    return scores

def load_activation_variances(variance_path: str) -> Dict[str, float]:
    """Load pre-computed activation variances from a CSV file."""
    variances = {}
    path = Path(variance_path)
    if not path.exists():
        raise FileNotFoundError(f"Activation variances file not found: {variance_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompt_id = row.get('id') or row.get('prompt_id')
            variance = float(row['variance'])
            variances[prompt_id] = variance
    return variances

def compute_pearson_correlation(
    entropy_scores: Dict[str, float],
    variances: Dict[str, float]
) -> Tuple[float, float]:
    """Compute Pearson correlation coefficient and p-value."""
    common_ids = set(entropy_scores.keys()) & set(variances.keys())
    if len(common_ids) < 2:
        raise ValueError("Insufficient overlapping data points for correlation.")
    
    entropies = [entropy_scores[i] for i in common_ids]
    vars = [variances[i] for i in common_ids]
    
    correlation, p_value = stats.pearsonr(entropies, vars)
    return float(correlation), float(p_value)

def analyze_correlation(correlation: float, p_value: float) -> Dict[str, Any]:
    """Analyze and summarize correlation results."""
    significance = "significant" if p_value < 0.05 else "not significant"
    strength = "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.4 else "weak"
    
    return {
        "correlation_coefficient": correlation,
        "p_value": p_value,
        "significance": significance,
        "strength": strength,
        "interpretation": f"The correlation is {significance} (p={p_value:.4f}) and {strength} (r={correlation:.4f})."
    }

def stream_prompts_and_compute_entropy(
    prompts_path: str,
    chunk_size: int = CHUNK_SIZE
) -> Generator[Tuple[str, float], None, None]:
    """
    Stream prompts from a CSV file in chunks and compute entropy for each.
    Yields (prompt_id, entropy_score) tuples.
    """
    loader = DataLoader()
    prompts = loader.load_prompts(prompts_path)
    
    entropy_proxy = EntropyProxy()
    logger.info(f"Starting entropy computation for {len(prompts)} prompts in chunks of {chunk_size}.")
    
    for i in range(0, len(prompts), chunk_size):
        chunk = prompts[i:i+chunk_size]
        chunk_ids = [p['id'] for p in chunk]
        chunk_captions = [p['caption'] for p in chunk]
        
        logger.info(f"Chunk processed: {i // chunk_size + 1} (IDs: {chunk_ids[0]}-{chunk_ids[-1]})")
        
        # Compute entropy for the chunk
        entropies = entropy_proxy.compute_batch_entropy(chunk_captions)
        
        for prompt_id, entropy in zip(chunk_ids, entropies):
            yield prompt_id, entropy

def stream_dit_generation_and_capture_variance(
    prompts_path: str,
    chunk_size: int = CHUNK_SIZE
) -> Generator[Tuple[str, float], None, None]:
    """
    Stream prompts, generate images with DiT, and capture activation variance.
    Yields (prompt_id, variance_score) tuples.
    """
    loader = DataLoader()
    prompts = loader.load_prompts(prompts_path)
    
    model_loader = ModelLoader()
    dit_wrapper = model_loader.load_model()
    
    logger.info(f"Starting DiT generation and variance capture for {len(prompts)} prompts in chunks of {chunk_size}.")
    
    for i in range(0, len(prompts), chunk_size):
        chunk = prompts[i:i+chunk_size]
        chunk_ids = [p['id'] for p in chunk]
        chunk_captions = [p['caption'] for p in chunk]
        
        logger.info(f"Chunk processed: {i // chunk_size + 1} (IDs: {chunk_ids[0]}-{chunk_ids[-1]})")
        
        # Capture variance for the chunk
        variances = []
        for caption in chunk_captions:
            with ActivationCapture(dit_wrapper) as capture:
                dit_wrapper.generate(caption)
                variance = np.var(capture.activations)
            variances.append(float(variance))
        
        for prompt_id, variance in zip(chunk_ids, variances):
            yield prompt_id, variance

def aggregate_variances(
    variance_stream: Generator[Tuple[str, float], None, None]
) -> Dict[str, float]:
    """Aggregate variance results from a stream into a dictionary."""
    variances = {}
    for prompt_id, variance in variance_stream:
        variances[prompt_id] = variance
    return variances

def compute_correlation(
    entropy_scores: Dict[str, float],
    variances: Dict[str, float]
) -> Tuple[float, float]:
    """Compute Pearson correlation between entropy and variance."""
    return compute_pearson_correlation(entropy_scores, variances)

def save_results(
    correlation: float,
    p_value: float,
    analysis: Dict[str, Any],
    output_path: str
) -> None:
    """Save correlation results to a JSON file."""
    results = {
        "correlation": correlation,
        "p_value": p_value,
        "analysis": analysis,
        "config": {
            "chunk_size": CHUNK_SIZE,
            "entropy_path": CONFIG.ENTROPY_PATH,
            "variance_path": CONFIG.VARIANCE_PATH,
            "output_path": output_path
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main() -> None:
    """Main entry point for correlation analysis with streaming."""
    logger.info("Starting correlation analysis with streaming.")
    
    # Ensure output directory exists
    output_dir = Path(CONFIG.OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load entropy scores (pre-computed)
    entropy_scores = load_entropy_scores(CONFIG.ENTROPY_PATH)
    logger.info(f"Loaded {len(entropy_scores)} entropy scores.")
    
    # Stream DiT generation and capture variance
    variance_stream = stream_dit_generation_and_capture_variance(CONFIG.PROMPTS_PATH)
    variances = aggregate_variances(variance_stream)
    logger.info(f"Captured {len(variances)} variance scores.")
    
    # Compute correlation
    correlation, p_value = compute_correlation(entropy_scores, variances)
    logger.info(f"Correlation: {correlation:.4f}, p-value: {p_value:.4f}")
    
    # Analyze results
    analysis = analyze_correlation(correlation, p_value)
    logger.info(f"Analysis: {analysis['interpretation']}")
    
    # Save results
    save_results(correlation, p_value, analysis, CONFIG.CORRELATION_OUTPUT_PATH)
    logger.info("Correlation analysis complete.")

if __name__ == "__main__":
    main()