import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)

# Constants for Construct Validity
MIN_CORRELATION_THRESHOLD = 0.3
MIN_R_SQUARED_THRESHOLD = 0.05

def encode_compositional_data(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """
    Encodes compositional data using one-hot encoding for categorical variables
    and calculates derived features like atomic radius variance.
    """
    if not feature_cols:
        return df

    # Identify categorical columns (simple heuristic: object dtype)
    cat_cols = [col for col in feature_cols if df[col].dtype == 'object']
    num_cols = [col for col in feature_cols if df[col].dtype in ['int64', 'float64', 'int32', 'float32']]

    if cat_cols:
        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        encoded = encoder.fit_transform(df[cat_cols])
        encoded_df = pd.DataFrame(
            encoded,
            columns=encoder.get_feature_names_out(cat_cols),
            index=df.index
        )
        df = pd.concat([df.drop(columns=cat_cols), encoded_df], axis=1)

    # Example derived feature: Atomic Radius Variance (placeholder logic if columns exist)
    # In a real scenario, specific atomic radius columns would be identified by name
    if 'atomic_radius' in df.columns:
        df['atomic_radius_variance'] = df.groupby('coating_id')['atomic_radius'].transform('var')

    return df

def standardize_surface_metrics(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """
    Standardizes surface metrics (RMS, skewness, kurtosis) using StandardScaler.
    """
    if not feature_cols:
        return df

    scaler = StandardScaler()
    for col in feature_cols:
        if col in df.columns:
            df[col] = scaler.fit_transform(df[[col]])
    return df

def perform_construct_validity_check(df: pd.DataFrame, proxy_cols: list, target_col: str) -> pd.DataFrame:
    """
    Performs a Construct Validity Check on derived proxies.
    
    For each proxy in `proxy_cols`:
    1. Calculates Pearson correlation with `target_col`.
    2. Fits a simple Linear Regression to calculate R².
    3. Excludes the proxy if |r| < 0.3 OR R² < 0.05.
    
    Args:
        df: The processed dataframe containing features and target.
        proxy_cols: List of column names representing derived proxies.
        target_col: The name of the target variable column.
        
    Returns:
        A dataframe containing ONLY the valid proxies (and original non-proxy columns).
        
    Raises:
        ValueError: If target_col is missing or data is invalid.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")

    valid_proxies = []
    logger.info(f"Starting Construct Validity Check for {len(proxy_cols)} proxies against '{target_col}'.")
    
    results_log = []

    for proxy in proxy_cols:
        if proxy not in df.columns:
            logger.warning(f"Proxy column '{proxy}' not found in dataframe. Skipping.")
            continue

        # Drop rows with NaN in proxy or target for this calculation
        valid_mask = df[[proxy, target_col]].dropna().index
        if len(valid_mask) < 2:
            logger.warning(f"Insufficient data for proxy '{proxy}'. Skipping.")
            continue

        subset = df.loc[valid_mask]
        X = subset[[proxy]].values
        y = subset[target_col].values

        # Calculate Pearson correlation
        corr_matrix = np.corrcoef(X.flatten(), y)
        r = corr_matrix[0, 1]
        
        # Calculate R² using Linear Regression
        model = LinearRegression()
        model.fit(X, y)
        r_squared = model.score(X, y)

        is_valid = abs(r) >= MIN_CORRELATION_THRESHOLD and r_squared >= MIN_R_SQUARED_THRESHOLD
        
        status = "VALID" if is_valid else "EXCLUDED"
        logger.info(f"Proxy '{proxy}': r={r:.4f}, R²={r_squared:.4f} -> {status}")
        
        results_log.append({
            "proxy": proxy,
            "correlation": r,
            "r_squared": r_squared,
            "status": status
        })

        if is_valid:
            valid_proxies.append(proxy)

    # Log summary
    excluded_count = len(proxy_cols) - len(valid_proxies)
    logger.info(f"Construct Validity Check complete. {excluded_count} proxies excluded.")

    # If the dataframe contains the proxy columns, drop the invalid ones
    # We assume 'df' contains all columns, and we want to return it with invalid proxies removed
    cols_to_drop = [p for p in proxy_cols if p not in valid_proxies]
    
    if cols_to_drop:
        logger.info(f"Dropping invalid proxy columns: {cols_to_drop}")
        df_validated = df.drop(columns=cols_to_drop)
    else:
        df_validated = df

    return df_validated

def create_preprocessing_pipeline(cat_features: list, num_features: list) -> Pipeline:
    """
    Creates a preprocessing pipeline for categorical and numerical features.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features),
            ('num', StandardScaler(), num_features)
        ])
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor)
    ])
    return pipeline

def create_preprocessing_pipeline_full(df: pd.DataFrame, target_col: str, proxy_cols: list = None) -> tuple:
    """
    Orchestrates the full preprocessing including Construct Validity Check.
    
    Returns:
        tuple: (processed_df, valid_proxy_cols)
    """
    if proxy_cols is None:
        proxy_cols = []

    # Step 1: Run Construct Validity Check first
    df_validated = perform_construct_validity_check(df, proxy_cols, target_col)
    
    # Determine which proxies are still present
    valid_proxy_cols = [col for col in proxy_cols if col in df_validated.columns]
    
    # Step 2: Identify remaining categorical and numerical features (excluding target)
    feature_cols = [col for col in df_validated.columns if col != target_col]
    cat_cols = [col for col in feature_cols if df_validated[col].dtype == 'object']
    num_cols = [col for col in feature_cols if df_validated[col].dtype in ['int64', 'float64', 'int32', 'float32']]

    # Step 3: Encode and Standardize
    if cat_cols:
        df_encoded = encode_compositional_data(df_validated, cat_cols)
    else:
        df_encoded = df_validated
        
    if num_cols:
        df_standardized = standardize_surface_metrics(df_encoded, num_cols)
    else:
        df_standardized = df_encoded

    return df_standardized, valid_proxy_cols

def main():
    """
    Main entry point for testing the preprocessing module.
    This function is intended for local validation and is not the primary pipeline runner.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create a mock dataset for testing the validity check logic
    data = {
        'target': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'valid_proxy': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], # Perfect correlation
        'weak_proxy': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],   # No correlation (constant)
        'noise_proxy': [1, 5, 2, 9, 3, 8, 4, 7, 5, 6], # Random noise
        'cat_feature': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B']
    }
    df = pd.DataFrame(data)
    
    proxies = ['valid_proxy', 'weak_proxy', 'noise_proxy']
    target = 'target'
    
    print("Original columns:", list(df.columns))
    df_result, valid_proxies = create_preprocessing_pipeline_full(df, target, proxies)
    
    print("Valid proxies found:", valid_proxies)
    print("Result columns:", list(df_result.columns))
    
    assert 'valid_proxy' in valid_proxies, "Valid proxy should be kept."
    assert 'weak_proxy' not in valid_proxies, "Weak proxy should be excluded."
    assert 'noise_proxy' not in valid_proxies, "Noise proxy should be excluded."
    
    logger.info("Construct Validity Check test passed.")

if __name__ == "__main__":
    main()