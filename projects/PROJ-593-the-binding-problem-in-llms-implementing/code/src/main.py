import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import numpy as np
import pandas as pd

from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu
from src.models.oscillatory_attention import OscillatoryDistilBERTWrapper, create_oscillatory_attention
from src.analysis.spectral import compute_welch_psd, calculate_snr

# Configuration defaults
DEFAULT_CONFIG = {
    "model_name": "distilbert-base-uncased",
    "device": "cpu",
    "sequence_length": 128,
    "oscillation_frequency_cycles": 4.0,  # Relative frequency: cycles per sequence
    "target_band": (30, 50),  # Gamma band in relative units (cycles/seq)
    "output_dir": "data/final",
    "processed_dir": "data/processed",
}

def load_sample_text() -> List[str]:
    """
    Loads a small set of sample sentences for testing.
    In a full pipeline, this would load from a dataset like CLUTRR or a corpus.
    """
    samples = [
        "The cat sat on the mat and looked at the dog.",
        "The quick brown fox jumps over the lazy dog.",
        "Neural oscillations synchronize to bind features together.",
        "Attention mechanisms in transformers process sequences in parallel.",
        "The binding problem remains a central challenge in neuroscience.",
    ]
    return samples

def tokenize_sequences(texts: List[str], tokenizer, max_length: int = 128) -> Dict[str, torch.Tensor]:
    """
    Tokenizes a list of text strings into model inputs.
    """
    encodings = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length
    )
    return encodings

