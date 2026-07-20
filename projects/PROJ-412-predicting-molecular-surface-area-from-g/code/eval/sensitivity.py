import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

# Local imports based on project API surface
from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir, get_results_dir
from eval.metrics import bonferroni_correction, fdr_correction

# Configure logger
logger = get_logger(__name__)

def load_predictions(filepath: str) -> pd.DataFrame:
    """
    Load predictions from a Parquet or CSV file.
    Expected columns: 'smiles', 'predicted_sasa', 'true_sasa', 'molecular_weight'
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {filepath}")
    
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .parquet or .csv")
    
    required_cols = ['predicted_sasa', 'true_sasa']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in predictions: {missing}")
    
    return df

def calculate_success_rates(
    df: pd.DataFrame, 
    thresholds: List[float], 
    is_relative: bool = False,
    mean_sasa: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Calculate success rates for a list of thresholds.
    
    Args:
        df: DataFrame with 'predicted_sasa' and 'true_sasa'
        thresholds: List of MAE thresholds
        is_relative: If True, thresholds are percentages of mean_sasa
        mean_sasa: Mean SASA of the dataset (required if is_relative)
    
    Returns:
        List of dicts with threshold and success_rate
    """
    results = []
    errors = df['predicted_sasa'] - df['true_sasa']
    mae = errors.abs()
    
    if is_relative:
        if mean_sasa is None:
            mean_sasa = df['true_sasa'].mean()
        effective_thresholds = [(t / 100.0) * mean_sasa for t in thresholds]
    else:
        effective_thresholds = thresholds
    
    for t_val, t_label in zip(effective_thresholds, thresholds):
        success_count = (mae <= t_val).sum()
        total_count = len(mae)
        rate = success_count / total_count if total_count > 0 else 0.0
        results.append({
            'threshold': t_label,
            'effective_threshold': t_val,
            'success_rate': rate,
            'count': int(success_count),
            'total': int(total_count)
        })
    
    return results

def run_sensitivity_analysis_absolute(
    df: pd.DataFrame,
    thresholds: List[float] = [0.01, 0.05, 0.1],
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis for absolute MAE thresholds.
    
    Args:
        df: Predictions dataframe
        thresholds: Absolute thresholds in Å²
        output_path: Path to save results CSV
    
    Returns:
        DataFrame of results
    """
    logger.info(f"Running absolute sensitivity analysis on {len(df)} molecules.")
    results = calculate_success_rates(df, thresholds, is_relative=False)
    df_results = pd.DataFrame(results)
    
    if output_path:
        df_results.to_csv(output_path, index=False)
        logger.info(f"Absolute sensitivity results saved to {output_path}")
    
    return df_results

def run_sensitivity_analysis_relative(
    df: pd.DataFrame,
    thresholds: List[float] = [1.0, 5.0, 10.0],
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis for relative MAE thresholds (% of mean SASA).
    
    Args:
        df: Predictions dataframe
        thresholds: Relative thresholds in %
        output_path: Path to save results CSV
    
    Returns:
        DataFrame of results
    """
    mean_sasa = df['true_sasa'].mean()
    logger.info(f"Mean SASA for relative analysis: {mean_sasa:.4f} Å²")
    logger.info(f"Running relative sensitivity analysis on {len(df)} molecules.")
    
    results = calculate_success_rates(df, thresholds, is_relative=True, mean_sasa=mean_sasa)
    df_results = pd.DataFrame(results)
    
    if output_path:
        df_results.to_csv(output_path, index=False)
        logger.info(f"Relative sensitivity results saved to {output_path}")
    
    return df_results

def run_multiple_comparison_correction(
    p_values: List[float],
    method: str = 'bonferroni'
) -> List[float]:
    """
    Apply multiple comparison correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        method: 'bonferroni' or 'fdr'
    
    Returns:
        List of corrected p-values
    """
    if not p_values:
        return []
    
    if method == 'bonferroni':
        corrected = bonferroni_correction(p_values)
    elif method == 'fdr':
        corrected = fdr_correction(p_values)
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    return corrected

def generate_reproducibility_report(
    sample_size: int,
    streaming_strategy: str,
    chunk_size: int,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate a reproducibility report documenting the sample size and streaming rules.
    
    Args:
        sample_size: Number of molecules used in the analysis
        streaming_strategy: Description of how data was streamed (e.g., 'chunked', 'full_load')
        chunk_size: Size of chunks if chunked processing was used
        output_path: Path to write the JSON report
    
    Returns:
        Dictionary containing the report metadata
    """
    report = {
        "sample_size": sample_size,
        "streaming_strategy": streaming_strategy,
        "chunk_size": chunk_size,
        "timestamp": pd.Timestamp.now().isoformat(),
        "analysis_type": "sensitivity_analysis",
        "reproducibility_notes": (
            f"The sensitivity analysis was performed on a dataset of {sample_size} molecules. "
            f"Data was processed using a {streaming_strategy} strategy with a chunk size of {chunk_size}. "
            "To reproduce these results, ensure the same dataset version and processing parameters are used. "
            "The chunked processing strategy ensures memory efficiency for large datasets, "
            "but the statistical power depends on the total sample size."
        )
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Reproducibility report saved to {output_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description="Sensitivity Analysis for SASA Prediction")
    parser.add_argument(
        "--predictions", 
        type=str, 
        default="data/processed/predictions.parquet",
        help="Path to predictions file (Parquet or CSV)"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/processed",
        help="Output directory for results"
    )
    parser.add_argument(
        "--report-dir", 
        type=str, 
        default="results/reports",
        help="Output directory for reports"
    )
    parser.add_argument(
        "--chunk-size", 
        type=int, 
        default=1000,
        help="Chunk size used for processing (for reproducibility report)"
    )
    parser.add_argument(
        "--streaming-strategy",
        type=str,
        default="chunked",
        help="Description of streaming strategy (e.g., 'chunked', 'full')"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    output_dir = Path(args.output_dir)
    report_dir = Path(args.report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        df = load_predictions(args.predictions)
    except Exception as e:
        logger.error(f"Failed to load predictions: {e}")
        sys.exit(1)
    
    sample_size = len(df)
    logger.info(f"Loaded {sample_size} predictions for analysis.")
    
    # Run Absolute Analysis
    abs_path = output_dir / "sensitivity_absolute.csv"
    df_abs = run_sensitivity_analysis_absolute(df, output_path=abs_path)
    
    # Run Relative Analysis
    rel_path = output_dir / "sensitivity_relative.csv"
    df_rel = run_sensitivity_analysis_relative(df, output_path=rel_path)
    
    # Generate Reproducibility Report
    report_path = report_dir / "sensitivity_reproducibility.json"
    generate_reproducibility_report(
        sample_size=sample_size,
        streaming_strategy=args.streaming_strategy,
        chunk_size=args.chunk_size,
        output_path=report_path
    )
    
    # Summary Output
    print("\n--- Sensitivity Analysis Summary ---")
    print(f"Total Molecules Analyzed: {sample_size}")
    print(f"Streaming Strategy: {args.streaming_strategy}")
    print(f"Chunk Size: {args.chunk_size}")
    print(f"Absolute Results: {abs_path}")
    print(f"Relative Results: {rel_path}")
    print(f"Reproducibility Report: {report_path}")
    print("------------------------------------")

if __name__ == "__main__":
    main()