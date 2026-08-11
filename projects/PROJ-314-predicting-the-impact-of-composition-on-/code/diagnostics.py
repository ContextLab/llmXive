import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from scipy import stats
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Loaders (Assuming these exist or are defined inline based on context) ---
# The prompt API surface lists these as public names in diagnostics.py, 
# but their implementation details were omitted in the "omitted for prompt budget" section.
# I will implement robust versions of them here to ensure the file is self-contained and runnable,
# matching the expected API surface.

def load_processed_data() -> pd.DataFrame:
    """Load the cleaned and processed dataset."""
    path = Path("data/processed/step4_final.csv")
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found at {path}")
    return pd.read_csv(path)

def load_best_model() -> Any:
    """Load the best trained model."""
    import joblib
    path = Path("data/models/best_model.pkl")
    if not path.exists():
        raise FileNotFoundError(f"Best model file not found at {path}")
    return joblib.load(str(path))

def load_model_metrics() -> Dict[str, Any]:
    """Load model performance metrics."""
    path = Path("data/results/model_metrics.json")
    if not path.exists():
        raise FileNotFoundError(f"Model metrics file not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_baseline_metrics() -> Dict[str, Any]:
    """Load baseline predictor metrics."""
    path = Path("data/results/baseline_metrics.json")
    if not path.exists():
        raise FileNotFoundError(f"Baseline metrics file not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def train_leakage_check_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """Train a model without the 'primary_anion_cation_group' feature to check for leakage."""
    feature_to_exclude = 'primary_anion_cation_group'
    if feature_to_exclude in X.columns:
        X_leakage = X.drop(columns=[feature_to_exclude])
    else:
        X_leakage = X.copy()
        logger.warning(f"Feature '{feature_to_exclude}' not found in dataset. Skipping exclusion.")

    model = RandomForestRegressor(random_state=42, n_estimators=100)
    model.fit(X_leakage, y)
    return model

def check_leakage(X: pd.DataFrame, y: pd.Series, baseline_model: Any) -> Dict[str, Any]:
    """
    Compare model performance with and without 'primary_anion_cation_group'.
    Returns a report dict.
    """
    from sklearn.metrics import mean_absolute_error

    # Original model performance (assuming baseline_model was trained on full data)
    y_pred_full = baseline_model.predict(X)
    mae_full = mean_absolute_error(y, y_pred_full)

    # Train leakage check model (without the specific feature)
    leakage_model = train_leakage_check_model(X, y)
    y_pred_leakage = leakage_model.predict(X)
    mae_leakage = mean_absolute_error(y, y_pred_leakage)

    # Calculate drop
    if mae_full == 0:
        drop_pct = 0.0
    else:
        drop_pct = ((mae_leakage - mae_full) / mae_full) * 100

    # Flag if drop is less than 10% (meaning the feature wasn't critical, or leakage exists if the feature is a proxy)
    # The task says: "If performance drops by less than 10%, flag 'Potential Leakage'"
    # This implies if the model performs almost as well without the feature, the feature might be leaking info
    # or the feature isn't important. However, the specific instruction is:
    # "If performance drops by less than 10%, flag 'Potential Leakage'"
    potential_leakage = drop_pct < 10.0

    # 7. Generate Report
    report = {
        "mae_full": mae_full,
        "mae_leakage_excluded": mae_leakage,
        "performance_drop_pct": drop_pct,
        "potential_leakage_flag": potential_leakage,
        "warning_message": "Potential Leakage: Performance drop < 10% when excluding 'primary_anion_cation_group'" if potential_leakage else "No significant leakage detected."
    }

    # Save report
    output_path = Path("data/results/leakage_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Leakage check report saved to {output_path}")
    return report

def calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    Returns a DataFrame with feature names and VIF scores.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    # Handle categorical variables by one-hot encoding if necessary, 
    # but for VIF calculation on numeric features, we assume X is numeric.
    # If X contains non-numeric columns, we must drop them or encode them.
    # Assuming X passed here is numeric descriptors.
    if not np.issubdtype(X.values.dtype, np.number):
        # Simple encoding for categorical if present
        X_encoded = pd.get_dummies(X, drop_first=True)
    else:
        X_encoded = X

    vif_data = []
    for i, col in enumerate(X_encoded.columns):
        try:
            vif = variance_inflation_factor(X_encoded.values, i)
            vif_data.append({"feature": col, "vif": vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")

    vif_df = pd.DataFrame(vif_data)
    
    # Flag high collinearity (VIF > 5 or 10)
    vif_df["high_collinearity"] = vif_df["vif"] > 5.0

    # Save VIF results
    output_path = Path("data/results/vif_analysis.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(vif_df.to_dict(orient='records'), f, indent=2)

    logger.info(f"VIF analysis saved to {output_path}")
    return vif_df

def group_correlated_features(X: pd.DataFrame, threshold: float = 0.85) -> Dict[str, List[str]]:
    """
    Cluster highly correlated features for interpretive grouping.
    Uses correlation matrix to find groups of features with correlation > threshold.
    Returns a dictionary mapping cluster names (or representative feature) to list of features.
    """
    if X.empty:
        logger.warning("Empty DataFrame passed to group_correlated_features")
        return {}

    # Ensure numeric only
    X_numeric = X.select_dtypes(include=[np.number])
    if X_numeric.empty:
        logger.warning("No numeric features found for correlation analysis")
        return {}

    corr_matrix = X_numeric.corr().abs()

    # Select upper triangle of correlation matrix
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

    # Find features with correlation above threshold
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]

    if not to_drop:
        logger.info("No highly correlated features found above threshold.")
        return {}

    # Grouping logic: simple clustering based on high correlation
    # We'll create groups where features are connected by high correlation
    from collections import defaultdict, deque

    adj = defaultdict(set)
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            feat_i = corr_matrix.columns[i]
            feat_j = corr_matrix.columns[j]
            if corr_matrix.iloc[i, j] > threshold:
                adj[feat_i].add(feat_j)
                adj[feat_j].add(feat_i)

    visited = set()
    clusters = []

    for node in adj:
        if node not in visited:
            cluster = []
            queue = deque([node])
            visited.add(node)
            while queue:
                curr = queue.popleft()
                cluster.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            clusters.append(cluster)

    # Format output: cluster_id -> list of features
    # Or representative -> list
    result = {}
    for idx, cluster in enumerate(clusters):
        # Use the first feature as the representative key
        rep = cluster[0]
        result[rep] = cluster

    # Save cluster info
    output_path = Path("data/results/correlated_feature_clusters.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Correlated feature clusters saved to {output_path}")
    return result

def main():
    """Main execution for diagnostics tasks."""
    logger.info("Starting diagnostics module execution.")
    try:
        # Load data
        df = load_processed_data()
        
        # Identify target and features
        target_col = 'weibull_modulus'
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in data.")
        
        # Assume all other numeric columns are features, excluding target
        feature_cols = [c for c in df.columns if c != target_col and df[c].dtype in ['int64', 'float64']]
        X = df[feature_cols]
        y = df[target_col]

        # 1. Calculate VIF
        logger.info("Calculating VIF...")
        vif_df = calculate_vif(X)
        print(vif_df)

        # 2. Group Correlated Features
        logger.info("Grouping correlated features...")
        clusters = group_correlated_features(X)
        print(f"Found {len(clusters)} clusters of correlated features.")

        # 3. Check Leakage (requires a trained model)
        # We need to load the best model to compare
        try:
            best_model = load_best_model()
            # Check leakage
            logger.info("Checking for data leakage...")
            leakage_report = check_leakage(X, y, best_model)
            print(leakage_report)
        except FileNotFoundError as e:
            logger.warning(f"Skipping leakage check: {e}")

        logger.info("Diagnostics execution completed.")
    except Exception as e:
        logger.error(f"Error during diagnostics: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()