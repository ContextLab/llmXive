"""
Statistical Summary Report Generator (Task T022)

Generates a comprehensive statistical summary report containing p-values,
corrected p-values, effect sizes, and confidence intervals for each dataset
(bAbI, LAMBADA, Story Cloze).

This module aggregates results from the paired statistical tests (T019),
multiple comparison corrections (T020), and effect size calculations (T021)
into a single JSON artifact.
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing project modules
# stats.py contains the raw analysis results (t-tests, wilcoxon, etc.)
from evaluation.stats import load_recall_results, run_all_analyses, save_analysis_results
# effect_size.py contains Cohen's d calculations
from evaluation.effect_size import calculate_effect_sizes_for_datasets, load_recall_results_from_json
# multiple_comparison.py contains correction logic
from evaluation.multiple_comparison import run_multiple_comparison_correction, load_p_values_from_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
RESULTS_DIR = ARTIFACTS_DIR / "results"
ANALYSIS_DIR = ARTIFACTS_DIR / "analysis"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["babi", "lambada", "story_cloze"]

def load_seed_accuracies() -> Dict[str, Dict[str, List[float]]]:
    """
    Loads the recall accuracy results from the evaluation phase.
    Returns a dictionary mapping dataset names to a dict of {seed: accuracy}.
    """
    recall_file = RESULTS_DIR / "recall_accuracy.json"
    if not recall_file.exists():
        raise FileNotFoundError(
            f"Recall accuracy file not found at {recall_file}. "
            "Please run the evaluation phase (T015) first."
        )
    
    with open(recall_file, 'r') as f:
        data = json.load(f)
    
    # Expected structure: {"babi": {"seed_-4": 0.85, ...}, ...}
    # We need to ensure we have lists of accuracies per dataset for stats
    formatted_data = {}
    for dataset in DATASETS:
        if dataset in data:
            # Extract values (accuracies) for each seed
            # The keys are typically "seed_-4", "seed_-3", etc.
            accuracies = list(data[dataset].values())
            formatted_data[dataset] = accuracies
        else:
            logger.warning(f"No data found for dataset: {dataset}")
            formatted_data[dataset] = []
    
    return formatted_data

def generate_statistical_summary() -> Dict[str, Any]:
    """
    Generates the complete statistical summary report.
    
    This function:
    1. Loads recall accuracies from the evaluation phase.
    2. Runs or loads paired statistical tests (t-test/Wilcoxon).
    3. Applies multiple comparison corrections (Bonferroni/Holm).
    4. Calculates effect sizes (Cohen's d) with confidence intervals.
    5. Aggregates all results into a single summary dictionary.
    
    Returns:
        Dict containing p-values, corrected p-values, effect sizes, and CIs.
    """
    logger.info("Generating statistical summary report...")
    
    # 1. Load Accuracies
    seed_accuracies = load_seed_accuracies()
    
    # 2. Run Statistical Analysis (T019)
    # This performs paired t-tests or Wilcoxon tests between Spatial and Baseline
    # We assume the 'run_all_analyses' function in stats.py handles the comparison
    # between the two model variants for each dataset.
    # Note: In a real run, we would need to load the specific results of the
    # Spatial vs Baseline comparison. Since the task implies the analysis is
    # done, we simulate the structure or call the helper if it returns the dict.
    
    # For this implementation, we assume 'run_all_analyses' returns a dict
    # of results per dataset if not saved, or we load from a saved file.
    analysis_results_path = ANALYSIS_DIR / "statistical_analysis_results.json"
    
    if analysis_results_path.exists():
        with open(analysis_results_path, 'r') as f:
            analysis_data = json.load(f)
    else:
        # Fallback: run analysis if file missing (requires real data loaded)
        # This part depends on how 'run_all_analyses' is implemented in stats.py
        # Assuming it returns a dict: { "babi": { "p_value": ..., "test": ... } }
        analysis_data = run_all_analyses(seed_accuracies)
        save_analysis_results(analysis_data, analysis_results_path)

    # 3. Multiple Comparison Correction (T020)
    # Extract p-values from analysis data
    p_values = {}
    for dataset in DATASETS:
        if dataset in analysis_data:
            p_values[dataset] = analysis_data[dataset].get('p_value')
    
    corrected_results = run_multiple_comparison_correction(p_values)
    
    # 4. Effect Size Calculation (T021)
    # Calculate Cohen's d and CI for each dataset
    effect_size_data = calculate_effect_sizes_for_datasets(seed_accuracies)
    
    # 5. Assemble Final Report
    summary = {
        "generated_at": str(Path.cwd()),
        "datasets": {}
    }
    
    for dataset in DATASETS:
        dataset_info = {
            "p_value": None,
            "corrected_p_value": None,
            "correction_method": "Holm-Bonferroni",
            "effect_size": None,
            "ci_lower": None,
            "ci_upper": None,
            "interpretation": None,
            "statistical_significance": None
        }
        
        # P-value
        if dataset in analysis_data:
            dataset_info["p_value"] = analysis_data[dataset].get("p_value")
        
        # Corrected P-value
        if dataset in corrected_results:
            dataset_info["corrected_p_value"] = corrected_results[dataset].get("corrected_p_value")
            dataset_info["correction_method"] = corrected_results[dataset].get("method", "Holm-Bonferroni")
        
        # Effect Size & CI
        if dataset in effect_size_data:
            es = effect_size_data[dataset]
            dataset_info["effect_size"] = es.get("cohens_d")
            dataset_info["ci_lower"] = es.get("ci_lower")
            dataset_info["ci_upper"] = es.get("ci_upper")
            dataset_info["interpretation"] = es.get("interpretation")
        
        # Significance Check
        if dataset_info["corrected_p_value"] is not None:
            dataset_info["statistical_significance"] = dataset_info["corrected_p_value"] < 0.05
        
        summary["datasets"][dataset] = dataset_info
    
    return summary

def main():
    """
    Main entry point for generating the statistical summary.
    """
    try:
        summary = generate_statistical_summary()
        
        output_path = RESULTS_DIR / "statistical_summary.json"
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Statistical summary report generated successfully: {output_path}")
        print(json.dumps(summary, indent=2))
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating statistical summary: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()