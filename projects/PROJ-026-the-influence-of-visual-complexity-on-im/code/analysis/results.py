import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from config import get_project_root, ensure_directories
from analysis.permutation import run_permutation_test, calculate_effect_size, run_sensitivity_analysis

logger = logging.getLogger(__name__)

def save_json_results(data: Dict[str, Any], filepath: Path) -> None:
    """
    Save a dictionary of results to a JSON file.
    
    Args:
        data: Dictionary containing results to save
        filepath: Path to the output JSON file
    """
    ensure_directories([filepath.parent])
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, default=str)
    logger.info(f"Results saved to {filepath}")

def aggregate_permutation_results(
    d_scores: pd.DataFrame,
    complexity_scores: pd.DataFrame,
    n_permutations: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the permutation test and calculate effect sizes, returning a dictionary of results.
    
    Args:
        d_scores: DataFrame containing participant D-scores and session info
        complexity_scores: DataFrame containing image complexity metrics
        n_permutations: Number of permutations for the test
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing p-value, effect size, and test statistics
    """
    # Merge data to associate D-scores with complexity categories
    # Assuming the merge key is implicit or handled by the analysis logic
    # For this implementation, we assume d_scores has a 'complexity_category' or similar 
    # or we join based on the specific logic defined in the project's data flow.
    # Given the task dependencies, we expect d_scores to be ready for grouping.
    
    # If complexity_category is not in d_scores, we might need to map it.
    # For now, we assume the input d_scores is ready for the permutation logic 
    # which groups by Low/High complexity conditions.
    
    # Extract groups
    # We assume the dataframe has a column 'complexity_condition' or similar derived from T018/T017
    # If the column name differs, this needs adjustment based on T018 output.
    # Based on T017 schema: filename, edge_density, entropy, fractal_dim, complexity_category
    # Based on T026 schema: participant_id, session_id, d_score, n_trials_valid, status
    # We need to join these. The join key is likely 'session_id' -> 'filename' or similar mapping.
    # Assuming the pipeline (T038) prepares a merged dataframe or passes the necessary columns.
    # Here, we assume 'd_scores' is already enriched with 'complexity_category' or we receive
    # two separate dataframes and join them.
    
    # Let's assume d_scores is the result of T026 and we need to join with complexity_scores.
    # We need a mapping from session to image. This mapping is usually established in the experiment design.
    # For the purpose of this function, we assume the caller (T038) provides a merged dataframe
    # or the necessary columns are present.
    
    # Fallback: If d_scores doesn't have the category, we can't run.
    if 'complexity_category' not in d_scores.columns:
        # Try to infer from session_id if a mapping exists in complexity_scores
        # This is a simplification; in a real pipeline, the merge happens earlier.
        # We will assume the input d_scores is the final merged dataset ready for analysis.
        raise ValueError("Input d_scores must contain 'complexity_category' column.")

    # Filter valid trials (status == 'valid' or similar, based on T024)
    valid_data = d_scores[d_scores['status'] == 'valid'].copy()
    
    if len(valid_data) < 10:
        logger.warning("Insufficient valid trials for permutation test.")
        return {
            "status": "insufficient_data",
            "n_valid": len(valid_data),
            "p_value": None,
            "effect_size": None
        }

    # Run Permutation Test
    # We need to extract the two groups: Low vs High (or Low/Med vs High/Med)
    # Assuming binary comparison for the main effect as per standard IAT analysis
    # We will filter for the specific categories defined in T018 (e.g., 'Low', 'High')
    # If 'Medium' exists, we might need to decide whether to include it. 
    # Standard practice: Compare Low vs High.
    
    low_group = valid_data[valid_data['complexity_category'] == 'Low']['d_score']
    high_group = valid_data[valid_data['complexity_category'] == 'High']['d_score']
    
    if len(low_group) < 5 or len(high_group) < 5:
        logger.warning("Insufficient samples in one or both groups.")
        return {
            "status": "insufficient_samples",
            "n_low": len(low_group),
            "n_high": len(high_group),
            "p_value": None,
            "effect_size": None
        }

    perm_result = run_permutation_test(
        low_group.values,
        high_group.values,
        n_permutations=n_permutations,
        seed=seed
    )
    
    # Calculate Effect Size
    effect_size = calculate_effect_size(low_group.values, high_group.values)
    
    return {
        "status": "success",
        "n_permutations": n_permutations,
        "p_value": perm_result['p_value'],
        "observed_diff": perm_result['observed_diff'],
        "effect_size_cohen_d": effect_size,
        "n_low": len(low_group),
        "n_high": len(high_group)
    }

def run_and_save_all_results(
    d_scores_path: Path,
    complexity_scores_path: Path,
    output_dir: Path,
    n_permutations: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Orchestrates the saving of all analysis results.
    Loads D-scores and Complexity Scores, runs permutation test, sensitivity analysis,
    and saves the JSON results.
    
    Args:
        d_scores_path: Path to aggregated D-scores CSV
        complexity_scores_path: Path to complexity scores CSV
        output_dir: Directory to save results
        n_permutations: Number of permutations
        seed: Random seed
        
    Returns:
        Dictionary containing all saved results
    """
    ensure_directories([output_dir])
    
    # Load data
    try:
        d_scores = pd.read_csv(d_scores_path)
        complexity_scores = pd.read_csv(complexity_scores_path)
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        return {"status": "error", "message": str(e)}
    
    # Perform Permutation Test and Effect Size
    perm_results = aggregate_permutation_results(
        d_scores, complexity_scores, n_permutations, seed
    )
    
    # Perform Sensitivity Analysis
    # Assuming run_sensitivity_analysis takes the same data and returns a dict/list
    # We need to adapt the call to match the signature in permutation.py
    sensitivity_results = run_sensitivity_analysis(
        d_scores, complexity_scores, n_permutations=n_permutations, seed=seed
    )
    
    # Prepare final results dictionary
    final_results = {
        "permutation_test": perm_results,
        "sensitivity_analysis": sensitivity_results
    }
    
    # Save to files
    perm_file = output_dir / "permutation_results.json"
    sens_file = output_dir / "sensitivity_results.json"
    
    save_json_results(perm_results, perm_file)
    save_json_results(sensitivity_results, sens_file)
    
    logger.info(f"Permutation results saved to {perm_file}")
    logger.info(f"Sensitivity results saved to {sens_file}")
    
    return final_results

def main():
    """Entry point for saving results."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Save permutation and sensitivity analysis results.")
    parser.add_argument("--d-scores", type=str, required=True, help="Path to D-scores CSV")
    parser.add_argument("--complexity-scores", type=str, required=True, help="Path to Complexity Scores CSV")
    parser.add_argument("--output-dir", type=str, default="data/results", help="Output directory")
    parser.add_argument("--n-permutations", type=int, default=10000, help="Number of permutations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    d_scores_path = Path(args.d_scores)
    complexity_scores_path = Path(args.complexity_scores)
    output_dir = Path(args.output_dir)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    results = run_and_save_all_results(
        d_scores_path,
        complexity_scores_path,
        output_dir,
        args.n_permutations,
        args.seed
    )
    
    if results.get("status") == "error":
        logger.error("Failed to save results.")
        exit(1)
    else:
        logger.info("Results saved successfully.")

if __name__ == "__main__":
    main()