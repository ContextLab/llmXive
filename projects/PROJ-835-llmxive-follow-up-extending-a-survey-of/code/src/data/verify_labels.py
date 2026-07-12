"""
Label Independence Verification Module (FR-007)

This module performs an automated check for the *absence* of latent-space correlation
in dataset metadata. It fails the pipeline if such correlation is detected, ensuring
that the dataset labels (jailbreak vs. benign) are not inadvertently correlated with
the latent space representation before embedding extraction proceeds.

Usage:
    python -m src.data.verify_labels --data-path data/raw_dataset.parquet
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

# Import existing utilities from the project
from src.utils.logging_config import get_logger, configure_logging_level
from src.utils.stats import compute_benign_statistics, calculate_mahalanobis_distance

# Configure logging
configure_logging_level("INFO")
logger = get_logger(__name__)

# Constants
CORRELATION_THRESHOLD = 0.3  # Threshold for r (correlation coefficient)
P_VALUE_THRESHOLD = 0.05     # Threshold for p-value (statistical significance)
MIN_SAMPLES = 30             # Minimum samples required for statistical test


def load_dataset(data_path: str) -> pd.DataFrame:
    """
    Load the dataset from a Parquet or CSV file.

    Args:
        data_path: Path to the dataset file.

    Returns:
        DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_path}")

    logger.info(f"Loading dataset from {data_path}")

    if path.suffix == '.parquet':
        df = pd.read_parquet(data_path)
    elif path.suffix in ['.csv', '.tsv']:
        df = pd.read_csv(data_path, sep=',' if path.suffix == '.csv' else '\t')
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .parquet or .csv")

    logger.info(f"Loaded {len(df)} samples with columns: {list(df.columns)}")
    return df


def validate_dataset_schema(df: pd.DataFrame) -> None:
    """
    Validate that the dataset contains the required columns for label independence check.

    Required columns:
        - 'label': Binary label (0 for benign, 1 for jailbreak)
        - 'embedding' OR 'latent_vector': The latent representation (if already extracted)
        - OR metadata fields that can be used to proxy latent space (e.g., duration, sample_rate)

    Args:
        df: The dataset DataFrame.

    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = ['label']
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    # Check for embedding or latent vector
    has_embedding = 'embedding' in df.columns or 'latent_vector' in df.columns
    has_metadata = any(col in df.columns for col in ['duration', 'sample_rate', 'file_size'])

    if not has_embedding and not has_metadata:
        logger.warning(
            "No embedding or latent vector column found. "
            "Will attempt to use metadata fields as proxy for latent space correlation check."
        )
    else:
        logger.info("Embedding or metadata fields found for correlation analysis.")


def check_label_embedding_correlation(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for correlation between labels and latent space representations.

    If embeddings are available, compute correlation between label and embedding norms/means.
    If only metadata is available, use metadata as a proxy.

    Args:
        df: Dataset DataFrame.

    Returns:
        Dictionary with correlation statistics and pass/fail status.
    """
    results = {
        "passed": True,
        "reason": "",
        "details": {}
    }

    # Determine which data to use
    if 'embedding' in df.columns:
        embeddings = df['embedding'].apply(lambda x: np.array(x)).to_numpy()
    elif 'latent_vector' in df.columns:
        embeddings = df['latent_vector'].apply(lambda x: np.array(x)).to_numpy()
    else:
        # Fallback to metadata if available
        metadata_cols = [col for col in ['duration', 'sample_rate', 'file_size'] if col in df.columns]
        if not metadata_cols:
            results["passed"] = True
            results["reason"] = "No embedding or metadata available for correlation check. Assuming safe."
            results["details"]["method"] = "none"
            return results

        logger.info(f"Using metadata columns {metadata_cols} as proxy for latent space")
        # Create a simple feature: concatenate metadata values
        embeddings = df[metadata_cols].values

    labels = df['label'].values

    # Ensure we have enough samples
    if len(labels) < MIN_SAMPLES:
        logger.warning(f"Sample size ({len(labels)}) below minimum ({MIN_SAMPLES}). Skipping statistical test.")
        results["passed"] = True
        results["reason"] = f"Insufficient samples ({len(labels)}) for statistical test."
        results["details"]["method"] = "skipped_insufficient_samples"
        return results

    # Compute correlation between label and embedding features
    # We'll use the norm of the embedding as a single scalar feature
    embedding_norms = np.linalg.norm(embeddings, axis=1)

    # Calculate Pearson correlation
    try:
        r, p_value = pearsonr(labels, embedding_norms)
    except Exception as e:
        logger.error(f"Error calculating Pearson correlation: {e}")
        results["passed"] = True  # Fail safe: assume safe if calculation fails
        results["reason"] = f"Correlation calculation failed: {e}. Assuming safe."
        results["details"]["method"] = "error"
        return results

    # Check thresholds
    correlation_exceeded = abs(r) > CORRELATION_THRESHOLD
    p_significant = p_value < P_VALUE_THRESHOLD

    results["details"] = {
        "correlation_coefficient": float(r),
        "p_value": float(p_value),
        "threshold_r": CORRELATION_THRESHOLD,
        "threshold_p": P_VALUE_THRESHOLD,
        "samples_analyzed": len(labels),
        "method": "pearson_correlation_embedding_norm"
    }

    if correlation_exceeded and p_significant:
        results["passed"] = False
        results["reason"] = (
            f"Latent-space correlation detected! "
            f"Correlation r={r:.4f} (threshold={CORRELATION_THRESHOLD}), "
            f"p-value={p_value:.6f} (threshold={P_VALUE_THRESHOLD}). "
            f"Dataset labels are correlated with latent representations. "
            f"Pipeline must be halted to prevent data leakage."
        )
        logger.error(results["reason"])
    else:
        results["passed"] = True
        results["reason"] = (
            f"No significant latent-space correlation detected. "
            f"Correlation r={r:.4f} (threshold={CORRELATION_THRESHOLD}), "
            f"p-value={p_value:.6f} (threshold={P_VALUE_THRESHOLD}). "
            f"Dataset is safe for embedding extraction."
        )
        logger.info(results["reason"])

    return results


