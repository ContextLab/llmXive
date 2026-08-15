import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from config import get_project_root, get_data_path
from .permutation import run_permutation_test, calculate_effect_size, run_sensitivity_analysis, calculate_power

logger = logging.getLogger(__name__)

def save_json_results(data: Dict[str, Any], filepath: Path) -> None:
    """
    Save a dictionary of results to a JSON file.
    
    Args:
        data: Dictionary containing results to save.
        filepath: Path to the output JSON file.
    """
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Results saved to {filepath}")

def aggregate_permutation_results(
    d_scores_df: pd.DataFrame,
    complexity_df: pd.DataFrame,
    n_permutations: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the permutation test and calculate effect sizes.
    
    Args:
        d_scores_df: DataFrame with participant D-scores.
        complexity_df: DataFrame with image complexity categories.
        n_permutations: Number of permutations for the test.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing permutation test results and effect sizes.
    """
    # Merge data to get complexity category for each response
    # Assuming d_scores_df has 'participant_id' and complexity_df links images to complexity
    # We need to map the session/image to complexity. 
    # For this implementation, we assume the d_scores_df already contains the complexity 
    # condition (Low/High) derived from the session design or image mapping.
    # If not, we would need to join with the stimuli processing results.
    
    # Check if complexity column exists, if not, we might need to join
    if 'complexity_category' not in d_scores_df.columns:
        # Attempt to join with complexity_df if it has participant/image mapping
        # This is a simplified assumption: d_scores_df should have the condition
        logger.warning("complexity_category not found in d_scores_df. "
                     "Assuming it needs to be derived or joined.")
        # In a full pipeline, we would perform the join here.
        # For now, we assume the data is prepared correctly by T026/T033 dependencies.
        raise ValueError("Input d_scores_df must contain 'complexity_category' or be joinable.")

    # Run permutation test
    perm_result = run_permutation_test(
        d_scores_df, 
        'd_score', 
        'complexity_category', 
        n_permutations=n_permutations, 
        seed=seed
    )
    
    # Calculate effect size (Cohen's d)
    effect_size = calculate_effect_size(
        d_scores_df, 
        'd_score', 
        'complexity_category'
    )
    
    # Calculate power
    # We need sample size N and effect size
    n_total = len(d_scores_df)
    power_result = calculate_power(effect_size, alpha=0.05, n=n_total)
    
    return {
        "permutation_test": {
            "p_value": float(perm_result['p_value']),
            "observed_statistic": float(perm_result['observed_statistic']),
            "n_permutations": n_permutations,
            "seed": seed
        },
        "effect_size": {
            "cohen_d": float(effect_size['cohen_d']),
            "interpretation": effect_size['interpretation']
        },
        "power_analysis": {
            "power_value": float(power_result['power_value']),
            "target": 0.8,
            "status": "pass" if power_result['power_value'] >= 0.8 else "fail",
            "sample_size": n_total
        },
        "metadata": {
            "total_participants": n_total,
            "timestamp": pd.Timestamp.now().isoformat()
        }
    }

def run_and_save_all_results(
    d_scores_path: Optional[str] = None,
    complexity_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    n_permutations: int = 10000,
    seed: int = 42
) -> Dict[str, str]:
    """
    Main function to load data, run analyses, and save all result files.
    
    Args:
        d_scores_path: Path to aggregated D-scores CSV.
        complexity_path: Path to complexity scores CSV (if needed for join).
        output_dir: Directory to save results.
        n_permutations: Number of permutations.
        seed: Random seed.
        
    Returns:
        Dictionary mapping result types to file paths.
    """
    project_root = get_project_root()
    
    # Default paths if not provided
    if d_scores_path is None:
        d_scores_path = str(project_root / "data" / "processed" / "aggregated_d_scores.csv")
    if output_dir is None:
        output_dir = str(project_root / "data" / "results")
        
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading D-scores from {d_scores_path}")
    if not Path(d_scores_path).exists():
        raise FileNotFoundError(f"Data file not found: {d_scores_path}")
        
    d_scores_df = pd.read_csv(d_scores_path)
    
    # Filter out invalid trials/participants if marked
    valid_df = d_scores_df[d_scores_df['status'] == 'valid'].copy()
    
    if len(valid_df) == 0:
        raise ValueError("No valid participant data found to analyze.")
    
    logger.info(f"Running permutation test on {len(valid_df)} valid records...")
    
    # 1. Permutation Results
    perm_results = aggregate_permutation_results(
        valid_df, 
        None, 
        n_permutations=n_permutations, 
        seed=seed
    )
    
    perm_file = output_path / "permutation_results.json"
    save_json_results(perm_results, perm_file)
    
    # 2. Sensitivity Analysis
    logger.info("Running sensitivity analysis...")
    sensitivity_results = run_sensitivity_analysis(
        valid_df,
        'd_score',
        'complexity_category',
        n_permutations=n_permutations,
        seed=seed
    )
    
    sens_file = output_path / "sensitivity_results.json"
    save_json_results(sensitivity_results, sens_file)
    
    return {
        "permutation_results": str(perm_file),
        "sensitivity_results": str(sens_file)
    }

def main():
    """Entry point for CLI execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Save analysis results to JSON.")
    parser.add_argument("--d-scores", type=str, help="Path to aggregated D-scores CSV")
    parser.add_argument("--n-permutations", type=int, default=10000, help="Number of permutations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, help="Output directory for results")
    
    args = parser.parse_args()
    
    setup_logger = logging.getLogger(__name__)
    setup_logger.setLevel(logging.INFO)
    if not setup_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        setup_logger.addHandler(handler)
    
    try:
        results = run_and_save_all_results(
            d_scores_path=args.d_scores,
            n_permutations=args.n_permutations,
            seed=args.seed,
            output_dir=args.output_dir
        )
        print(f"Analysis complete. Results saved to:")
        for k, v in results.items():
            print(f"  {k}: {v}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()