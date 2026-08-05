"""
Statistical analysis module for Dream-State Learning experiments.

Implements Wilcoxon signed-rank test and accuracy difference calculations
to compare experimental (Dream-State) vs baseline (Continuous SFT) models.
"""
from typing import List, Tuple, Dict, Any
import numpy as np
from scipy.stats import wilcoxon
from utils.logger import get_logger
import json
from pathlib import Path
from config import Config

logger = get_logger(__name__)

def load_accuracy_results(results_path: str) -> Dict[str, List[float]]:
    """
    Load accuracy results from a JSON file containing lists of accuracies per seed.
    
    Expected JSON structure:
    {
        "experimental": [acc1, acc2, acc3, acc4, acc5],
        "baseline": [acc1, acc2, acc3, acc4, acc5]
    }
    
    Args:
        results_path: Path to the JSON file containing accuracy results.
        
    Returns:
        Dictionary with 'experimental' and 'baseline' keys mapping to lists of floats.
        
    Raises:
        FileNotFoundError: If the results file does not exist.
        ValueError: If the file format is invalid or missing required keys.
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
        
    with open(path, 'r') as f:
        data = json.load(f)
        
    if 'experimental' not in data or 'baseline' not in data:
        raise ValueError("Results file must contain 'experimental' and 'baseline' keys")
        
    if not isinstance(data['experimental'], list) or not isinstance(data['baseline'], list):
        raise ValueError("Accuracies must be stored as lists")
        
    if len(data['experimental']) != 5 or len(data['baseline']) != 5:
        logger.warning(f"Expected 5 seeds per model, found {len(data['experimental'])} experimental and {len(data['baseline'])} baseline")
        
    return {
        'experimental': [float(x) for x in data['experimental']],
        'baseline': [float(x) for x in data['baseline']]
    }

def compute_accuracy_difference(experimental_acc: List[float], baseline_acc: List[float]) -> float:
    """
    Compute the mean accuracy difference between experimental and baseline models.
    
    Args:
        experimental_acc: List of accuracy values for the experimental model across seeds.
        baseline_acc: List of accuracy values for the baseline model across seeds.
        
    Returns:
        Mean difference (experimental - baseline).
    """
    if len(experimental_acc) != len(baseline_acc):
        raise ValueError("Experimental and baseline accuracy lists must have the same length")
        
    experimental_arr = np.array(experimental_acc)
    baseline_arr = np.array(baseline_acc)
    
    diff = np.mean(experimental_arr - baseline_arr)
    logger.info(f"Mean accuracy difference (Experimental - Baseline): {diff:.6f}")
    return float(diff)

def run_wilcoxon_test(experimental_acc: List[float], baseline_acc: List[float], 
                     alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test to determine statistical significance.
    
    Args:
        experimental_acc: List of accuracy values for the experimental model across seeds.
        baseline_acc: List of accuracy values for the baseline model across seeds.
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing:
            - statistic: Wilcoxon test statistic
            - pvalue: p-value from the test
            - significant: Boolean indicating if p-value < alpha
            - alpha: The significance level used
    """
    if len(experimental_acc) != len(baseline_acc):
        raise ValueError("Experimental and baseline accuracy lists must have the same length")
        
    if len(experimental_acc) < 2:
        raise ValueError("Wilcoxon test requires at least 2 paired samples")
        
    experimental_arr = np.array(experimental_acc)
    baseline_arr = np.array(baseline_acc)
    
    # Perform Wilcoxon signed-rank test
    statistic, pvalue = wilcoxon(experimental_arr, baseline_arr)
    
    significant = pvalue < alpha
    
    logger.info(f"Wilcoxon Test Results:")
    logger.info(f"  Statistic: {statistic:.6f}")
    logger.info(f"  P-value: {pvalue:.6f}")
    logger.info(f"  Alpha: {alpha}")
    logger.info(f"  Significant (p < alpha): {significant}")
    
    return {
        'statistic': float(statistic),
        'pvalue': float(pvalue),
        'significant': significant,
        'alpha': alpha
    }

