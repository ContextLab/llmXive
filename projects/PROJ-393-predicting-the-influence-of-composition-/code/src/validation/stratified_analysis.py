import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from src.utils.logging_config import setup_logging, create_logger

logger = create_logger(__name__)

# Minimum samples required to train a model in a stratum
MIN_STRATUM_SAMPLES = 5

def load_features_data(file_path: str) -> pd.DataFrame:
    """Load the feature-engineered dataset."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {file_path}")
    df = pd.read_csv(file_path)
    
    # Parse composition if it's a string representation of a dict
    if 'composition' in df.columns and isinstance(df['composition'].iloc[0], str):
        df['composition'] = df['composition'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    
    return df

def get_strata_groups(df: pd.DataFrame, stratify_col: str = 'synthesis_method') -> Dict[str, pd.DataFrame]:
    """Group data by the stratification column."""
    if stratify_col not in df.columns:
        logger.warning(f"Stratification column '{stratify_col}' not found in data.")
        return {}
    
    groups = {}
    for val in df[stratify_col].unique():
        if pd.isna(val):
            continue
        groups[str(val)] = df[df[stratify_col] == val].copy()
    return groups

def train_model_on_stratum(
    stratum_df: pd.DataFrame,
    target_col: str = 'coercivity_oe',
    feature_cols: List[str] = None
) -> Tuple[Optional[Any], Dict[str, float], str]:
    """
    Train a model on a specific stratum.
    
    Returns:
        model: Trained model or None if skipped
        metrics: Dict of metrics (r2, mae)
        status: 'trained', 'skipped_insufficient_data', or 'skipped_no_target'
    """
    if feature_cols is None:
        # Default to common descriptor columns if they exist
        feature_cols = [col for col in stratum_df.columns if col.startswith('avg_') or col.startswith('VEC')]
        # Fallback to numeric columns if descriptors aren't found
        if not feature_cols:
            feature_cols = stratum_df.select_dtypes(include=[np.number]).columns.tolist()
            if target_col in feature_cols:
                feature_cols.remove(target_col)
    
    if not feature_cols:
        logger.warning("No feature columns found for training.")
        return None, {}, 'skipped_no_features'

    # Check for target
    if target_col not in stratum_df.columns:
        logger.warning(f"Target column '{target_col}' not found in stratum.")
        return None, {}, 'skipped_no_target'

    # Check sample size
    n_samples = len(stratum_df)
    if n_samples < MIN_STRATUM_SAMPLES:
        logger.warning(
            f"Stratum has {n_samples} samples (< {MIN_STRATUM_SAMPLES}). "
            f"Skipping model training to avoid unreliable results."
        )
        return None, {}, 'skipped_insufficient_data'

    X = stratum_df[feature_cols].dropna()
    y = stratum_df.loc[X.index, target_col]

    if len(X) < MIN_STRATUM_SAMPLES:
        logger.warning(
            f"After dropping NaNs, stratum has {len(X)} samples. "
            f"Skipping model training."
        )
        return None, {}, 'skipped_insufficient_data_after_dropna'

    if y.isna().any():
        logger.warning("Target contains NaNs after filtering. Skipping.")
        return None, {}, 'skipped_target_nan'

    # Split
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    except ValueError as e:
        logger.warning(f"Train/test split failed: {e}. Skipping.")
        return None, {}, 'skipped_split_failed'

    if len(X_train) < 2 or len(X_test) < 1:
        logger.warning("Split resulted in insufficient data. Skipping.")
        return None, {}, 'skipped_split_insufficient'

    # Train Random Forest (robust baseline)
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    return model, {'r2': r2, 'mae': mae}, 'trained'

def run_stratified_analysis(
    input_path: str,
    output_path: str,
    stratify_col: str = 'synthesis_method',
    target_col: str = 'coercivity_oe',
    feature_cols: List[str] = None
) -> Dict[str, Any]:
    """
    Run stratified analysis, skipping strata with insufficient data.
    
    Args:
        input_path: Path to feature-engineered CSV
        output_path: Path to save results JSON
        stratify_col: Column to group by
        target_col: Target variable
        feature_cols: List of feature columns to use
    
    Returns:
        Dictionary of results per stratum
    """
    logger.info(f"Starting stratified analysis on {input_path}")
    df = load_features_data(input_path)
    groups = get_strata_groups(df, stratify_col)

    if not groups:
        logger.warning("No valid strata found.")
        return {}

    results = {
        "stratify_column": stratify_col,
        "target_column": target_col,
        "min_samples_threshold": MIN_STRATUM_SAMPLES,
        "strata": {}
    }

    for name, group_df in groups.items():
        logger.info(f"Processing stratum: {name} (n={len(group_df)})")
        model, metrics, status = train_model_on_stratum(
            group_df, target_col, feature_cols
        )
        
        results["strata"][name] = {
            "sample_count": len(group_df),
            "status": status,
            "metrics": metrics if metrics else None
        }

        if status == 'trained':
            logger.info(f"  -> Trained. R2: {metrics['r2']:.3f}, MAE: {metrics['mae']:.3f}")
        else:
            logger.info(f"  -> Skipped ({status})")

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to JSON-serializable format
    import json
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Stratified analysis results saved to {output_path}")
    return results

def main():
    """Entry point for CLI execution."""
    setup_logging()
    input_file = "data/processed/alloys_features.csv"
    output_file = "data/processed/stratified_analysis_results.json"
    
    # Check if input exists
    if not Path(input_file).exists():
        logger.error(f"Input file {input_file} not found. Cannot run stratified analysis.")
        sys.exit(1)
    
    results = run_stratified_analysis(input_file, output_file)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    import json
    import sys
    main()
