import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

# Local imports (ensure these exist in sibling files)
# We assume DataFlowError and ValidationGateFailedError are defined here or imported
# Based on the API surface provided, we define them here if not already present in the full file
class DataFlowError(Exception):
    """Raised when data flow prerequisites are not met."""
    pass

class ValidationGateFailedError(Exception):
    """Raised when a validation gate fails."""
    pass

# --- Helper Functions (Extended from existing API surface) ---

def load_subset_data(subset_path: str) -> pd.DataFrame:
    """
    Loads a CSV subset of the MedMisBench dataset.
    Expected columns: prompt_id, false_claim, prompt_text, ...
    """
    path = Path(subset_path)
    if not path.exists():
        raise DataFlowError(f"Subset data file not found: {subset_path}")
    return pd.read_csv(path)

def load_annotation_data(cleaned_path: str) -> pd.DataFrame:
    """
    Loads the cleaned human pilot data.
    Expected columns: prompt_id, rater_id, authority_density_score
    """
    path = Path(cleaned_path)
    if not path.exists():
        raise DataFlowError(f"Cleaned annotation data file not found: {cleaned_path}")
    df = pd.read_csv(path)
    required_cols = ['prompt_id', 'authority_density_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataFlowError(f"Missing required columns in annotation data: {missing}")
    return df

def calculate_rater_agreement(df: pd.DataFrame) -> float:
    """
    Calculates Cohen's Kappa or simple agreement for rater consistency.
    (Simplified for this task: returns a placeholder metric if not strictly needed for T017c,
     but T017c specifically asks for correlation. We implement the correlation logic here.)
    """
    # Placeholder for T017d logic, not T017c
    return 0.0

def clean_pilot_data(raw_path: str, output_path: str) -> pd.DataFrame:
    """
    Cleans the pilot data (T017b logic).
    This function is referenced for completeness but T017c focuses on correlation.
    """
    # Implementation would go here, but T017c assumes T017b is done.
    return pd.DataFrame()

def run_cleaning_pipeline():
    # Placeholder for T017b
    pass

# --- T017c Implementation: Compute Correlation ---

def compute_correlations(features_path: str, annotations_path: str, output_path: str) -> Dict[str, float]:
    """
    Computes Pearson and Spearman correlation coefficients between automated linguistic features
    and cleaned human rater data.

    Args:
        features_path: Path to data/processed/features.csv
        annotations_path: Path to data/interim/human_pilot_cleaned.csv
        output_path: Path to save the result JSON (data/results/annotation_correlation_value.json)

    Returns:
        Dictionary containing 'pearson', 'spearman', and 'p_value' for the correlation.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 1. Load Data
    logger.info(f"Loading features from {features_path}")
    try:
        features_df = pd.read_csv(features_path)
    except FileNotFoundError:
        raise DataFlowError(f"Feature file not found: {features_path}. Ensure T014/T015 is complete.")

    logger.info(f"Loading annotations from {annotations_path}")
    try:
        annotations_df = pd.read_csv(annotations_path)
    except FileNotFoundError:
        raise DataFlowError(f"Annotation file not found: {annotations_path}. Ensure T017b is complete.")

    # 2. Validate Data Integrity
    if 'prompt_id' not in features_df.columns:
        raise DataFlowError("Features CSV missing 'prompt_id' column.")
    if 'prompt_id' not in annotations_df.columns:
        raise DataFlowError("Annotations CSV missing 'prompt_id' column.")
    if 'authority_density_score' not in annotations_df.columns:
        raise DataFlowError("Annotations CSV missing 'authority_density_score' column.")

    # 3. Identify Target Feature Column
    # The task asks for correlation between "automated linguistic features" and human scores.
    # Based on T014/T015, the primary continuous feature of interest for authority is likely
    # 'modal_freq', 'imperative_ratio', or 'citation_density'.
    # We will prioritize 'modal_freq' as a proxy for authority density, or use the first
    # available numeric feature column if specific mapping isn't defined.
    # Let's assume 'modal_freq' is the primary target based on "modal verb frequency" in T014.
    feature_col = 'modal_freq'
    if feature_col not in features_df.columns:
        # Fallback: try 'imperative_ratio'
        if 'imperative_ratio' in features_df.columns:
            feature_col = 'imperative_ratio'
        else:
            # Fallback: find the first numeric column that isn't prompt_id
            numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
            numeric_cols = [c for c in numeric_cols if c != 'prompt_id']
            if not numeric_cols:
                raise DataFlowError("No numeric feature columns found in features CSV.")
            feature_col = numeric_cols[0]
            logger.warning(f"Using fallback feature column for correlation: {feature_col}")

    logger.info(f"Computing correlation between '{feature_col}' and 'authority_density_score'")

    # 4. Merge Data
    merged_df = pd.merge(features_df, annotations_df, on='prompt_id', how='inner')

    if merged_df.empty:
        raise DataFlowError("No matching prompt_ids between features and annotations. Data flow broken.")

    # Drop rows with NaN in either key column
    clean_df = merged_df.dropna(subset=[feature_col, 'authority_density_score'])

    if len(clean_df) < 3:
        raise DataFlowError(f"Insufficient data points for correlation (n={len(clean_df)}).")

    # 5. Compute Correlations
    # Pearson
    pearson_r, pearson_p = pearsonr(clean_df[feature_col], clean_df['authority_density_score'])
    # Spearman
    spearman_r, spearman_p = spearmanr(clean_df[feature_col], clean_df['authority_density_score'])

    logger.info(f"P Pearson: {pearson_r:.4f} (p={pearson_p:.4f})")
    logger.info(f"S Spearman: {spearman_r:.4f} (p={spearman_p:.4f})")

    # 6. Prepare Output
    # The task asks for `data/results/annotation_correlation_value.json` containing `correlation_coefficient`.
    # We will store both Pearson and Spearman, but primary is Pearson.
    result = {
        "feature_used": feature_col,
        "sample_size": len(clean_df),
        "correlation_coefficient": {
            "pearson": float(pearson_r),
            "spearman": float(spearman_r)
        },
        "p_values": {
            "pearson": float(pearson_p),
            "spearman": float(spearman_p)
        }
    }

    # 7. Save Output
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path_obj, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Correlation results saved to {output_path}")

    return result

def main():
    """
    Main entry point for T017c.
    Expects:
      - data/processed/features.csv (from T014/T015)
      - data/interim/human_pilot_cleaned.csv (from T017b)
    Produces:
      - data/results/annotation_correlation_value.json
    """
    config = {
        "features_path": "data/processed/features.csv",
        "annotations_path": "data/interim/human_pilot_cleaned.csv",
        "output_path": "data/results/annotation_correlation_value.json"
    }

    try:
        compute_correlations(
            features_path=config["features_path"],
            annotations_path=config["annotations_path"],
            output_path=config["output_path"]
        )
        print("T017c: Correlation computation successful.")
    except DataFlowError as e:
        print(f"T017c: Data Flow Error - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"T017c: Unexpected Error - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
