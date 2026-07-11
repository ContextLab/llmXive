import logging
import pandas as pd
import numpy as np
from pathlib import Path
from .config import NOISE_THRESHOLD_LOW, NOISE_THRESHOLD_HIGH, ROOT_DIR

logger = logging.getLogger(__name__)

def replicate_final_score_only(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run analysis using only final task-switching scores (controlling for baseline).
    
    This function filters the input dataframe to analyze only the 'final_score' 
    column, which represents the primary performance metric after baseline control.
    It calculates summary statistics and returns a DataFrame with the results.
    
    Args:
        df: Preprocessed dataframe containing 'final_score' and 'participant_id'
    
    Returns:
        DataFrame with summary statistics for the final score analysis
    """
    if df.empty:
        logger.warning("Input dataframe is empty.")
        return pd.DataFrame()

    # Validate required columns
    required_cols = ['final_score', 'participant_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for final score analysis: {missing_cols}")

    # Calculate summary statistics
    mean_score = df['final_score'].mean()
    std_score = df['final_score'].std()
    median_score = df['final_score'].median()
    min_score = df['final_score'].min()
    max_score = df['final_score'].max()
    n_participants = df['participant_id'].nunique()
    n_observations = len(df)

    result = {
        "analysis_type": "final_score_only",
        "mean_score": mean_score,
        "std_score": std_score,
        "median_score": median_score,
        "min_score": min_score,
        "max_score": max_score,
        "n_participants": n_participants,
        "n_observations": n_observations
    }
    
    return pd.DataFrame([result])

def sweep_noise_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Iterate over fixed sets of lower and upper decibel ranges and report significance variation.
    
    This function performs a sensitivity analysis by varying the thresholds used to 
    categorize noise levels (Low, Moderate, High) and reports the distribution of 
    participants across these categories for each threshold combination.
    
    Thresholds are defined in the task specification:
    - Lower thresholds: [40, 45, 50] dB
    - Upper thresholds: [60, 65, 70] dB
    
    Args:
        df: Preprocessed dataframe with 'avg_noise' column
    
    Returns:
        DataFrame with sweep results including threshold combinations and proportions
    """
    if df.empty:
        logger.warning("Input dataframe is empty.")
        return pd.DataFrame()

    if 'avg_noise' not in df.columns:
        raise ValueError("Column 'avg_noise' not found in input dataframe.")

    # Define threshold sweeps as per specification
    lower_thresholds = [40, 45, 50]
    upper_thresholds = [60, 65, 70]
    
    results = []
    
    for low in lower_thresholds:
        for high in upper_thresholds:
            # Create bins based on current thresholds
            def categorize(level):
                if level < low:
                    return 'Low'
                elif level <= high:
                    return 'Moderate'
                else:
                    return 'High'
            
            df_temp = df.copy()
            df_temp['noise_level_sweep'] = df_temp['avg_noise'].apply(categorize)
            
            # Calculate distribution proportions
            proportions = df_temp['noise_level_sweep'].value_counts(normalize=True)
            
            results.append({
                "low_threshold": low,
                "high_threshold": high,
                "low_prop": proportions.get('Low', 0.0),
                "moderate_prop": proportions.get('Moderate', 0.0),
                "high_prop": proportions.get('High', 0.0)
            })
    
    logger.info(f"Sweep completed for {len(results)} threshold combinations.")
    return pd.DataFrame(results)

def exclude_extreme_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Re-run analysis excluding participants with extreme self-reported noise sensitivity.
    
    This function identifies participants in the top 10% of the 'noise_sensitivity_score'
    distribution and excludes them from the analysis to test the robustness of results
    against extreme sensitivity outliers.
    
    Args:
        df: Preprocessed dataframe with 'noise_sensitivity_score' and 'participant_id'
    
    Returns:
        DataFrame with summary statistics of the exclusion and the filtered dataset
    """
    if df.empty:
        logger.warning("Input dataframe is empty.")
        return pd.DataFrame()

    if 'noise_sensitivity_score' not in df.columns:
        logger.warning("Column 'noise_sensitivity_score' not found. Returning original data.")
        return pd.DataFrame([{
            "analysis_type": "exclude_extreme",
            "threshold_used": None,
            "n_excluded": 0,
            "n_remaining": len(df),
            "n_participants_remaining": df['participant_id'].nunique() if 'participant_id' in df.columns else 0
        }])

    # Define extreme sensitivity as top 10%
    threshold = df['noise_sensitivity_score'].quantile(0.90)
    df_filtered = df[df['noise_sensitivity_score'] <= threshold]
    
    n_excluded = len(df) - len(df_filtered)
    n_remaining = len(df_filtered)
    
    # Calculate participant counts
    n_participants_original = df['participant_id'].nunique() if 'participant_id' in df.columns else 0
    n_participants_remaining = df_filtered['participant_id'].nunique() if 'participant_id' in df_filtered.columns else 0
    
    result = {
        "analysis_type": "exclude_extreme",
        "threshold_used": threshold,
        "n_excluded": n_excluded,
        "n_remaining": n_remaining,
        "n_participants_original": n_participants_original,
        "n_participants_remaining": n_participants_remaining,
        "exclusion_rate": n_excluded / len(df) if len(df) > 0 else 0.0
    }
    
    logger.info(f"Excluded {n_excluded} observations ({exclusion_rate:.2%}) with sensitivity score > {threshold:.2f}")
    
    # Return summary result and optionally the filtered dataframe could be handled by caller
    # For this function, we return the summary stats as a DataFrame
    return pd.DataFrame([result])