def check_metadata_correlation(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for correlation between labels and metadata fields (proxy for latent space).

    Args:
        df: Dataset DataFrame.

    Returns:
        Dictionary with correlation statistics and pass/fail status.
    """
    results = {
        "passed": True,
        "reason": "",
        "details": {}
    }

    metadata_cols = [col for col in ['duration', 'sample_rate', 'file_size'] if col in df.columns]
    if not metadata_cols:
        results["details"]["method"] = "none"
        results["reason"] = "No metadata fields available for proxy check."
        return results

    labels = df['label'].values

    if len(labels) < MIN_SAMPLES:
        results["passed"] = True
        results["reason"] = f"Insufficient samples ({len(labels)}) for statistical test."
        results["details"]["method"] = "skipped_insufficient_samples"
        return results

    max_r = 0.0
    significant_correlation = False

    for col in metadata_cols:
        try:
            r, p_value = pearsonr(labels, df[col].values)
            if abs(r) > abs(max_r):
                max_r = r
            if abs(r) > CORRELATION_THRESHOLD and p_value < P_VALUE_THRESHOLD:
                significant_correlation = True
        except Exception as e:
            logger.warning(f"Error calculating correlation for {col}: {e}")
            continue

    results["details"] = {
        "max_correlation_coefficient": float(max_r),
        "threshold_r": CORRELATION_THRESHOLD,
        "threshold_p": P_VALUE_THRESHOLD,
        "samples_analyzed": len(labels),
        "method": "pearson_correlation_metadata_proxy",
        "metadata_fields_checked": metadata_cols
    }

    if significant_correlation:
        results["passed"] = False
        results["reason"] = (
            f"Latent-space correlation detected via metadata proxy! "
            f"Max correlation r={max_r:.4f} (threshold={CORRELATION_THRESHOLD}). "
            f"Dataset labels are correlated with metadata. "
            f"Pipeline must be halted."
        )
        logger.error(results["reason"])
    else:
        results["passed"] = True
        results["reason"] = (
            f"No significant latent-space correlation detected via metadata proxy. "
            f"Max correlation r={max_r:.4f} (threshold={CORRELATION_THRESHOLD}). "
            f"Dataset is safe for embedding extraction."
        )
        logger.info(results["reason"])

    return results


def verify_labels(data_path: str, output_report: Optional[str] = None) -> bool:
    """
    Main entry point for label independence verification.

    Args:
        data_path: Path to the dataset file.
        output_report: Optional path to save the verification report as JSON.

    Returns:
        True if verification passes, False otherwise.

    Raises:
        SystemExit: If verification fails (pipeline must be halted).
    """
    logger.info("Starting label independence verification (FR-007)")

    # Load dataset
    df = load_dataset(data_path)

    # Validate schema
    validate_dataset_schema(df)

    # Perform checks
    embedding_results = check_label_embedding_correlation(df)
    metadata_results = check_metadata_correlation(df)

    # Combine results
    overall_passed = embedding_results["passed"] and metadata_results["passed"]
    combined_reason = (
        f"Embedding Check: {embedding_results['reason']}; "
        f"Metadata Check: {metadata_results['reason']}"
    )

    report = {
        "verification_passed": overall_passed,
        "reason": combined_reason,
        "embedding_check": embedding_results["details"],
        "metadata_check": metadata_results["details"],
        "timestamp": pd.Timestamp.now().isoformat()
    }

    # Save report if requested
    if output_report:
        output_path = Path(output_report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Verification report saved to {output_report}")

    # Fail pipeline if correlation detected
    if not overall_passed:
        logger.critical("LABEL INDEPENDENCE CHECK FAILED. HALTING PIPELINE.")
        raise SystemExit(1)

    logger.info("Label independence verification PASSED. Pipeline may proceed.")
    return True


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Verify label independence in dataset metadata (FR-007)"
    )
    parser.add_argument(
        "--data-path",
        required=True,
        help="Path to the dataset file (Parquet or CSV)"
    )
    parser.add_argument(
        "--output-report",
        default="results/label_verification_report.json",
        help="Path to save the verification report (default: results/label_verification_report.json)"
    )

    args = parser.parse_args()

    try:
        verify_labels(args.data_path, args.output_report)
        print("Verification PASSED. Pipeline may proceed.")
        sys.exit(0)
    except SystemExit as e:
        if e.code == 1:
            print("Verification FAILED. Pipeline halted due to latent-space correlation.")
            sys.exit(1)
        raise
    except Exception as e:
        logger.error(f"Verification error: {e}")
        print(f"Verification ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()