def analyze_model_performance(experimental_acc: List[float], baseline_acc: List[float],
                             alpha: float = 0.05) -> Dict[str, Any]:
    """
    Comprehensive analysis of model performance comparing experimental vs baseline.
    
    Args:
        experimental_acc: List of accuracy values for the experimental model across seeds.
        baseline_acc: List of accuracy values for the baseline model across seeds.
        alpha: Significance level for statistical test (default 0.05).
        
    Returns:
        Dictionary containing:
            - experimental_stats: Mean, std, min, max of experimental accuracies
            - baseline_stats: Mean, std, min, max of baseline accuracies
            - accuracy_difference: Mean difference (experimental - baseline)
            - wilcoxon_test: Results from Wilcoxon signed-rank test
    """
    if len(experimental_acc) != len(baseline_acc):
        raise ValueError("Experimental and baseline accuracy lists must have the same length")
        
    # Calculate statistics
    experimental_arr = np.array(experimental_acc)
    baseline_arr = np.array(baseline_acc)
    
    experimental_stats = {
        'mean': float(np.mean(experimental_arr)),
        'std': float(np.std(experimental_arr)),
        'min': float(np.min(experimental_arr)),
        'max': float(np.max(experimental_arr))
    }
    
    baseline_stats = {
        'mean': float(np.mean(baseline_arr)),
        'std': float(np.std(baseline_arr)),
        'min': float(np.min(baseline_arr)),
        'max': float(np.max(baseline_arr))
    }
    
    # Compute difference and run statistical test
    accuracy_difference = compute_accuracy_difference(experimental_acc, baseline_acc)
    wilcoxon_results = run_wilcoxon_test(experimental_acc, baseline_acc, alpha)
    
    return {
        'experimental_stats': experimental_stats,
        'baseline_stats': baseline_stats,
        'accuracy_difference': accuracy_difference,
        'wilcoxon_test': wilcoxon_results
    }

def save_analysis_report(analysis_results: Dict[str, Any], output_path: str) -> None:
    """
    Save the analysis results to a JSON file.
    
    Args:
        analysis_results: Dictionary containing analysis results.
        output_path: Path to save the JSON report.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
        
    logger.info(f"Analysis report saved to: {output_path}")

def load_and_analyze(results_path: str, output_path: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Convenience function to load results, perform analysis, and save report.
    
    Args:
        results_path: Path to JSON file containing accuracy results.
        output_path: Path to save the analysis report.
        alpha: Significance level for statistical test.
        
    Returns:
        Dictionary containing the full analysis results.
    """
    # Load results
    results = load_accuracy_results(results_path)
    
    # Perform analysis
    analysis = analyze_model_performance(
        results['experimental'],
        results['baseline'],
        alpha
    )
    
    # Save report
    save_analysis_report(analysis, output_path)
    
    return analysis

def main():
    """
    Main function to run statistical analysis on model comparison results.
    
    This function loads accuracy results from data/results/accuracies.json,
    performs Wilcoxon signed-rank test, and saves the analysis report to
    data/results/statistical_analysis.json.
    """
    config = Config()
    
    results_path = config.data_dir / "results" / "accuracies.json"
    output_path = config.data_dir / "results" / "statistical_analysis.json"
    
    if not results_path.exists():
        logger.error(f"Results file not found: {results_path}")
        logger.error("Please run experiments first to generate accuracy results.")
        return
        
    logger.info(f"Loading results from: {results_path}")
    logger.info(f"Output will be saved to: {output_path}")
    
    try:
        analysis = load_and_analyze(
            results_path=str(results_path),
            output_path=str(output_path),
            alpha=config.statistical_alpha
        )
        
        logger.info("Analysis complete!")
        logger.info(f"Mean difference: {analysis['accuracy_difference']:.6f}")
        logger.info(f"P-value: {analysis['wilcoxon_test']['pvalue']:.6f}")
        logger.info(f"Significant: {analysis['wilcoxon_test']['significant']}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()