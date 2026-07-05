import os
import csv
import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np

from config import get_path, set_seed, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_human_rated_ambiguity(ambiguity_file: Optional[str] = None) -> pd.DataFrame:
    """
    Load human-rated ambiguity scores from external verified sources.
    Returns an empty DataFrame if file is missing or unavailable.
    """
    if ambiguity_file is None:
        ambiguity_file = str(get_path("data/processed/human_rated_ambiguity.csv"))
    
    path = Path(ambiguity_file)
    if not path.exists():
        logger.info(f"Human rated ambiguity file not found at {path}. Returning empty DataFrame.")
        return pd.DataFrame(columns=['stimulus_id', 'ambiguity_score'])
    
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} human-rated ambiguity scores from {path}")
        return df
    except Exception as e:
        logger.error(f"Error loading human rated ambiguity: {e}")
        return pd.DataFrame(columns=['stimulus_id', 'ambiguity_score'])

def aggregate_human_ratings(human_df: pd.DataFrame) -> Dict[str, float]:
    """
    Aggregate human ratings to a dictionary: {stimulus_id: mean_ambiguity}
    """
    if human_df.empty:
        return {}
    return human_df.groupby('stimulus_id')['ambiguity_score'].mean().to_dict()

def derive_synthetic_ambiguity(linked_trials_path: str, output_path: str) -> pd.DataFrame:
    """
    Derive synthetic ambiguity scores if human ratings are unavailable.
    Uses a simple heuristic: variance in response times per stimulus as a proxy for ambiguity.
    """
    logger.info("Deriving synthetic ambiguity scores...")
    
    if not os.path.exists(linked_trials_path):
        raise FileNotFoundError(f"Linked trials file not found: {linked_trials_path}")
    
    df = pd.read_csv(linked_trials_path)
    
    # Heuristic: Higher variance in RTs for a stimulus implies higher ambiguity
    # Group by stimulus_id and calculate variance of response_time
    if 'stimulus_id' not in df.columns or 'response_time' not in df.columns:
        raise ValueError("Linked trials must contain 'stimulus_id' and 'response_time' columns")
    
    stats = df.groupby('stimulus_id')['response_time'].agg(['mean', 'std', 'count']).reset_index()
    stats.columns = ['stimulus_id', 'mean_rt', 'rt_std', 'trial_count']
    
    # Normalize std to 0-1 range for ambiguity score
    max_std = stats['rt_std'].max()
    if max_std == 0:
        stats['ambiguity_score'] = 0.0
    else:
        stats['ambiguity_score'] = stats['rt_std'] / max_std
    
    # Filter out stimuli with insufficient trials
    stats = stats[stats['trial_count'] >= 3]
    
    stats[['stimulus_id', 'ambiguity_score']].to_csv(output_path, index=False)
    logger.info(f"Saved {len(stats)} synthetic ambiguity scores to {output_path}")
    return stats[['stimulus_id', 'ambiguity_score']]

