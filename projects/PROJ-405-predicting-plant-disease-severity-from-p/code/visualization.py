import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import PartialDependenceDisplay
from sklearn.metrics import f1_score, confusion_matrix
from sklearn.isotonic import IsotonicRegression

from config import get_path, ensure_dirs
from utils.reporting import load_results, save_results
from utils.logging_config import get_logger

logger = get_logger(__name__)

def generate_partial_dependence_plots(
    model: Any,
    features: pd.DataFrame,
    target: pd.Series,
    weather_features: List[str],
    image_features: List[str],
    output_dir: Path
) -> None:
    """
    Generate Partial Dependence Plots for interaction effects between
    weather variables and image features on predicted residual severity.
    """
    ensure_dirs([output_dir])
    logger.info(f"Generating Partial Dependence Plots for {len(weather_features)} weather features.")

    # We focus on interactions: Weather vs Image Features
    # Select a subset of key weather and image features for plotting to avoid clutter
    # Assuming features contain both sets
    plot_features = []
    for wf in weather_features[:2]: # Limit to top 2 weather features
        for ift in image_features[:2]: # Limit to top 2 image features
            plot_features.append((wf, ift))

    for wf, ift in plot_features:
        if wf not in features.columns or ift not in features.columns:
            logger.warning(f"Feature pair ({wf}, {ift}) not found in data, skipping.")
            continue

        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            PartialDependenceDisplay.from_estimator(
                model,
                features,
                [wf, ift],
                kind="average",
                ax=ax
            )
            plt.title(f"Partial Dependence: {wf} vs {ift}")
            plt.tight_layout()
            out_path = output_dir / f"pdp_{wf}_{ift}.png"
            plt.savefig(out_path)
            plt.close()
            logger.info(f"Saved PDP to {out_path}")
        except Exception as e:
            logger.error(f"Failed to generate PDP for {wf}, {ift}: {e}")

    logger.info("Partial Dependence Plot generation complete.")


