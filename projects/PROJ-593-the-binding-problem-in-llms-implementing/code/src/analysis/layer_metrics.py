import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from src.analysis.sdc import spectral_density_correlation
from src.analysis.spectral import compute_welch_psd, normalize_psd_to_unit_area
from src.analysis.control_run import load_sample_text, tokenize_sequences, extract_activations
from src.models.base_model import load_distilbert_cpu, DistilBERTWrapper
from src.models.oscillatory_attention import OscillatoryDistilBERTWrapper, create_oscillatory_attention


def load_activation_time_series(filepath: str) -> Dict[str, np.ndarray]:
    """
    Load activation time series from a saved JSON or NPY file.
    Expected structure: Dict[layer_id] -> Dict[head_id] -> np.ndarray (time series)
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Activation time series file not found: {filepath}")
    
    if path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
            # Convert lists back to numpy arrays
            for layer in data:
                for head in data[layer]:
                    data[layer][head] = np.array(data[layer][head])
            return data
    elif path.suffix == '.npy':
        return np.load(path, allow_pickle=True).item()
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def load_control_run_comparison(filepath: str) -> Dict[str, float]:
    """
    Load control run comparison data.
    Expected structure: {"oscillatory_coherence": float, "baseline_coherence": float, "coherence_difference": float}
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Control run comparison file not found: {filepath}")
    
    with open(path, 'r') as f:
        return json.load(f)