def check_confounding(linked_trials_path: str, output_path: str) -> Dict[str, Any]:
    """
    Check if 'prime' condition is confounded with trial order or block structure.
    Outputs a JSON report with correlation matrix and trial-order check results.
    
    Logic:
    1. Load linked_trials.csv
    2. Ensure 'trial_id' is numeric or sortable. If string, try to extract numeric part or sort by appearance.
    3. Calculate correlation between trial_order (numeric index) and prime_condition (encoded).
    4. If correlation is high (> 0.3 absolute), flag as potential confound.
    5. Save report to output_path.
    """
    logger.info(f"Running confounding check on {linked_trials_path}...")
    
    if not os.path.exists(linked_trials_path):
        raise FileNotFoundError(f"Linked trials file not found: {linked_trials_path}")
    
    df = pd.read_csv(linked_trials_path)
    
    required_cols = ['trial_id', 'prime_condition']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Linked trials must contain columns: {required_cols}")
    
    # Create a numeric trial order based on appearance or parsed ID
    # Try to parse trial_id as int, otherwise use index
    if pd.api.types.is_numeric_dtype(df['trial_id']):
        trial_order = df['trial_id'].values
    else:
        # Try to extract digits
        try:
            trial_order = df['trial_id'].astype(str).str.extract(r'(\d+)')[0].astype(float).values
        except:
            trial_order = np.arange(len(df))
    
    # Encode prime_condition if categorical
    if not pd.api.types.is_numeric_dtype(df['prime_condition']):
        df['prime_condition_encoded'] = pd.factorize(df['prime_condition'])[0]
    else:
        df['prime_condition_encoded'] = df['prime_condition']
    
    # Calculate correlation
    correlation = np.corrcoef(trial_order, df['prime_condition_encoded'])[0, 1]
    
    # Determine if confounded (threshold 0.3)
    is_confounded = abs(correlation) > 0.3
    
    # Build report
    report = {
        "confounding_check": {
            "method": "Pearson correlation between trial order and prime condition",
            "correlation_coefficient": float(correlation),
            "threshold": 0.3,
            "is_confounded": bool(is_confounded),
            "sample_size": len(df),
            "trial_id_type": str(type(df['trial_id'].iloc[0]).__name__)
        },
        "correlation_matrix": {
            "trial_order_vs_prime_condition": float(correlation)
        },
        "recommendation": "Proceed with analysis" if not is_confounded else "WARNING: Potential confound detected. Consider blocking or randomization checks."
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Confounding check complete. Report saved to {output_path}")
    if is_confounded:
        logger.warning(f"High correlation ({correlation:.3f}) detected between trial order and prime condition.")
    else:
        logger.info(f"No significant confounding detected (correlation: {correlation:.3f}).")
    
    return report

def run_preprocessing(
    linked_trials_path: Optional[str] = None,
    ambiguity_output_path: Optional[str] = None,
    confounding_output_path: Optional[str] = None,
    use_synthetic_ambiguity: bool = True
) -> Dict[str, Any]:
    """
    Orchestrate preprocessing: load/derive ambiguity and run confounding checks.
    """
    if linked_trials_path is None:
        linked_trials_path = str(get_path("data/processed/linked_trials.csv"))
    if ambiguity_output_path is None:
        ambiguity_output_path = str(get_path("data/processed/stimulus_metadata.csv"))
    if confounding_output_path is None:
        confounding_output_path = str(get_path("data/processed/confounding_report.json"))
    
    ensure_directories()
    
    results = {}
    
    # 1. Check for human-rated ambiguity
    human_df = load_human_rated_ambiguity()
    
    if human_df.empty and not use_synthetic_ambiguity:
        logger.error("No human-rated ambiguity available and synthetic derivation disabled. Halting.")
        raise RuntimeError("Data Gap: Ambiguity derivation failed (human ratings missing, synthetic disabled).")
    
    if human_df.empty:
        logger.info("No human ratings found. Deriving synthetic ambiguity.")
        derive_synthetic_ambiguity(linked_trials_path, ambiguity_output_path)
        results['ambiguity_source'] = 'synthetic'
    else:
        # Aggregate and save human ratings
        aggregated = aggregate_human_ratings(human_df)
        agg_df = pd.DataFrame([{'stimulus_id': k, 'ambiguity_score': v} for k, v in aggregated.items()])
        agg_df.to_csv(ambiguity_output_path, index=False)
        results['ambiguity_source'] = 'human'
    
    # 2. Run confounding check
    confounding_results = check_confounding(linked_trials_path, confounding_output_path)
    results['confounding'] = confounding_results
    
    return results

def main():
    """
    Entry point for preprocessing script.
    """
    try:
        result = run_preprocessing()
        logger.info("Preprocessing completed successfully.")
        logger.info(f"Ambiguity source: {result['ambiguity_source']}")
        logger.info(f"Confounding status: {'Confounded' if result['confounding']['confounding_check']['is_confounded'] else 'Not Confounded'}")
        return 0
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())