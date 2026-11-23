import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import torch
from transformers import DistilBertTokenizerFast

# Import from existing API surface
from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu
from src.models.oscillatory_attention import OscillatoryDistilBERTWrapper
from src.analysis.spectral import compute_welch_psd, calculate_snr


def load_sample_text() -> List[str]:
    """Load a sample sequence of text for the control run.
    
    Returns a list containing a single sample sentence.
    In a full implementation, this would load from a dataset.
    """
    return [
        "The cat sat on the mat while the dog ran across the lawn."
    ]


def tokenize_sequences(tokenizer: DistilBertTokenizerFast, texts: List[str]) -> Dict[str, torch.Tensor]:
    """Tokenize input texts for the model.
    
    Args:
        tokenizer: The HuggingFace tokenizer instance.
        texts: List of input text strings.
        
    Returns:
        Tokenized inputs ready for model forward pass.
    """
    return tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128
    )


def extract_activations(model: torch.nn.Module, inputs: Dict[str, torch.Tensor]) -> Dict[str, np.ndarray]:
    """Extract activation time series from model layers during forward pass.
    
    Args:
        model: The transformer model (baseline or oscillatory).
        inputs: Tokenized inputs.
        
    Returns:
        Dictionary mapping layer/head IDs to activation time series.
    """
    activations = {}
    
    # Register hooks to capture attention outputs
    def get_activation_hook(layer_name):
        def hook(module, input, output):
            # output is typically (hidden_states, attention_scores)
            if isinstance(output, tuple) and len(output) > 1:
                attn_scores = output[1]
                # Store attention scores as activation time series
                activations[layer_name] = attn_scores.detach().cpu().numpy()
        return hook
    
    hooks = []
    if hasattr(model, 'distilbert'):
        for i, layer in enumerate(model.distilbert.transformer.layer):
            hook_fn = get_activation_hook(f"layer_{i}")
            hooks.append(layer.register_forward_hook(hook_fn))
    
    # Forward pass
    with torch.no_grad():
        _ = model(**inputs)
    
    # Remove hooks
    for hook in hooks:
        hook.remove()
        
    return activations


def compute_coherence_metric(activations: Dict[str, np.ndarray], 
                             target_band: Tuple[float, float] = (38.0, 42.0),
                             sample_rate: float = 100.0) -> float:
    """Compute a coherence metric from activation time series.
    
    This metric quantifies the degree of synchronized oscillatory activity
    in the target frequency band across attention heads.
    
    Args:
        activations: Dictionary of activation time series.
        target_band: Tuple of (low_freq, high_freq) in Hz.
        sample_rate: Sampling rate in Hz.
        
    Returns:
        Coherence metric value (higher indicates stronger synchronization).
    """
    if not activations:
        return 0.0
        
    # Compute PSD for each activation
    psd_values = []
    for key, act in activations.items():
        # Average across batch and heads to get a representative signal
        if act.ndim >= 3:
            signal = act.mean(axis=0).mean(axis=0)  # [batch, heads, seq_len] -> [seq_len]
        elif act.ndim == 2:
            signal = act.mean(axis=0)
        else:
            signal = act
            
        # Compute Welch PSD
        freqs, psd = compute_welch_psd(signal, fs=sample_rate, nperseg=min(256, len(signal)))
        
        # Integrate power in target band
        band_mask = (freqs >= target_band[0]) & (freqs <= target_band[1])
        if band_mask.any():
            band_power = psd[band_mask].sum()
            psd_values.append(band_power)
    
    if not psd_values:
        return 0.0
        
    # Coherence metric: normalized sum of band powers
    # Higher values indicate stronger synchronized activity in target band
    total_power = sum(psd_values)
    mean_power = total_power / len(psd_values)
    
    # Normalize by total power across all frequencies for each signal
    # to get a relative measure
    coherence = np.mean(psd_values) / (np.mean(psd_values) + 1e-8)
    
    return float(coherence)


