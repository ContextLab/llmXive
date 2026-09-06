"""
Statistical analysis module for Dream-State Learning project.

Implements Wilcoxon signed-rank test for comparing experimental vs baseline
model performance across multiple seeds.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy.stats import wilcoxon
from utils.logger import get_logger
import json
from pathlib import Path
from config import Config

logger = get_logger(__name__)


def load_accuracy_results(results_dir: Path, model_type: str) -> List[float]:
    """
    Load accuracy results for a specific model type across all seeds.
    
    Args:
        results_dir: Directory containing seed result files
        model_type: Either 'experimental' or 'baseline'
        
    Returns:
        List of accuracy floats (one per seed)
        
    Raises:
        FileNotFoundError: If no results found for the model type
    """
    accuracies = []
    seed_files = sorted(results_dir.glob(f"{model_type}_seed_*.json"))
    
    if not seed_files:
        raise FileNotFoundError(f"No results found for {model_type} model in {results_dir}")
    
    for seed_file in seed_files:
        try:
            with open(seed_file, 'r') as f:
                data = json.load(f)
                # Expecting 'final_accuracy' key in result files
                accuracy = float(data.get('final_accuracy', 0.0))
                accuracies.append(accuracy)
                logger.info(f"Loaded {model_type} accuracy {accuracy:.4f} from {seed_file.name}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse {seed_file.name}: {e}")
            continue
    
    if len(accuracies) == 0:
        raise FileNotFoundError(f"No valid accuracy results found for {model_type}")
        
    return accuracies


def compute_accuracy_difference(experimental_accs: List[float], 
                              baseline_accs: List[float]) -> float:
    """
    Compute the mean accuracy difference between experimental and baseline.
    
    Args:
        experimental_accs: List of experimental model accuracies
        baseline_accs: List of baseline model accuracies
        
    Returns:
        Mean difference (experimental - baseline)
    """
    if len(experimental_accs) != len(baseline_accs):
        logger.warning(f"Accuracy lists have different lengths: {len(experimental_accs)} vs {len(baseline_accs)}")
        min_len = min(len(experimental_accs), len(baseline_accs))
        experimental_accs = experimental_accs[:min_len]
        baseline_accs = baseline_accs[:min_len]
    
    diff = np.array(experimental_accs) - np.array(baseline_accs)
    return float(np.mean(diff))


def run_wilcoxon_test(experimental_accs: List[float], 
                    baseline_accs: List[float],
                    alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test to compare experimental vs baseline.
    
    Args:
        experimental_accs: List of experimental model accuracies (n seeds)
        baseline_accs: List of baseline model accuracies (n seeds)
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary containing:
            - statistic: Wilcoxon test statistic
            - pvalue: Two-sided p-value
            - significant: Boolean indicating if p < alpha
            - alpha: The significance level used
            - n_seeds: Number of seeds tested
    """
    if len(experimental_accs) != len(baseline_accs):
        raise ValueError(f"Accuracy lists must have same length: {len(experimental_accs)} vs {len(baseline_accs)}")
    
    if len(experimental_accs) < 2:
        raise ValueError(f"Need at least 2 seeds for Wilcoxon test, got {len(experimental_accs)}")
    
    # Convert to numpy arrays
    exp_arr = np.array(experimental_accs)
    base_arr = np.array(baseline_accs)
    
    # Run Wilcoxon signed-rank test
    statistic, pvalue = wilcoxon(exp_arr, base_arr)
    
    result = {
        "statistic": float(statistic),
        "pvalue": float(pvalue),
        "significant": bool(pvalue < alpha),
        "alpha": alpha,
        "n_seeds": len(experimental_accs),
        "experimental_mean": float(np.mean(exp_arr)),
        "baseline_mean": float(np.mean(base_arr)),
        "experimental_std": float(np.std(exp_arr)),
        "baseline_std": float(np.std(base_arr)),
        "mean_difference": float(np.mean(exp_arr - base_arr))
    }
    
    logger.info(f"Wilcoxon test: statistic={statistic:.4f}, p-value={pvalue:.4f}, significant={result['significant']}")
    return result


