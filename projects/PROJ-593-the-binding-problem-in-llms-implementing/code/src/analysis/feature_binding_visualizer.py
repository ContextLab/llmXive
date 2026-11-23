import json
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, List, Tuple

def load_synthetic_data(data_path: str) -> Dict[str, Any]:
    """Load synthetic binding data from JSON file"""
    with open(data_path, 'r') as f:
        return json.load(f)

def extract_target_tokens(sequence_data: Dict[str, Any], feature_type: str) -> List[Dict[str, Any]]:
    """Extract tokens with a specific feature tag from sequence data"""
    return [token for token in sequence_data['tokens'] if token['feature_tag'] == feature_type]

def run_attention_analysis(
    sequence_text: str,
    model_wrapper,
    tokenizer,
    device: str = "cpu"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run forward pass with and without oscillatory attention to get attention weights.
    
    Returns:
        Tuple of (baseline_attention, oscillatory_attention) matrices
    """
    from src.models.base_model import DistilBERTWrapper
    from src.models.oscillatory_attention import OscillatoryDistilBERTWrapper
    
    # Tokenize
    inputs = tokenizer(sequence_text, return_tensors="pt", truncation=True, padding=True)
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)
    
    # Baseline run (no oscillation)
    baseline_model = DistilBERTWrapper.from_pretrained("distilbert-base-uncased")
    baseline_model.to(device)
    baseline_model.model.eval()
    
    with torch.no_grad():
        baseline_outputs = baseline_model.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=True
        )
        baseline_attention = baseline_outputs.attentions  # Tuple of attention matrices per layer
    
    # Oscillatory run
    oscillatory_model = OscillatoryDistilBERTWrapper.from_pretrained("distilbert-base-uncased")
    oscillatory_model.to(device)
    oscillatory_model.model.eval()
    
    with torch.no_grad():
        oscillatory_outputs = oscillatory_model.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=True
        )
        oscillatory_attention = oscillatory_outputs.attentions
    
    return baseline_attention, oscillatory_attention

def compute_binding_difference(
    baseline_attention: Tuple,
    oscillatory_attention: Tuple,
    color_token_idx: int,
    motion_token_idx: int
) -> Dict[str, Any]:
    """
    Compute the difference in attention weights between baseline and oscillatory models
    for specific color-motion token pairs.
    
    Args:
        baseline_attention: Attention matrices from baseline model
        oscillatory_attention: Attention matrices from oscillatory model
        color_token_idx: Index of color token in sequence
        motion_token_idx: Index of motion token in sequence
        
    Returns:
        Dictionary with binding difference metrics per layer
    """
    results = {
        "color_token_idx": color_token_idx,
        "motion_token_idx": motion_token_idx,
        "layer_differences": [],
        "max_difference": 0.0,
        "mean_difference": 0.0
    }
    
    differences = []
    for layer_idx, (base_layer, osc_layer) in enumerate(zip(baseline_attention, oscillatory_attention)):
        # Extract attention from specific query (color) to key (motion)
        # Shape: (batch, heads, seq_len, seq_len)
        base_attn = base_layer[0].cpu().numpy()  # Take first batch item
        osc_attn = osc_layer[0].cpu().numpy()
        
        # Get attention from color token to motion token across all heads
        base_color_motion = base_attn[:, :, color_token_idx, motion_token_idx]
        osc_color_motion = osc_attn[:, :, color_token_idx, motion_token_idx]
        
        # Compute difference
        diff = np.abs(osc_color_motion - base_color_motion)
        mean_diff = np.mean(diff)
        max_diff = np.max(diff)
        
        differences.append(mean_diff)
        
        layer_result = {
            "layer_id": layer_idx,
            "mean_attention_difference": float(mean_diff),
            "max_attention_difference": float(max_diff),
            "heads": [
                {
                    "head_id": h,
                    "difference": float(diff[0, h])
                }
                for h in range(diff.shape[1])
            ]
        }
        results["layer_differences"].append(layer_result)
    
    results["mean_difference"] = float(np.mean(differences))
    results["max_difference"] = float(np.max(differences))
    
    return results

def generate_binding_diagnostic(
    analysis_results: List[Dict[str, Any]],
    sequences_metadata: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Generate a diagnostic plot showing how attention weights shift for color/motion tokens
    under oscillation vs baseline.
    
    Args:
        analysis_results: List of binding difference results for each sequence
        sequences_metadata: Metadata about the sequences (token positions, etc.)
        output_path: Path to save the plot
    """
    # Ensure output directory exists
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for plotting
    num_sequences = len(analysis_results)
    if num_sequences == 0:
        print("No analysis results to plot")
        return
    
    # Extract mean differences per sequence
    mean_differences = [result['mean_difference'] for result in analysis_results]
    max_differences = [result['max_difference'] for result in analysis_results]
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Mean attention difference per sequence
    ax1 = axes[0]
    bars1 = ax1.bar(range(num_sequences), mean_differences, color='skyblue', edgecolor='black', alpha=0.7)
    ax1.set_xlabel('Sequence ID', fontsize=12)
    ax1.set_ylabel('Mean Attention Difference (Oscillatory - Baseline)', fontsize=12)
    ax1.set_title('Mean Attention Weight Shift for Color-Motion Binding', fontsize=14)
    ax1.set_xticks(range(num_sequences))
    ax1.set_xticklabels([f"Seq {i+1}" for i in range(num_sequences)])
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, val in zip(bars1, mean_differences):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    # Plot 2: Max attention difference per sequence
    ax2 = axes[1]
    bars2 = ax2.bar(range(num_sequences), max_differences, color='lightcoral', edgecolor='black', alpha=0.7)
    ax2.set_xlabel('Sequence ID', fontsize=12)
    ax2.set_ylabel('Max Attention Difference (Oscillatory - Baseline)', fontsize=12)
    ax2.set_title('Maximum Attention Weight Shift for Color-Motion Binding', fontsize=14)
    ax2.set_xticks(range(num_sequences))
    ax2.set_xticklabels([f"Seq {i+1}" for i in range(num_sequences)])
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, val in zip(bars2, max_differences):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    plt.suptitle('Feature Binding Diagnostic: Attention Weight Shifts\n'
                'Demonstrating how oscillatory attention enhances color-motion feature integration',
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Diagnostic plot saved to {output_path}")

def main():
    """Main function to run feature binding analysis and visualization"""
    import torch
    from transformers import DistilBertTokenizerFast
    
    # Configuration
    synthetic_data_path = "data/synthetic/color_motion.json"
    output_analysis_path = "data/final/feature_binding_analysis.json"
    output_plot_path = "plots/feature_binding_diagnostic.png"
    device = "cpu"
    
    # Load synthetic data
    print("Loading synthetic binding data...")
    synthetic_data = load_synthetic_data(synthetic_data_path)
    print(f"Loaded {len(synthetic_data['sequences'])} sequences")
    
    # Initialize tokenizer
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    
    # Analyze each sequence
    all_results = []
    all_attention_matrices = []
    
    for seq_data in synthetic_data['sequences']:
        print(f"\nAnalyzing sequence: {seq_data['id']}")
        print(f"Text: {seq_data['text']}")
        
        # Run attention analysis
        baseline_attn, oscillatory_attn = run_attention_analysis(
            seq_data['text'], None, tokenizer, device
        )
        
        # Extract target tokens
        color_tokens = extract_target_tokens(seq_data, 'color')
        motion_tokens = extract_target_tokens(seq_data, 'motion')
        
        seq_results = {
            "sequence_id": seq_data['id'],
            "text": seq_data['text'],
            "feature_pairs": [],
            "attention_matrices": {
                "baseline_shape": [attn.shape for attn in baseline_attn],
                "oscillatory_shape": [attn.shape for attn in oscillatory_attn]
            }
        }
        
        # Analyze each color-motion pair
        for pair in seq_data['feature_pairs']:
            # Find token indices
            color_token = next((t for t in seq_data['tokens'] if t['token'] == pair['color_token']), None)
            motion_token = next((t for t in seq_data['tokens'] if t['token'] == pair['motion_token']), None)
            
            if color_token and motion_token:
                color_idx = color_token['pos']
                motion_idx = motion_token['pos']
                
                # Compute binding difference
                binding_diff = compute_binding_difference(
                    baseline_attn, oscillatory_attn, color_idx, motion_idx
                )
                
                pair_result = {
                    "color_token": pair['color_token'],
                    "color_token_idx": color_idx,
                    "motion_token": pair['motion_token'],
                    "motion_token_idx": motion_idx,
                    "expected_binding": pair['expected_binding'],
                    "binding_difference": binding_diff
                }
                seq_results['feature_pairs'].append(pair_result)
        
        all_results.append(seq_results)
        all_attention_matrices.append({
            "sequence_id": seq_data['id'],
            "baseline": [attn.cpu().numpy().tolist() for attn in baseline_attn],
            "oscillatory": [attn.cpu().numpy().tolist() for attn in oscillatory_attn]
        })
    
    # Save analysis results
    analysis_output = {
        "metadata": {
            "description": "Feature binding analysis results",
            "total_sequences": len(all_results),
            "analysis_type": "oscillatory_vs_baseline_attention_comparison"
        },
        "results": all_results,
        "attention_matrices": all_attention_matrices
    }
    
    # Ensure output directory exists
    Path(output_analysis_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_analysis_path, 'w') as f:
        json.dump(analysis_output, f, indent=2)
    print(f"\nAnalysis results saved to {output_analysis_path}")
    
    # Generate diagnostic plot
    print("\nGenerating diagnostic plot...")
    generate_binding_diagnostic(
        [r['feature_pairs'][0]['binding_difference'] if r['feature_pairs'] else {'mean_difference': 0, 'max_difference': 0} 
         for r in all_results],
        synthetic_data['sequences'],
        output_plot_path
    )
    
    print("\nFeature binding analysis complete!")
    print(f"  - Analysis results: {output_analysis_path}")
    print(f"  - Diagnostic plot: {output_plot_path}")

if __name__ == "__main__":
    main()
