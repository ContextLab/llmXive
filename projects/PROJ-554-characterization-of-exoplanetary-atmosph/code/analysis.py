import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from config import get_config
import scipy.stats as stats

def calculate_detection_limit(snr: float, resolution: float, noise_floor: float = 1e-5) -> float:
    """
    Calculate the minimum detectable mixing ratio (detection limit) for a given
    Signal-to-Noise Ratio (SNR) and Spectral Resolution (R).

    This function implements the reviewer's requirement (FR-002) to define the
    detection limit for water vapor lines based on instrument capabilities.

    The detection limit is approximated by:
    Limit = (Noise_Floor * Resolution) / SNR

    Where:
    - Noise_Floor: A baseline noise factor (default 1e-5) representing the
                   instrument's intrinsic noise level in mixing ratio units.
    - Resolution: Spectral resolution (R = lambda / delta_lambda).
    - SNR: Signal-to-Noise Ratio of the observation.

    Args:
        snr (float): Signal-to-Noise Ratio.
        resolution (float): Spectral Resolution (R).
        noise_floor (float): Baseline noise factor.

    Returns:
        float: The calculated detection limit (minimum detectable mixing ratio).
    """
    if snr <= 0:
        raise ValueError("SNR must be positive.")
    if resolution <= 0:
        raise ValueError("Resolution must be positive.")

    # Calculate detection limit
    detection_limit = (noise_floor * resolution) / snr
    return detection_limit

def generate_detection_limits_csv(metadata_path: str, output_path: str) -> pd.DataFrame:
    """
    Reads metadata from the processed metadata CSV, calculates the detection limit
    for each spectrum, and saves the results to a new CSV file.

    Args:
        metadata_path (str): Path to the input metadata CSV (e.g., data/processed/metadata.csv).
        output_path (str): Path to the output detection limits CSV.

    Returns:
        pd.DataFrame: The dataframe containing detection limits.
    """
    config = get_config()
    logger = logging.getLogger(__name__)

    try:
        df = pd.read_csv(metadata_path)
    except FileNotFoundError:
        logger.error(f"Metadata file not found: {metadata_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading metadata file: {e}")
        raise

    required_cols = ['SNR', 'Resolution']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Metadata missing required columns: {missing_cols}")

    # Calculate detection limits
    df['Detection_Limit'] = df.apply(
        lambda row: calculate_detection_limit(row['SNR'], row['Resolution']),
        axis=1
    )

    # Save to output
    output_df = df[['Planet_Name', 'SNR', 'Resolution', 'Detection_Limit']]
    output_df.to_csv(output_path, index=False)
    logger.info(f"Detection limits saved to {output_path}")

    return output_df

def run_loo_correlation_check(
    water_abundance: List[float],
    temperature: List[float],
    is_censored: List[bool],
    n_bootstrap: int = 1000
) -> Dict[str, float]:
    """
    Performs a Leave-One-Out (LOO) correlation check to assess the stability
    of the correlation between water abundance and temperature.

    This function addresses SC-004 by calculating the `max_correlation_drift` metric.
    It iteratively removes one data point, recalculates the correlation coefficient,
    and measures the maximum deviation from the full-dataset correlation.

    For censored data (upper limits), this implementation uses a simplified
    approach suitable for the robustness check: it treats censored values as
    their upper limit bounds for the calculation, acknowledging that a full
    censored-LOO would require specialized survival analysis resampling which
    is computationally intensive. The primary goal here is to detect outliers
    that disproportionately drive the correlation.

    Args:
        water_abundance (List[float]): List of water mixing ratios (log10).
        temperature (List[float]): List of equilibrium temperatures (K).
        is_censored (List[bool]): List of booleans indicating if the value is an upper limit.
        n_bootstrap (int): Number of bootstrap iterations (reserved for future expansion,
                           currently used for internal consistency check if needed).

    Returns:
        Dict[str, float]: A dictionary containing:
            - 'full_correlation': Correlation of the full dataset.
            - 'max_correlation_drift': The maximum absolute difference in correlation
                                      when any single point is removed.
            - 'sensitive_index': The index of the point whose removal caused the max drift.
    """
    if len(water_abundance) != len(temperature) or len(water_abundance) != len(is_censored):
        raise ValueError("Input lists must have the same length.")
    if len(water_abundance) < 3:
        raise ValueError("LOO check requires at least 3 data points.")

    arr_water = np.array(water_abundance)
    arr_temp = np.array(temperature)
    arr_censored = np.array(is_censored)

    # Calculate full dataset correlation (Pearson for this robustness check)
    # Note: In a full survival analysis context, one might use Kendall's Tau,
    # but for LOO drift detection on the magnitude of the relationship, Pearson
    # on the available values (treating limits as values) is a standard diagnostic
    # for outlier influence.
    full_corr, _ = stats.pearsonr(arr_water, arr_temp)
    if np.isnan(full_corr):
        full_corr = 0.0

    max_drift = 0.0
    sensitive_idx = -1

    logger = logging.getLogger(__name__)
    logger.info(f"Starting LOO correlation check on {len(arr_water)} points.")

    for i in range(len(arr_water)):
        # Create mask excluding current index
        mask = np.ones(len(arr_water), dtype=bool)
        mask[i] = False

        subset_water = arr_water[mask]
        subset_temp = arr_temp[mask]

        if len(subset_water) < 2:
            continue

        # Recalculate correlation
        try:
            loo_corr, _ = stats.pearsonr(subset_water, subset_temp)
            if np.isnan(loo_corr):
                loo_corr = 0.0
        except Exception:
            # If correlation cannot be computed (e.g., constant values), treat as 0 or skip
            loo_corr = 0.0

        drift = abs(loo_corr - full_corr)

        if drift > max_drift:
            max_drift = drift
            sensitive_idx = i

    result = {
        'full_correlation': float(full_corr),
        'max_correlation_drift': float(max_drift),
        'sensitive_index': int(sensitive_idx)
    }

    logger.info(f"LOO Check Complete. Max Drift: {max_drift:.4f} at index {sensitive_idx}")
    return result