def analyze_model_performance(experimental_accs: List[float], 
                            baseline_accs: List[float],
                            alpha: float = 0.05) -> Dict[str, Any]:
    """
    Comprehensive analysis comparing experimental and baseline models.
    
    Args:
        experimental_accs: List of experimental model accuracies
        baseline_accs: List of baseline model accuracies
        alpha: Significance level for statistical test
        
    Returns:
        Dictionary containing full analysis results
    """
    # Basic statistics
    exp_mean = float(np.mean(experimental_accs))
    exp_std = float(np.std(experimental_accs))
    base_mean = float(np.mean(baseline_accs))
    base_std = float(np.std(baseline_accs))
    mean_diff = exp_mean - base_mean
    
    # Statistical test
    wilcoxon_result = run_wilcoxon_test(experimental_accs, baseline_accs, alpha)
    
    # Effect size (Cohen's d approximation for paired data)
    if base_std > 0:
        effect_size = mean_diff / base_std
    else:
        effect_size = 0.0
    
    return {
        "experimental": {
            "mean": exp_mean,
            "std": exp_std,
            "n": len(experimental_accs),
            "values": experimental_accs
        },
        "baseline": {
            "mean": base_mean,
            "std": base_std,
            "n": len(baseline_accs),
            "values": baseline_accs
        },
        "comparison": {
            "mean_difference": mean_diff,
            "effect_size": effect_size,
            "wilcoxon": wilcoxon_result
        },
        "conclusion": "Experimental model outperforms baseline" if mean_diff > 0 and wilcoxon_result['significant'] else
                     "No significant difference" if not wilcoxon_result['significant'] else
                     "Baseline outperforms experimental"
    }


def save_analysis_report(analysis_result: Dict[str, Any], 
                       output_path: Path) -> None:
    """
    Save analysis results to a JSON file.
    
    Args:
        analysis_result: Dictionary containing analysis results
        output_path: Path to save the JSON report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(analysis_result, f, indent=2)
    
    logger.info(f"Analysis report saved to {output_path}")

def load_and_analyze(results_dir: Path, 
                   output_path: Optional[Path] = None,
                   alpha: float = 0.05) -> Dict[str, Any]:
    """
    Convenience function to load results and perform full analysis.
    
    Args:
        results_dir: Directory containing seed result files
        output_path: Optional path to save the analysis report
        alpha: Significance level for statistical test
        
    Returns:
        Dictionary containing analysis results
    """
    results_dir = Path(results_dir)
    
    # Load accuracies for both models
    experimental_accs = load_accuracy_results(results_dir, "experimental")
    baseline_accs = load_accuracy_results(results_dir, "baseline")
    
    logger.info(f"Loaded {len(experimental_accs)} experimental and {len(baseline_accs)} baseline results")
    
    # Perform analysis
    analysis_result = analyze_model_performance(experimental_accs, baseline_accs, alpha)
    
    # Save if output path provided
    if output_path:
        save_analysis_report(analysis_result, output_path)
    
    return analysis_result


def main():
    """
    Main entry point for statistical analysis script.
    
    Usage:
        python code/eval/statistical_analysis.py [--results-dir DATA/results] [--output DATA/results/analysis.json]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Statistical analysis for Dream-State Learning")
    parser.add_argument("--results-dir", type=str, default="data/results",
                      help="Directory containing seed result files")
    parser.add_argument("--output", type=str, default="data/results/statistical_analysis.json",
                      help="Output path for analysis report")
    parser.add_argument("--alpha", type=float, default=0.05,
                      help="Significance level for statistical test")
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_path = Path(args.output)
    
    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}")
        return 1
    
    try:
        analysis_result = load_and_analyze(results_dir, output_path, args.alpha)
        
        # Print summary to stdout
        print("\n" + "="*60)
        print("STATISTICAL ANALYSIS SUMMARY")
        print("="*60)
        print(f"Experimental: mean={analysis_result['experimental']['mean']:.4f} ± {analysis_result['experimental']['std']:.4f} (n={analysis_result['experimental']['n']})")
        print(f"Baseline:     mean={analysis_result['baseline']['mean']:.4f} ± {analysis_result['baseline']['std']:.4f} (n={analysis_result['baseline']['n']})")
        print(f"Difference:   {analysis_result['comparison']['mean_difference']:.4f}")
        print(f"Wilcoxon:     statistic={analysis_result['comparison']['wilcoxon']['statistic']:.4f}, p-value={analysis_result['comparison']['wilcoxon']['pvalue']:.4f}")
        print(f"Significant:  {analysis_result['comparison']['wilcoxon']['significant']} (α={args.alpha})")
        print(f"Conclusion:   {analysis_result['conclusion']}")
        print("="*60 + "\n")
        
        logger.info("Analysis completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data loading error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Analysis error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())