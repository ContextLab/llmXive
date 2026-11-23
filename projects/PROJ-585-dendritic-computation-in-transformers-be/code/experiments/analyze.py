import os
import sys
import json
import csv
import argparse
import logging
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, ttest_rel
from statsmodels.stats.multitest import multipletests

# Add project root to path to resolve imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from probe module as per API surface
from experiments.probe import set_seed, load_checkpoint, extract_layer_features, train_linear_probe, load_sst2_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path='code/config/config.yaml'):
    """
    Load configuration from YAML file.
    Handles basic parsing without requiring pyyaml if possible, or uses it.
    """
    import yaml
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_probing_for_threshold(threshold, checkpoint_dir, output_dir, seed=42):
    """
    Run probing logic for a specific dendritic threshold.
    This function orchestrates loading data, extracting features, training probes,
    and returning results for a single threshold value.
    """
    set_seed(seed)
    logger.info(f"Starting probing analysis for threshold: {threshold}")

    # Load SST-2 data (real data)
    try:
        train_data, val_data, test_data = load_sst2_data()
    except Exception as e:
        logger.error(f"Failed to load SST-2 data: {e}")
        raise

    # Load checkpoints (assuming they exist from T021/T025)
    # We expect checkpoints to be named based on threshold or model type
    # For this analysis, we assume a specific naming convention or we scan the directory
    checkpoint_files = [f for f in os.listdir(checkpoint_dir) if f.endswith('.pt') or f.endswith('.pth')]
    
    if not checkpoint_files:
        raise FileNotFoundError(f"No checkpoint files found in {checkpoint_dir}")

    results = []

    for ckpt_file in checkpoint_files:
        ckpt_path = os.path.join(checkpoint_dir, ckpt_file)
        logger.info(f"Processing checkpoint: {ckpt_file}")
        
        try:
            model_state = load_checkpoint(ckpt_path)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint {ckpt_file}: {e}")
            continue

        # Extract features for all layers
        layer_features = {}
        for layer_idx in range(12): # Assuming 12 layers for standard transformer
            try:
                features = extract_layer_features(model_state, train_data, layer_idx=layer_idx)
                layer_features[layer_idx] = features
            except Exception as e:
                logger.warning(f"Failed to extract features for layer {layer_idx}: {e}")
                continue

        # Train linear probes for each layer
        layer_accuracies = {}
        for layer_idx, features in layer_features.items():
            try:
                acc = train_linear_probe(features, train_data['label'])
                layer_accuracies[layer_idx] = acc
            except Exception as e:
                logger.warning(f"Failed to train probe for layer {layer_idx}: {e}")
                layer_accuracies[layer_idx] = 0.0

        results.append({
            'threshold': threshold,
            'checkpoint': ckpt_file,
            'layer_accuracies': layer_accuracies
        })

    # Save intermediate results
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"probing_results_threshold_{threshold}.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved probing results for threshold {threshold} to {output_file}")
    return results

