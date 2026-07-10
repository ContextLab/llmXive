"""
Generate metrics_summary.csv with F-statistic, p-value, adjusted p-value, and effect size.

This script orchestrates the final step of the statistical analysis pipeline (US2).
It loads cleaned data, performs Repeated Measures ANOVA, applies Holm-Bonferroni correction,
calculates effect sizes (Partial Eta Squared), and writes the results to data/processed/metrics_summary.csv.

Dependencies:
- data_cleaner.DataCleaner (for loading/cleaning)
- stat_utils.StatUtils (for ANOVA, effect size, correction)
- config.settings (for paths)
"""
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config.settings import get_settings
from analysis.data_cleaner import DataCleaner
from analysis.stat_utils import StatUtils
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_effect_size(f_statistic: float, df_num: int, df_denom: int) -> float:
    """
    Calculate Partial Eta Squared (η²p) from F-statistic.
    η²p = (F * df_num) / (F * df_num + df_denom)
    """
    if df_denom == 0:
        return 0.0
    numerator = f_statistic * df_num
    denominator = numerator + df_denom
    if denominator == 0:
        return 0.0
    return numerator / denominator

def generate_metrics_summary():
    """
    Main entry point to generate the metrics summary CSV.
    """
    settings = get_settings()
    data_cleaner = DataCleaner()
    stat_utils = StatUtils()
    
    output_dir = Path(settings.processed_data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "metrics_summary.csv"
    
    logger.info(f"Starting metrics summary generation. Output: {output_path}")
    
    # Load cleaned data
    # The DataCleaner loads from data/raw and applies SUS imputation/filtering
    cleaned_df = data_cleaner.load_and_clean()
    
    if cleaned_df is None or cleaned_df.empty:
        logger.warning("No valid data found for analysis. Creating empty summary.")
        # Create header-only file if no data
        summary_df = pd.DataFrame(columns=[
            "metric_name", 
            "interface_comparison", 
            "f_statistic", 
            "p_value", 
            "p_adjusted", 
            "effect_size_partial_eta_squared",
            "df_num",
            "df_denom"
        ])
        summary_df.to_csv(output_path, index=False)
        return output_path

    # Define metrics to test (excluding explanation_engagement_time per spec)
    metrics_to_test = ["completion_time", "error_count", "sus_score"]
    interface_variants = ["Traditional", "Explainable"]
    
    summary_records = []
    
    for metric in metrics_to_test:
        if metric not in cleaned_df.columns:
            logger.warning(f"Metric '{metric}' not found in cleaned data. Skipping.")
            continue
        
        # Check if we have both interface types for this metric
        # We expect a wide format or a way to pivot. 
        # Assuming data_cleaner produces a format where we can compare pairs.
        # If data is long format (session_id, interface, metric_value), we pivot.
        
        # Check data structure
        if "interface_type" in cleaned_df.columns:
            # Long format: Pivot to wide for ANOVA
            try:
                wide_df = cleaned_df.pivot_table(
                    index="session_id", 
                    columns="interface_type", 
                    values=metric, 
                    aggfunc="mean" # In case of multiple entries per session
                ).reset_index()
                
                # Ensure both columns exist
                if interface_variants[0] not in wide_df.columns or interface_variants[1] not in wide_df.columns:
                    logger.warning(f"Missing one or both interface types for metric {metric}. Skipping.")
                    continue
                
                x = wide_df[interface_variants[0]].dropna()
                y = wide_df[interface_variants[1]].dropna()
                
                # Perform Repeated Measures ANOVA
                # stat_utils.run_rm_anova expects two arrays (or handles pairing)
                # The spec implies a paired comparison (within-subjects)
                # We pass the two arrays. The function handles the pairing logic if needed.
                result = stat_utils.run_rm_anova(x, y)
                
                if result is None:
                    logger.warning(f"ANOVA failed for {metric}. Skipping.")
                    continue
                
                f_stat = result.get("f_statistic", 0.0)
                p_val = result.get("p_value", 1.0)
                df_num = result.get("df_num", 1)
                df_denom = result.get("df_denom", 1)
                
                # Apply Holm-Bonferroni correction
                # Since we are processing one by one, we collect p-values first?
                # Or we assume the StatUtils has a global list or we do it post-hoc.
                # The task T024 implemented Holm-Bonferroni.
                # Let's assume we need to correct against the set of metrics.
                # We will collect raw p-values first, then correct, then write.
                
                summary_records.append({
                    "metric_name": metric,
                    "interface_comparison": f"{interface_variants[0]} vs {interface_variants[1]}",
                    "f_statistic": f_stat,
                    "p_value": p_val,
                    "df_num": df_num,
                    "df_denom": df_denom,
                    "effect_size_partial_eta_squared": calculate_effect_size(f_stat, df_num, df_denom)
                })
                
            except Exception as e:
                logger.error(f"Error processing metric {metric}: {e}", exc_info=True)
        else:
            logger.warning(f"Data does not contain 'interface_type' column. Cannot perform paired analysis for {metric}.")

    if not summary_records:
        logger.warning("No results generated. Writing empty CSV.")
        summary_df = pd.DataFrame(columns=[
            "metric_name", 
            "interface_comparison", 
            "f_statistic", 
            "p_value", 
            "p_adjusted", 
            "effect_size_partial_eta_squared",
            "df_num",
            "df_denom"
        ])
        summary_df.to_csv(output_path, index=False)
        return output_path

    # Convert to DataFrame for easier manipulation
    summary_df = pd.DataFrame(summary_records)
    
    # Apply Holm-Bonferroni correction to the p_values
    # We need the raw p-values to correct them
    raw_p_values = summary_df["p_value"].tolist()
    
    # Use the StatUtils method for correction
    # Assuming StatUtils has a method that takes a list and returns adjusted list
    # If not, we implement it here based on T024's logic
    if hasattr(stat_utils, 'apply_holm_bonferroni'):
        adjusted_p_values = stat_utils.apply_holm_bonferroni(raw_p_values)
    else:
        # Fallback implementation if the method is missing in the provided surface
        # Sort p-values, apply Holm-Bonferroni
        n = len(raw_p_values)
        sorted_indices = sorted(range(n), key=lambda k: raw_p_values[k])
        adjusted = [0.0] * n
        for i, idx in enumerate(sorted_indices):
            # Holm-Bonferroni: p_adj = p_raw * (n - i)
            # But ensure it doesn't exceed 1.0 and is monotonic
            val = raw_p_values[idx] * (n - i)
            val = min(val, 1.0)
            # Ensure monotonicity (adjusted p-values should be non-decreasing with rank)
            # Actually, Holm's method ensures the adjusted p-values are non-decreasing in the sorted order
            # But when unsorting, we just assign the calculated value to the original index
            # However, standard practice is to take the max of current and previous to ensure monotonicity
            # Let's do the simple multiplication first, then enforce monotonicity on the sorted list
            adjusted[idx] = val
        
        # Enforce monotonicity on the sorted list
        # In the sorted list, adjusted[i] should be >= adjusted[i-1]
        # But since we multiply by decreasing factors, we might get non-monotonic if raw p's are weird?
        # Actually, Holm's procedure: p_(i) * (n-i+1). We take the max of this and the previous adjusted.
        # Let's re-do properly:
        sorted_p = [raw_p_values[i] for i in sorted_indices]
        final_adj_sorted = []
        current_max = 0.0
        for i, p in enumerate(sorted_p):
            adj = p * (n - i)
            adj = min(adj, 1.0)
            if adj < current_max:
                adj = current_max
            else:
                current_max = adj
            final_adj_sorted.append(adj)
        
        # Map back to original order
        adjusted_p_values = [0.0] * n
        for i, idx in enumerate(sorted_indices):
            adjusted_p_values[idx] = final_adj_sorted[i]
    
    summary_df["p_adjusted"] = adjusted_p_values
    
    # Reorder columns to match spec
    final_columns = [
        "metric_name",
        "interface_comparison",
        "f_statistic",
        "p_value",
        "p_adjusted",
        "effect_size_partial_eta_squared",
        "df_num",
        "df_denom"
    ]
    
    # Ensure all columns exist (some might be missing if data was weird, but we handled that)
    for col in final_columns:
        if col not in summary_df.columns:
            summary_df[col] = 0.0 if col in ["f_statistic", "p_value", "p_adjusted", "effect_size_partial_eta_squared", "df_num", "df_denom"] else ""
    
    summary_df = summary_df[final_columns]
    
    # Round numeric columns for readability
    numeric_cols = ["f_statistic", "p_value", "p_adjusted", "effect_size_partial_eta_squared", "df_num", "df_denom"]
    for col in numeric_cols:
        if col in summary_df.columns:
            summary_df[col] = summary_df[col].round(4)
    
    # Write to CSV
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Metrics summary generated successfully: {output_path}")
    logger.info(summary_df.to_string())
    
    return output_path

def main():
    """
    CLI entry point.
    """
    try:
        output_path = generate_metrics_summary()
        if output_path:
            print(f"Success: {output_path}")
            sys.exit(0)
        else:
            print("Failed to generate metrics summary.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()