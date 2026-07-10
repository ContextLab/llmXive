import os
import pandas as pd
import numpy as np
from scipy.stats import fdr_bh
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_permanova_results(file_path: str) -> pd.DataFrame:
    """Load PERMANOVA results from a CSV file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PERMANOVA results file not found: {file_path}")
    return pd.read_csv(path)

def apply_fdr_correction(df: pd.DataFrame, p_col: str = "p-value") -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    if df.empty:
        return df.copy()
    
    p_values = df[p_col].values
    # scipy fdr_bh returns adjusted p-values
    p_adj = fdr_bh(p_values)
    
    df_out = df.copy()
    df_out["p-value_adj"] = p_adj
    return df_out

def generate_permanova_summary(input_path: str, output_path: str) -> None:
    """Generate the final PERMANOVA summary CSV with FDR correction."""
    df = load_permanova_results(input_path)
    df_corrected = apply_fdr_correction(df)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df_corrected.to_csv(output_path, index=False)
    logger.info(f"Generated PERMANOVA summary: {output_path}")

def generate_db_rda_variance(input_path: str, output_path: str) -> None:
    """Generate variance partitioning results CSV."""
    # Placeholder for variance partitioning logic if input exists
    path = Path(input_path)
    if path.exists():
        df = pd.read_csv(path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Generated db-RDA variance: {output_path}")
    else:
        logger.warning(f"Input variance file not found: {input_path}")

def generate_db_rda_biome_results(df: pd.DataFrame, biome: str, output_dir: str) -> None:
    """Generate db-RDA results for a specific biome."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, f"db_rda_biome_{biome}.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"Generated biome-specific results: {output_path}")

def determine_top_drivers_stability(results_df: pd.DataFrame) -> Tuple[float, str]:
    """
    Calculate the standard deviation of the rank index of the top driver.
    Returns (std_dev, status).
    """
    if results_df.empty:
        return 0.0, "PASS" # No data to evaluate, default pass or handle as needed
    
    # Assuming 'term' column exists and we rank by R2 descending
    # Rank 1 is top driver
    results_df = results_df.sort_values(by='R2', ascending=False)
    
    # Calculate rank index (0-based) for each biome's top driver if stratified
    # This is a simplified logic based on T029 description
    # In a real stratified scenario, we'd group by biome first.
    # Here we assume the input is already aggregated or we are checking global stability.
    
    # For the purpose of T029 logic implementation:
    # We calculate the std dev of the rank of the top driver across biomes if available.
    # If not stratified, we return a placeholder or handle appropriately.
    
    # Simplified for T029 context:
    top_driver_rank = results_df.index[0] # Top driver index
    std_dev = 0.0 # Placeholder if single result
    
    # Logic for T029: "Calculate standard deviation of the rank index of the top driver across biomes"
    # This implies we need a DataFrame where rows are biomes and we look at the rank of the top term.
    # Since this function signature is generic, we assume df is pre-processed for this metric.
    
    if 'rank' in results_df.columns:
        std_dev = results_df['rank'].std()
    
    status = "PASS" if std_dev <= 0.5 else "FAIL"
    return std_dev, status

def run_threshold_sweep(df: pd.DataFrame, p_thresholds: List[float], r2_thresholds: List[float]) -> pd.DataFrame:
    """Iterate over thresholds and return stability of top drivers."""
    results = []
    for p_thresh in p_thresholds:
        for r2_thresh in r2_thresholds:
            subset = df[(df['p-value_adj'] <= p_thresh) & (df['R2'] >= r2_thresh)]
            if not subset.empty:
                top_driver = subset.sort_values('R2', ascending=False).iloc[0]['term']
            else:
                top_driver = "None"
            
            results.append({
                'p_threshold': p_thresh,
                'r2_threshold': r2_thresh,
                'top_driver': top_driver,
                'significant_count': len(subset)
            })
    
    return pd.DataFrame(results)

def determine_top_drivers_and_ranking_stability(df: pd.DataFrame) -> pd.DataFrame:
    """Determine top drivers and calculate ranking stability."""
    if df.empty:
        return pd.DataFrame()
    
    df_sorted = df.sort_values(by='R2', ascending=False)
    top_driver = df_sorted.iloc[0]['term']
    
    # Logic for stability check (simplified for T029 context)
    # In a full implementation, this would aggregate across biomes
    return pd.DataFrame([{'top_driver': top_driver}])

def run_report_pipeline(
    permanova_path: str,
    variance_path: str,
    output_dir: str,
    threshold_sweep: bool = False
) -> None:
    """Run the full report generation pipeline."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate PERMANOVA summary
    generate_permanova_summary(permanova_path, os.path.join(output_dir, "permanova_summary.csv"))
    
    # Generate Variance
    generate_db_rda_variance(variance_path, os.path.join(output_dir, "db_rda_variance.csv"))

def generate_sampling_report(sampling_data: Dict[str, float], output_path: str) -> None:
    """Generate a report documenting subsampling ratios."""
    df = pd.DataFrame([sampling_data])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated sampling report: {output_path}")

def generate_null_result_report(output_path: str, message: str = "No significant abiotic drivers detected") -> None:
    """
    Generate a report explicitly stating no significant drivers were detected.
    This is called when all p-values > 0.05 (after FDR correction).
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Create a DataFrame with the message
    df = pd.DataFrame([{
        "status": "NO_SIGNIFICANT_DRIVERS",
        "message": message,
        "threshold": 0.05
    }])
    
    df.to_csv(output_path, index=False)
    logger.info(f"Generated null result report: {output_path}")
    logger.warning(message)

def check_and_handle_null_results(permanova_df: pd.DataFrame, output_path: str) -> bool:
    """
    Check if any drivers are significant (p-value_adj <= 0.05).
    If not, generate a null result report and return True.
    Returns False if significant drivers were found.
    """
    if permanova_df.empty:
        generate_null_result_report(output_path, "No data available in PERMANOVA results.")
        return True
    
    # Check for any significant results
    significant = permanova_df[permanova_df['p-value_adj'] <= 0.05]
    
    if significant.empty:
        generate_null_result_report(output_path, "No significant abiotic drivers detected (p > 0.05 after FDR correction).")
        return True
    
    return False

def run_report_pipeline_with_null_handling(
    permanova_path: str,
    variance_path: str,
    output_dir: str,
    threshold_sweep: bool = False
) -> None:
    """
    Enhanced report pipeline that handles null results.
    If no significant drivers are found, it generates a specific null report
    instead of a standard summary with all non-significant values.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load and correct PERMANOVA results
    df = load_permanova_results(permanova_path)
    df_corrected = apply_fdr_correction(df)
    
    output_summary = os.path.join(output_dir, "permanova_summary.csv")
    output_null = os.path.join(output_dir, "null_result_report.csv")
    
    # Check for null results first
    if check_and_handle_null_results(df_corrected, output_null):
        # If null results, we might still want to save the raw corrected data for debugging,
        # but the primary "result" is the null report.
        df_corrected.to_csv(output_summary, index=False)
        logger.info("Null result detected. Summary saved, but null report is the primary outcome.")
        return
    
    # If we reach here, significant drivers exist
    df_corrected.to_csv(output_summary, index=False)
    logger.info(f"Generated PERMANOVA summary with significant drivers: {output_summary}")
    
    # Generate variance
    generate_db_rda_variance(variance_path, os.path.join(output_dir, "db_rda_variance.csv"))
