import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
def ensure_dirs() -> Path:
    """Create necessary output directories if they don't exist."""
    validation_dir = Path("data/validation")
    validation_dir.mkdir(parents=True, exist_ok=True)
    return validation_dir

def load_models(model_dir: Path = Path("data/models")) -> Dict[str, Any]:
    """Load trained models from disk."""
    models = {}
    model_files = {
        "rf": "rf_model.joblib",
        "gb": "gb_model.joblib",
        "lr": "lr_model.joblib"
    }
    
    for name, filename in model_files.items():
        model_path = model_dir / filename
        if model_path.exists():
            try:
                models[name] = joblib.load(model_path)
                logger.info(f"Loaded model: {name}")
            except Exception as e:
                logger.warning(f"Failed to load {name} model: {e}")
        else:
            logger.warning(f"Model file not found: {model_path}")
    
    return models

def load_test_data(data_path: Path = Path("data/processed/processed_data.csv")) -> Tuple[pd.DataFrame, List[str]]:
    """Load test data and return features and targets."""
    if not data_path.exists():
        raise FileNotFoundError(f"Test data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    # Assuming standard columns based on project specs
    target_cols = ["langmuir_capacity", "henry_constant"]
    feature_cols = [col for col in df.columns if col not in target_cols + ["material_id", "adsorbate_smiles"]]
    
    # Filter to only numeric features
    numeric_features = []
    for col in feature_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_features.append(col)
    
    return df, numeric_features

def get_best_model(models: Dict[str, Any], metrics_file: Path = Path("data/models/metrics.json")) -> Tuple[Optional[Any], str]:
    """Identify the best model based on saved metrics."""
    if not metrics_file.exists():
        logger.warning("Metrics file not found, defaulting to Random Forest")
        if "rf" in models:
            return models["rf"], "rf"
        return None, ""
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    best_model_name = None
    best_r2 = -np.inf
    
    for model_name, model_metrics in metrics.items():
        # Average R2 if multiple targets, or pick the first one if single
        r2_val = model_metrics.get("r2_score", model_metrics.get("mean_r2", -np.inf))
        if r2_val > best_r2:
            best_r2 = r2_val
            best_model_name = model_name
    
    if best_model_name and best_model_name in models:
        logger.info(f"Best model selected: {best_model_name} with R2={best_r2:.4f}")
        return models[best_model_name], best_model_name
    
    logger.warning("No suitable best model found, defaulting to RF")
    if "rf" in models:
        return models["rf"], "rf"
    return None, ""

def retrain_top_features(
    data: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = "langmuir_capacity",
    top_n: int = 3,
    validation_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Retrain a model using only the top N features (based on feature importance)
    and verify R2 >= 0.60. Generates SC-003 report.
    
    Args:
        data: DataFrame containing features and targets
        feature_cols: List of all feature column names
        target_col: Name of the target column
        top_n: Number of top features to use
        validation_file: Path to save the SC-003 report JSON
    
    Returns:
        Dictionary containing retraining results and report data
    """
    logger.info(f"Starting retraining on top {top_n} features for target: {target_col}")
    
    # Drop non-feature columns
    X_full = data[feature_cols].copy()
    y = data[target_col].dropna()
    X_full = X_full.iloc[:len(y)]
    
    # Remove rows with missing values in features
    mask = X_full.notna().all(axis=1)
    X_clean = X_full[mask]
    y_clean = y[mask]
    
    if len(X_clean) < 10:
        logger.error(f"Insufficient data after cleaning: {len(X_clean)} samples")
        raise ValueError("Insufficient data for training")
    
    # Train a Random Forest on ALL features to get importance rankings
    rf_full = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_full.fit(X_clean, y_clean)
    importances = rf_full.feature_importances_
    
    # Create a DataFrame for sorting
    feat_imp_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": importances
    }).sort_values("importance", ascending=False)
    
    top_features = feat_imp_df["feature"].head(top_n).tolist()
    logger.info(f"Top {top_n} features selected: {top_features}")
    
    # Retrain on top features only
    X_top = X_clean[top_features]
    
    # Split data for validation (simple train/test split since we need to verify performance)
    # Using 80/20 split
    split_idx = int(len(X_top) * 0.8)
    X_train, X_test = X_top.iloc[:split_idx], X_top.iloc[split_idx:]
    y_train, y_test = y_clean.iloc[:split_idx], y_clean.iloc[split_idx:]
    
    # Train model on top features
    model_top = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model_top.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model_top.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"R² score on top {top_n} features: {r2:.4f}")
    
    # Determine if SC-003 is satisfied
    sc003_satisfied = r2 >= 0.60
    
    # Prepare report
    report = {
        "status": "success",
        "top_n": top_n,
        "selected_features": top_features,
        "r2_score": float(r2),
        "sc003_satisfied": sc003_satisfied,
        "sc003_criteria": "R² >= 0.60 when using only top 3 descriptors",
        "model_type": "RandomForestRegressor",
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    # Save report if path provided
    if validation_file:
        with open(validation_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"SC-003 report saved to {validation_file}")
    
    return report

def generate_shap_summary_plot(model: Any, X: pd.DataFrame, output_path: Path):
    """Generate SHAP summary plot (requires shap library)."""
    try:
        import shap
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)
        shap.summary_plot(shap_values, X, show=False)
        import matplotlib.pyplot as plt
        plt.savefig(output_path)
        plt.close()
        logger.info(f"SHAP summary plot saved to {output_path}")
    except ImportError:
        logger.warning("SHAP library not installed. Skipping SHAP plot generation.")
    except Exception as e:
        logger.error(f"Error generating SHAP plot: {e}")

def generate_partial_dependence_plots(model: Any, X: pd.DataFrame, features: List[str], output_dir: Path):
    """Generate Partial Dependence Plots for top features."""
    try:
        from sklearn.inspection import PartialDependenceDisplay
        import matplotlib.pyplot as plt
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for feat in features:
            fig, ax = plt.subplots()
            PartialDependenceDisplay.from_estimator(model, X, [feat], ax=ax)
            plt.title(f"Partial Dependence: {feat}")
            plt.savefig(output_dir / f"pdp_{feat}.png")
            plt.close()
            logger.info(f"Saved PDP for {feat}")
    except ImportError:
        logger.warning("Matplotlib or sklearn missing. Skipping PDP generation.")
    except Exception as e:
        logger.error(f"Error generating PDP: {e}")

def validate_consensus(top_features: List[str], consensus_list: List[str] = None) -> Dict[str, Any]:
    """Validate top features against literature consensus."""
    if consensus_list is None:
        consensus_list = ["polarizability", "kinetic_diameter", "lennard_jones_energy", 
                        "quadrupole_moment", "molecular_volume"]
    
    matches = [f for f in top_features if f in consensus_list]
    match_ratio = len(matches) / len(top_features) if top_features else 0
    
    return {
        "top_features": top_features,
        "consensus_matches": matches,
        "match_ratio": match_ratio,
        "sc002_satisfied": match_ratio >= 0.66  # At least 2/3 match
    }

def run_shap_analysis_pipeline(
    data_path: Path = Path("data/processed/processed_data.csv"),
    model_dir: Path = Path("data/models"),
    output_dir: Path = Path("data/validation"),
    top_n: int = 3
):
    """
    Run the full SHAP analysis pipeline including:
    1. Loading models and data
    2. Generating SHAP plots
    3. Validating consensus
    4. Retraining on top features (SC-003)
    """
    logger.info("Starting SHAP analysis pipeline")
    
    # Ensure directories
    output_dir = ensure_dirs()
    plot_dir = Path("figures/shap")
    plot_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        df, feature_cols = load_test_data(data_path)
        logger.info(f"Loaded {len(df)} samples with {len(feature_cols)} features")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return
    
    # Load models
    models = load_models(model_dir)
    if not models:
        logger.error("No models loaded. Cannot proceed.")
        return
    
    # Get best model
    best_model, model_name = get_best_model(models)
    if best_model is None:
        logger.error("No best model found.")
        return
    
    # Generate SHAP plots
    try:
        generate_shap_summary_plot(best_model, df[feature_cols], plot_dir / "shap_summary.png")
    except Exception as e:
        logger.error(f"SHAP plot generation failed: {e}")
    
    # Validate consensus (SC-002)
    # Note: In a real scenario, we would extract top features from SHAP values
    # Here we use a placeholder logic or assume the model's feature importances
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        feat_imp_df = pd.DataFrame({
            "feature": feature_cols,
            "importance": importances
        }).sort_values("importance", ascending=False)
        top_features = feat_imp_df["feature"].head(top_n).tolist()
        
        consensus_report = validate_consensus(top_features)
        consensus_path = output_dir / "sc002_match_report.json"
        with open(consensus_path, 'w') as f:
            json.dump(consensus_report, f, indent=2)
        logger.info(f"Consensus report saved to {consensus_path}")
    
    # Retrain on top features (SC-003)
    try:
        # Use the first target column as default
        target_col = "langmuir_capacity"
        if target_col not in df.columns:
            target_col = df.columns[0] # Fallback
        
        sc003_report = retrain_top_features(
            df, 
            feature_cols, 
            target_col=target_col, 
            top_n=top_n, 
            validation_file=output_dir / "sc003_r2_report.json"
        )
        logger.info(f"SC-003 R² Score: {sc003_report['r2_score']:.4f}")
        
    except Exception as e:
        logger.error(f"SC-003 retraining failed: {e}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="SHAP Analysis Pipeline")
    parser.add_argument("--data", type=str, default="data/processed/processed_data.csv", help="Path to processed data")
    parser.add_argument("--models", type=str, default="data/models", help="Path to models directory")
    parser.add_argument("--output", type=str, default="data/validation", help="Output directory for reports")
    parser.add_argument("--top-n", type=int, default=3, help="Number of top features to use for SC-003")
    
    args = parser.parse_args()
    
    run_shap_analysis_pipeline(
        data_path=Path(args.data),
        model_dir=Path(args.models),
        output_dir=Path(args.output),
        top_n=args.top_n
    )

if __name__ == "__main__":
    import argparse
    main()