"""
Evaluation script for Dream-State Learning project.

This script orchestrates the evaluation phase, loading results from training
runs and generating comparative analysis reports.

Usage:
    python code/eval.py --results-dir data/results/
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from utils.logger import get_logger
from eval.statistical_analysis import load_accuracy_results, run_ttest_paired, analyze_model_performance, save_analysis_report
from eval.reporting import save_comparison_report, generate_interpretation
from eval.sensitivity_report import load_temperature_sweep_results, compute_variance_metrics, generate_sensitivity_report

logger = get_logger(__name__)

def load_training_results(results_dir: Path) -> Dict[str, Any]:
    """
    Load all training result files from the specified directory.
    
    Args:
        results_dir: Path to the directory containing result JSON files
        
    Returns:
        Dictionary mapping seed/model type to result data
    """
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    
    results = {}
    result_files = list(results_dir.glob("*.json"))
    
    if not result_files:
        logger.warning(f"No JSON files found in {results_dir}")
        return results
    
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
                # Use filename as key
                key = result_file.stem
                results[key] = data
                logger.info(f"Loaded results from {result_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {result_file}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error loading {result_file}: {e}")
            continue
    
    return results

def run_statistical_analysis(results: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """
    Run statistical analysis on the loaded results.
    
    Args:
        results: Dictionary of training results
        config: Configuration object
        
    Returns:
        Analysis results dictionary
    """
    # Separate experimental and baseline results
    experimental_results = []
    baseline_results = []
    
    for key, data in results.items():
        if 'experimental' in key.lower() or 'dream' in key.lower():
            if 'accuracy' in data:
                experimental_results.append(data['accuracy'])
        elif 'baseline' in key.lower() or 'wake' in key.lower():
            if 'accuracy' in data:
                baseline_results.append(data['accuracy'])
    
    if len(experimental_results) < 2 or len(baseline_results) < 2:
        logger.warning("Insufficient results for paired statistical analysis")
        return {
            'error': 'Insufficient results for paired analysis',
            'experimental_count': len(experimental_results),
            'baseline_count': len(baseline_results)
        }
    
    # Run paired t-test
    t_stat, p_value = run_ttest_paired(experimental_results, baseline_results)
    
    analysis = {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'experimental_mean': float(sum(experimental_results) / len(experimental_results)),
        'baseline_mean': float(sum(baseline_results) / len(baseline_results)),
        'experimental_count': len(experimental_results),
        'baseline_count': len(baseline_results),
        'significance_level': config.get('significance_level', 0.05),
        'is_significant': p_value < config.get('significance_level', 0.05)
    }
    
    return analysis

def generate_evaluation_report(results: Dict[str, Any], analysis: Dict[str, Any], output_dir: Path) -> Path:
    """
    Generate and save the evaluation report.
    
    Args:
        results: Raw training results
        analysis: Statistical analysis results
        output_dir: Directory to save the report
        
    Returns:
        Path to the saved report
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        'timestamp': str(Path(output_dir).parent),
        'results_summary': {
            'total_runs': len(results),
            'files_processed': list(results.keys())
        },
        'statistical_analysis': analysis,
        'interpretation': generate_interpretation(analysis)
    }
    
    report_path = output_dir / 'evaluation_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Evaluation report saved to {report_path}")
    return report_path

def main():
    """Main entry point for the evaluation script."""
    parser = argparse.ArgumentParser(
        description='Evaluate Dream-State Learning training results'
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='data/results/',
        help='Directory containing training result files (default: data/results/)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/results/',
        help='Directory to save evaluation report (default: data/results/)'
    )
    
    args = parser.parse_args()
    
    # Initialize configuration
    config = Config()
    
    # Load results
    logger.info(f"Loading results from {args.results_dir}")
    results = load_training_results(Path(args.results_dir))
    
    if not results:
        logger.error("No results found to evaluate")
        sys.exit(1)
    
    logger.info(f"Loaded {len(results)} result files")
    
    # Run statistical analysis
    logger.info("Running statistical analysis")
    analysis = run_statistical_analysis(results, config)
    
    # Generate and save report
    logger.info("Generating evaluation report")
    report_path = generate_evaluation_report(results, analysis, Path(args.output_dir))
    
    # Print summary
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    print(f"Total runs analyzed: {len(results)}")
    if 'p_value' in analysis:
        print(f"Paired t-test p-value: {analysis['p_value']:.4f}")
        print(f"Statistically significant (α={config.get('significance_level', 0.05)}): {analysis.get('is_significant', False)}")
    print(f"Report saved to: {report_path}")
    print("="*50)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())