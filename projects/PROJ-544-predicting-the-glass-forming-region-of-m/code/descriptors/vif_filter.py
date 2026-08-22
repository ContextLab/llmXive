"""
VIF Filter Module for Glass-Forming Alloy Descriptors.

Reads VIF scores from data/derived/vif_report.json.
Removes descriptors with VIF > 33.
If all descriptors have VIF > 5.0, performs PCA on the three descriptors,
retains the first two components (>90% variance), and writes pca_components.csv.
Outputs the filtered feature file to data/derived/descriptor_vector_vif_filtered.csv.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants defined per task specification
VIF_THRESHOLD_REMOVAL = 33.0
VIF_THRESHOLD_PCA_TRIGGER = 5.0
PCA_VARIANCE_TARGET = 0.90
PCA_COMPONENTS_COUNT = 2

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VIF_REPORT_PATH = PROJECT_ROOT / "data" / "derived" / "vif_report.json"
DESCRIPTOR_INPUT_PATH = PROJECT_ROOT / "data" / "derived" / "descriptor_vector.csv"
DESCRIPTOR_OUTPUT_PATH = PROJECT_ROOT / "data" / "derived" / "descriptor_vector_vif_filtered.csv"
PCA_OUTPUT_PATH = PROJECT_ROOT / "data" / "derived" / "pca_components.csv"


def load_vif_report(path: Path) -> Dict[str, float]:
    """
    Loads the VIF report JSON file.

    Args:
        path: Path to vif_report.json

    Returns:
        Dictionary mapping descriptor names to their VIF scores.

    Raises:
        FileNotFoundError: If the report file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"VIF report not found at {path}. "
                                "Run scripts/compute_vif.py or code/descriptors/vif_report.py first.")

    with open(path, 'r') as f:
        data = json.load(f)

    # Handle potential nested structure if vif_report.json stores it under a key
    if isinstance(data, dict) and 'vif_scores' in data:
        return data['vif_scores']
    return data


def load_descriptors(path: Path) -> pd.DataFrame:
    """
    Loads the descriptor vector CSV.

    Args:
        path: Path to descriptor_vector.csv

    Returns:
        DataFrame containing descriptors.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Descriptor vector not found at {path}. "
                                "Run code/descriptors/compute.py first.")
    return pd.read_csv(path)


def filter_descriptors_by_vif(
    df: pd.DataFrame,
    vif_scores: Dict[str, float],
    threshold: float
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Filters descriptors based on VIF threshold.

    Args:
        df: DataFrame with descriptor columns.
        vif_scores: Dict of {descriptor_name: vif_score}.
        threshold: VIF threshold for removal.

    Returns:
        Tuple of (filtered_df, kept_columns, removed_columns).
    """
    # Identify columns in the dataframe that have VIF scores
    descriptor_cols = [col for col in df.columns if col in vif_scores]
    
    if not descriptor_cols:
        logger.warning("No descriptor columns found in dataframe matching VIF report keys.")
        return df, [], []

    # Determine which columns to keep (VIF <= threshold)
    kept_cols = [col for col in descriptor_cols if vif_scores.get(col, 0.0) <= threshold]
    removed_cols = [col for col in descriptor_cols if vif_scores.get(col, 0.0) > threshold]

    logger.info(f"VIF Filter: Keeping {len(kept_cols)} descriptors, removing {len(removed_cols)}.")
    logger.info(f"Removed: {removed_cols}")

    # Construct the new dataframe
    # We assume the dataframe contains other columns (like sample_id, phase_label) that must be preserved
    non_descriptor_cols = [col for col in df.columns if col not in descriptor_cols]
    final_cols = non_descriptor_cols + kept_cols
    
    return df[final_cols], kept_cols, removed_cols


def check_pca_trigger(vif_scores: Dict[str, float], threshold: float) -> bool:
    """
    Checks if ALL descriptors exceed the PCA trigger threshold.

    Args:
        vif_scores: Dict of VIF scores.
        threshold: The threshold (5.0) to check against.

    Returns:
        True if all descriptors have VIF > threshold.
    """
    if not vif_scores:
        return False
    return all(score > threshold for score in vif_scores.values())


