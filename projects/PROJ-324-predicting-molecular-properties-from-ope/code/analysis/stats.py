"""
Statistical analysis module for baseline and Random Forest model evaluation.
Calculates metrics (MAE, RMSE), performs statistical tests, and generates plots.
"""
import os
import sys
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def ensure_dirs():
    """Ensure required directories exist."""
    derived_dir = Path("data/derived")
    derived_dir.mkdir(parents=True, exist_ok=True)

def load_baseline_predictions(filepath="data/derived/baseline_test_predictions.csv"):
    """Load baseline test predictions from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}. "
                                "Ensure T014.5 (Extract Test Set Predictions) is completed.")
    df = pd.read_csv(filepath)
    required_cols = ['smiles', 'property_name', 'experimental_value', 'predicted_value', 'residual']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")
    return df

def load_rf_predictions(filepath="data/derived/rf_test_predictions.csv"):
    """Load RF test predictions from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}. "
                                "Ensure T020.1 (Evaluate on Test Set) is completed.")
    df = pd.read_csv(filepath)
    required_cols = ['smiles', 'property_name', 'experimental_value', 'predicted_value', 'residual']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")
    return df

def load_metadata(filepath="data/raw/dataset_metadata.json"):
    """Load dataset metadata."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metadata file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_absolute_errors(predictions_df):
    """Calculate absolute errors for a predictions dataframe."""
    if 'experimental_value' not in predictions_df.columns or 'predicted_value' not in predictions_df.columns:
        raise ValueError("Predictions dataframe must contain 'experimental_value' and 'predicted_value' columns.")
    return np.abs(predictions_df['experimental_value'] - predictions_df['predicted_value'])

def calculate_metrics(predictions_df):
    """Calculate MAE and RMSE for a predictions dataframe."""
    abs_errors = calculate_absolute_errors(predictions_df)
    mae = np.mean(abs_errors)
    rmse = np.sqrt(np.mean(abs_errors**2))
    return {'MAE': mae, 'RMSE': rmse}

def generate_residual_plot(predictions_df, output_path="data/derived/baseline_residuals.png"):
    """Generate a histogram of residuals for the baseline model."""
    if 'residual' not in predictions_df.columns:
        raise ValueError("Predictions dataframe must contain 'residual' column.")

    residuals = predictions_df['residual'].dropna()
    if len(residuals) == 0:
        raise ValueError("No valid residuals found in the data.")

    plt.figure(figsize=(10, 6))
    plt.hist(residuals, bins=50, alpha=0.7, color='blue', edgecolor='black')
    plt.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Error')
    plt.title('Distribution of Baseline Model Residuals')
    plt.xlabel('Residual (Experimental - Predicted)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Residual plot saved to {output_path}")

def calculate_baseline_metrics():
    """
    Calculate MAE/RMSE for baseline predictions on the held-out test set
    and generate residual distribution plots.
    """
    ensure_dirs()
    input_file = "data/derived/baseline_test_predictions.csv"
    output_plot = "data/derived/baseline_residuals.png"
    output_metrics = "data/derived/baseline_metrics.json"

    logger.info(f"Loading baseline test predictions from {input_file}")
    try:
        df = load_baseline_predictions(input_file)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Check for NaN values in critical columns
    if df[['experimental_value', 'predicted_value']].isnull().any().any():
        logger.error("NaN values detected in experimental or predicted values. Data is invalid.")
        sys.exit(1)

    logger.info(f"Calculating metrics for {len(df)} predictions")
    metrics = calculate_metrics(df)
    
    # Log metrics per property if multiple properties exist
    if 'property_name' in df.columns:
        for prop in df['property_name'].unique():
            prop_df = df[df['property_name'] == prop]
            if len(prop_df) > 0:
                prop_metrics = calculate_metrics(prop_df)
                logger.info(f"Metrics for {prop}: MAE={prop_metrics['MAE']:.4f}, RMSE={prop_metrics['RMSE']:.4f}")

    logger.info(f"Overall Metrics: MAE={metrics['MAE']:.4f}, RMSE={metrics['RMSE']:.4f}")

    # Save metrics to JSON
    with open(output_metrics, 'w') as f:
        json.dump(metrics, f, indent=4)
    logger.info(f"Metrics saved to {output_metrics}")

    # Generate residual plot
    try:
        generate_residual_plot(df, output_plot)
    except ValueError as e:
        logger.error(f"Failed to generate residual plot: {e}")
        sys.exit(1)

    return metrics

def perform_wilcoxon_test(baseline_df, rf_df):
    """Perform paired Wilcoxon signed-rank test on absolute errors."""
    baseline_errors = calculate_absolute_errors(baseline_df).values
    rf_errors = calculate_absolute_errors(rf_df).values

    if len(baseline_errors) != len(rf_errors):
        raise ValueError("Baseline and RF prediction sets must have the same number of samples for paired test.")
    
    if len(baseline_errors) == 0:
        raise ValueError("No data points to perform Wilcoxon test.")

    statistic, p_value = stats.wilcoxon(baseline_errors, rf_errors)
    return {'statistic': statistic, 'p_value': p_value}

def run_statistical_comparison():
    """Run statistical comparison between baseline and RF models."""
    ensure_dirs()
    baseline_file = "data/derived/baseline_test_predictions.csv"
    rf_file = "data/derived/rf_test_predictions.csv"

    try:
        baseline_df = load_baseline_predictions(baseline_file)
        rf_df = load_rf_predictions(rf_file)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Ensure alignment by SMILES if possible, otherwise assume order is preserved
    if 'smiles' in baseline_df.columns and 'smiles' in rf_df.columns:
        merged = pd.merge(baseline_df, rf_df, on='smiles', suffixes=('_baseline', '_rf'))
        if len(merged) != len(baseline_df):
            logger.warning("SMILES alignment resulted in fewer rows. Ensure test sets match exactly.")
            # Fallback to positional if alignment fails significantly
            if len(merged) < len(baseline_df) * 0.9:
                logger.error("Significant mismatch in SMILES. Cannot perform paired test.")
                sys.exit(1)
        baseline_errors = calculate_absolute_errors(merged.rename(columns={'experimental_value_baseline': 'experimental_value', 'predicted_value_baseline': 'predicted_value'}))
        rf_errors = calculate_absolute_errors(merged.rename(columns={'experimental_value_rf': 'experimental_value', 'predicted_value_rf': 'predicted_value'}))
    else:
        baseline_errors = calculate_absolute_errors(baseline_df)
        rf_errors = calculate_absolute_errors(rf_df)

    if len(baseline_errors) != len(rf_errors):
        logger.error("Error vectors mismatched in length after processing.")
        sys.exit(1)

    test_result = perform_wilcoxon_test(
        pd.DataFrame({'experimental_value': baseline_df['experimental_value'], 'predicted_value': baseline_df['predicted_value']}),
        pd.DataFrame({'experimental_value': rf_df['experimental_value'], 'predicted_value': rf_df['predicted_value']})
    )
    
    logger.info(f"Wilcoxon Test Result: Statistic={test_result['statistic']:.4f}, p-value={test_result['p_value']:.4e}")
    
    # Save report
    report_path = "data/derived/statistical_test_report.md"
    with open(report_path, 'w') as f:
        f.write("# Statistical Comparison Report\n\n")
        f.write(f"## Wilcoxon Signed-Rank Test\n")
        f.write(f"Statistic: {test_result['statistic']:.4f}\n")
        f.write(f"P-value: {test_result['p_value']:.4e}\n\n")
        if test_result['p_value'] < 0.05:
            f.write("**Conclusion**: There is a statistically significant difference between the baseline and RF models (p < 0.05).\n")
        else:
            f.write("**Conclusion**: No statistically significant difference found between the baseline and RF models (p >= 0.05).\n")
    
    logger.info(f"Statistical report saved to {report_path}")
    return test_result

def check_experimental_threshold():
    """Check if the experimental data ratio is substantial (>=50%)."""
    metadata_path = "data/raw/dataset_metadata.json"
    if not os.path.exists(metadata_path):
        logger.warning("Metadata file not found. Assuming threshold passed.")
        return True
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    ratio = metadata.get('experimental_ratio', 0.0)
    logger.info(f"Experimental ratio: {ratio}")
    if ratio < 0.5:
        logger.warning(f"Experimental ratio ({ratio}) is below 50% threshold.")
        return False
    return True

def save_comparison_results(baseline_metrics, rf_metrics, test_result):
    """Save comparison results to a file."""
    output_path = "data/derived/comparison_results.json"
    data = {
        'baseline': baseline_metrics,
        'rf': rf_metrics,
        'wilcoxon_test': test_result
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
    logger.info(f"Comparison results saved to {output_path}")

def generate_comparison_plots(baseline_df, rf_df):
    """Generate comparison plots for Baseline vs RF MAE/RMSE."""
    ensure_dirs()
    baseline_metrics = calculate_metrics(baseline_df)
    rf_metrics = calculate_metrics(rf_df)
    
    plt.figure(figsize=(10, 6))
    x = np.arange(2)
    width = 0.35
    
    metrics_names = ['MAE', 'RMSE']
    baseline_vals = [baseline_metrics['MAE'], baseline_metrics['RMSE']]
    rf_vals = [rf_metrics['MAE'], rf_metrics['RMSE']]
    
    plt.bar(x - width/2, baseline_vals, width, label='Baseline', color='blue', alpha=0.7)
    plt.bar(x + width/2, rf_vals, width, label='Random Forest', color='orange', alpha=0.7)
    
    plt.ylabel('Error')
    plt.title('Model Performance Comparison (Test Set)')
    plt.xticks(x, metrics_names)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    output_path = "data/derived/model_comparison.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Comparison plot saved to {output_path}")
    
    return baseline_metrics, rf_metrics

def generate_validation_protocol_summary():
    """Generate a validation protocol summary."""
    ensure_dirs()
    # Placeholder for future implementation
    pass

def generate_measurement_audit():
    """Generate a measurement audit."""
    ensure_dirs()
    # Placeholder for future implementation
    pass

def main():
    """Main entry point for statistical analysis."""
    logger.info("Starting Baseline Metrics Calculation (T015)")
    try:
        metrics = calculate_baseline_metrics()
        logger.info("T015 completed successfully.")
        
        # Optional: Run comparison if RF predictions exist
        if os.path.exists("data/derived/rf_test_predictions.csv"):
            logger.info("RF predictions found. Running statistical comparison...")
            run_statistical_comparison()
            baseline_df = load_baseline_predictions()
            rf_df = load_rf_predictions()
            generate_comparison_plots(baseline_df, rf_df)
        else:
            logger.info("RF predictions not found. Skipping comparison.")
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()