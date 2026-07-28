import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
import sys
from sklearn.metrics import mean_absolute_error, r2_score
from typing import Dict, Any, List, Tuple, Optional
from modeling import prepare_splits, train_models
from config import get_project_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate_models(
    X: pd.DataFrame, 
    y: pd.Series, 
    strat_col: Optional[str], 
    models: Dict[str, Any]
) -> Tuple[Dict[str, Dict[str, float]], pd.DataFrame]:
    """
    Evaluate models and return metrics.
    
    Returns:
        metrics: Dict mapping model name to {mae, r2}
        results_df: DataFrame with actual vs predicted for analysis
    """
    if strat_col and X[strat_col].nunique() >= 5:
        logger.info(f"Using stratified split on {strat_col}")
        X_train, X_test, y_train, y_test, strat_col_train, strat_col_test = prepare_splits(
            X, y, strat_col
        )
    else:
        logger.info("Using simple train/test split (insufficient classes for stratification)")
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        strat_col_train = strat_col_test = None

    metrics = {}
    results_list = []

    for name, model in models.items():
        logger.info(f"Evaluating {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        metrics[name] = {
            "mae": float(mae),
            "r2": float(r2),
            "test_size": len(y_test),
            "train_size": len(y_train)
        }
        
        results_list.append(pd.DataFrame({
            "model": name,
            "actual": y_test.values,
            "predicted": y_pred,
            "strat_group": strat_col_test if strat_col_test is not None else ["N/A"] * len(y_test)
        }))

    results_df = pd.concat(results_list, ignore_index=True)
    return metrics, results_df

def generate_stratification_report(X: pd.DataFrame, strat_col: str) -> Dict[str, Any]:
    """Generate a report on the distribution of the stratification column."""
    if strat_col not in X.columns:
        return {"error": f"Stratification column {strat_col} not found"}
    
    distribution = X[strat_col].value_counts().to_dict()
    total = len(X)
    distribution_pct = {k: (v / total) * 100 for k, v in distribution.items()}
    
    return {
        "column": strat_col,
        "unique_classes": int(X[strat_col].nunique()),
        "total_samples": total,
        "distribution": distribution,
        "distribution_percent": distribution_pct,
        "min_class_count": int(min(distribution.values())),
        "max_class_count": int(max(distribution.values()))
    }

def main():
    """
    Main entry point to run modeling, evaluation, and save metrics.
    This function orchestrates the US2 pipeline and ensures data/results/model_metrics.json is generated.
    """
    config = get_project_config()
    processed_data_path = Path(config.get("data.processed_path", "data/processed/cleaned_data.csv"))
    output_dir = Path(config.get("data.results_path", "data/results"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading processed data from {processed_data_path}")
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {processed_data_path}. Run US1 ingestion first.")
    
    df = pd.read_csv(processed_data_path)
    
    # Identify features and target
    # Based on T018/T019, we expect specific columns. 
    # We filter out non-numeric or non-feature columns.
    target_col = "weibull_modulus"
    strat_col = "primary_anion_cation_group"
    
    feature_cols = [c for c in df.columns if c not in [target_col, strat_col, "composition", "sample_count", "is_range_flag", "range_original", "range_uncertainty", "is_imputed"] and df[c].dtype in ['int64', 'float64']]
    
    logger.info(f"Features identified: {feature_cols}")
    logger.info(f"Target: {target_col}, Stratification: {strat_col}")
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
        
    X = df[feature_cols]
    y = df[target_col]
    
    # Train models (RF and GBM)
    models = train_models(X, y)
    
    # Evaluate
    metrics, results_df = evaluate_models(X, y, strat_col, models)
    
    # Generate Stratification Report
    strat_report = {}
    if strat_col and strat_col in df.columns:
        strat_report = generate_stratification_report(df, strat_col)
        # Check if split was valid
        if strat_report.get("unique_classes", 0) < 2:
            logger.warning("Stratification column has < 2 unique classes. Using hold-out logic.")
    
    # Compile final metrics artifact
    final_metrics = {
        "models": metrics,
        "stratification_report": strat_report,
        "feature_count": len(feature_cols),
        "total_samples": len(df),
        "target_distribution": {
            "mean": float(y.mean()),
            "std": float(y.std()),
            "min": float(y.min()),
            "max": float(y.max())
        }
    }
    
    output_path = output_dir / "model_metrics.json"
    with open(output_path, "w") as f:
        json.dump(final_metrics, f, indent=2)
        
    logger.info(f"Metrics saved to {output_path}")
    
    # Also save the detailed results dataframe for further analysis (optional but useful)
    results_path = output_dir / "model_predictions.csv"
    results_df.to_csv(results_path, index=False)
    logger.info(f"Predictions saved to {results_path}")
    
    return final_metrics

if __name__ == "__main__":
    main()