def analyze_threshold_sensitivity(all_results, output_path):
    """
    Perform statistical analysis on results across different thresholds.
    Uses Wilcoxon signed-rank test or paired t-tests and Benjamini-Hochberg correction.
    """
    logger.info("Starting statistical analysis of threshold sensitivity")

    if not all_results:
        raise ValueError("No results provided for analysis")

    # Aggregate data for analysis
    # We expect results to be structured as a list of dicts, each with 'threshold' and 'layer_accuracies'
    # We will compare each threshold against a baseline (e.g., threshold=0.5 or the first threshold)
    
    thresholds = sorted(list(set([r['threshold'] for r in all_results])))
    if len(thresholds) < 2:
        logger.warning("Less than 2 thresholds found, skipping comparative statistical analysis")
        # Still save the raw data
        with open(output_path, 'w') as f:
            json.dump({'thresholds': thresholds, 'results': all_results}, f, indent=2)
        return

    # Assume the first threshold is the baseline for comparison
    baseline_threshold = thresholds[0]
    baseline_results = [r for r in all_results if r['threshold'] == baseline_threshold]
    
    # Collect accuracies for each layer across thresholds
    # Structure: { layer_idx: { threshold: [acc1, acc2, ...] } }
    layer_data = {}
    max_layers = 0
    for res in all_results:
        for layer_idx, acc in res['layer_accuracies'].items():
            if layer_idx not in layer_data:
                layer_data[layer_idx] = {}
            if res['threshold'] not in layer_data[layer_idx]:
                layer_data[layer_idx][res['threshold']] = []
            layer_data[layer_idx][res['threshold']].append(acc)
        max_layers = max(max_layers, max(res['layer_accuracies'].keys()) + 1)

    statistical_results = []

    for layer_idx in range(max_layers):
        if layer_idx not in layer_data:
            continue
        
        layer_stats = {'layer': layer_idx, 'comparisons': []}
        
        # Compare each non-baseline threshold against baseline
        for threshold in thresholds[1:]:
            if threshold not in layer_data[layer_idx] or baseline_threshold not in layer_data[layer_idx]:
                continue
            
            baseline_vals = np.array(layer_data[layer_idx][baseline_threshold])
            test_vals = np.array(layer_data[layer_idx][threshold])
            
            if len(baseline_vals) == 0 or len(test_vals) == 0:
                continue

            # Ensure paired data if possible (same checkpoints)
            # If lengths differ, we take the minimum length to pair them
            min_len = min(len(baseline_vals), len(test_vals))
            if min_len < 2:
                continue # Need at least 2 pairs for statistical test
            
            baseline_vals = baseline_vals[:min_len]
            test_vals = test_vals[:min_len]

            # Perform Wilcoxon signed-rank test (non-parametric) or t-test
            # Using Wilcoxon as primary for small sample sizes
            try:
                stat, p_val = wilcoxon(baseline_vals, test_vals)
                test_type = "wilcoxon"
            except Exception as e:
                logger.warning(f"Wilcoxon failed for layer {layer_idx}, threshold {threshold}: {e}. Trying t-test.")
                try:
                    stat, p_val = ttest_rel(baseline_vals, test_vals)
                    test_type = "ttest"
                except Exception as e2:
                    logger.error(f"Both tests failed for layer {layer_idx}, threshold {threshold}: {e2}")
                    continue

            layer_stats['comparisons'].append({
                'threshold': threshold,
                'test_type': test_type,
                'statistic': float(stat),
                'p_value': float(p_val),
                'baseline_mean': float(np.mean(baseline_vals)),
                'test_mean': float(np.mean(test_vals)),
                'n': min_len
            })

        statistical_results.append(layer_stats)

    # Apply Benjamini-Hochberg correction for multiple comparisons
    # Flatten all p-values for correction
    all_p_values = []
    p_value_indices = [] # (layer_idx, comparison_idx)
    
    for layer_idx, layer_stat in enumerate(statistical_results):
        for comp_idx, comp in enumerate(layer_stat['comparisons']):
            all_p_values.append(comp['p_value'])
            p_value_indices.append((layer_idx, comp_idx))

    if len(all_p_values) > 0:
        # Perform BH correction
        reject, p_corrected, _, _ = multipletests(all_p_values, alpha=0.05, method='fdr_bh')
        
        # Map corrected p-values back
        for idx, corrected_p in enumerate(p_corrected):
          layer_idx, comp_idx = p_value_indices[idx]
          statistical_results[layer_idx]['comparisons'][comp_idx]['p_value_corrected'] = float(corrected_p)
          statistical_results[layer_idx]['comparisons'][comp_idx]['rejected'] = bool(reject[idx])

    # Save final results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(statistical_results, f, indent=2)

    logger.info(f"Saved statistical analysis results to {output_path}")
    return statistical_results

def main():
    parser = argparse.ArgumentParser(description="Analyze dendritic threshold sensitivity")
    parser.add_argument('--config', type=str, default='code/config/config.yaml', help='Path to config file')
    parser.add_argument('--checkpoint-dir', type=str, default='artifacts/checkpoints', help='Directory containing model checkpoints')
    parser.add_argument('--output-dir', type=str, default='artifacts/results', help='Directory for output results')
    parser.add_argument('--thresholds', type=str, nargs='+', help='List of thresholds to analyze (optional, otherwise read from config)')
    
    args = parser.parse_args()

    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Determine thresholds
    if args.thresholds:
        thresholds = [float(t) for t in args.thresholds]
    else:
        # Read from config as per FR-007
        thresholds = config.get('dendritic_thresholds', [0.1, 0.5, 0.9])
        if not isinstance(thresholds, list):
            thresholds = [float(thresholds)]

    logger.info(f"Analyzing thresholds: {thresholds}")

    all_results = []
    for threshold in thresholds:
        try:
            results = run_probing_for_threshold(
                threshold=threshold,
                checkpoint_dir=args.checkpoint_dir,
                output_dir=args.output_dir
            )
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Failed to analyze threshold {threshold}: {e}")
            # Continue with other thresholds, but log the failure
            continue

    if not all_results:
        logger.error("No results generated for any threshold.")
        sys.exit(1)

    # Perform statistical analysis
    analysis_output = os.path.join(args.output_dir, 'threshold_sensitivity_analysis.json')
    try:
        analyze_threshold_sensitivity(all_results, analysis_output)
        logger.info("Analysis complete.")
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()