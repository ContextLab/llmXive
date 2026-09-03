import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch
import numpy as np
from datasets import load_dataset

from config import load_config, get_config, DatasetConfig, FeatureConfig
from utils.data_loader import load_gsm8k_streaming, load_humaneval_streaming, load_common_crawl_streaming, load_dolly_streaming
from utils.metrics import calculate_latency

# Mock model initialization for the purpose of this implementation if real model is heavy
# In a real run, this would load the specific architecture defined in config
def initialize_model(config):
    """Initialize the model for feature extraction."""
    model_name = config.model.get("name", "meta-llama/Llama-2-7b")
    # Placeholder for actual model loading logic
    # This function ensures we have a model object to extract features from
    logging.info(f"Initializing model: {model_name} for feature extraction")
    # In a real scenario: model = AutoModel.from_pretrained(model_name)
    # For this script to be runnable without 7GB+ weights in a test env,
    # we assume the environment has the model or we mock the extraction logic
    # if the task is strictly about the pipeline flow.
    # However, to satisfy "real code", we attempt to load or raise if missing.
    try:
        from transformers import AutoModel, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name, device_map="auto")
        return model, tokenizer
    except Exception as e:
        logging.error(f"Failed to load model {model_name}: {e}")
        raise e

def extract_features(sample: Dict[str, Any], model: Any, tokenizer: Any, config: FeatureConfig) -> Dict[str, float]:
    """
    Extract static features from a single sample.
    Features:
    1. Prompt Length
    2. Mean Attention Entropy
    3. Hidden State Norms
    """
    prompt = sample.get("question", sample.get("text", ""))
    
    # 1. Prompt Length
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    prompt_length = input_ids.shape[1]
    
    # 2 & 3. Attention Entropy and Hidden State Norms
    # We perform a forward pass to get these internal states.
    # To avoid OOM on large batches, we process one sample at a time.
    try:
        with torch.no_grad():
            outputs = model(input_ids, output_attentions=True, output_hidden_states=True)
            
            # Mean Attention Entropy
            # Shape: (num_layers, batch, num_heads, seq_len, seq_len)
            attentions = outputs.attentions
            # Calculate entropy per layer, per head, then average
            entropy_values = []
            for layer_att in attentions:
                # Softmax is already applied by model usually, but safe to ensure
                # p * log(p) where p is probability.
                # Handle log(0) by masking or using stable log
                p = layer_att
                # Avoid log(0)
                p = torch.clamp(p, min=1e-10)
                entropy = -torch.sum(p * torch.log(p), dim=-1) # Sum over the last dimension
                # Average across heads and batch
                entropy_values.append(entropy.mean().item())
            mean_attention_entropy = np.mean(entropy_values) if entropy_values else 0.0
            
            # Hidden State Norms
            # Shape: (num_layers, batch, seq_len, hidden_dim)
            hidden_states = outputs.hidden_states
            norms = []
            for layer_hs in hidden_states:
                # L2 norm across hidden dimension, then average
                norm = torch.norm(layer_hs, p=2, dim=-1)
                norms.append(norm.mean().item())
            mean_hidden_norm = np.mean(norms) if norms else 0.0

    except RuntimeError as e:
        if "CUDA out of memory" in str(e):
            logging.warning(f"OOM during feature extraction for sample. Skipping.")
            return None
        raise e

    # Handle NaN/Inf
    if np.isnan(mean_attention_entropy) or np.isinf(mean_attention_entropy):
        logging.warning(f"NaN/Inf detected in attention entropy. Imputing with 0.0")
        mean_attention_entropy = 0.0
    if np.isnan(mean_hidden_norm) or np.isinf(mean_hidden_norm):
        logging.warning(f"NaN/Inf detected in hidden norm. Imputing with 0.0")
        mean_hidden_norm = 0.0

    return {
        "prompt_length": float(prompt_length),
        "mean_attention_entropy": float(mean_attention_entropy),
        "mean_hidden_norm": float(mean_hidden_norm)
    }

def run_feature_extraction(config, output_path: str, logger: logging.Logger):
    """
    Main entry point for feature extraction.
    Reads from dataset, extracts features, and writes to JSONL.
    """
    logger.info("Starting feature extraction pipeline...")
    
    # Load dataset (Streaming)
    dataset_name = config.dataset.get("name", "gsm8k")
    streaming = config.dataset.get("streaming", True)
    
    logger.info(f"Loading dataset: {dataset_name} (streaming={streaming})")
    
    if dataset_name == "gsm8k":
        data_iter = load_gsm8k_streaming()
    elif dataset_name == "humaneval":
        data_iter = load_humaneval_streaming()
    elif dataset_name == "common_crawl":
        data_iter = load_common_crawl_streaming()
    elif dataset_name == "dolly":
        data_iter = load_dolly_streaming()
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    # Initialize Model
    try:
        model, tokenizer = initialize_model(config)
    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        raise e

    # Process
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    start_time = time.time()
    
    with open(output_file, 'w') as f:
        for sample in data_iter:
            # Extract features
            features = extract_features(sample, model, tokenizer, config.feature)
            
            if features is not None:
                # Add sample ID
                sample_id = sample.get("id", f"sample_{count}")
                record = {
                    "sample_id": sample_id,
                    "features": features,
                    "timestamp": time.time()
                }
                f.write(json.dumps(record) + "\n")
                count += 1
                
                # Log progress
                if count % 10 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"Processed {count} samples. Latency: {elapsed/count:.4f}s/sample")

    total_time = time.time() - start_time
    logger.info(f"Feature extraction complete. Processed {count} samples in {total_time:.2f}s.")
    logger.info(f"Output written to {output_path}")

def main():
    config = load_config()
    logger = logging.getLogger("features")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)
    
    run_feature_extraction(config, "data/processed/features.jsonl", logger)

if __name__ == "__main__":
    main()