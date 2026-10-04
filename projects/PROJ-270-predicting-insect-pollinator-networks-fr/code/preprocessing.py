import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from utils.logger import get_logger
from config import get_data_processed
from pathlib import Path
import logging

logger = get_logger("preprocessing")

class MissingTemporalMetadataError(Exception):
    """Raised when temporal metadata is missing and required."""
    pass

def check_temporal_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate presence of start_date and end_date fields in ecosystem metadata.
    Logs a warning if missing.
    """
    if 'start_date' not in metadata or 'end_date' not in metadata:
        logger.warning(f"Missing temporal metadata (start_date/end_date) in ecosystem: {metadata.get('ecosystem_id', 'unknown')}")
        return False
    return True

def enforce_temporal_cooccurrence(metadata: Dict[str, Any]) -> None:
    """
    If temporal metadata is missing for an ecosystem, raise MissingTemporalMetadataError.
    This strictly enforces FR-007.
    """
    if not check_temporal_metadata(metadata):
        raise MissingTemporalMetadataError(
            f"Temporal metadata missing for ecosystem {metadata.get('ecosystem_id', 'unknown')}. "
            "Cannot proceed with temporal co-occurrence enforcement."
        )

def generate_negative_samples(
    interactions: pd.DataFrame,
    cooccurrence_matrix: pd.DataFrame,
    temporal_valid_mask: pd.Series
) -> pd.DataFrame:
    """
    Generate negative samples (unobserved links) based on Cartesian product of
    plant and pollinator species in the ecosystem, excluding observed links,
    filtered by temporal co-occurrence.
    """
    plants = interactions['plant_species'].unique()
    pollinators = interactions['pollinator_species'].unique()

    # Create all possible pairs
    all_pairs = pd.DataFrame([
        {'plant_species': p, 'pollinator_species': po}
        for p in plants for po in pollinators
    ])

    # Filter by temporal co-occurrence mask (assuming index alignment)
    # This assumes cooccurrence_matrix index aligns with the pair generation
    if temporal_valid_mask is not None:
        valid_pairs_mask = temporal_valid_mask
        all_pairs = all_pairs.loc[valid_pairs_mask]

    # Remove observed links
    observed_keys = set(
        zip(interactions['plant_species'], interactions['pollinator_species'])
    )
    negative_samples = all_pairs[
        ~all_pairs.apply(lambda row: (row['plant_species'], row['pollinator_species']) in observed_keys, axis=1)
    ]
    negative_samples['link_label'] = 0
    return negative_samples

def validate_negative_samples(negative_samples: pd.DataFrame, cooccurrence_matrix: pd.DataFrame) -> bool:
    """
    Assert all negative pairs exist in the co-occurrence matrix derived from T014
    and satisfy the temporal constraint.
    """
    # Check if all negative pairs are in the cooccurrence matrix
    # Assuming cooccurrence matrix index is (plant, pollinator) or similar structure
    # Simplified check: ensure no negative pair violates co-occurrence
    for idx, row in negative_samples.iterrows():
        # Logic depends on specific cooccurrence structure; assuming boolean check
        if not cooccurrence_matrix.loc[(row['plant_species'], row['pollinator_species']), 'valid']:
            logger.error(f"Negative sample {row['plant_species']}-{row['pollinator_species']} violates co-occurrence.")
            return False
    return True

def median_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply median imputation to all continuous columns in feature_matrix.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
    return df

def flag_missingness(df: pd.DataFrame, threshold: float = 0.15) -> pd.DataFrame:
    """
    Flag ecosystem if missingness > 15% and log warning.
    """
    missing_ratio = df.isnull().sum() / len(df)
    high_missing_cols = missing_ratio[missing_ratio > threshold]
    if not high_missing_cols.empty:
        logger.warning(f"High missingness detected (>15%) in columns: {list(high_missing_cols.index)}")
    return df

def winsorize_outliers(df: pd.DataFrame, lower_percentile: float = 1, upper_percentile: float = 99) -> pd.DataFrame:
    """
    Winsorize continuous columns at extreme percentiles.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        lower = df[col].quantile(lower_percentile / 100)
        upper = df[col].quantile(upper_percentile / 100)
        df[col] = df[col].clip(lower=lower, upper=upper)
    return df