def load_meg_psd(filepath: str) -> np.ndarray:
    """
    Load pre-processed MEG PSD data.
    Returns: np.ndarray of shape (n_channels, n_freqs) or (n_freqs,) if single channel
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"MEG PSD file not found: {filepath}")
    
    data = np.load(path, allow_pickle=True)
    if isinstance(data, np.ndarray) and data.ndim == 1:
        # Single channel, expand to (1, n_freqs) for consistency
        return data.reshape(1, -1)
    return data


def compute_frequency_stability(activations: np.ndarray, sample_rate: float = 100.0) -> float:
    """
    Compute frequency stability metric for a given activation time series.
    
    This measures how consistent the dominant frequency is across the sequence.
    We use the coefficient of variation of the spectral peak across sliding windows.
    
    Args:
        activations: np.ndarray of shape (n_timepoints,)
        sample_rate: Sample rate in Hz (default 100 for simulation)
    
    Returns:
        float: Frequency stability score (lower is more stable)
    """
    if len(activations) < 10:
        return float('nan')
    
    # Divide into windows
    window_size = len(activations) // 4
    if window_size < 10:
        window_size = 10
    
    n_windows = len(activations) // window_size
    dominant_freqs = []
    
    for i in range(n_windows):
        start_idx = i * window_size
        end_idx = start_idx + window_size
        window_data = activations[start_idx:end_idx]
        
        # Compute PSD
        freqs, psd = compute_welch_psd(window_data, fs=sample_rate, nperseg=min(256, len(window_data)))
        
        # Find dominant frequency (excluding 0 Hz)
        if len(freqs) > 1:
            psd_nonzero = psd[1:]
            freqs_nonzero = freqs[1:]
            if len(psd_nonzero) > 0:
                dominant_idx = np.argmax(psd_nonzero)
                dominant_freqs.append(freqs_nonzero[dominant_idx])
    
    if len(dominant_freqs) < 2:
        return float('nan')
    
    # Coefficient of variation as stability metric
    mean_freq = np.mean(dominant_freqs)
    std_freq = np.std(dominant_freqs)
    
    if mean_freq == 0:
        return float('nan')
    
    return std_freq / mean_freq


def compute_layer_metrics(
    activation_data: Dict[str, Dict[str, np.ndarray]],
    meg_psd: np.ndarray,
    sample_rate: float = 100.0
) -> pd.DataFrame:
    """
    Compute comprehensive metrics for each layer and head.
    
    Args:
        activation_data: Dict[layer_id][head_id] -> np.ndarray (time series)
        meg_psd: Pre-processed MEG PSD data for SDC calculation
        sample_rate: Sample rate for frequency analysis
    
    Returns:
        pd.DataFrame with columns: [layer_id, head_id, frequency_stability, sdc_metric]
    """
    results = []
    
    # Ensure meg_psd is 2D
    if meg_psd.ndim == 1:
        meg_psd = meg_psd.reshape(1, -1)
    
    # Compute frequency and PSD for MEG (for SDC)
    meg_time_series = np.random.RandomState(42).randn(meg_psd.shape[1])  # Dummy for freq calculation
    meg_freqs, _ = compute_welch_psd(meg_time_series, fs=sample_rate, nperseg=min(256, len(meg_time_series)))
    
    for layer_id, heads in activation_data.items():
        for head_id, activations in heads.items():
            # Compute frequency stability
            freq_stability = compute_frequency_stability(activations, sample_rate)
            
            # Compute SDC
            # First, compute PSD for the activation
            act_freqs, act_psd = compute_welch_psd(activations, fs=sample_rate, nperseg=min(256, len(activations)))
            
            # Normalize both PSDs to unit area
            act_psd_norm = normalize_psd_to_unit_area(act_psd, act_freqs)
            meg_psd_norm = normalize_psd_to_unit_area(meg_psd[0], meg_freqs)  # Use first channel
            
            # Compute SDC
            sdc = spectral_density_correlation(act_psd_norm, meg_psd_norm, act_freqs, meg_freqs)
            
            results.append({
                'layer_id': int(layer_id),
                'head_id': int(head_id),
                'frequency_stability': freq_stability,
                'sdc_metric': sdc
            })
    
    return pd.DataFrame(results)


def save_layer_metrics(df: pd.DataFrame, filepath: str) -> None:
    """
    Save layer metrics to a CSV file.
    
    Args:
        df: DataFrame with layer metrics
        filepath: Output file path
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main():
    """
    Main function to compute and save layer metrics.
    
    This function:
    1. Loads activation time series from control run
    2. Loads MEG PSD data
    3. Computes frequency stability and SDC for each layer/head
    4. Saves results to data/processed/layer_metrics.csv
    """
    # Define paths
    project_root = Path(__file__).parent.parent.parent.parent
    activation_file = project_root / "data" / "final" / "control_run_comparison.json"
    meg_psd_file = project_root / "data" / "processed" / "meg_psd_normalized.npy"
    output_file = project_root / "data" / "processed" / "layer_metrics.csv"
    
    # Check if required files exist
    if not activation_file.exists():
        raise FileNotFoundError(f"Control run comparison file not found: {activation_file}")
    
    if not meg_psd_file.exists():
        raise FileNotFoundError(f"MEG PSD file not found: {meg_psd_file}")
    
    # Load data
    print("Loading activation time series...")
    # Note: We need to load the actual activation time series, not just the comparison
    # For this, we assume the activations were saved during the control run
    # If not available, we'll run the control run again to get activations
    
    # Try to load activations from a standard location
    activations_file = project_root / "data" / "final" / "activations_oscillatory.npy"
    
    if not activations_file.exists():
        print("Activations not found, running control run to generate them...")
        # Run control run to generate activations
        from src.analysis.control_run import main as control_run_main
        control_run_main()
    
    activation_data = load_activation_time_series(str(activations_file))
    meg_psd = load_meg_psd(str(meg_psd_file))
    
    print(f"Loaded activations for {len(activation_data)} layers")
    print(f"Loaded MEG PSD with shape {meg_psd.shape}")
    
    # Compute metrics
    print("Computing layer metrics...")
    metrics_df = compute_layer_metrics(activation_data, meg_psd)
    
    # Save results
    print(f"Saving results to {output_file}")
    save_layer_metrics(metrics_df, str(output_file))
    
    print(f"Layer metrics computed and saved successfully!")
    print(f"Summary statistics:")
    print(metrics_df.describe())


if __name__ == "__main__":
    main()