def perform_sensitivity_analysis(
    results_df: pd.DataFrame,
    residual_col: str,
    thresholds: List[float],
    output_path: Path
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping classification thresholds.
    Calculates F1 scores and False Positive Rates for each threshold.

    Args:
        results_df: DataFrame containing 'residual' (or similar) and potentially other metrics.
                    We treat 'residual' as the continuous target.
        residual_col: Name of the column containing the residual values.
        thresholds: List of threshold values (absolute deviations from 90th percentile baseline).
        output_path: Path to save the sensitivity report.

    Returns:
        Dictionary containing the sensitivity analysis results.
    """
    logger.info(f"Performing sensitivity analysis with thresholds: {thresholds}")

    residuals = results_df[residual_col].values
    baseline_90 = np.percentile(np.abs(residuals), 90)
    
    sensitivity_results = []

    for t_dev in thresholds:
        # Define the threshold for "severe" error
        # Assuming we classify as "severe" if absolute residual > baseline + t_dev
        # Or simply if absolute residual > t_dev (if t_dev is absolute)
        # The task says: "absolute deviations {, 0.05, 0.1} from the 90th percentile baseline"
        # So the actual threshold = baseline_90 + t_dev
        
        actual_threshold = baseline_90 + t_dev
        
        # Create binary labels: 1 if |residual| > actual_threshold, else 0
        # This simulates a "failure" or "high severity" classification
        y_true_binary = (np.abs(residuals) > actual_threshold).astype(int)
        
        # For the "predicted" part, we need a model prediction.
        # Since we are analyzing the *residuals* themselves in the context of the
        # augmented model's performance on residuals, we assume the "prediction"
        # is the model's estimate of the residual.
        # However, the task asks to sweep thresholds on the *residuals* to see
        # how the classification of "severe" changes.
        # If we don't have a separate "predicted residual" column in results_df,
        # we might be evaluating the distribution of residuals directly as a proxy
        # for the model's error distribution.
        # But F1 and FPR require a True vs Predicted comparison.
        
        # Re-reading T035/T036: "Sensitivity Analysis logic sweeping thresholds... on classification thresholds".
        # This implies we are classifying the *outcome* (residual) based on a threshold.
        # To calculate F1/FPR, we need a binary prediction.
        # In the context of US3, we are likely evaluating the model's ability to
        # predict "high severity" (high residual).
        # If the model predicts the residual directly (regression), we can threshold the PREDICTION
        # and compare to thresholded TRUE.
        
        # Let's assume results_df has a column 'predicted_residual' from the Augmented Model (T027).
        # If not, we might have to infer or the task implies evaluating the thresholding of the 
        # continuous residual itself as a "detection" problem against a ground truth?
        # But Spec says "no ground truth".
        
        # Alternative interpretation: We are evaluating the *stability* of the "severe" classification
        # if we change the threshold. But F1 requires a truth.
        # Let's assume the "truth" is the high residual itself, and we are testing a "perfect" detector?
        # No, that's trivial.
        
        # Most likely scenario in this pipeline:
        # We have `y_true` (original severity) and `y_pred` (model prediction).
        # Residual = y_true - y_pred.
        # We define "Severe Error" as |Residual| > Threshold.
        # We want to see how many "Severe Errors" we catch (Recall) and how many false alarms (FPR)
        # if we use a threshold-based alert system.
        # But without a separate "alert" signal, FPR is undefined unless we compare against a baseline.
        
        # Let's assume the task implies:
        # 1. Define "Severe" as |Residual| > Threshold.
        # 2. Use the model's *predicted* residual (if available) to classify.
        # 3. If `predicted_residual` is not in results_df, we might be comparing against a null model?
        
        # Let's look at the data flow. T027 trains Augmented RF to predict Residuals.
        # So results_df should have `predicted_residual` (or similar).
        # Let's assume column name 'predicted_residual' exists. If not, we skip or use 0.
        
        pred_residual_col = 'predicted_residual'
        if pred_residual_col not in results_df.columns:
            # Fallback: If we don't have predictions, we can't calculate F1/FPR properly.
            # We might be forced to assume the "prediction" is the residual itself (perfect fit) for demo?
            # Or use a simple heuristic.
            # Given the strict "no synthetic" rule, we must handle missing data.
            # If the column is missing, the pipeline is incomplete.
            # However, for the sake of T036 implementation, let's assume the column exists.
            # If it doesn't, we log a warning and skip.
            logger.warning(f"Column '{pred_residual_col}' not found. Cannot compute F1/FPR.")
            continue

        y_pred_residual = results_df[pred_residual_col].values
        
        y_true_severe = (np.abs(residuals) > actual_threshold).astype(int)
        y_pred_severe = (np.abs(y_pred_residual) > actual_threshold).astype(int)
        
        # Avoid division by zero
        if np.sum(y_true_severe) == 0:
            f1 = 0.0
            fpr = 0.0
        else:
            tn, fp, fn, tp = confusion_matrix(y_true_severe, y_pred_severe).ravel()
            f1 = f1_score(y_true_severe, y_pred_severe)
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        sensitivity_results.append({
            "threshold_deviation": t_dev,
            "actual_threshold": actual_threshold,
            "f1_score": float(f1),
            "false_positive_rate": float(fpr),
            "num_severe_true": int(np.sum(y_true_severe)),
            "num_severe_pred": int(np.sum(y_pred_severe))
        })

    # Create DataFrame and save
    sens_df = pd.DataFrame(sensitivity_results)
    sens_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis saved to {output_path}")
    
    return {
        "thresholds": thresholds,
        "baseline_90_percentile": float(baseline_90),
        "results": sensitivity_results
    }


def run_visual_stage(
    model: Any,
    unified_data_path: Path,
    model_output_path: Path,
    output_figures_dir: Path,
    output_report_path: Path
) -> Dict[str, Any]:
    """
    Orchestrate the visualization stage:
    1. Load data and model.
    2. Generate Partial Dependence Plots.
    3. Perform Sensitivity Analysis.
    4. Update results.json.
    """
    logger.info("Starting Visual Stage.")
    
    # Load data
    if not unified_data_path.exists():
        raise FileNotFoundError(f"Unified dataset not found at {unified_data_path}")
    
    df = pd.read_csv(unified_data_path)
    logger.info(f"Loaded {len(df)} records from {unified_data_path}")

    # Identify features
    # Assuming columns: lesion_area_ratio, necrosis_color_index, texture_entropy, mean_temp, mean_humidity
    # and a 'residual' column from previous stage, and 'predicted_residual' from T027
    # If 'residual' or 'predicted_residual' are missing, we need to handle it.
    # T026/T027 should have generated these.
    
    if 'residual' not in df.columns:
        # Try to calculate residual if we have y_true and y_pred
        if 'lesion_area_ratio' in df.columns and 'predicted_lesion_area_ratio' in df.columns:
            df['residual'] = df['lesion_area_ratio'] - df['predicted_lesion_area_ratio']
            logger.info("Calculated residual from lesion_area_ratio.")
        else:
            raise ValueError("Column 'residual' or necessary components to calculate it not found in dataset.")
    
    if 'predicted_residual' not in df.columns:
        # If T027 output is not in the unified CSV, we might need to load the model and predict.
        # But T027 should have saved results. Let's assume 'predicted_residual' is in the CSV.
        # If not, we might need to re-predict.
        logger.warning("Column 'predicted_residual' not found. Re-predicting if model is available.")
        # This part depends on how the model is passed and what features it expects.
        # For now, we assume the pipeline ensures this column exists or we skip.
        # To be safe, let's assume we need to predict.
        # We need feature columns.
        feature_cols = [c for c in df.columns if c not in ['residual', 'predicted_residual', 'lesion_area_ratio']]
        # Filter out non-numeric
        feature_cols = [c for c in feature_cols if df[c].dtype in ['float64', 'int64']]
        
        if model is None:
            raise RuntimeError("Model is None and 'predicted_residual' is missing.")
        
        X = df[feature_cols].fillna(0)
        df['predicted_residual'] = model.predict(X)
        logger.info("Generated predicted_residual.")

    # 1. Generate PDPs
    weather_features = ['mean_temp', 'mean_humidity', 'total_precipitation']
    image_features = ['lesion_area_ratio', 'necrosis_color_index', 'texture_entropy']
    
    # Filter features that exist
    weather_features = [f for f in weather_features if f in df.columns]
    image_features = [f for f in image_features if f in df.columns]
    
    generate_partial_dependence_plots(
        model, df, df['residual'], weather_features, image_features, output_figures_dir
    )

    # 2. Sensitivity Analysis
    thresholds = [0.0, 0.05, 0.1] # Deviations from 90th percentile
    sens_results = perform_sensitivity_analysis(
        df, 'residual', thresholds, output_report_path
    )

    # 3. Update results.json
    results = load_results()
    results['sensitivity_analysis'] = {
        "thresholds_tested": thresholds,
        "baseline_90_percentile": sens_results['baseline_90_percentile'],
        "metrics": sens_results['results']
    }
    
    # Flag if findings hold (simple heuristic: F1 > 0.5 for all thresholds)
    all_f1_good = all(r['f1_score'] > 0.5 for r in sens_results['results'])
    results['sensitivity_analysis']['headlines_hold'] = all_f1_good
    
    save_results(results)
    logger.info("Visual Stage complete. Results updated.")
    return results


def main():
    """
    Entry point for the visualization stage.
    """
    ensure_dirs([get_path('figures'), get_path('artifacts')])
    
    # Load config paths
    unified_data_path = get_path('data', 'processed', 'unified_analysis.csv')
    # We need the model. In a real pipeline, the model would be loaded from a pickle.
    # For this script, we assume the model is passed or loaded.
    # Since we are implementing the script, we need to load the model.
    # Let's assume it's saved in artifacts/model.pkl or similar.
    # But the task doesn't specify the model path.
    # Let's assume we load it from the standard location or fail.
    
    model_path = get_path('artifacts', 'model', 'augmented_rf.pkl')
    if not model_path.exists():
        # Try to find it
        logger.warning("Model not found at standard path. Attempting to find in artifacts.")
        # Fallback logic or error
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    import joblib
    model = joblib.load(model_path)
    
    run_visual_stage(
        model=model,
        unified_data_path=unified_data_path,
        model_output_path=get_path('artifacts', 'model_output.json'), # Placeholder
        output_figures_dir=get_path('figures'),
        output_report_path=get_path('data', 'sensitivity_report.csv')
    )

if __name__ == "__main__":
    main()