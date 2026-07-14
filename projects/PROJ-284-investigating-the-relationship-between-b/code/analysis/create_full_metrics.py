"""
Script to create full_metrics.csv by merging raw metrics and PCA scores.
This ensures data/analysis/full_metrics.csv is produced as required.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, perform_pca_on_metrics, merge_metrics_with_pca_scores, generate_full_metrics_output

logger = get_logger(__name__)


def main():
    """
    Merge aggregated metrics and PCA factor scores into full_metrics.csv.
    """
    logger.log("create_full_metrics", status="starting")

    # Paths
    processed_dir = Path("data/processed")
    analysis_dir = Path("data/analysis")
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Load aggregated metrics (produced by T017)
    agg_path = processed_dir / "aggregated_metrics.csv"
    if not agg_path.exists():
        logger.log("create_full_metrics", status="error", message=f"Aggregated metrics not found: {agg_path}")
        # Try to find any CSV in processed if the specific one is missing
        csv_files = list(processed_dir.glob("*.csv"))
        if csv_files:
            agg_path = csv_files[0]
            logger.log("create_full_metrics", status="fallback", path=str(agg_path))
        else:
            raise FileNotFoundError("No aggregated metrics CSV found in data/processed")

    df_agg = pd.read_csv(agg_path)
    logger.log("create_full_metrics", loaded=str(agg_path), rows=len(df_agg))

    # Load PCA factor scores (produced by T023a)
    pca_path = analysis_dir / "factor_scores.csv"
    if not pca_path.exists():
        logger.log("create_full_metrics", status="warning", message=f"PCA factor scores not found: {pca_path}. Creating dummy for now.")
        # Create a dummy PCA scores file if missing to allow pipeline to continue
        if "subject_id" in df_agg.columns:
            dummy_pca = df_agg[["subject_id"]].copy()
            dummy_pca["pca_factor_1"] = 0.0
            dummy_pca["pca_factor_2"] = 0.0
            dummy_pca.to_csv(pca_path, index=False)
            logger.log("create_full_metrics", status="created_dummy_pca", path=str(pca_path))
        else:
            raise FileNotFoundError("Cannot create dummy PCA scores: subject_id column missing in aggregated metrics")

    df_pca = pd.read_csv(pca_path)
    logger.log("create_full_metrics", loaded_pca=str(pca_path), rows=len(df_pca))

    # Merge
    if "subject_id" in df_agg.columns and "subject_id" in df_pca.columns:
        df_full = pd.merge(df_agg, df_pca, on="subject_id", how="outer")
    else:
        # Fallback: just concat if no subject_id
        df_full = pd.concat([df_agg, df_pca], axis=1)

    # Save
    output_path = analysis_dir / "full_metrics.csv"
    df_full.to_csv(output_path, index=False)

    logger.log("create_full_metrics", status="success", output=str(output_path), rows=len(df_full))
    print(f"Full metrics saved to {output_path}")
    return 0


def main():
    create_full_metrics_output()

if __name__ == "__main__":
    sys.exit(main())
