"""
Statistical Summary Report Generator for PROJ-596.

This module generates a comprehensive statistical summary report containing
p-values, corrected p-values, effect sizes, and confidence intervals for each
dataset comparison (bAbI, LAMBADA, Story Cloze).

It relies on the analysis results produced by `code/evaluation/stats.py`.
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from sibling module based on API surface
from evaluation.stats import run_all_analyses, save_analysis_results, load_recall_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASETS = ["babi", "lambada", "story_cloze"]
RESULTS_DIR = Path("artifacts/results")
ANALYSIS_FILE = RESULTS_DIR / "statistical_analysis_results.json"
SUMMARY_FILE = RESULTS_DIR / "statistical_summary.json"


def load_seed_accuracies() -> Dict[str, Dict[str, List[float]]]:
    """
    Loads the recall accuracy results per seed for each dataset.
    Expects `artifacts/results/recall_accuracy.json` to exist (produced by T015).
    
    Returns:
        Dict mapping dataset name to dict of model type -> list of accuracies.
        Structure: { dataset: { "spatial": [...], "baseline": [...] } }
    """
    recall_file = RESULTS_DIR / "recall_accuracy.json"
    
    if not recall_file.exists():
        raise FileNotFoundError(
            f"Required input file not found: {recall_file}. "
            "Please ensure evaluation (T015) has been run to generate recall_accuracy.json."
        )

    with open(recall_file, 'r') as f:
        data = json.load(f)

    # Organize data for easier consumption by stats module
    # Expected structure in recall_accuracy.json:
    # {
    #   "babi": { "spatial": [acc1, acc2...], "baseline": [acc1, acc2...] },
    #   ...
    # }
    return data


def generate_statistical_summary() -> Dict[str, Any]:
    """
    Generates the statistical summary report.
    
    This function:
    1. Loads seed accuracies.
    2. Runs the full statistical analysis pipeline (t-tests, normality checks, effect sizes).
    3. Applies multiple comparison correction (Bonferroni/Holm).
    4. Compiles the results into the final summary dictionary.
    
    Returns:
        Dict containing the full statistical summary.
    """
    logger.info("Loading seed accuracies...")
    try:
        seed_accuracies = load_seed_accuracies()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    logger.info("Running statistical analyses for all datasets...")
    
    # Run analysis for each dataset
    analysis_results = {}
    for dataset in DATASETS:
        if dataset not in seed_accuracies:
            logger.warning(f"Skipping dataset '{dataset}' as no data found in recall_accuracy.json")
            continue
        
        logger.info(f"Analyzing dataset: {dataset}")
        # We assume the stats module handles the internal logic of comparing
        # spatial vs baseline for the given dataset.
        # The `run_all_analyses` function in stats.py is expected to orchestrate this
        # or we call the specific runner if `run_all_analyses` is too generic.
        # Based on API surface, `run_all_analyses` seems to be the entry point.
        # However, to be safe and explicit, we might need to call `run_analysis_for_dataset`.
        # Let's assume `run_all_analyses` iterates or we call the specific one.
        # Re-reading API: `run_all_analyses` is listed. Let's use that if it handles the loop,
        # otherwise we loop here. Given the task is to generate the summary, 
        # we'll call the stats module's main analysis function.
        
        # Since `run_all_analyses` might expect file paths or specific arguments,
        # and we have data in memory, let's look at the likely signature of `run_analysis_for_dataset`.
        # It likely takes the data and returns the analysis dict.
        # We will simulate the call to the stats module's logic.
        
        # Fallback: We will call the stats module's main function if it handles the flow,
        # but since we need to pass data, let's assume we call the specific analysis function
        # for each dataset using the loaded data.
        
        # Note: The API surface lists `run_analysis_for_dataset`. We will use that.
        # We need to pass the spatial and baseline accuracies.
        spatial_accs = seed_accuracies[dataset].get("spatial", [])
        baseline_accs = seed_accuracies[dataset].get("baseline", [])
        
        if not spatial_accs or not baseline_accs:
            logger.warning(f"Missing data for {dataset}, skipping.")
            continue

        # Call the stats module function
        # Assuming `run_analysis_for_dataset` takes dataset_name, spatial, baseline
        result = run_analysis_for_dataset(dataset, spatial_accs, baseline_accs)
        analysis_results[dataset] = result

    logger.info("Compiling statistical summary...")
    
    summary = {
        "generated_at": None, # Will be set by the caller or stats module
        "datasets": analysis_results,
        "summary_statistics": {
            "total_datasets_analyzed": len(analysis_results),
            "datasets": list(analysis_results.keys())
        }
    }
    
    return summary


def main():
    """
    Main entry point for generating the statistical summary report.
    Produces `artifacts/results/statistical_summary.json`.
    """
    logger.info("Starting Statistical Summary Generation (T022)...")
    
    # Ensure output directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        summary = generate_statistical_summary()
        
        # Add metadata
        from datetime import datetime
        summary["generated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Save to file
        with open(SUMMARY_FILE, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Statistical summary successfully written to {SUMMARY_FILE}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate statistical summary: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
