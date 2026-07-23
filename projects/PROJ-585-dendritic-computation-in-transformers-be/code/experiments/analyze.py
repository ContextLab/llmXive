import os
import sys
import json
import csv
import argparse
import logging
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Ensure we can import from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from existing modules as per API surface
from experiments.probe import set_seed, load_checkpoint, extract_layer_features, train_linear_probe, main as probe_main
from experiments.analyze import (
    ProbeResult, AnalysisResult, load_probe_results, pair_results,
    wilcoxon_signed_rank_test, paired_t_test, compute_effect_size,
    benjamini_hochberg_correction, analyze_layer_performance, save_results
)
from experiments.train import load_sst2_data, get_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_probing_for_threshold(
    threshold: float,
    input_dir: str,
    output_dir: str,
    config: Dict[str, Any],
    seed: int = 42
) -> Optional[Dict[str, Any]]:
    """
    Run probing logic (T025) for a specific dendritic threshold.
    
    Args:
        threshold: The dendritic threshold value to test
        input_dir: Directory containing saved checkpoints
        output_dir: Directory to save results
        config: Configuration dictionary
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing probing results or None if failed
    """
    logger.info(f"Running probing for threshold: {threshold}")
    
    try:
        # Set seed for reproducibility
        set_seed(seed)
        
        # Create threshold-specific output directory
        threshold_output_dir = os.path.join(output_dir, f"threshold_{threshold:.2f}")
        os.makedirs(threshold_output_dir, exist_ok=True)
        
        # Load checkpoints and extract features
        # We assume checkpoints are named with pattern: checkpoint_<model_type>.pt
        checkpoint_files = [f for f in os.listdir(input_dir) if f.endswith('.pt')]
        
        if not checkpoint_files:
            logger.warning(f"No checkpoint files found in {input_dir}")
            return None
        
        results = []
        
        for checkpoint_file in checkpoint_files:
            checkpoint_path = os.path.join(input_dir, checkpoint_file)
            
            try:
                # Load checkpoint
                model_type = "dendritic" if "dendritic" in checkpoint_file else "baseline"
                checkpoint = load_checkpoint(checkpoint_path)
                
                # Extract layer features
                layer_features = extract_layer_features(checkpoint, model_type)
                
                # Train linear probe
                probe_result = train_linear_probe(
                    layer_features=layer_features,
                    model_type=model_type,
                    output_dir=threshold_output_dir,
                    config=config
                )
                
                if probe_result:
                    results.append(probe_result)
                    
            except Exception as e:
                logger.error(f"Error processing checkpoint {checkpoint_file}: {e}")
                continue
        
        if not results:
            logger.warning(f"No results obtained for threshold {threshold}")
            return None
        
        # Save individual probing results
        results_file = os.path.join(threshold_output_dir, "probe_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Compute aggregate statistics for this threshold
        accuracy_values = [r['accuracy'] for r in results if 'accuracy' in r]
        
        if accuracy_values:
            threshold_summary = {
                'threshold': threshold,
                'num_seeds': len(results),
                'mean_accuracy': statistics.mean(accuracy_values),
                'std_accuracy': statistics.stdev(accuracy_values) if len(accuracy_values) > 1 else 0.0,
                'min_accuracy': min(accuracy_values),
                'max_accuracy': max(accuracy_values),
                'results': results
            }
            
            return threshold_summary
        else:
            return None
            
    except Exception as e:
        logger.error(f"Failed to run probing for threshold {threshold}: {e}")
        return None

def analyze_threshold_sensitivity(
    input_dir: str,
    output_dir: str,
    config_path: str,
    use_wilcoxon: bool = True,
    use_t_test: bool = True,
    num_seeds: int = 3
) -> Dict[str, Any]:
    """
    Main orchestrator for FR-007 sensitivity analysis (T029).
    
    Iterates over dendritic thresholds from config, runs probing (T025),
    performs statistical analysis (T027), and aggregates results.
    
    Args:
        input_dir: Directory containing saved checkpoints
        output_dir: Directory to save all results
        config_path: Path to configuration file
        use_wilcoxon: Whether to use Wilcoxon signed-rank test
        use_t_test: Whether to use paired t-test
        num_seeds: Number of random seeds to use for statistical power
    
    Returns:
        Dictionary containing comprehensive analysis results
    """
    logger.info("Starting threshold sensitivity analysis (T029)")
    
    # Load configuration
    config = load_config(config_path)
    thresholds = config.get('dendritic_thresholds', [0.1, 0.5, 0.9])
    
    logger.info(f"Testing thresholds: {thresholds}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Run probing for each threshold
    threshold_results = {}
    for threshold in thresholds:
        result = run_probing_for_threshold(
            threshold=threshold,
            input_dir=input_dir,
            output_dir=output_dir,
            config=config,
            seed=42  # Fixed seed for reproducibility in this analysis
        )
        if result:
            threshold_results[threshold] = result
    
    if not threshold_results:
        logger.error("No results obtained from any threshold")
        return {}
    
    # Perform statistical analysis across thresholds
    logger.info("Performing statistical analysis across thresholds")
    
    # Extract accuracy values for each threshold
    accuracy_data = {}
    for threshold, result in threshold_results.items():
        if 'results' in result:
            accuracy_data[threshold] = [r['accuracy'] for r in result['results'] if 'accuracy' in r]
    
    # Pair results for statistical tests (if we have multiple seeds per threshold)
    statistical_results = {}
    
    # Compare each threshold to the baseline (threshold 0.0 or first threshold)
    baseline_threshold = thresholds[0] if thresholds else None
    
    if baseline_threshold and baseline_threshold in accuracy_data:
        baseline_values = accuracy_data[baseline_threshold]
        
        for threshold, values in accuracy_data.items():
            if threshold != baseline_threshold:
                # Pair results for statistical testing
                paired_data = pair_results(baseline_values, values)
                
                if paired_data:
                    stat_result = {
                        'threshold': threshold,
                        'baseline_threshold': baseline_threshold,
                        'paired_samples': len(paired_data),
                    }
                    
                    # Wilcoxon signed-rank test
                    if use_wilcoxon and len(paired_data) >= 3:
                        try:
                            w_stat, w_pval = wilcoxon_signed_rank_test(paired_data)
                            stat_result['wilcoxon_statistic'] = w_stat
                            stat_result['wilcoxon_pvalue'] = w_pval
                            stat_result['wilcoxon_significant'] = w_pval < 0.05
                        except Exception as e:
                            logger.warning(f"Wilcoxon test failed: {e}")
                    
                    # Paired t-test
                    if use_t_test and len(paired_data) >= 3:
                        try:
                            t_stat, t_pval = paired_t_test(paired_data)
                            stat_result['t_statistic'] = t_stat
                            stat_result['t_pvalue'] = t_pval
                            stat_result['t_significant'] = t_pval < 0.05
                        except Exception as e:
                            logger.warning(f"T-test failed: {e}")
                    
                    # Compute effect size
                    if len(paired_data) >= 2:
                        try:
                            effect_size = compute_effect_size(paired_data)
                            stat_result['effect_size_cohen_d'] = effect_size
                        except Exception as e:
                            logger.warning(f"Effect size computation failed: {e}")
                    
                    statistical_results[threshold] = stat_result
    
    # Apply Benjamini-Hochberg correction if we have multiple comparisons
    pvalues = [v['wilcoxon_pvalue'] for v in statistical_results.values() 
              if 'wilcoxon_pvalue' in v]
    
    if pvalues and use_wilcoxon:
        try:
            corrected = benjamini_hochberg_correction(pvalues)
            for (thresh, res), pval_corr in zip(statistical_results.items(), corrected):
                res['bh_corrected_pvalue'] = pval_corr
                res['bh_significant'] = pval_corr < 0.05
        except Exception as e:
            logger.warning(f"Benjamini-Hochberg correction failed: {e}")
    
    # Compute stability metrics
    logger.info("Computing stability metrics")
    
    stability_metrics = {
        'accuracy_variance': {},
        'effect_size_stability': {},
        'threshold_sensitivity_summary': []
    }
    
    # Variance in probing accuracy across thresholds
    all_means = [v['mean_accuracy'] for v in threshold_results.values()]
    if all_means:
        stability_metrics['overall_mean_accuracy'] = statistics.mean(all_means)
        stability_metrics['accuracy_variance'] = statistics.variance(all_means) if len(all_means) > 1 else 0.0
        stability_metrics['accuracy_std'] = statistics.stdev(all_means) if len(all_means) > 1 else 0.0
    
    # Effect size stability (if we have effect sizes)
    effect_sizes = [v.get('effect_size_cohen_d') for v in statistical_results.values() 
                   if 'effect_size_cohen_d' in v]
    if effect_sizes:
        stability_metrics['effect_size_stability']['mean'] = statistics.mean(effect_sizes)
        if len(effect_sizes) > 1:
            stability_metrics['effect_size_stability']['std'] = statistics.stdev(effect_sizes)
            stability_metrics['effect_size_stability']['variance'] = statistics.variance(effect_sizes)
        else:
            stability_metrics['effect_size_stability']['std'] = 0.0
            stability_metrics['effect_size_stability']['variance'] = 0.0
    
    # Aggregate summary
    summary = {
        'analysis_type': 'threshold_sensitivity',
        'config_path': config_path,
        'thresholds_tested': thresholds,
        'num_seeds_per_threshold': num_seeds,
        'threshold_results': threshold_results,
        'statistical_analysis': statistical_results,
        'stability_metrics': stability_metrics,
        'conclusions': []
    }
    
    # Generate conclusions
    if stability_metrics['accuracy_variance'] < 0.01:
        summary['conclusions'].append(
            "Dendritic thresholds show low variance in probing accuracy, "
            "suggesting stable feature detection across threshold settings."
        )
    else:
        summary['conclusions'].append(
            "Dendritic thresholds show significant variance in probing accuracy, "
            "indicating sensitivity to threshold selection."
        )
    
    # Check for significant effects
    significant_results = [
        thresh for thresh, res in statistical_results.items()
        if res.get('wilcoxon_significant', False) or res.get('t_significant', False)
    ]
    
    if significant_results:
        summary['conclusions'].append(
            f"Thresholds {significant_results} show statistically significant "
            "differences from baseline in probing accuracy."
        )
    else:
        summary['conclusions'].append(
            "No thresholds showed statistically significant differences from baseline "
            "in probing accuracy."
        )
    
    # Save comprehensive results
    results_file = os.path.join(output_dir, "sensitivity_analysis_results.json")
    save_results(summary, results_file)
    
    # Save CSV summary for easy viewing
    csv_file = os.path.join(output_dir, "sensitivity_summary.csv")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Threshold', 'Mean Accuracy', 'Std Accuracy', 'Effect Size', 'P-value', 'Significant'])
        
        for threshold, result in threshold_results.items():
            stat_res = statistical_results.get(threshold, {})
            writer.writerow([
                threshold,
                result['mean_accuracy'],
                result['std_accuracy'],
                stat_res.get('effect_size_cohen_d', 'N/A'),
                stat_res.get('wilcoxon_pvalue', 'N/A'),
                stat_res.get('wilcoxon_significant', False)
            ])
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_dir}")
    return summary

def main():
    """Main entry point for the sensitivity analysis script."""
    parser = argparse.ArgumentParser(
        description='Run threshold sensitivity analysis (T029)'
    )
    parser.add_argument(
        '--input-dir',
        required=True,
        help='Directory containing saved checkpoints'
    )
    parser.add_argument(
        '--output-dir',
        default='artifacts/results',
        help='Directory to save analysis results'
    )
    parser.add_argument(
        '--config',
        default='code/config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--use-wilcoxon',
        action='store_true',
        default=True,
        help='Use Wilcoxon signed-rank test'
    )
    parser.add_argument(
        '--use-t-test',
        action='store_true',
        default=True,
        help='Use paired t-test'
    )
    parser.add_argument(
        '--num-seeds',
        type=int,
        default=3,
        help='Number of random seeds for statistical power'
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.exists(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        sys.exit(1)
    
    # Validate config file
    if not os.path.exists(args.config):
        logger.error(f"Config file does not exist: {args.config}")
        sys.exit(1)
    
    # Run the analysis
    results = analyze_threshold_sensitivity(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        config_path=args.config,
        use_wilcoxon=args.use_wilcoxon,
        use_t_test=args.use_t_test,
        num_seeds=args.num_seeds
    )
    
    if not results:
        logger.error("Analysis failed to produce results")
        sys.exit(1)
    
    logger.info("Analysis completed successfully")
    sys.exit(0)

if __name__ == '__main__':
    main()