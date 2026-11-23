import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from matminer.featurizers.composition import Magpie
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUTS_LOGS_DIR
from utils.logging import setup_logger
from utils.validation import check_missing_bond_lengths, check_degenerate_voronoi_cells

# Setup logger
logger = setup_logger(__name__)

def load_raw_data() -> pd.DataFrame:
    """Load raw data from CSV."""
    input_path = RAW_DATA_DIR / "oqmd_filtered.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} entries from {input_path}")
    return df

def compute_magpie_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Magpie compositional features.

    Args:
        df: DataFrame with 'composition' column

    Returns:
        DataFrame with Magpie features
    """
    logger.info("Computing Magpie features...")

    magpie = Magpie.from_preset("all")
    feature_names = magpie.feature_labels()

    # Extract composition strings
    compositions = df['composition'].tolist()

    # Compute features
    feature_df = magpie.featurize_dataframe(
        df,
        col_id="composition",
        ignore_errors=True,
        pbar=False
    )

    # Handle missing values
    missing_count = feature_df.isna().sum().sum()
    if missing_count > 0:
        logger.warning(f"Found {missing_count} missing values in Magpie features")
        # Impute with median
        for col in feature_df.columns:
            if feature_df[col].isna().any():
                median_val = feature_df[col].median()
                feature_df[col].fillna(median_val, inplace=True)
                logger.info(f"Imputed {feature_df[col].isna().sum()} missing values in {col} with median {median_val}")

    logger.info(f"Computed {len(feature_names)} Magpie features")
    return feature_df

def compute_voronoi_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Voronoi tessellation features.

    Args:
        df: DataFrame with structure data

    Returns:
        DataFrame with Voronoi features
    """
    logger.info("Computing Voronoi features...")

    # Placeholder for Voronoi feature computation
    # In production, use pymatgen's VoronoiNN to extract features
    voronoi_features = []
    skipped_count = 0

    for idx, row in df.iterrows():
        try:
            # This would require actual Structure objects
            # For now, create placeholder features
            features = {
                'voronoi_coordination_number': np.nan,
                'voronoi_face_area': np.nan,
                'voronoi_solid_angle': np.nan
            }
            voronoi_features.append(features)
        except Exception as e:
            skipped_count += 1
            logger.warning(f"Failed to compute Voronoi features for entry {row['material_id']}: {e}")

    if skipped_count > 0:
        logger.warning(f"Skipped {skipped_count} entries due to Voronoi computation failures")

    return pd.DataFrame(voronoi_features)

def compute_bond_length_histograms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute bond length histogram features.

    Args:
        df: DataFrame with structure data

    Returns:
        DataFrame with bond length histogram features
    """
    logger.info("Computing bond length histogram features...")

    # Placeholder for bond length histogram computation
    bond_features = []
    skipped_count = 0

    for idx, row in df.iterrows():
        try:
            # This would require actual Structure objects
            # For now, create placeholder features
            features = {
                'bond_length_mean': np.nan,
                'bond_length_std': np.nan,
                'bond_length_min': np.nan,
                'bond_length_max': np.nan
            }
            bond_features.append(features)
        except Exception as e:
            skipped_count += 1
            logger.warning(f"Failed to compute bond length features for entry {row['material_id']}: {e}")

    if skipped_count > 0:
        logger.warning(f"Skipped {skipped_count} entries due to bond length computation failures")

    return pd.DataFrame(bond_features)

def log_imputation(imputed_count: int, imputed_columns: list) -> None:
    """Log imputation statistics."""
    log_file = OUTPUTS_LOGS_DIR / "imputation_log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, 'a') as f:
        f.write(f"Imputed {imputed_count} values in columns: {imputed_columns}\n")

def main():
    """Main function for feature engineering."""
    logger.info("Starting feature engineering...")

    # Load raw data
    df = load_raw_data()

    # Compute Magpie features
    magpie_features = compute_magpie_features(df)

    # Save baseline features
    output_path = PROCESSED_DATA_DIR / "baseline_features.parquet"
    magpie_features.to_parquet(output_path)
    logger.info(f"Saved baseline features to {output_path}")

    # Log imputation
    imputed_count = magpie_features.isna().sum().sum()
    if imputed_count > 0:
        imputed_columns = magpie_features.columns[magpie_features.isna().any()].tolist()
        log_imputation(imputed_count, imputed_columns)

    # Compute Voronoi features (placeholder)
    voronoi_features = compute_voronoi_features(df)

    # Compute bond length histograms (placeholder)
    bond_features = compute_bond_length_histograms(df)

    # Combine all features
    all_features = pd.concat([magpie_features, voronoi_features, bond_features], axis=1)

    # Save augmented features
    augmented_output_path = PROCESSED_DATA_DIR / "augmented_features.parquet"
    all_features.to_parquet(augmented_output_path)
    logger.info(f"Saved augmented features to {augmented_output_path}")

    return all_features

if __name__ == "__main__":
    main()
