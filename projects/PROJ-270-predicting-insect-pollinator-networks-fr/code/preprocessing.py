import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from utils.logger import get_logger
from config import get_data_processed
from pathlib import Path
import json

logger = get_logger(__name__)

def winsorize_outliers(df: pd.DataFrame, lower_pct: float = 0.01, upper_pct: float = 0.99) -> pd.DataFrame:
    """
    Winsorize outliers in numeric columns of the DataFrame.
    
    Args:
        df: Input DataFrame
        lower_pct: Lower percentile for winsorization
        upper_pct: Upper percentile for winsorization
        
    Returns:
        DataFrame with winsorized values
    """
    df_winsorized = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        lower_bound = df[col].quantile(lower_pct)
        upper_bound = df[col].quantile(upper_pct)
        df_winsorized[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        
    return df_winsorized

def z_score_normalize(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Tuple[float, float]]]:
    """
    Apply Z-score normalization to numeric columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (normalized DataFrame, dict of (mean, std) for each column)
    """
    df_normalized = df.copy()
    stats = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()
        if std == 0:
            std = 1.0  # Avoid division by zero
        stats[col] = (mean, std)
        df_normalized[col] = (df[col] - mean) / std
        
    return df_normalized, stats

def encode_categorical_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """
    One-hot encode categorical features without data leakage.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (encoded DataFrame, dict of original categories per column)
    """
    df_encoded = df.copy()
    category_map = {}
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    
    for col in categorical_cols:
        # Store categories for potential inverse transform or validation
        categories = df[col].unique().tolist()
        category_map[col] = categories
        
        # One-hot encode
        dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)
        df_encoded = df_encoded.drop(columns=[col])
        df_encoded = pd.concat([df_encoded, dummies], axis=1)
        
    return df_encoded, category_map

def extract_sampling_effort(df: pd.DataFrame, effort_col: Optional[str] = 'sampling_effort') -> pd.DataFrame:
    """
    Extract and handle sampling effort metadata.
    
    Args:
        df: Input DataFrame
        effort_col: Name of the sampling effort column
        
    Returns:
        DataFrame with sampling effort as a feature
    """
    if effort_col and effort_col in df.columns:
        df['sampling_effort'] = df[effort_col].fillna(0)
        df = df.drop(columns=[effort_col])
    else:
        # If no sampling effort column, create a default (e.g., 1.0 for all)
        logger.warning(f"Sampling effort column '{effort_col}' not found. Using default value.")
        df['sampling_effort'] = 1.0
        
    return df

def build_feature_matrix(interactions_df: pd.DataFrame, traits_df: pd.DataFrame, 
                         ecosystem_id: str) -> pd.DataFrame:
    """
    Build unified feature matrix from interactions and trait data.
    
    Args:
        interactions_df: DataFrame with interaction data (plant, pollinator, ecosystem)
        traits_df: DataFrame with trait data for species
        ecosystem_id: Identifier for the current ecosystem
        
    Returns:
        Feature matrix with rows as plant-pollinator pairs and columns as traits + label
    """
    logger.info(f"Building feature matrix for ecosystem: {ecosystem_id}")
    
    # Merge interactions with plant traits
    merged = interactions_df.merge(traits_df, left_on='plant_species', right_on='species_id', how='left', suffixes=('_plant', '_pollinator'))
    
    # Merge with pollinator traits (assuming same traits_df structure)
    # This might need adjustment based on actual data structure
    # For now, we assume traits_df has both plant and pollinator traits
    
    # Create feature columns
    feature_cols = [col for col in merged.columns if col not in ['plant_species', 'pollinator_species', 'ecosystem_id']]
    
    feature_matrix = merged[feature_cols].copy()
    
    # Ensure label column exists
    if 'label' not in feature_matrix.columns:
        feature_matrix['label'] = 1  # Positive samples from interactions
        
    return feature_matrix

def save_feature_matrix(feature_matrix: pd.DataFrame, output_path: Path) -> None:
    """
    Save feature matrix to disk.
    
    Args:
        feature_matrix: DataFrame to save
        output_path: Path to save the file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    feature_matrix.to_csv(output_path, index=False)
    logger.info(f"Feature matrix saved to {output_path}")

def validate_ecosystem_count(valid_count: int, min_threshold: int = 8) -> bool:
    """
    Validate the count of valid ecosystems against a minimum threshold.
    
    Args:
        valid_count: Number of valid ecosystems retrieved
        min_threshold: Minimum required count (default 8)
        
    Returns:
        True if count meets threshold, False otherwise
        
    Note:
        This function logs a warning if count is below threshold but does NOT
        raise SystemExit. It allows the pipeline to proceed with reduced data.
    """
    if valid_count < min_threshold:
        logger.warning(
            f"Valid ecosystem count ({valid_count}) is below the recommended threshold "
            f"({min_threshold}). Proceeding with available data, but results may be limited."
        )
        return False
    else:
        logger.info(f"Valid ecosystem count ({valid_count}) meets the threshold ({min_threshold}).")
        return True

def run_validation_check(ingestion_output_path: str = "data/processed/ingestion_summary.json") -> int:
    """
    Run validation check on ingestion output to verify ecosystem count.
    
    Args:
        ingestion_output_path: Path to the ingestion summary file
        
    Returns:
        Number of valid ecosystems found
    """
    try:
        with open(ingestion_output_path, 'r') as f:
            summary = json.load(f)
        
        valid_count = summary.get('valid_ecosystem_count', 0)
        validate_ecosystem_count(valid_count)
        return valid_count
        
    except FileNotFoundError:
        logger.error(f"Ingestion summary file not found: {ingestion_output_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in ingestion summary file: {ingestion_output_path}")
        raise

if __name__ == "__main__":
    # Example usage for testing
    import sys
    if len(sys.argv) > 1:
        count = run_validation_check(sys.argv[1])
        print(f"Valid ecosystem count: {count}")
    else:
        print("Usage: python preprocessing.py <path_to_ingestion_summary.json>")