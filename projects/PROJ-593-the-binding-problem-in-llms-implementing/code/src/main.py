import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import numpy as np
from transformers import DistilBertTokenizerFast

from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu
from src.models.oscillatory_attention import OscillatoryDistilBERTWrapper, create_oscillatory_attention
from src.analysis.plv import compute_plv
from src.analysis.spectral import compute_welch_psd, normalize_psd_to_unit_area

# Ensure paths are relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FINAL_DIR = DATA_DIR / "final"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
FINAL_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_sample_text() -> List[str]:
    """Load a sample text sequence for the control run."""
    # Using a fixed sentence that requires feature integration (subject-verb-object coherence)
    return [
        "The cat chased the mouse across the garden.",
        "The scientist analyzed the data with a new method.",
        "The musician played the violin in the orchestra."
    ]

def tokenize_sequences(tokenizer, sentences: List[str], max_length: int = 512) -> Dict[str, torch.Tensor]:
    """Tokenize input sentences."""
    return tokenizer(
        sentences,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length
    )

def extract_activations(model, inputs: Dict[str, torch.Tensor], layer_indices: List[int] = None) -> Dict[str, np.ndarray]:
    """
    Run forward pass and extract hidden states from specified layers.
    Returns a dictionary mapping layer_id to activation array (batch, seq_len, hidden_dim).
    """
    if layer_indices is None:
        # Default: extract from all transformer layers (DistilBERT has 6)
        layer_indices = list(range(6))

    activations = {}
    
    # Register hooks to capture activations
    handles = []
    def get_activation(name):
        def hook(model, input, output):
            # output is usually a tuple (hidden_states, attentions) or just hidden_states depending on config
            # For DistilBERT, output.last_hidden_state is (batch, seq, hidden)
            if isinstance(output, tuple):
                activations[name] = output[0].detach().cpu().numpy()
            else:
                activations[name] = output.detach().cpu().numpy()
        return hook

    for i, layer in enumerate(model.distilbert.transformer.layer):
        if i in layer_indices:
            handle = layer.register_forward_hook(get_activation(f"layer_{i}"))
            handles.append(handle)

    with torch.no_grad():
        outputs = model(**inputs)

    # Remove hooks
    for h in handles:
        h.remove()

    return activations

def compute_coherence_metric(activations: Dict[str, np.ndarray]) -> float:
    """
    Compute a simplified coherence metric for the control run comparison.
    We calculate the average Phase Locking Value (PLV) across all layer pairs
    at the dominant frequency to quantify 'integration'.
    
    Note: This is a proxy metric for the 'binding' effect.
    """
    layer_ids = sorted(activations.keys())
    if len(layer_ids) < 2:
        return 0.0

    plv_values = []
    
    # Flatten activations to time series (average over batch and hidden dim to get a representative signal)
    time_series = {}
    for lid in layer_ids:
        # Shape: (batch, seq_len, hidden) -> (seq_len,) by averaging
        arr = activations[lid]
        mean_arr = np.mean(arr, axis=(0, 2)) # Average over batch and hidden
        time_series[lid] = mean_arr

    # Compute PLV between adjacent layers as a proxy for integration
    for i in range(len(layer_ids) - 1):
        l1 = layer_ids[i]
        l2 = layer_ids[i+1]
        
        ts1 = time_series[l1]
        ts2 = time_series[l2]
        
        # Ensure same length
        min_len = min(len(ts1), len(ts2))
        ts1 = ts1[:min_len]
        ts2 = ts2[:min_len]
        
        # Compute PLV (using the existing implementation)
        try:
            plv = compute_plv(ts1, ts2, sampling_rate=100) # Arbitrary sampling rate for relative freq
            if not np.isnan(plv):
                plv_values.append(plv)
        except Exception:
            continue

    return float(np.mean(plv_values)) if plv_values else 0.0

def run_baseline_forward_pass(model: DistilBERTWrapper, tokenizer, sentences: List[str]) -> float:
    """Run model without oscillation and return coherence metric."""
    inputs = tokenize_sequences(tokenizer, sentences)
    activations = extract_activations(model, inputs)
    return compute_coherence_metric(activations)

def run_oscillatory_forward_pass(model: OscillatoryDistilBERTWrapper, tokenizer, sentences: List[str], freq_cycles: float = 4.0) -> float:
    """Run model with oscillation and return coherence metric."""
    # Ensure oscillation is active
    model.activate_oscillation(freq_cycles=freq_cycles)
    
    inputs = tokenize_sequences(tokenizer, sentences)
    activations = extract_activations(model, inputs)
    return compute_coherence_metric(activations)

def main():
    """
    Execute the Control Run (T021).
    Compares oscillatory vs baseline coherence on the same sequence.
    """
    print("Starting Control Run (T021) - Feynman/Krakauer Address")
    
    # Load model
    print("Loading DistilBERT model...")
    model = load_distilbert_cpu()
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    
    # Prepare baseline model (no oscillation)
    baseline_model = DistilBERTWrapper(model)
    
    # Prepare oscillatory model
    # We need to inject the oscillatory module into a copy or the same model instance
    # For safety, we create a new wrapper that wraps the same base model but adds the hook
    oscillatory_model = OscillatoryDistilBERTWrapper(model)
    
    sentences = load_sample_text()
    print(f"Running on {len(sentences)} sentences.")
    
    # 1. Baseline Run (Oscillation Disabled)
    print("Running Baseline (Oscillation Disabled)...")
    baseline_coherence = run_baseline_forward_pass(baseline_model, tokenizer, sentences)
    print(f"Baseline Coherence: {baseline_coherence:.4f}")
    
    # 2. Oscillatory Run (Oscillation Enabled)
    print("Running Oscillatory Run (Oscillation Enabled)...")
    # Use a relative frequency of 4 cycles per sequence (approx gamma range in token space)
    oscillatory_coherence = run_oscillatory_forward_pass(oscillatory_model, tokenizer, sentences, freq_cycles=4.0)
    print(f"Oscillatory Coherence: {oscillatory_coherence:.4f}")
    
    # 3. Compute Difference
    difference = oscillatory_coherence - baseline_coherence
    print(f"Coherence Difference: {difference:.4f}")
    
    # 4. Save Results
    result = {
        "oscillatory_coherence": float(oscillatory_coherence),
        "baseline_coherence": float(baseline_coherence),
        "coherence_difference": float(difference)
    }
    
    output_path = FINAL_DIR / "control_run_comparison.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to {output_path}")
    return result

if __name__ == "__main__":
    main()
