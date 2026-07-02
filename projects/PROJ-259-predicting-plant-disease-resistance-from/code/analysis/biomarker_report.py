import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

from config import get_path, load_config
from utils.exceptions import PipelineException
from utils.logging import setup_logger, log_pipeline_step
from analysis.feature_selection import load_split_data, calculate_effect_sizes

logger = setup_logger("biomarker_report")

def load_feature_selection_results(selection_frequency_path: Path) -> pd.DataFrame:
    """
    Load the selection frequency results from the sensitivity sweep.
    Expects a CSV with columns: feature_id, threshold, frequency.
    """
    if not selection_frequency_path.exists():
        raise PipelineException(
            code="FILE_NOT_FOUND",
            message=f"Selection frequency file not found: {selection_frequency_path}",
            context={"path": str(selection_frequency_path)}
        )
    
    df = pd.read_csv(selection_frequency_path)
    required_cols = {"feature_id", "threshold", "frequency"}
    if not required_cols.issubset(df.columns):
        raise PipelineException(
            code="INVALID_SCHEMA",
            message=f"Selection frequency file missing required columns. Expected: {required_cols}, Found: {set(df.columns)}",
            context={"path": str(selection_frequency_path), "columns": list(df.columns)}
        )
    
    return df

def load_effect_sizes(effect_sizes_path: Path) -> pd.DataFrame:
    """
    Load the effect sizes calculated during feature selection.
    Expects a CSV with columns: feature_id, effect_size, p_value, feature_type.
    """
    if not effect_sizes_path.exists():
        raise PipelineException(
            code="FILE_NOT_FOUND",
            message=f"Effect sizes file not found: {effect_sizes_path}",
            context={"path": str(effect_sizes_path)}
        )
    
    df = pd.read_csv(effect_sizes_path)
    required_cols = {"feature_id", "effect_size", "p_value", "feature_type"}
    if not required_cols.issubset(df.columns):
        raise PipelineException(
            code="INVALID_SCHEMA",
            message=f"Effect sizes file missing required columns. Expected: {required_cols}, Found: {set(df.columns)}",
            context={"path": str(effect_sizes_path), "columns": list(df.columns)}
        )
    
    return df

def apply_significance_filter(
    df: pd.DataFrame,
    p_value_threshold: float = 0.05,
    min_frequency: float = 0.66
) -> pd.DataFrame:
    """
    Filter features based on BH-adjusted p-value and selection frequency.
    
    Args:
        df: DataFrame containing feature metrics.
        p_value_threshold: Maximum allowed p-value.
        min_frequency: Minimum selection frequency across thresholds.
    
    Returns:
        Filtered DataFrame.
    """
    # Ensure p_value is numeric
    df['p_value'] = pd.to_numeric(df['p_value'], errors='coerce')
    df['frequency'] = pd.to_numeric(df['frequency'], errors='coerce')
    
    # Filter by p-value
    df_sig = df[df['p_value'] <= p_value_threshold].copy()
    
    # Filter by frequency (aggregated across thresholds)
    # We assume the input df is already aggregated or we take the max frequency per feature
    if 'frequency' in df_sig.columns:
        # If multiple rows per feature (e.g. per threshold), aggregate
        if df_sig.groupby('feature_id').size().max() > 1:
            df_agg = df_sig.groupby('feature_id').agg({
                'effect_size': 'mean',
                'p_value': 'min',  # Most significant
                'frequency': 'mean', # Average frequency
                'feature_type': 'first'
            }).reset_index()
        else:
            df_agg = df_sig
        
        df_final = df_agg[df_agg['frequency'] >= min_frequency]
    else:
        df_final = df_sig
    
    return df_final.sort_values(by=['frequency', 'p_value'], ascending=[False, True])

