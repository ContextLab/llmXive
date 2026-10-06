"""
Orchestration script for T017: Correlation Analysis.
Refactored for T044: Implements streaming for MS-COCO dataset to avoid memory bottlenecks.
Processes data in chunks, accumulating variance statistics online.
"""
import os
import sys
import json
import logging
import csv
import time
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional

import torch
import numpy as np
from datasets import load_dataset
from scipy import stats

# Project imports
from config import Config
from analysis.entropy_proxy import EntropyProxy
from models.flux_wan_loader import ModelLoader
from models.dit_wrapper import create_dit_wrapper, ActivationCapture
from utils.gpu_offload import check_gpu_availability, GPUOffloadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

CONFIG = Config()

def load_prompts_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Loads diverse prompts from data/processed/diverse_prompts.csv in a streaming manner.
    Yields one prompt dict at a time to avoid loading the whole CSV into memory.
    """
    prompt_path = CONFIG.data_processed_path / "diverse_prompts.csv"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompts file not found at {prompt_path}. Run T006d first.")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {
                "id": row.get('id', ''),
                "caption": row.get('caption', ''),
                "source": row.get('source', 'unknown')
            }

def compute_entropy_scores(prompts_stream: Generator[Dict[str, Any], None, None], 
                           chunk_size: int = 50) -> Dict[str, float]:
    """
    Computes semantic entropy for a stream of prompts.
    Processes in chunks to manage LLM proxy overhead, but yields results incrementally.
    """
    logger.info("Starting entropy calculation for streamed prompts...")
    entropy_scores = {}
    
    # Initialize proxy
    proxy = EntropyProxy()
    
    current_chunk = []
    batch_ids = []
    
    for prompt in prompts_stream:
        current_chunk.append(prompt['caption'])
        batch_ids.append(prompt['id'])
        
        if len(current_chunk) >= chunk_size:
            logger.info(f"Processing entropy chunk of {len(current_chunk)} prompts...")
            try:
                batch_scores = proxy.compute_batch_entropy(current_chunk)
                for pid, score in zip(batch_ids, batch_scores):
                    entropy_scores[pid] = score
            except Exception as e:
                logger.error(f"Entropy calculation failed for chunk: {e}")
                # Fallback to median for failed batch if proxy allows, else raise
                raise e
            
            current_chunk = []
            batch_ids = []
    
    # Process remaining
    if current_chunk:
        logger.info(f"Processing final entropy chunk of {len(current_chunk)} prompts...")
        try:
            batch_scores = proxy.compute_batch_entropy(current_chunk)
            for pid, score in zip(batch_ids, batch_scores):
                entropy_scores[pid] = score
        except Exception as e:
            logger.error(f"Entropy calculation failed for final chunk: {e}")
            raise e

    return entropy_scores

def run_dit_generation_and_capture_variance_streaming(
    prompts_stream: Generator[Dict[str, Any], None, None],
    entropy_scores: Dict[str, float],
    chunk_size: int = 10
) -> Generator[Dict[str, Any], None, None]:
    """
    Generates images and captures activation variance in a streaming fashion.
    Yields results immediately after processing a chunk to free memory.
    """
    logger.info("Starting DiT generation and variance capture (streaming mode)...")
    
    # Setup Model
    if not check_gpu_availability():
        logger.warning("GPU not available. Attempting offload or CPU fallback.")
        # In a real pipeline, this might trigger offload logic here
        device = "cpu"
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Using device: {device}")
    
    loader = ModelLoader()
    model = loader.load_model(device=device)
    wrapper = create_dit_wrapper(model)
    
    # Activation capture setup
    captures = ActivationCapture(wrapper)
    
    current_prompts = []
    current_ids = []
    
    for prompt_data in prompts_stream:
        pid = prompt_data['id']
        caption = prompt_data['caption']
        
        # Check if we have entropy for this prompt (should exist)
        entropy = entropy_scores.get(pid)
        if entropy is None:
            logger.warning(f"No entropy score found for {pid}, skipping.")
            continue
        
        current_prompts.append(caption)
        current_ids.append(pid)
        
        if len(current_prompts) >= chunk_size:
            logger.info(f"Processing generation chunk of {len(current_prompts)} prompts...")
            try:
                with torch.no_grad():
                    # Run generation and capture activations
                    # Note: This assumes the wrapper handles the loop internally
                    # and the ActivationCapture context manager collects the variances.
                    _ = wrapper.generate_batch(current_prompts)
                    
                    # Extract variances from the capture buffer
                    variance_data = captures.get_variances()
                    
                    for i, pid in enumerate(current_ids):
                        # Aggregate variances per layer or global
                        # Here we compute a global variance metric per prompt for correlation
                        if i < len(variance_data):
                            # variance_data structure depends on implementation, assuming list of tensors
                            # We compute mean variance across layers/heads for a single scalar
                            if isinstance(variance_data[i], torch.Tensor):
                                var_val = variance_data[i].mean().item()
                            else:
                                var_val = np.mean(variance_data[i])
                            
                            yield {
                                "id": pid,
                                "entropy": entropy,
                                "activation_variance": var_val
                            }
            except Exception as e:
                logger.error(f"Generation/Variance capture failed for chunk: {e}")
                raise e
            
            # Clear memory
            captures.reset()
            current_prompts = []
            current_ids = []
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    # Process remaining
    if current_prompts:
        logger.info(f"Processing final generation chunk of {len(current_prompts)} prompts...")
        try:
            with torch.no_grad():
                _ = wrapper.generate_batch(current_prompts)
                variance_data = captures.get_variances()
                
                for i, pid in enumerate(current_ids):
                    if i < len(variance_data):
                        if isinstance(variance_data[i], torch.Tensor):
                            var_val = variance_data[i].mean().item()
                        else:
                            var_val = np.mean(variance_data[i])
                        
                        yield {
                            "id": pid,
                            "entropy": entropy_scores[pid],
                            "activation_variance": var_val
                        }
        except Exception as e:
            logger.error(f"Generation/Variance capture failed for final chunk: {e}")
            raise e

def aggregate_variances(results_stream: Generator[Dict[str, Any], None, None]) -> List[Dict[str, Any]]:
    """
    Aggregates results from the streaming generator.
    Returns a list of dicts ready for correlation analysis.
    """
    logger.info("Aggregating variance results...")
    aggregated = []
    for item in results_stream:
        aggregated.append(item)
    logger.info(f"Aggregated {len(aggregated)} data points.")
    return aggregated

def compute_correlation(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes Pearson correlation between entropy and activation variance.
    """
    logger.info("Computing Pearson correlation...")
    if len(data) < 2:
        raise ValueError("Insufficient data points for correlation.")
    
    entropies = [d['entropy'] for d in data]
    variances = [d['activation_variance'] for d in data]
    
    # Remove NaNs if any
    clean_data = [(e, v) for e, v in zip(entropies, variances) if not (np.isnan(e) or np.isnan(v))]
    if len(clean_data) < 2:
        raise ValueError("Cleaned data has insufficient points.")
    
    entropies, variances = zip(*clean_data)
    
    correlation, p_value = stats.pearsonr(entropies, variances)
    
    return {
        "correlation_coefficient": float(correlation),
        "p_value": float(p_value),
        "sample_size": len(clean_data),
        "method": "pearson"
    }

