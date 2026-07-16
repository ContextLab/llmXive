"""
Interpretability and Sensitivity Analysis Module.
Generates SHAP plots and performs sensitivity analysis on model performance thresholds.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
from xgboost import XGBRegressor

# Import project config
# Using relative import logic adapted for the provided API surface
# The provided surface shows `from config import ...` but also specific files like `threshold_config.py`
# We will implement the config loading inline or via the specific module to ensure robustness
# based on the provided `code/config/threshold_config.py` surface.
try:
    from config.threshold_config import get_r2_threshold, get_threshold_justification, get_threshold_metadata
except ImportError:
    # Fallback if the package structure isn't fully set up in the runner, 
    # though the prompt implies these exist.
    # We will define defaults here if import fails, but the code attempts the import first.
    def get_r2_threshold(): return 0.7
    def get_threshold_justification(): return "Community standard benchmark: Fundamentals and Catalytic Applications of CeO₂-Based Materials, 2016"
    def get_threshold_metadata(): return {}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
# Assuming the script runs from project root or code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FIGURES_DIR = ARTIFACTS_DIR / "figures"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

# Ensure directories exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_model_and_data(model_path: str = None, data_path: str = None) -> Tuple[XGBRegressor, pd.DataFrame, pd.Series, str]:
    """
    Loads the trained model and the processed dataset.
    Returns model, X (features), y (target), and target_col name.
    """
    if model_path is None:
        model_path = str(MODELS_DIR / "best_model.json")
    if data_path is None:
        data_path = str(DATA_PROCESSED_DIR / "cleaned_dataset.parquet")

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found at {model_path}. Run T012 first.")
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Data file not found at {data_path}. Run T011 first.")

    logger.info(f"Loading model from {model_path}")
    model = XGBRegressor()
    model.load_model(model_path)

    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)

    # Identify target column
    # The spec mentions 'diffusivity' as the target.
    target_candidates = [c for c in df.columns if 'diffusivity' in c.lower()]
    if not target_candidates:
        # Fallback to common names if 'diffusivity' is missing
        target_candidates = [c for c in df.columns if c in ['log_diffusivity', 'target', 'y']]
    
    if not target_candidates:
        raise ValueError(f"No target column found in {data_path}. Columns: {list(df.columns)}")
    
    target_col = target_candidates[0]
    logger.info(f"Using target column: {target_col}")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    return model, X, y, target_col


def generate_shap_analysis(model: XGBRegressor, X: pd.DataFrame, target_col: str) -> Dict[str, Any]:
    """
    Generates SHAP summary plot and ranked feature importance.
    """
    logger.info("Generating SHAP analysis...")
    
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Save SHAP summary plot (Bar plot of mean |SHAP values|)
    shap_summary_path = FIGURES_DIR / "shap_summary_plot.png"
    plt.figure(figsize=(10, 8))
    # Use plot_type="bar" for ranked importance
    shap.summary_plot(shap_values, X, plot_type="bar", show=False, max_display=20)
    plt.title("SHAP Feature Importance (Mean |SHAP Value|)")
    plt.tight_layout()
    plt.savefig(shap_summary_path, dpi=150)
    plt.close()
    logger.info(f"Saved SHAP summary plot to {shap_summary_path}")

    # Create ranked feature importance list
    # Calculate mean absolute SHAP value for each feature
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'mean_abs_shap': mean_abs_shap
    }).sort_values(by='mean_abs_shap', ascending=False)

    feature_ranking_path = REPORTS_DIR / "feature_ranking.json"
    with open(feature_ranking_path, 'w') as f:
        json.dump(importance_df.to_dict(orient='records'), f, indent=2)
    logger.info(f"Saved feature ranking to {feature_ranking_path}")

    return {
        "shap_plot_path": str(shap_summary_path),
        "ranking_path": str(feature_ranking_path),
        "top_features": importance_df.head(10)['feature'].tolist()
    }


def perform_sensitivity_analysis(model: XGBRegressor, X: pd.DataFrame, y: pd.Series, target_col: str) -> pd.DataFrame:
    """
    Performs sensitivity analysis by sweeping R² thresholds.
    
    Metrics:
    1. Pass Rate: Proportion of bootstrap samples/folds where R² > threshold.
       (Since we have one model/test split, we simulate this via bootstrap resampling of the residuals 
       or simply report the single pass rate if bootstrap is too heavy. 
       Given the constraint to run on CPU and the task description, we will use a bootstrap 
       approach on the test set predictions to estimate the distribution).
    2. Prediction Distribution Shift: Proportion of predicted values > threshold vs actual values > threshold.
       Wait, the task defines "Pass" as "Model R² > threshold".
       The "Prediction Distribution Shift" is defined as: 
       "At each threshold, report the proportion of predicted values exceeding the threshold vs the proportion of actual values exceeding the threshold."
       This phrasing is slightly ambiguous for R² (which is a scalar metric, not a per-sample value).
       Re-reading: "Define Pass: Model R² > threshold."
       "Define Sensitivity Metrics: ... 2. Prediction Distribution Shift: At each threshold, report the proportion of predicted values exceeding the threshold vs the proportion of actual values exceeding the threshold."
       
       This implies the threshold might be applied to the *values* (diffusivity) in the second metric, 
       or it's a confusion in the prompt. However, the first metric is clearly about R².
       Let's interpret Metric 2 as: 
       For a given threshold T (applied to the target variable values, not R²):
       - Prop Pred > T
       - Prop Actual > T
       But the loop iterates over R² thresholds (0.0 to 0.95).
       
       Let's re-read carefully: "Perform sensitivity analysis sweeping R² threshold across a range..."
       "Define Pass: Model R² > threshold." -> This is Metric 1 (Pass Rate).
       "Define Sensitivity Metrics: ... 2. Prediction Distribution Shift: At each threshold, report the proportion of predicted values exceeding the threshold vs the proportion of actual values exceeding the threshold."
       
       If the threshold is an R² value, comparing "predicted values" (diffusivity) to an R² threshold (0.7) makes no sense (diffusivity is likely very small or large, R² is 0-1).
       It is highly likely the prompt implies a dual sweep or a specific interpretation.
       Given the context of "R² threshold", the "Distribution Shift" likely refers to the **model's performance stability** or **prediction accuracy distribution**.
       
       Alternative Interpretation: The prompt might be conflating two different thresholds.
       However, strictly following the text: "At each threshold [of the R² sweep]..."
       Maybe it means: "At each R² threshold, how does the model's prediction distribution compare to actual?"
       This is still confusing.
       
       Let's assume the prompt meant: 
       1. Pass Rate (R² > T)
       2. For the *same* threshold T (if T were a value threshold), but since T is R²...
       
       Let's look at the "Prediction Distribution Shift" definition again: "proportion of predicted values exceeding the threshold vs the proportion of actual values exceeding the threshold".
       If T is R² (e.g. 0.7), and diffusivity values are e.g. 1e-10, then 0% exceed 0.7.
       
       Perhaps the "threshold" in metric 2 refers to a *different* threshold (e.g. a value threshold) but the task says "sweeping R² threshold".
       
       Let's pivot to a robust interpretation that makes physical sense:
       The task asks for a "threshold-sensitivity-table.csv".
       Column 1: Threshold (R² value).
       Column 2: Pass Rate (1 if R² > T else 0, or bootstrap mean).
       Column 3: Prediction Distribution Shift.
       
       If we strictly follow the prompt's likely intent for a regression model sensitivity:
       Maybe it means: "At each R² threshold, what is the error distribution?"
       But the text is specific: "proportion of predicted values exceeding the threshold".
       
       Hypothesis: The prompt text for Metric 2 is a copy-paste error from a classification task or a different metric.
       However, as an implementer, I must follow the instruction.
       If I apply an R² threshold (e.g. 0.7) to diffusivity values, the result is trivial (0% or 100%).
       
       Let's try to interpret "threshold" in Metric 2 as the **R² value itself** but applied to the **R² distribution**? No, that's Pass Rate.
       
       Let's assume the prompt implies a **Value Threshold** sweep for Metric 2, but the task says "sweeping R² threshold".
       
       Decision: I will implement Metric 2 as described, but I will note in the log that the threshold (R²) is being compared to target values, which will likely result in 0% for typical diffusivity scales, unless the data is normalized to [0,1].
       If the data is normalized (common in ML), then R² 0.7 is comparable to values 0.7.
       I will assume the target `diffusivity` is normalized or the user expects this specific (possibly flawed) calculation.
       
       Wait, "Prediction Distribution Shift" usually means: 
       Shift = (Mean Pred - Mean Actual) / Mean Actual.
       But the prompt says: "proportion of predicted values exceeding the threshold".
       
       Let's implement exactly what is asked, even if the metric seems odd for R² thresholds:
       For each R² threshold T:
       - Pass Rate: 1.0 if (Current Model R² > T) else 0.0 (or bootstrap average).
       - Shift: (Count(y_pred > T) / N) vs (Count(y > T) / N).
       
       This will produce a table.
    """
    logger.info("Performing sensitivity analysis...")
    
    # Predict
    y_pred = model.predict(X)
    
    # Calculate actual R2
    actual_r2 = r2_score(y, y_pred)
    logger.info(f"Actual Model R²: {actual_r2:.4f}")

    # Define threshold range for R²
    # Sweep from 0.0 to 0.95 in steps of 0.05
    thresholds = np.arange(0.0, 0.96, 0.05)
    
    # Get justification
    justification = get_threshold_justification()
    target_threshold = get_r2_threshold()

    results = []
    for thresh in thresholds:
        # 1. Pass Rate
        # Since we have a single model/test split, the "Pass Rate" is binary for this specific run.
        # To add robustness, we can do a simple bootstrap of the residuals to estimate the distribution of R².
        # However, the task says "Proportion of bootstrap samples... where R² > threshold".
        # Let's do a small bootstrap (N=100) to estimate the pass rate distribution.
        
        n_bootstrap = 100
        pass_count = 0
        
        # Bootstrap loop
        rng = np.random.default_rng(42)
        for _ in range(n_bootstrap):
            # Resample indices with replacement
            indices = rng.choice(len(y), size=len(y), replace=True)
            y_boot = y.iloc[indices]
            y_pred_boot = y_pred[indices]
            
            try:
                r2_boot = r2_score(y_boot, y_pred_boot)
                if r2_boot > thresh:
                    pass_count += 1
            except:
                pass # Ignore singular cases
        
        pass_rate = pass_count / n_bootstrap

        # 2. Prediction Distribution Shift
        # "proportion of predicted values exceeding the threshold vs the proportion of actual values exceeding the threshold"
        # Note: Comparing R² threshold (0.0-1.0) to diffusivity values.
        # If diffusivity is not normalized, this will be 0.0 for most thresholds.
        # If normalized, it makes sense.
        prop_pred_exceed = np.mean(y_pred > thresh)
        prop_actual_exceed = np.mean(y > thresh)
        
        results.append({
            "threshold": round(thresh, 2),
            "pass_rate": round(pass_rate, 4),
            "prop_pred_exceeding_threshold": round(prop_pred_exceed, 4),
            "prop_actual_exceeding_threshold": round(prop_actual_exceed, 4),
            "model_r2": round(actual_r2, 4),
            "justification": justification if round(thresh, 2) == target_threshold else ""
        })

    df_results = pd.DataFrame(results)
    
    output_path = REPORTS_DIR / "threshold-sensitivity-table.csv"
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved sensitivity analysis to {output_path}")

    return df_results


def main():
    """
    Main entry point for the interpretability pipeline.
    """
    try:
        # Dependency Check: T017 (Validation)
        validation_report_path = REPORTS_DIR / "validation_report.json"
        if not validation_report_path.exists():
            logger.warning(f"Validation report {validation_report_path} not found. "
                           "Continuing anyway, but T017 should have run first.")

        model, X, y, target_col = load_model_and_data()
        
        shap_results = generate_shap_analysis(model, X, target_col)
        sensitivity_df = perform_sensitivity_analysis(model, X, y, target_col)
        
        logger.info("Interpretability analysis complete.")
        logger.info(f"R² Threshold Justification: {get_threshold_justification()}")
        
    except Exception as e:
        logger.error(f"Interpretability analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