def z_score_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply z-score normalization to continuous columns after winsorization.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()
        if std > 0:
            df[col] = (df[col] - mean) / std
        else:
            df[col] = 0.0
    return df

def one_hot_encode(df: pd.DataFrame, columns: List[str], drop_unknown: bool = True) -> pd.DataFrame:
    """
    One-hot encode categorical columns.
    """
    if not columns:
        return df
    encoded = pd.get_dummies(df, columns=columns, drop_first=True, dummy_na=not drop_unknown)
    return encoded

def extract_sampling_effort(df: pd.DataFrame, effort_col: str = 'sampling_effort') -> pd.DataFrame:
    """
    Extract sampling effort column if present, otherwise create a default/normalized column.
    """
    if effort_col not in df.columns:
        logger.warning(f"Column '{effort_col}' not found. Creating default effort column.")
        df[effort_col] = 1.0
    return df

def assemble_feature_matrix(
    interactions: pd.DataFrame,
    traits: pd.DataFrame,
    effort_col: str = 'sampling_effort'
) -> pd.DataFrame:
    """
    Assemble feature matrix: Rows: plant-pollinator pairs;
    Columns: [trait_1,..., trait_n, sampling_effort, link_label].
    """
    # Merge traits with interactions
    # Assuming traits has 'species' column matching both plant and pollinator
    # This is a simplified merge logic; real implementation might need more complex joining
    df_plants = traits.rename(columns={'species': 'plant_species'})
    df_pollinators = traits.rename(columns={'species': 'pollinator_species'})

    merged = interactions.merge(df_plants, on='plant_species', how='left')
    merged = merged.merge(df_pollinators, on='pollinator_species', how='left', suffixes=('_plant', '_pollinator'))

    # Combine trait columns (simplified: just take plant traits + pollinator traits)
    # In reality, one might average or concatenate specific trait vectors
    trait_cols = [c for c in merged.columns if c.startswith('trait_')]
    for col in trait_cols:
        if f"{col}_plant" in merged.columns and f"{col}_pollinator" in merged.columns:
            merged[col] = merged[f"{col}_plant"].fillna(0) + merged[f"{col}_pollinator"].fillna(0)
            merged.drop(columns=[f"{col}_plant", f"{col}_pollinator"], inplace=True)

    # Ensure effort column exists
    merged = extract_sampling_effort(merged, effort_col)

    # Add link label (1 for observed)
    merged['link_label'] = 1

    return merged

def exclude_species_ids(df: pd.DataFrame, id_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Ensure no species/ID columns remain in the final feature matrix.
    Removes columns like 'plant_species', 'pollinator_species', or any column
    containing 'species', 'id', or 'taxon' in the name if not explicitly kept.
    """
    if id_columns is None:
        # Common species/ID column patterns to exclude
        patterns = ['species', 'id', 'taxon', 'plant_species', 'pollinator_species']
        cols_to_drop = [col for col in df.columns if any(p in col.lower() for p in patterns)]
    else:
        cols_to_drop = [col for col in id_columns if col in df.columns]

    if cols_to_drop:
        logger.info(f"Dropping species/ID columns: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)

    return df

def save_feature_matrix(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the feature matrix to CSV.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Feature matrix saved to {output_file}")

def process_in_chunks(
    input_path: str,
    output_path: str,
    chunk_size: int = 10000,
    process_func: Optional[callable] = None
) -> None:
    """
    Read CSV in chunks, process, and append to final dataframe.
    """
    if process_func is None:
        process_func = lambda x: x

    first_chunk = True
    for chunk in pd.read_csv(input_path, chunksize=chunk_size):
        processed_chunk = process_func(chunk)
        if first_chunk:
            processed_chunk.to_csv(output_path, index=False)
            first_chunk = False
        else:
            processed_chunk.to_csv(output_path, mode='a', header=False, index=False)

def validate_ecosystem_count(count: int, min_threshold: int = 8) -> bool:
    """
    Validate ecosystem count. If < min_threshold, log warning and return True (proceed).
    """
    if count < min_threshold:
        logger.warning(f"Warning: valid_count ({count}) < {min_threshold}. Proceeding with reduced sample size.")
        return True
    return True

def run_validation_check(ecosystem_count: int) -> None:
    """
    Wrapper to run validation check and log results.
    """
    validate_ecosystem_count(ecosystem_count)