import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from src.config import load_config

logger = logging.getLogger(__name__)

def calculate_spearman_correlation(diversity_values: pd.Series, sleep_values: pd.Series) -> float:
    """
    Calculate Spearman rank correlation coefficient between two series.
    """
    if diversity_values.empty or sleep_values.empty:
        return np.nan
    
    # Drop NaNs for calculation
    mask = diversity_values.notna() & sleep_values.notna()
    if mask.sum() < 3:
        return np.nan
    
    r, p = spearmanr(diversity_values[mask], sleep_values[mask])
    return r

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    Returns adjusted q-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate q-values
    q = np.zeros(n)
    for i in range(n):
        q[sorted_indices[i]] = (sorted_p[i] * n) / (i + 1)
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        q[i] = min(q[i], q[i+1])
    
    # Cap at 1.0
    q = np.clip(q, 0, 1.0)
    
    return q.tolist()

def flag_correlations(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add columns 'is_moderate' and 'is_significant' to the results DataFrame.
    is_moderate: |r| > 0.3
    is_significant: q-value < 0.05
    """
    if results_df.empty:
        return results_df
    
    results_df['is_moderate'] = results_df['r'].abs() > 0.3
    results_df['is_significant'] = results_df['q'] < 0.05
    return results_df

def handle_no_significant_associations(results_df: pd.DataFrame, output_path: Path):
    """
    Handle the case where no significant associations are found.
    Logs a message and ensures the file is saved (even if empty or with a status row).
    """
    logger.warning("No significant associations found after FDR correction.")
    # The file will be saved by the caller, but we log the state.
    # If the DataFrame is empty, we might want to add a status row.
    if results_df.empty:
        # Create a minimal dataframe indicating no results
        results_df = pd.DataFrame(columns=['sample_id', 'diversity_index', 'sleep_metric', 'r', 'p', 'q', 'is_moderate', 'is_significant', 'status'])
        # We don't add a row here, just return the empty DF to be saved.
    return results_df

def run_correlation_analysis(diversity_df: pd.DataFrame, sleep_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full correlation analysis pipeline:
    1. Merge diversity and sleep data on sample_id
    2. Calculate Spearman correlation for each diversity index vs each sleep metric
    3. Apply Benjamini-Hochberg correction
    4. Flag results
    """
    # Merge data
    merged_df = pd.merge(diversity_df, sleep_df, on='sample_id', how='inner')
    
    if merged_df.empty:
        logger.warning("No overlapping samples between diversity and sleep data.")
        return pd.DataFrame(columns=['sample_id', 'diversity_index', 'sleep_metric', 'r', 'p', 'q', 'is_moderate', 'is_significant', 'status'])
    
    # Identify diversity indices and sleep metrics
    diversity_indices = [col for col in merged_df.columns if col in ['shannon', 'simpson', 'observed_otus']]
    sleep_metrics = [col for col in merged_df.columns if col in ['sleep_efficiency', 'sleep_duration_hours']]
    
    results = []
    p_values = []
    correlation_data = []
    
    for div_idx in diversity_indices:
        for sleep_met in sleep_metrics:
            r = calculate_spearman_correlation(merged_df[div_idx], merged_df[sleep_met])
            if not np.isnan(r):
                # We need to calculate p-value here too for BH correction
                # Re-calculate p-value
                mask = merged_df[div_idx].notna() & merged_df[sleep_met].notna()
                if mask.sum() >= 3:
                    _, p = spearmanr(merged_df[div_idx][mask], merged_df[sleep_met][mask])
                    p_values.append(p)
                    correlation_data.append({
                        'diversity_index': div_idx,
                        'sleep_metric': sleep_met,
                        'r': r,
                        'p': p
                    })
    
    if not p_values:
        logger.warning("No valid correlations calculated.")
        return pd.DataFrame(columns=['sample_id', 'diversity_index', 'sleep_metric', 'r', 'p', 'q', 'is_moderate', 'is_significant', 'status'])
    
    # Apply BH correction
    q_values = apply_benjamini_hochberg(p_values)
    
    for i, data in enumerate(correlation_data):
        data['q'] = q_values[i]
        results.append(data)
    
    results_df = pd.DataFrame(results)
    
    # Flag correlations
    results_df = flag_correlations(results_df)
    
    # Add status column
    results_df['status'] = 'success'
    
    # Handle no significant associations
    if not results_df[results_df['is_significant']].empty:
        logger.info(f"Found {results_df['is_significant'].sum()} significant associations.")
    else:
        results_df = handle_no_significant_associations(results_df, Path("data/processed/correlation_results.csv"))
    
    return results_df

def main():
    """
    Main entry point for correlation analysis (Happy Path).
    This function expects to be called when data is available.
    """
    config = load_config()
    data_dir = Path(config.get("DATA_PROCESSED_DIR", "data/processed"))
    
    diversity_path = data_dir / "diversity_results.csv"
    sleep_path = data_dir / "cleaned_microbiome_sleep.csv"
    
    if not diversity_path.exists():
        raise FileNotFoundError(f"Diversity results not found at {diversity_path}")
    if not sleep_path.exists():
        raise FileNotFoundError(f"Sleep data not found at {sleep_path}")
    
    diversity_df = pd.read_csv(diversity_path)
    sleep_df = pd.read_csv(sleep_path)
    
    results_df = run_correlation_analysis(diversity_df, sleep_df)
    
    output_path = data_dir / "correlation_results.csv"
    results_df.to_csv(output_path, index=False)
    logger.info(f"Correlation results saved to {output_path}")
    
    return results_df

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()