def generate_biomarker_report(
    selection_frequency_path: Path,
    effect_sizes_path: Path,
    output_path: Path,
    p_value_threshold: float = 0.05,
    min_frequency: float = 0.66
) -> Dict[str, Any]:
    """
    Generate the top features biomarker report.
    
    Args:
        selection_frequency_path: Path to selection_frequency.csv.
        effect_sizes_path: Path to effect_sizes.csv.
        output_path: Path to write top_features.csv.
        p_value_threshold: Significance threshold for p-values.
        min_frequency: Minimum selection frequency to be considered robust.
    
    Returns:
        Dictionary with report statistics.
    """
    log_pipeline_step(logger, "Starting biomarker report generation")
    
    # Load data
    freq_df = load_feature_selection_results(selection_frequency_path)
    effect_df = load_effect_sizes(effect_sizes_path)
    
    # Aggregate frequency per feature if necessary
    freq_agg = freq_df.groupby('feature_id').agg({
        'frequency': 'mean'
    }).reset_index()
    
    # Merge with effect sizes
    merged_df = pd.merge(
        effect_df,
        freq_agg,
        on='feature_id',
        how='inner'
    )
    
    # Apply filters
    significant_features = apply_significance_filter(
        merged_df,
        p_value_threshold=p_value_threshold,
        min_frequency=min_frequency
    )
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    significant_features.to_csv(output_path, index=False)
    
    # Generate summary stats
    report_stats = {
        "total_features_analyzed": len(effect_df),
        "significant_features_count": len(significant_features),
        "p_value_threshold": p_value_threshold,
        "min_frequency_threshold": min_frequency,
        "snps_count": len(significant_features[significant_features['feature_type'] == 'snp']),
        "metabolites_count": len(significant_features[significant_features['feature_type'] == 'metabolite']),
        "output_path": str(output_path)
    }
    
    log_pipeline_step(logger, "Biomarker report generated", extra={"stats": report_stats})
    
    return report_stats

def biomarker_report_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main pipeline function for generating the biomarker report.
    
    Args:
        config: Configuration dictionary.
    
    Returns:
        Report statistics dictionary.
    """
    logger.info("Starting biomarker report pipeline")
    
    # Determine paths from config
    base_path = get_path("artifacts/reports")
    selection_freq_path = base_path / "selection_frequency.csv"
    effect_sizes_path = base_path / "effect_sizes.csv"
    output_path = base_path / "top_features.csv"
    
    # Allow overrides via config
    if "selection_frequency_path" in config:
        selection_freq_path = Path(config["selection_frequency_path"])
    if "effect_sizes_path" in config:
        effect_sizes_path = Path(config["effect_sizes_path"])
    if "output_path" in config:
        output_path = Path(config["output_path"])
    
    p_val_thresh = config.get("p_value_threshold", 0.05)
    min_freq = config.get("min_frequency", 0.66)
    
    try:
        stats = generate_biomarker_report(
            selection_frequency_path=selection_freq_path,
            effect_sizes_path=effect_sizes_path,
            output_path=output_path,
            p_value_threshold=p_val_thresh,
            min_frequency=min_freq
        )
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Biomarker report pipeline failed: {str(e)}")
        return {"status": "failed", "error": str(e)}

def main():
    """CLI entry point for biomarker report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate biomarker report (top_features.csv)")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--selection-frequency", type=str, help="Path to selection_frequency.csv")
    parser.add_argument("--effect-sizes", type=str, help="Path to effect_sizes.csv")
    parser.add_argument("--output", type=str, help="Path to output top_features.csv")
    parser.add_argument("--p-value-threshold", type=float, default=0.05, help="P-value threshold")
    parser.add_argument("--min-frequency", type=float, default=0.66, help="Minimum selection frequency")
    
    args = parser.parse_args()
    
    config = load_config()
    
    if args.config:
        with open(args.config, 'r') as f:
            config.update(json.load(f))
    
    if args.selection_frequency:
        config["selection_frequency_path"] = args.selection_frequency
    if args.effect_sizes:
        config["effect_sizes_path"] = args.effect_sizes
    if args.output:
        config["output_path"] = args.output
    if args.p_value_threshold:
        config["p_value_threshold"] = args.p_value_threshold
    if args.min_frequency:
        config["min_frequency"] = args.min_frequency
    
    result = biomarker_report_pipeline(config)
    
    if result["status"] == "success":
        print(json.dumps(result["stats"], indent=2))
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