def run_baseline_forward_pass(model: DistilBERTWrapper, 
                              inputs: Dict[str, torch.Tensor]) -> Tuple[Dict[str, np.ndarray], float]:
    """Run forward pass with baseline model (no oscillations).
    
    Args:
        model: The baseline DistilBERT wrapper.
        inputs: Tokenized inputs.
        
    Returns:
        Tuple of (activations, elapsed_time).
    """
    start_time = time.perf_counter()
    activations = extract_activations(model, inputs)
    elapsed = time.perf_counter() - start_time
    
    return activations, elapsed


def run_oscillatory_forward_pass(model: OscillatoryDistilBERTWrapper, 
                                 inputs: Dict[str, torch.Tensor],
                                 frequency: float = 40.0) -> Tuple[Dict[str, np.ndarray], float]:
    """Run forward pass with oscillatory attention module.
    
    Args:
        model: The oscillatory DistilBERT wrapper.
        inputs: Tokenized inputs.
        frequency: Target oscillation frequency in Hz (cycles per sequence).
        
    Returns:
        Tuple of (activations, elapsed_time).
    """
    start_time = time.perf_counter()
    activations = extract_activations(model, inputs)
    elapsed = time.perf_counter() - start_time
    
    return activations, elapsed


def save_activations(activations: Dict[str, np.ndarray], output_path: Path):
    """Save activation data to a JSON file.
    
    Args:
        activations: Dictionary of activation time series.
        output_path: Path to save the JSON file.
    """
    # Convert numpy arrays to lists for JSON serialization
    serializable = {
        key: value.tolist() if isinstance(value, np.ndarray) else value
        for key, value in activations.items()
    }
    
    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2)


def main():
    """Main entry point for the control run comparison.
    
    Executes the following steps:
    1. Load sample text
    2. Tokenize inputs
    3. Run baseline forward pass
    4. Run oscillatory forward pass
    5. Compute coherence metrics for both
    6. Calculate difference
    7. Save results to data/final/control_run_comparison.json
    """
    # Paths
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "final" / "control_run_comparison.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Loading sample text...")
    texts = load_sample_text()
    
    print("Initializing tokenizer and models...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    
    # Load baseline model
    print("Loading baseline model...")
    baseline_model = load_distilbert_cpu()
    
    # Load oscillatory model
    print("Loading oscillatory model...")
    oscillatory_model = OscillatoryDistilBERTWrapper.from_pretrained("distilbert-base-uncased")
    
    # Tokenize
    print("Tokenizing inputs...")
    inputs = tokenize_sequences(tokenizer, texts)
    
    # Run baseline
    print("Running baseline forward pass...")
    baseline_activations, baseline_time = run_baseline_forward_pass(baseline_model, inputs)
    baseline_coherence = compute_coherence_metric(baseline_activations)
    print(f"  Baseline coherence: {baseline_coherence:.6f}")
    
    # Run oscillatory
    print("Running oscillatory forward pass...")
    oscillatory_activations, oscillatory_time = run_oscillatory_forward_pass(
        oscillatory_model, inputs, frequency=40.0
    )
    oscillatory_coherence = compute_coherence_metric(oscillatory_activations)
    print(f"  Oscillatory coherence: {oscillatory_coherence:.6f}")
    
    # Compute difference
    coherence_difference = oscillatory_coherence - baseline_coherence
    print(f"  Coherence difference: {coherence_difference:.6f}")
    
    # Save results
    results = {
        "oscillatory_coherence": float(oscillatory_coherence),
        "baseline_coherence": float(baseline_coherence),
        "coherence_difference": float(coherence_difference),
        "baseline_time_seconds": float(baseline_time),
        "oscillatory_time_seconds": float(oscillatory_time),
        "sample_text": texts[0],
        "target_frequency_hz": 40.0
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print("Control run comparison complete.")
    
    return results


if __name__ == "__main__":
    main()