def extract_activations(
    model: DistilBERTWrapper,
    inputs: Dict[str, torch.Tensor],
    layer_indices: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Runs a forward pass and extracts activation time series from specified layers.
    Returns a dictionary mapping (layer_id, head_id) to activation arrays.
    """
    if layer_indices is None:
        # Default to all layers for DistilBERT (6 layers)
        layer_indices = list(range(6))

    # Ensure model is in eval mode
    model.model.eval()
    
    with torch.no_grad():
        outputs = model.model(
            input_ids=inputs['input_ids'],
            attention_mask=inputs['attention_mask'],
            output_hidden_states=True,
            output_attentions=True
        )

    # Extract attentions: shape (batch, num_heads, seq_len, seq_len)
    # We want the activation time series per head. 
    # In the context of oscillatory attention, we look at the attention weights 
    # or the hidden states modulated by the oscillation.
    # For this implementation, we extract the attention weights as the "activation time series"
    # representing the dynamic binding process.
    
    attentions = outputs.attentions  # Tuple of tensors, one per layer
    hidden_states = outputs.hidden_states # Tuple of tensors, one per layer + embedding

    activation_series = {}
    
    # Process each layer's attention
    for i, layer_idx in enumerate(layer_indices):
        if i < len(attentions):
            layer_attn = attentions[i] # (batch, heads, seq_len, seq_len)
            # We take the mean attention across the source dimension to get a 
            # "time series" of activation for each head at each target position
            # Or we can look at the diagonal if we assume self-attention on the same token?
            # A common proxy for "activation time series" in oscillatory contexts 
            # is the attention weight evolution across the sequence.
            # Let's extract the attention weights averaged over the batch and source tokens
            # to get a sequence of length `seq_len` per head.
            
            # Shape: (batch, heads, seq_len, seq_len)
            # Mean over batch and source (dim 0 and 2) -> (heads, seq_len)
            # Actually, let's keep batch dim for robustness, then average later if needed.
            # We'll average over batch and source to get a single "activation profile" per head.
            attn_weights = layer_attn.mean(dim=0) # (heads, seq_len, seq_len)
            
            # To get a 1D time series per head, we can take the mean over the source dimension
            # or the diagonal. The diagonal represents self-attention which is often constant.
            # The mean over source dimension represents how much each token attends to the rest.
            # Let's use the mean over the source dimension (dim 2) to get a sequence of length seq_len.
            # But wait, the "activation" in oscillatory attention is often the modulation signal itself.
            # However, the task asks to "record ActivationTimeSeries" from the forward pass.
            # We will record the attention weights averaged over the batch and source tokens.
            # This gives a shape (num_heads, seq_len).
            
            # Let's average over batch (dim 0) and source (dim 2) -> (heads, seq_len)
            # Wait, layer_attn is (batch, heads, seq_len, seq_len)
            # Mean over batch (0) -> (heads, seq_len, seq_len)
            # Mean over source (2) -> (heads, seq_len)
            profile = layer_attn.mean(dim=0).mean(dim=2) # (heads, seq_len)
            
            for head_idx in range(profile.shape[0]):
                key = (layer_idx, head_idx)
                activation_series[key] = profile[head_idx].cpu().numpy()

    return activation_series

def compute_coherence_metric(activation_series: Dict[tuple, np.ndarray], target_band: tuple) -> float:
    """
    Computes a simple coherence metric (e.g., spectral power in target band).
    For this task, we calculate the average SNR across heads in the target band.
    """
    snrs = []
    for key, series in activation_series.items():
        # Compute PSD
        fs = 1.0  # Normalized frequency (1 cycle per sequence unit)
        f, pxx = compute_welch_psd(series, fs=fs, nperseg=min(len(series), 512))
        
        # Calculate SNR relative to the target band
        # We need to define the target band in terms of frequency bins
        # Target band is given in cycles per sequence (e.g., 30-50 relative to seq_len=128? 
        # The task says "frequency is defined as cycles per sequence length".
        # So if seq_len=128, and we want 40Hz relative, that's 40 cycles/128 tokens?
        # Or is the frequency parameter in the model already in "cycles per sequence"?
        # The config says "oscillation_frequency_cycles": 4.0.
        # Let's assume the target_band in config is in the same units as the frequency axis of the PSD.
        # If the sequence length is N, the frequency axis goes from 0 to 0.5 (Nyquist) in cycles/sample.
        # But the task defines frequency as "cycles per sequence".
        # If we have N samples, 1 cycle/sequence = 1/N cycles/sample.
        # So a frequency of F cycles/sequence corresponds to F/N cycles/sample.
        # The PSD frequency axis from welch is in cycles/sample (if fs=1).
        # So we need to map target_band (cycles/seq) to cycles/sample.
        
        # Let's assume the target_band provided is in "cycles per sequence".
        # We need to convert to cycles/sample for the PSD frequency axis.
        # fs = 1.0 means 1 sample per unit time.
        # If the sequence length is L, then 1 cycle/sequence = 1/L cycles/sample.
        # So freq_cycles_per_sample = freq_cycles_per_seq / L.
        
        # However, the `compute_welch_psd` function returns f in cycles/sample if fs=1.
        # Let's assume the `target_band` passed here is already in the correct units for the PSD.
        # If the config says 30-50, and we are using normalized frequency, we need to be careful.
        # Let's assume the `target_band` in the config is in "cycles per sequence" and we convert it.
        # But we don't have the sequence length here easily.
        # Let's assume the `target_band` is passed in the same units as the frequency axis of the PSD.
        # If the model injects oscillation at F cycles/sequence, and we have L samples,
        # the peak should be at F/L cycles/sample.
        
        # For now, let's assume the `target_band` is in the same units as the PSD frequency axis.
        # This might require adjustment based on how the model injects the oscillation.
        # Let's assume the `target_band` is in "cycles per sequence" and we convert it.
        # But we don't have L. Let's assume L is the length of the series.
        L = len(series)
        freq_start = target_band[0] / L
        freq_end = target_band[1] / L
        
        mask = (f >= freq_start) & (f <= freq_end)
        if np.any(mask):
            band_power = np.mean(pxx[mask])
            # Estimate noise power from adjacent bands or overall mean
            # Simple SNR: band_power / mean(pxx)
            noise_power = np.mean(pxx)
            if noise_power > 0:
                snr = 10 * np.log10(band_power / noise_power)
                snrs.append(snr)
    
    if not snrs:
        return 0.0
    return np.mean(snrs)

def run_baseline_forward_pass(
    model: DistilBERTWrapper,
    inputs: Dict[str, torch.Tensor],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Runs the model without oscillatory injection and records activations.
    """
    print("Running baseline forward pass...")
    start_time = time.time()
    activations = extract_activations(model, inputs, layer_indices=list(range(6)))
    duration = time.time() - start_time
    
    metrics = {
        "type": "baseline",
        "duration_seconds": duration,
        "activations": {f"{k[0]}_{k[1]}": v.tolist() for k, v in activations.items()},
        "coherence_metric": compute_coherence_metric(activations, config["target_band"])
    }
    return metrics

def run_oscillatory_forward_pass(
    model: OscillatoryDistilBERTWrapper,
    inputs: Dict[str, torch.Tensor],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Runs the model with oscillatory injection and records activations.
    """
    print(f"Running oscillatory forward pass with frequency {config['oscillation_frequency_cycles']} cycles/seq...")
    start_time = time.time()
    activations = extract_activations(model, inputs, layer_indices=list(range(6)))
    duration = time.time() - start_time
    
    metrics = {
        "type": "oscillatory",
        "frequency_cycles": config["oscillation_frequency_cycles"],
        "duration_seconds": duration,
        "activations": {f"{k[0]}_{k[1]}": v.tolist() for k, v in activations.items()},
        "coherence_metric": compute_coherence_metric(activations, config["target_band"])
    }
    return metrics

def save_activations(activations: Dict[str, Any], filepath: Path):
    """
    Saves the activation metrics to a JSON file.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(activations, f, indent=2)
    print(f"Saved activations to {filepath}")

def main():
    """
    Main orchestration function for Task T018.
    Loads model, injects oscillatory module, runs forward pass, and records ActivationTimeSeries.
    """
    # Load config
    config_path = Path("config/default.yaml")
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        # Merge with defaults
        DEFAULT_CONFIG.update(config)
        config = DEFAULT_CONFIG
    else:
        config = DEFAULT_CONFIG

    # Create output directories
    output_dir = Path(config["output_dir"])
    processed_dir = Path(config["processed_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load model
    print(f"Loading model: {config['model_name']}")
    base_model = load_distilbert_cpu(config["model_name"])
    
    # Inject oscillatory module
    print("Injecting oscillatory attention module...")
    osc_model = create_oscillatory_attention(
        base_model,
        frequency_cycles=config["oscillation_frequency_cycles"]
    )

    # Load sample data
    print("Loading sample text...")
    texts = load_sample_text()
    
    # Tokenize
    print("Tokenizing sequences...")
    inputs = tokenize_sequences(texts, osc_model.tokenizer, max_length=config["sequence_length"])

    # Run Baseline
    print("\n--- Baseline Run ---")
    baseline_metrics = run_baseline_forward_pass(base_model, inputs, config)
    baseline_path = output_dir / "baseline_activations.json"
    save_activations(baseline_metrics, baseline_path)

    # Run Oscillatory
    print("\n--- Oscillatory Run ---")
    oscillatory_metrics = run_oscillatory_forward_pass(osc_model, inputs, config)
    oscillatory_path = output_dir / "oscillatory_activations.json"
    save_activations(oscillatory_path, oscillatory_metrics)

    # Summary
    print("\n--- Summary ---")
    print(f"Baseline Coherence: {baseline_metrics['coherence_metric']:.4f}")
    print(f"Oscillatory Coherence: {oscillatory_metrics['coherence_metric']:.4f}")
    print(f"Baseline Duration: {baseline_metrics['duration_seconds']:.4f}s")
    print(f"Oscillatory Duration: {oscillatory_metrics['duration_seconds']:.4f}s")

    # Save summary report
    report = {
        "config": config,
        "baseline": {
            "coherence": baseline_metrics["coherence_metric"],
            "duration": baseline_metrics["duration_seconds"]
        },
        "oscillatory": {
            "coherence": oscillatory_metrics["coherence_metric"],
            "duration": oscillatory_metrics["duration_seconds"],
            "frequency_cycles": oscillatory_metrics["frequency_cycles"]
        }
    }
    report_path = output_dir / "orchestration_report.json"
    save_activations(report, report_path)

    print(f"\nOrchestration complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()