def perform_pca_reduction(
    df: pd.DataFrame,
    descriptor_cols: List[str],
    target_variance: float = PCA_VARIANCE_TARGET,
    n_components: int = PCA_COMPONENTS_COUNT
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Performs PCA on the specified descriptor columns.

    Args:
        df: DataFrame.
        descriptor_cols: List of columns to apply PCA to.
        target_variance: Target explained variance ratio.
        n_components: Number of components to retain.

    Returns:
        Tuple of (new_df_with_pca_cols, pca_metadata).
    """
    logger.info(f"Performing PCA on {descriptor_cols}...")
    
    # Extract data
    X = df[descriptor_cols].values
    
    # Handle potential NaNs or infinite values if any (though unlikely in computed descriptors)
    if np.isnan(X).any() or np.isinf(X).any():
        logger.warning("NaN or Inf values found in descriptor data. Imputing NaNs with mean.")
        X = np.nan_to_num(X, nan=np.nanmean(X, axis=0))

    # Initialize PCA
    pca = PCA(n_components=n_components)
    pca.fit(X)
    
    # Check if we met the variance target
    explained_variance = np.sum(pca.explained_variance_ratio_)
    logger.info(f"PCA explained variance ratio: {explained_variance:.4f} (Target: {target_variance})")
    
    if explained_variance < target_variance:
        logger.warning(f"PCA with {n_components} components only explains {explained_variance:.4f} variance. "
                       f"Target was {target_variance}. Proceeding anyway as per task spec.")

    # Transform data
    pca_features = pca.transform(X)
    
    # Create new column names
    pca_col_names = [f"pca_comp_{i+1}" for i in range(n_components)]
    
    # Create metadata
    metadata = {
        "original_columns": descriptor_cols,
        "n_components_retained": n_components,
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "total_explained_variance": float(explained_variance),
        "components_matrix": pca.components_.tolist()
    }

    # Construct new dataframe
    # Remove old descriptor columns, keep non-descriptor columns, add PCA columns
    non_descriptor_cols = [col for col in df.columns if col not in descriptor_cols]
    new_df = df[non_descriptor_cols].copy()
    
    for i, col_name in enumerate(pca_col_names):
        new_df[col_name] = pca_features[:, i]

    return new_df, metadata


def write_pca_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """
    Writes PCA metadata to a CSV file (as required by task spec: 'pca_components.csv').
    Since metadata is structured, we will write the components matrix and variance info.
    The spec says 'writes data/derived/pca_components.csv'. 
    We will interpret this as a CSV containing the component loadings and variance info.
    """
    rows = []
    # Header row for metadata
    rows.append({
        "metric": "total_explained_variance",
        "value": metadata["total_explained_variance"],
        "components_retained": metadata["n_components_retained"]
    })
    
    # Component details
    for i, comp in enumerate(metadata["components_matrix"]):
        for j, loading in enumerate(comp):
            rows.append({
                "component": f"pca_comp_{i+1}",
                "original_feature": metadata["original_columns"][j],
                "loading": loading
            })
    
    df_pca = pd.DataFrame(rows)
    df_pca.to_csv(output_path, index=False)
    logger.info(f"PCA metadata written to {output_path}")


def main() -> int:
    """
    Main entry point for VIF filtering.
    """
    parser = argparse.ArgumentParser(
        description="Filter descriptors based on VIF scores or apply PCA if necessary."
    )
    parser.add_argument(
        "--vif-report",
        type=str,
        default=str(VIF_REPORT_PATH),
        help="Path to vif_report.json"
    )
    parser.add_argument(
        "--input-descriptors",
        type=str,
        default=str(DESCRIPTOR_INPUT_PATH),
        help="Path to input descriptor_vector.csv"
    )
    parser.add_argument(
        "--output-descriptors",
        type=str,
        default=str(DESCRIPTOR_OUTPUT_PATH),
        help="Path for output filtered descriptors"
    )
    parser.add_argument(
        "--output-pca",
        type=str,
        default=str(PCA_OUTPUT_PATH),
        help="Path for output PCA components metadata"
    )
    
    args = parser.parse_args()
    
    vif_path = Path(args.vif_report)
    input_path = Path(args.input_descriptors)
    output_path = Path(args.output_descriptors)
    pca_output_path = Path(args.output_pca)

    try:
        # 1. Load VIF Report
        logger.info(f"Loading VIF report from {vif_path}")
        vif_scores = load_vif_report(vif_path)
        logger.info(f"Loaded VIF scores for {len(vif_scores)} descriptors.")

        # 2. Load Descriptors
        logger.info(f"Loading descriptors from {input_path}")
        df = load_descriptors(input_path)
        logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns.")

        # 3. Check for PCA Trigger Condition: ALL descriptors > 5.0
        # We need to identify which columns in the dataframe correspond to VIF scores
        descriptor_cols_in_df = [col for col in df.columns if col in vif_scores]
        
        if not descriptor_cols_in_df:
            logger.error("No descriptor columns in the input dataframe match keys in the VIF report. "
                         "Cannot proceed with filtering or PCA.")
            return 1

        all_above_pca_threshold = check_pca_trigger(
            {k: v for k, v in vif_scores.items() if k in descriptor_cols_in_df},
            VIF_THRESHOLD_PCA_TRIGGER
        )

        if all_above_pca_threshold:
            logger.warning(f"All descriptors exceed VIF threshold {VIF_THRESHOLD_PCA_TRIGGER}. "
                           f"Triggering PCA reduction.")
            
            # Perform PCA
            df_filtered, pca_metadata = perform_pca_reduction(
                df, 
                descriptor_cols_in_df,
                target_variance=PCA_VARIANCE_TARGET,
                n_components=PCA_COMPONENTS_COUNT
            )
            
            # Write PCA metadata
            write_pca_metadata(pca_metadata, pca_output_path)
            
            # The output file will now contain PCA components
            # We overwrite the standard output path with the PCA result
            final_output_path = output_path
            logger.info(f"Writing PCA-filtered descriptors to {final_output_path}")
            df_filtered.to_csv(final_output_path, index=False)
            
            return 0

        # 4. Standard VIF Filtering (Remove VIF > 33)
        logger.info(f"Applying standard VIF filter (threshold={VIF_THRESHOLD_REMOVAL})")
        df_filtered, kept_cols, removed_cols = filter_descriptors_by_vif(
            df, 
            vif_scores, 
            VIF_THRESHOLD_REMOVAL
        )

        if not removed_cols:
            logger.info("No descriptors removed. No VIF scores exceeded the threshold.")

        # 5. Write Output
        logger.info(f"Writing filtered descriptors to {output_path}")
        df_filtered.to_csv(output_path, index=False)
        
        # Log summary
        logger.info(f"Process complete. Output saved to {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in VIF report: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during VIF filtering: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
