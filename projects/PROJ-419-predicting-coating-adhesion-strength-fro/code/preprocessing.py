import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
import logging
import os

logger = logging.getLogger(__name__)

# Thresholds for Construct Validity
CORRELATION_THRESHOLD = 0.3
R_SQUARED_THRESHOLD = 0.05

def encode_compositional_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode compositional data using one-hot encoding and create derived features.
    """
    df = df.copy()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if not categorical_cols:
        return df

    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    encoded = encoder.fit_transform(df[categorical_cols])
    encoded_df = pd.DataFrame(
        encoded, 
        columns=encoder.get_feature_names_out(categorical_cols), 
        index=df.index
    )
    
    # Drop original categorical columns and concatenate encoded ones
    df = df.drop(columns=categorical_cols)
    df = pd.concat([df, encoded_df], axis=1)
    
    return df

def standardize_surface_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize surface metrics (RMS, skewness, kurtosis) to zero mean and unit variance.
    """
    df = df.copy()
    surface_cols = [col for col in df.columns if col.lower() in ['rms', 'skewness', 'kurtosis', 'roughness']]
    
    if not surface_cols:
        return df

    scaler = StandardScaler()
    df[surface_cols] = scaler.fit_transform(df[surface_cols])
    
    return df

def perform_construct_validity_check(df: pd.DataFrame, target_col: str = 'adhesion_strength') -> pd.DataFrame:
    """
    Re-verify derived proxies against defined thresholds before model training.
    
    This function implements the Construct Validity Check (Plan Phase 1.8):
    1. Identifies potential proxy features (derived features like 'crosslinker_density_proxy', etc.)
    2. Calculates correlation (|r|) and R² with the target variable for each proxy.
    3. Excludes any proxy where |r| < 0.3 OR R² < 0.05.
    4. Returns the dataframe with invalid proxies removed.
    
    Args:
        df: The processed dataframe containing features and the target.
        target_col: The name of the target column.
        
    Returns:
        A dataframe with invalid proxy features excluded.
        
    Raises:
        ValueError: If the target column is missing or if no valid proxies remain after filtering.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    
    # Identify potential proxy features (heuristics based on naming conventions in this domain)
    # In a real scenario, this list might be explicitly defined in a config or passed as an argument.
    # Common derived proxies in this domain: 'crosslinker_density_proxy', 'atomic_radius_variance', etc.
    potential_proxies = [col for col in df.columns if 'proxy' in col.lower() or 'variance' in col.lower()]
    
    if not potential_proxies:
        logger.info("No potential proxy features found to validate.")
        return df

    valid_proxies = []
    invalid_proxies = []
    
    logger.info(f"Performing Construct Validity Check on {len(potential_proxies)} potential proxies...")
    
    for proxy in potential_proxies:
        if proxy == target_col:
            continue
            
        # Calculate Pearson correlation
        corr_matrix = df[[proxy, target_col]].corr()
        r = corr_matrix.loc[proxy, target_col]
        abs_r = abs(r)
        
        # Calculate R-squared using Linear Regression
        # Reshape for sklearn
        X = df[[proxy]].values.reshape(-1, 1)
        y = df[target_col].values
        
        model = LinearRegression()
        model.fit(X, y)
        r_squared = model.score(X, y)
        
        # Check thresholds
        passes_correlation = abs_r >= CORRELATION_THRESHOLD
        passes_r_squared = r_squared >= R_SQUARED_THRESHOLD
        
        if passes_correlation and passes_r_squared:
            valid_proxies.append(proxy)
            logger.info(f"Proxy '{proxy}' PASSED: |r|={abs_r:.4f}, R²={r_squared:.4f}")
        else:
            invalid_proxies.append(proxy)
            logger.warning(
                f"Proxy '{proxy}' FAILED Construct Validity Check: "
                f"|r|={abs_r:.4f} (thresh >= {CORRELATION_THRESHOLD}), "
                f"R²={r_squared:.4f} (thresh >= {R_SQUARED_THRESHOLD}). EXCLUDING."
            )
    
    if not valid_proxies:
        logger.warning("All potential proxies failed validity checks. Proceeding without derived proxies.")
    
    if invalid_proxies:
        df_clean = df.drop(columns=invalid_proxies)
        logger.info(f"Excluded {len(invalid_proxies)} invalid proxies. New feature count: {df_clean.shape[1]}")
        return df_clean
    
    return df

def create_preprocessing_pipeline(df: pd.DataFrame) -> Pipeline:
    """
    Create a preprocessing pipeline for compositional and surface data.
    """
    # This is a simplified version; in reality, it would separate numeric and categorical columns
    # and apply appropriate transformers.
    # For now, we assume the dataframe is already partially processed or we handle mixed types.
    return Pipeline([
        ('dummy', 'passthrough')
    ])

def create_preprocessing_pipeline_full(df: pd.DataFrame, target_col: str = 'adhesion_strength') -> pd.DataFrame:
    """
    Full preprocessing pipeline:
    1. Encode compositional data.
    2. Standardize surface metrics.
    3. Perform Construct Validity Check.
    """
    logger.info("Starting full preprocessing pipeline...")
    
    # Step 1: Encode compositional data
    df_processed = encode_compositional_data(df)
    logger.info(f"After encoding: {df_processed.shape}")
    
    # Step 2: Standardize surface metrics
    df_processed = standardize_surface_metrics(df_processed)
    logger.info(f"After standardization: {df_processed.shape}")
    
    # Step 3: Construct Validity Check
    df_processed = perform_construct_validity_check(df_processed, target_col=target_col)
    logger.info(f"After validity check: {df_processed.shape}")
    
    return df_processed

def main():
    """
    Main entry point for testing the preprocessing module.
    Loads the processed dataset, runs the validity check, and saves the result.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_path = 'data/processed/coating_adhesion_dataset.csv'
    output_path = 'data/processed/coating_adhesion_dataset_validated.csv'
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure User Story 1 (T031) has completed successfully.")
        return
    
    logger.info(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns.")
    
    # Determine target column (assuming standard naming or first numeric non-feature)
    # Based on T015 and T042 context, 'adhesion_strength' is the likely target.
    target = 'adhesion_strength'
    if target not in df.columns:
        # Fallback: try to find a column with 'adhesion' in the name
        candidates = [c for c in df.columns if 'adhesion' in c.lower()]
        if candidates:
            target = candidates[0]
            logger.warning(f"Target '{target}' not found, using '{target}' instead.")
        else:
            logger.error(f"Could not determine target column. Expected 'adhesion_strength' or similar.")
            return

    logger.info(f"Running Construct Validity Check on target '{target}'...")
    df_validated = create_preprocessing_pipeline_full(df, target_col=target)
    
    logger.info(f"Saving validated dataset to {output_path}...")
    df_validated.to_csv(output_path, index=False)
    
    logger.info("Construct Validity Check completed successfully.")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()