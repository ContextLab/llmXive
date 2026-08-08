import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import numpy as np
from transformers import DistilBertTokenizerFast

# Import base model components
from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu

# Configuration loading (using default.yaml if present, otherwise hardcoded defaults)
CONFIG_PATH = Path("config/default.yaml")

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file or return defaults."""
    import yaml
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    return {
        "model_name": "distilbert-base-uncased",
        "device": "cpu",
        "batch_size": 4,
        "seq_len": 128,
        "target_frequency": 40.0,  # Relative frequency (cycles/sequence)
        "output_dir": "data/final"
    }

def load_sample_text() -> List[str]:
    """Load sample text sequences for processing."""
    # Using a small set of sample sentences for the baseline run
    samples = [
        "The cat sat on the mat.",
        "The dog chased the ball in the park.",
        "She read the book quickly.",
        "They walked to the store together."
    ]
    return samples

def tokenize_sequences(texts: List[str], tokenizer: DistilBertTokenizerFast, seq_len: int) -> torch.Tensor:
    """Tokenize text sequences and return input IDs."""
    encoded = tokenizer(
        texts,
        padding='max_length',
        truncation=True,
        max_length=seq_len,
        return_tensors='pt'
    )
    return encoded['input_ids']

def extract_activations(
    model: DistilBERTWrapper,
    input_ids: torch.Tensor,
    layer_indices: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Run forward pass and extract activation time series from specified layers.
    Returns a dictionary mapping layer/head to activation arrays.
    """
    model.model.eval()
    with torch.no_grad():
        outputs = model.model(
            input_ids=input_ids,
            output_hidden_states=True,
            output_attentions=True
        )
    
    # Extract hidden states and attentions
    hidden_states = outputs.hidden_states  # List of tensors: (batch, seq_len, hidden)
    attentions = outputs.attentions  # List of tensors: (batch, num_heads, seq_len, seq_len)
    
    activations = {}
    
    # If no specific layers requested, use all layers
    if layer_indices is None:
        layer_indices = list(range(len(hidden_states)))
    
    for i, layer_idx in enumerate(layer_indices):
        if layer_idx < len(hidden_states):
            # Store hidden state activations for this layer
            activations[f"layer_{layer_idx}"] = hidden_states[layer_idx].numpy()
        
        if layer_idx - 1 < len(attentions):  # Attention corresponds to previous layer
            attn_idx = layer_idx - 1
            if attn_idx >= 0:
                activations[f"layer_{layer_idx}_attentions"] = attentions[attn_idx].numpy()
    
    return activations

def run_baseline_forward_pass(
    model: DistilBERTWrapper,
    input_ids: torch.Tensor,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run a forward pass WITHOUT oscillatory modulation.
    This is the baseline/control run for comparison.
    """
    print(f"Running baseline forward pass (no oscillatory module)...")
    start_time = time.time()
    
    activations = extract_activations(model, input_ids, config.get("layers", None))
    
    elapsed = time.time() - start_time
    print(f"Baseline forward pass completed in {elapsed:.2f}s")
    
    return {
        "activations": activations,
        "elapsed_time": elapsed,
        "run_type": "baseline",
        "config": config
    }

def save_activations(results: Dict[str, Any], output_path: Path):
    """Save activation data to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy arrays to lists for JSON serialization
    def convert_for_json(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_for_json(i) for i in obj]
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        return obj
    
    serializable_results = convert_for_json(results)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"Baseline activations saved to {output_path}")

def main():
    """
    Main entry point for the baseline run (T018b).
    Loads the model without oscillatory module, runs forward pass,
    and records ActivationTimeSeries for control comparison.
    """
    print("=" * 60)
    print("T018b: Baseline Run - No Oscillatory Module")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    print(f"Configuration loaded: {config}")
    
    # Create output directory
    output_dir = Path(config.get("output_dir", "data/final"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load model (CPU-only, no oscillatory module)
    print("Loading DistilBERT model (baseline)...")
    model = load_distilbert_cpu(config.get("model_name", "distilbert-base-uncased"))
    print("Model loaded successfully.")
    
    # Load sample text
    texts = load_sample_text()
    print(f"Loaded {len(texts)} sample texts.")
    
    # Tokenize
    tokenizer = DistilBertTokenizerFast.from_pretrained(config.get("model_name", "distilbert-base-uncased"))
    seq_len = config.get("seq_len", 128)
    input_ids = tokenize_sequences(texts, tokenizer, seq_len)
    print(f"Tokenized sequences: shape {input_ids.shape}")
    
    # Run baseline forward pass
    results = run_baseline_forward_pass(model, input_ids, config)
    
    # Add metadata
    results["metadata"] = {
        "task_id": "T018b",
        "description": "Baseline run without oscillatory attention module",
        "num_samples": len(texts),
        "sequence_length": seq_len,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save results
    output_file = output_dir / "baseline_activations.json"
    save_activations(results, output_file)
    
    print("=" * 60)
    print("Baseline run completed successfully.")
    print(f"Output saved to: {output_file}")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    main()