def save_results(correlation_results: Dict[str, Any], aggregated_data: List[Dict[str, Any]]):
    """
    Saves correlation results and raw data to JSON.
    """
    output_path = CONFIG.data_processed_path / "correlation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "correlation": correlation_results,
        "raw_data": aggregated_data,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for the correlation pipeline with streaming support.
    """
    logger.info("Starting T017 Correlation Analysis (Streaming Mode)...")
    
    try:
        # 1. Load Prompts (Streaming)
        prompts_stream = load_prompts_streaming()
        
        # 2. Compute Entropy (Chunked processing of stream)
        entropy_scores = compute_entropy_scores(prompts_stream)
        
        # 3. Reset stream for generation (re-generate or cache? 
        #    Ideally we cache the prompt list in memory if it fits, 
        #    but for true streaming we might need a second pass or a cache file.
        #    Given memory constraints, we re-open the CSV for the second pass.
        prompts_stream_2 = load_prompts_streaming()
        
        # 4. Generate & Capture Variance (Streaming)
        variance_stream = run_dit_generation_and_capture_variance_streaming(
            prompts_stream_2, 
            entropy_scores
        )
        
        # 5. Aggregate
        aggregated_data = aggregate_variances(variance_stream)
        
        # 6. Compute Correlation
        correlation_results = compute_correlation(aggregated_data)
        
        # 7. Save
        save_results(correlation_results, aggregated_data)
        
        logger.info("T017 Correlation Analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"T017 Correlation Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