def main():
    """
    Main entry point for the LOO correlation check task (T037).
    Reads retrieval results and metadata, performs the check, and logs the metric.
    """
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    logger = logging.getLogger(__name__)

    # Define paths based on project structure
    # Assuming retrieval results are in data/processed/retrieval_results.csv
    # and metadata is in data/processed/metadata.csv
    retrieval_path = config['paths'].get('retrieval_results', 'data/processed/retrieval_results.csv')
    metadata_path = config['paths'].get('processed_metadata', 'data/processed/metadata.csv')

    logger.info(f"Loading data for LOO check from {retrieval_path} and {metadata_path}")

    try:
        # Load retrieval results
        df_retrieval = pd.read_csv(retrieval_path)
        # Load metadata to get temperature and censoring info
        df_meta = pd.read_csv(metadata_path)

        # Merge on planet name (adjust column names if necessary)
        # Expected columns in retrieval: Planet_Name, log10_H2O, Uncertainty, Is_Censored (or similar)
        # Expected columns in meta: Planet_Name, Temperature
        
        # Normalize column names for robustness
        df_retrieval.columns = df_retrieval.columns.str.strip().str.lower()
        df_meta.columns = df_meta.columns.str.strip().str.lower()

        # Identify common key
        key_col = 'planet_name' if 'planet_name' in df_retrieval.columns and 'planet_name' in df_meta.columns else None
        if not key_col:
            # Fallback to 'planet' or 'name'
            for col in ['planet', 'name', 'id']:
                if col in df_retrieval.columns and col in df_meta.columns:
                    key_col = col
                    break

        if not key_col:
            raise KeyError("Could not find a common key column to merge retrieval and metadata.")

        df_merged = pd.merge(df_retrieval, df_meta, on=key_col, how='inner')

        if df_merged.empty:
            raise ValueError("Merged dataframe is empty. Check key columns.")

        # Extract required series
        # Map generic names to expected data
        water_col = [c for c in df_merged.columns if 'h2o' in c or 'water' in c or 'mixing' in c]
        temp_col = [c for c in df_merged.columns if 'temp' in c or 'equilibrium' in c]
        censor_col = [c for c in df_merged.columns if 'censor' in c or 'limit' in c]

        if not water_col or not temp_col:
            raise ValueError("Required columns (Water Abundance, Temperature) not found in merged data.")

        water_series = df_merged[water_col[0]]
        temp_series = df_merged[temp_col[0]]
        censor_series = df_merged[censor_col[0]] if censor_col else pd.Series([False] * len(df_merged))

        # Convert to lists
        water_list = water_series.tolist()
        temp_list = temp_series.tolist()
        censor_list = censor_series.tolist()

        # Run LOO check
        results = run_loo_correlation_check(water_list, temp_list, censor_list)

        logger.info("=== LOO Correlation Check Results ===")
        logger.info(f"Full Correlation: {results['full_correlation']:.4f}")
        logger.info(f"Max Correlation Drift: {results['max_correlation_drift']:.4f}")
        logger.info(f"Most Sensitive Index: {results['sensitive_index']}")

        # Save results to a JSON file for downstream reporting
        output_path = config['paths'].get('analysis_results', 'data/processed/analysis_results.json')
        # Load existing if exists, or create new
        import json
        import os
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}

        existing_data['loo_correlation_check'] = results
        with open(output_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        logger.info(f"LOO results saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to run LOO correlation check: {e}")
        raise

if __name__ == "__main__":
    main()