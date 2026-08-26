import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from config import CONFIG
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def load_preprocessed_data() -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Load the preprocessed features and target from the modeling pipeline.
    Returns:
        X: Feature DataFrame
        y: Target Series
        feature_names: List of feature names
    """
    X_path = Path(CONFIG.PROCESSED_FEATURES_PATH)
    y_path = Path(CONFIG.PROCESSED_TARGET_PATH)
    
    if not X_path.exists():
        raise FileNotFoundError(f"Preprocessed features not found at {X_path}. Run modeling pipeline first.")
    if not y_path.exists():
        raise FileNotFoundError(f"Preprocessed target not found at {y_path}. Run modeling pipeline first.")
    
    X = pd.read_csv(X_path)
    y = pd.read_csv(y_path)
    
    # Ensure y is a Series
    if isinstance(y, pd.DataFrame):
        y = y.iloc[:, 0]
    
    feature_names = X.columns.tolist()
    return X, y, feature_names

def load_trained_model() -> RandomForestRegressor:
    """
    Load the trained Random Forest model from the modeling pipeline.
    Returns:
        model: Trained RandomForestRegressor
    """
    model_path = Path(CONFIG.TRAINED_MODEL_PATH)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Trained model not found at {model_path}. Run modeling pipeline first.")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model

def calculate_shap_values(model: RandomForestRegressor, X: pd.DataFrame) -> shap.Explanation:
    """
    Calculate SHAP values for the trained model.
    Args:
        model: Trained RandomForestRegressor
        X: Feature DataFrame
    Returns:
        shap_values: SHAP explanation object
    """
    logger.info("Calculating SHAP values...")
    # Use TreeExplainer for tree-based models
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # For regression, shap_values is already an array of shape (n_samples, n_features)
    # If it's a list (for classification), we handle it, but here we assume regression
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    
    return shap_values

def calculate_permutation_importance(
    model: RandomForestRegressor, 
    X: pd.DataFrame, 
    y: pd.Series, 
    n_repeats: int = 10, 
    random_state: int = 42
) -> pd.DataFrame:
    """
    Calculate permutation importance for the trained model.
    This method highlights the contribution of each feature, including DFT descriptors,
    by measuring the decrease in model performance when a feature's values are randomly shuffled.
    
    Args:
        model: Trained RandomForestRegressor
        X: Feature DataFrame
        y: Target Series
        n_repeats: Number of times to permute a feature
        random_state: Random seed for reproducibility
    
    Returns:
        importance_df: DataFrame with feature names and importance scores
    """
    logger.info("Calculating permutation importance...")
    
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        n_jobs=-1,
        scoring='r2'  # Use R2 score as the metric
    )
    
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    })
    
    # Sort by importance (descending)
    importance_df = importance_df.sort_values(by='importance_mean', ascending=False)
    
    logger.info(f"Permutation importance calculated for {len(importance_df)} features.")
    
    return importance_df

def analyze_feature_importance(
    shap_values: shap.Explanation, 
    importance_df: pd.DataFrame, 
    feature_names: List[str]
) -> Dict[str, Any]:
    """
    Analyze and summarize feature importance from SHAP and permutation methods.
    Highlights DFT descriptors if present.
    
    Args:
        shap_values: SHAP explanation object
        importance_df: Permutation importance DataFrame
        feature_names: List of feature names
    
    Returns:
        analysis: Dictionary containing importance analysis
    """
    logger.info("Analyzing feature importance...")
    
    # Get mean absolute SHAP values
    mean_shap_importance = np.abs(shap_values).mean(axis=0)
    shap_importance_df = pd.DataFrame({
        'feature': feature_names,
        'shap_importance': mean_shap_importance
    }).sort_values(by='shap_importance', ascending=False)
    
    # Identify DFT descriptors (assuming they contain 'dft' or 'shear' or 'bulk' in name)
    dft_features = [f for f in feature_names if any(kw in f.lower() for kw in ['dft', 'shear', 'bulk', 'elastic'])]
    
    analysis = {
        'shap_ranking': shap_importance_df.to_dict(orient='records'),
        'permutation_ranking': importance_df.to_dict(orient='records'),
        'dft_features': dft_features,
        'top_5_features': shap_importance_df.head(5)['feature'].tolist(),
        'dft_importance_summary': {
            'count': len(dft_features),
            'avg_shap_importance': float(shap_importance_df[shap_importance_df['feature'].isin(dft_features)]['shap_importance'].mean()) if dft_features else 0.0,
            'avg_permutation_importance': float(importance_df[importance_df['feature'].isin(dft_features)]['importance_mean'].mean()) if dft_features else 0.0
        }
    }
    
    return analysis

def generate_shap_plots(
    shap_values: shap.Explanation, 
    X: pd.DataFrame, 
    output_dir: Path, 
    importance_df: pd.DataFrame
) -> Dict[str, str]:
    """
    Generate SHAP summary plots and permutation importance plots.
    
    Args:
        shap_values: SHAP explanation object
        X: Feature DataFrame
        output_dir: Directory to save plots
        importance_df: Permutation importance DataFrame
    
    Returns:
        plot_paths: Dictionary mapping plot type to file path
    """
    logger.info("Generating SHAP plots...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plot_paths = {}
    
    # SHAP summary plot
    shap_summary_path = output_dir / "shap_summary.png"
    plt = shap.summary_plot(shap_values, X, show=False)
    plt.figure().savefig(shap_summary_path, dpi=150, bbox_inches='tight')
    plt.figure().close()
    plot_paths['shap_summary'] = str(shap_summary_path)
    logger.info(f"Saved SHAP summary plot to {shap_summary_path}")
    
    # SHAP bar plot (mean absolute SHAP values)
    shap_bar_path = output_dir / "shap_bar.png"
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.figure().savefig(shap_bar_path, dpi=150, bbox_inches='tight')
    plt.figure().close()
    plot_paths['shap_bar'] = str(shap_bar_path)
    logger.info(f"Saved SHAP bar plot to {shap_bar_path}")
    
    # Permutation importance plot
    perm_path = output_dir / "permutation_importance.png"
    plt.figure(figsize=(10, 8))
    plt.barh(importance_df['feature'], importance_df['importance_mean'], 
             xerr=importance_df['importance_std'], capsize=3)
    plt.xlabel('Mean Decrease in R² Score')
    plt.ylabel('Feature')
    plt.title('Permutation Importance')
    plt.gca().invert_yaxis()  # Highest importance at top
    plt.tight_layout()
    plt.savefig(perm_path, dpi=150, bbox_inches='tight')
    plt.close()
    plot_paths['permutation_importance'] = str(perm_path)
    logger.info(f"Saved permutation importance plot to {perm_path}")
    
    return plot_paths

def save_shap_results(
    analysis: Dict[str, Any], 
    plot_paths: Dict[str, str], 
    output_path: Path
) -> None:
    """
    Save SHAP analysis results to a JSON file.
    
    Args:
        analysis: Feature importance analysis dictionary
        plot_paths: Dictionary of plot file paths
        output_path: Path to save the results JSON
    """
    logger.info("Saving SHAP results...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        'analysis': analysis,
        'plots': plot_paths
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved SHAP results to {output_path}")

def run_shap_analysis() -> Dict[str, Any]:
    """
    Main function to run the full SHAP and permutation importance analysis.
    
    Returns:
        results: Dictionary containing all analysis results
    """
    logger.info("Starting SHAP and permutation importance analysis...")
    
    # Load data and model
    X, y, feature_names = load_preprocessed_data()
    model = load_trained_model()
    
    # Calculate SHAP values
    shap_values = calculate_shap_values(model, X)
    
    # Calculate permutation importance
    importance_df = calculate_permutation_importance(model, X, y)
    
    # Analyze feature importance
    analysis = analyze_feature_importance(shap_values, importance_df, feature_names)
    
    # Generate plots
    plots_dir = Path(CONFIG.RESULTS_DIR) / "figures"
    plot_paths = generate_shap_plots(shap_values, X, plots_dir, importance_df)
    
    # Save results
    results_path = Path(CONFIG.RESULTS_DIR) / "shap_analysis_results.json"
    save_shap_results(analysis, plot_paths, results_path)
    
    # Log provenance
    log_provenance_event(
        event_type="shap_analysis_completed",
        details={
            "output_file": str(results_path),
            "top_features": analysis['top_5_features'],
            "dft_features_count": analysis['dft_importance_summary']['count']
        }
    )
    
    logger.info("SHAP and permutation importance analysis completed successfully.")
    
    return {
        'analysis': analysis,
        'plots': plot_paths,
        'results_file': str(results_path)
    }

def main():
    """
    Entry point for the script.
    """
    try:
        results = run_shap_analysis()
        print(f"Analysis complete. Results saved to: {results['results_file']}")
        print(f"Top 5 features: {results['analysis']['top_5_features']}")
        print(f"DFT features count: {results['analysis']['dft_importance_summary']['count']}")
    except Exception as e:
        logger.error(f"Error during SHAP analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()