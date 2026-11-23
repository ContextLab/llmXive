import os
import sys
import json
import time
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import numpy as np

from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu
from src.models.oscillatory_attention import OscillatoryAttentionModule, OscillatoryDistilBERTWrapper
from src.analysis.spectral import compute_welch_psd, calculate_snr
from src.analysis.control_run import run_baseline_forward_pass, run_oscillatory_forward_pass, extract_activations

def load_config(config_path: str = "config/default.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_frequency_sweep(
    model_wrapper: OscillatoryDistilBERTWrapper,
    baseline_wrapper: DistilBERTWrapper,
    tokenizer,
    sequences: List[str],
    frequency_range: List[float],
    output_path: str
) -> Dict[str, Any]:
    """
    Iterate relative frequencies across a range of cycle counts per sequence.
    
    Args:
        model_wrapper: Oscillatory model with injected attention module
        baseline_wrapper: Baseline model without oscillation
        tokenizer: HuggingFace tokenizer
        sequences: List of input text sequences
        frequency_range: List of relative frequencies (cycles per sequence) to test
        output_path: Path to save results CSV
    
    Returns:
        Dictionary containing sweep results
    """
    results = []
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting frequency sweep with {len(frequency_range)} frequencies...")
    print(f"Frequency range: {frequency_range}")
    
    for freq in frequency_range:
        print(f"\nProcessing frequency: {freq:.2f} cycles/sequence")
        
        sweep_results = {
            'frequency': freq,
            'sequence_results': []
        }
        
        for seq_idx, text in enumerate(sequences):
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            seq_len = inputs['input_ids'].shape[1]
            
            # Configure oscillation for this frequency
            model_wrapper.configure_oscillation(frequency=freq, seq_len=seq_len)
            
            # Run forward passes
            try:
                # Oscillatory run
                osc_activations = run_oscillatory_forward_pass(
                    model_wrapper, inputs, tokenizer, extract_activations=True
                )
                
                # Baseline run
                base_activations = run_baseline_forward_pass(
                    baseline_wrapper, inputs, tokenizer, extract_activations=True
                )
                
                # Compute spectral metrics for each layer/head
                layer_metrics = []
                
                for layer_id, layer_activations in osc_activations.items():
                    for head_id, head_data in layer_activations.items():
                        if isinstance(head_data, np.ndarray) and len(head_data) > 0:
                            # Compute PSD
                            psd, freqs = compute_welch_psd(head_data, fs=1.0)  # fs=1 for relative frequency
                            
                            # Calculate SNR
                            snr_db = calculate_snr(psd, freqs, target_band=(0.8, 1.2))  # Around 1 cycle/seq
                            
                            layer_metrics.append({
                                'layer_id': int(layer_id),
                                'head_id': int(head_id),
                                'psd_peak_freq': float(freqs[np.argmax(psd)]) if len(psd) > 0 else 0.0,
                                'psd_peak_power': float(np.max(psd)) if len(psd) > 0 else 0.0,
                                'snr_db': float(snr_db)
                            })
                
                sweep_results['sequence_results'].append({
                    'sequence_index': seq_idx,
                    'sequence_length': seq_len,
                    'layer_metrics': layer_metrics,
                    'success': True
                })
                
            except Exception as e:
                sweep_results['sequence_results'].append({
                    'sequence_index': seq_idx,
                    'error': str(e),
                    'success': False
                })
                print(f"  Error processing sequence {seq_idx}: {e}")
        
        results.append(sweep_results)
    
    # Save results to CSV
    save_sweep_results_csv(results, output_path)
    
    return results

def save_sweep_results_csv(results: List[Dict[str, Any]], output_path: str):
    """Save sweep results to CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'frequency', 'sequence_index', 'sequence_length', 
            'layer_id', 'head_id', 'psd_peak_freq', 'psd_peak_power', 'snr_db', 'success', 'error'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for sweep_result in results:
            freq = sweep_result['frequency']
            for seq_result in sweep_result['sequence_results']:
                if seq_result.get('success', False):
                    for layer_metric in seq_result.get('layer_metrics', []):
                        row = {
                            'frequency': freq,
                            'sequence_index': seq_result['sequence_index'],
                            'sequence_length': seq_result['sequence_length'],
                            'layer_id': layer_metric['layer_id'],
                            'head_id': layer_metric['head_id'],
                            'psd_peak_freq': layer_metric['psd_peak_freq'],
                            'psd_peak_power': layer_metric['psd_peak_power'],
                            'snr_db': layer_metric['snr_db'],
                            'success': True,
                            'error': ''
                        }
                        writer.writerow(row)
                else:
                    row = {
                        'frequency': freq,
                        'sequence_index': seq_result['sequence_index'],
                        'sequence_length': seq_result.get('sequence_length', 0),
                        'layer_id': 0,
                        'head_id': 0,
                        'psd_peak_freq': 0.0,
                        'psd_peak_power': 0.0,
                        'snr_db': 0.0,
                        'success': False,
                        'error': seq_result.get('error', 'Unknown error')
                    }
                    writer.writerow(row)

def main():
    """Main entry point for frequency sweep analysis."""
    print("=== Frequency Sweep Analysis ===")
    
    # Load configuration
    config = load_config()
    
    # Configuration parameters
    device = config.get('device', 'cpu')
    seq_len = config.get('sequence_length', 512)
    frequency_range = config.get('frequency_sweep', {
        'start': 0.5,
        'end': 2.0,
        'steps': 10
    })
    output_path = config.get('output_paths', {}).get('sweep_results', 'data/processed/sweep_results.csv')
    
    # Generate frequency range
    frequencies = list(np.linspace(
        frequency_range['start'], 
        frequency_range['end'], 
        frequency_range['steps']
    ))
    
    # Sample sequences for testing
    sample_sequences = [
        "The cat sat on the mat and looked at the bird.",
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning models can learn complex patterns in data.",
        "Neural networks with oscillatory dynamics may solve the binding problem.",
        "Attention mechanisms allow models to focus on relevant information."
    ]
    
    # Load models
    print("Loading baseline model...")
    baseline_model = load_distilbert_cpu()
    baseline_wrapper = DistilBERTWrapper(baseline_model)
    
    print("Loading oscillatory model...")
    osc_model = load_distilbert_cpu()
    osc_wrapper = OscillatoryDistilBERTWrapper(osc_model)
    
    # Load tokenizer
    from transformers import DistilBertTokenizerFast
    tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
    
    # Run frequency sweep
    print(f"Running frequency sweep on {len(sample_sequences)} sequences...")
    results = run_frequency_sweep(
        osc_wrapper,
        baseline_wrapper,
        tokenizer,
        sample_sequences,
        frequencies,
        output_path
    )
    
    print(f"\nSweep completed. Results saved to: {output_path}")
    print(f"Total frequencies tested: {len(frequencies)}")
    print(f"Total sequences: {len(sample_sequences)}")
    
    # Summary statistics
    successful_runs = sum(
        1 for sweep in results 
        for seq in sweep['sequence_results'] 
        if seq.get('success', False)
    )
    total_runs = len(results) * len(sample_sequences)
    
    print(f"Successful runs: {successful_runs}/{total_runs}")
    
    return results

if __name__ == "__main__":
    main()