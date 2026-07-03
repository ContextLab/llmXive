import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from scipy import stats

# Import existing utilities from the project
from evaluation.stats import load_recall_results, check_normality, perform_paired_ttest, perform_wilcoxon_signed_rank, compute_cohens_d, compute_cohens_d_confidence_interval, get_cohen_interpretation, run_analysis_for_dataset
from utils.logger import load_run_summary


def generate_statistical_summary(
    results_dir: Path,
    datasets: List[str] = ["babi", "lambada", "story_cloze"]
) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical summary report for all datasets.
    
    This function loads recall results from previous runs, performs statistical
    analyses (t-tests or Wilcoxon signed-rank tests), calculates effect sizes,
    and applies multiple comparison corrections.
    
    Args:
        results_dir: Path to the directory containing recall results
        datasets: List of dataset names to analyze
        
    Returns:
        Dictionary containing the complete statistical summary
    """
    summary = {
        "datasets": {},
        "correction_method": "holm-bonferroni",
        "total_comparisons": len(datasets),
        "analysis_timestamp": None
    }
    
    # Load recall results
    recall_data = load_recall_results(results_dir)
    
    if not recall_data:
        raise ValueError("No recall results found in the specified directory")
    
    # Perform analysis for each dataset
    dataset_results = []
    for dataset_name in datasets:
        if dataset_name not in recall_data:
            continue
            
        # Run statistical analysis for this dataset
        analysis_result = run_analysis_for_dataset(
            recall_data[dataset_name],
            dataset_name
        )
        
        if analysis_result:
            dataset_results.append(analysis_result)
            summary["datasets"][dataset_name] = analysis_result
    
    # Apply multiple comparison correction
    if dataset_results:
        p_values = [r["p_value"] for r in dataset_results]
        
        # Holm-Bonferroni correction
        corrected_p_values = stats.multipletests(
            p_values, 
            method='holm'
        )[1]
        
        # Update results with corrected p-values
        for i, dataset_name in enumerate(summary["datasets"].keys()):
            summary["datasets"][dataset_name]["corrected_p_value"] = float(corrected_p_values[i])
            summary["datasets"][dataset_name]["is_significant_after_correction"] = corrected_p_values[i] < 0.05
    
    # Calculate overall statistics
    if dataset_results:
        all_p_values = [r["p_value"] for r in dataset_results]
        all_effect_sizes = [r["effect_size"] for r in dataset_results]
        
        summary["overall"] = {
            "min_p_value": float(min(all_p_values)),
            "max_p_value": float(max(all_p_values)),
            "mean_effect_size": float(np.mean(all_effect_sizes)),
            "significant_results": sum(1 for p in all_p_values if p < 0.05),
            "significant_after_correction": sum(1 for r in summary["datasets"].values() if r.get("is_significant_after_correction", False))
        }
    
    return summary


def save_statistical_summary(
    summary: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save the statistical summary to a JSON file.
    
    Args:
        summary: The statistical summary dictionary
        output_path: Path where the summary should be saved
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"Statistical summary saved to {output_path}")


def main():
    """Main entry point for generating statistical summary."""
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / "artifacts" / "results"
    output_file = results_dir / "statistical_summary.json"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating statistical summary...")
    
    try:
        # Generate summary
        summary = generate_statistical_summary(results_dir)
        
        # Save to file
        save_statistical_summary(summary, output_file)
        
        print(f"Statistical summary generated successfully!")
        print(f"Datasets analyzed: {list(summary['datasets'].keys())}")
        
        if "overall" in summary:
            print(f"Significant results: {summary['overall']['significant_results']}/{summary['total_comparisons']}")
            print(f"Significant after correction: {summary['overall']['significant_after_correction']}/{summary['total_comparisons']}")
            
    except Exception as e:
        print(f"Error generating statistical summary: {str(e)}")
        raise


if __name__ == "__main__":
    main()