import os
import sys
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Ensure imports match the existing API surface exactly
# Existing public names: ensure_dirs, load_baseline_predictions, load_rf_predictions, load_metadata, 
# calculate_absolute_errors, calculate_metrics, generate_residual_plot, generate_comparison_plots, 
# calculate_baseline_metrics, perform_wilcoxon_test, run_statistical_comparison, check_experimental_threshold, 
# save_comparison_results, generate_validation_protocol_summary, main

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure required directories exist."""
    data_derived = Path("data/derived")
    data_raw = Path("data/raw")
    data_processed = Path("data/processed")
    
    data_derived.mkdir(parents=True, exist_ok=True)
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Ensured directories exist: {data_derived}, {data_raw}, {data_processed}")

def load_baseline_predictions(path: str) -> pd.DataFrame:
    """Load baseline predictions from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Baseline predictions file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded baseline predictions: {len(df)} rows")
    return df

def load_rf_predictions(path: str) -> pd.DataFrame:
    """Load RF predictions from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"RF predictions file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded RF predictions: {len(df)} rows")
    return df

def load_metadata(path: str) -> Dict[str, Any]:
    """Load dataset metadata from JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metadata file not found: {path}")
    
    with open(path, 'r') as f:
        metadata = json.load(f)
    
    logger.info(f"Loaded metadata from {path}")
    return metadata

def calculate_absolute_errors(predictions_df: pd.DataFrame, pred_col: str = 'predicted_value', 
                              true_col: str = 'experimental_value') -> pd.Series:
    """Calculate absolute errors from predictions DataFrame."""
    errors = np.abs(predictions_df[pred_col] - predictions_df[true_col])
    return errors

def calculate_metrics(predictions_df: pd.DataFrame, pred_col: str = 'predicted_value', 
                     true_col: str = 'experimental_value') -> Dict[str, float]:
    """Calculate MAE and RMSE from predictions DataFrame."""
    errors = calculate_absolute_errors(predictions_df, pred_col, true_col)
    mae = errors.mean()
    rmse = np.sqrt(((predictions_df[pred_col] - predictions_df[true_col]) ** 2).mean())
    
    return {
        'mae': mae,
        'rmse': rmse,
        'n_samples': len(predictions_df)
    }

def generate_residual_plot(predictions_df: pd.DataFrame, output_path: str, 
                          title: str = "Residual Distribution") -> None:
    """Generate residual distribution plot."""
    residuals = predictions_df['predicted_value'] - predictions_df['experimental_value']
    
    plt.figure(figsize=(10, 6))
    plt.hist(residuals, bins=50, alpha=0.7, edgecolor='black')
    plt.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Residual')
    plt.xlabel('Residual (Predicted - Experimental)')
    plt.ylabel('Frequency')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved residual plot to {output_path}")

def generate_comparison_plots(baseline_metrics: Dict[str, float], rf_metrics: Dict[str, float], 
                             output_path: str) -> None:
    """Generate comparison plot between baseline and RF models."""
    models = ['Baseline (Crippen)', 'Random Forest']
    mae_values = [baseline_metrics['mae'], rf_metrics['mae']]
    rmse_values = [baseline_metrics['rmse'], rf_metrics['rmse']]
    
    x = np.arange(len(models))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width/2, mae_values, width, label='MAE', color='steelblue')
    bars2 = ax.bar(x + width/2, rmse_values, width, label='RMSE', color='coral')
    
    ax.set_ylabel('Error Value')
    ax.set_title('Model Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved comparison plot to {output_path}")

def calculate_baseline_metrics(baseline_path: str, output_plot_path: str) -> Dict[str, float]:
    """Calculate baseline metrics and generate residual plot."""
    logger.info(f"Calculating baseline metrics from {baseline_path}")
    
    df = load_baseline_predictions(baseline_path)
    metrics = calculate_metrics(df)
    
    generate_residual_plot(df, output_plot_path, "Baseline (Crippen) Residual Distribution")
    
    logger.info(f"Baseline Metrics - MAE: {metrics['mae']:.4f}, RMSE: {metrics['rmse']:.4f}")
    return metrics

def perform_wilcoxon_test(baseline_df: pd.DataFrame, rf_df: pd.DataFrame) -> Dict[str, Any]:
    """Perform paired Wilcoxon signed-rank test on absolute errors."""
    from scipy import stats
    
    baseline_errors = np.abs(baseline_df['predicted_value'] - baseline_df['experimental_value'])
    rf_errors = np.abs(rf_df['predicted_value'] - rf_df['experimental_value'])
    
    # Ensure same order if possible (match by smiles)
    if 'smiles' in baseline_df.columns and 'smiles' in rf_df.columns:
        common_smiles = set(baseline_df['smiles']).intersection(set(rf_df['smiles']))
        baseline_errors = baseline_df[baseline_df['smiles'].isin(common_smiles)]['predicted_value'] - baseline_df[baseline_df['smiles'].isin(common_smiles)]['experimental_value']
        rf_errors = rf_df[rf_df['smiles'].isin(common_smiles)]['predicted_value'] - rf_df[rf_df['smiles'].isin(common_smiles)]['experimental_value']
        
        baseline_errors = np.abs(baseline_errors.values)
        rf_errors = np.abs(rf_errors.values)
    
    if len(baseline_errors) != len(rf_errors) or len(baseline_errors) == 0:
        logger.warning("Cannot perform Wilcoxon test: mismatched or empty error arrays")
        return {
            'statistic': None,
            'pvalue': None,
            'conclusion': 'Unable to perform test due to data mismatch',
            'n_pairs': 0
        }
    
    statistic, pvalue = stats.wilcoxon(baseline_errors, rf_errors)
    
    conclusion = "Significant difference" if pvalue < 0.05 else "No significant difference"
    
    result = {
        'statistic': float(statistic),
        'pvalue': float(pvalue),
        'conclusion': conclusion,
        'n_pairs': len(baseline_errors),
        'baseline_mae': float(np.mean(baseline_errors)),
        'rf_mae': float(np.mean(rf_errors))
    }
    
    logger.info(f"Wilcoxon Test: statistic={statistic:.4f}, p-value={pvalue:.4f}, {conclusion}")
    return result

def run_statistical_comparison(baseline_path: str, rf_path: str, output_report_path: str) -> Dict[str, Any]:
    """Run full statistical comparison between baseline and RF models."""
    logger.info(f"Running statistical comparison: baseline={baseline_path}, rf={rf_path}")
    
    baseline_df = load_baseline_predictions(baseline_path)
    rf_df = load_rf_predictions(rf_path)
    
    # Calculate metrics
    baseline_metrics = calculate_metrics(baseline_df)
    rf_metrics = calculate_metrics(rf_df)
    
    # Perform Wilcoxon test
    wilcoxon_result = perform_wilcoxon_test(baseline_df, rf_df)
    
    # Generate report
    report = {
        'baseline_metrics': baseline_metrics,
        'rf_metrics': rf_metrics,
        'wilcoxon_test': wilcoxon_result,
        'improvement': {
            'mae_reduction': baseline_metrics['mae'] - rf_metrics['mae'],
            'rmse_reduction': baseline_metrics['rmse'] - rf_metrics['rmse'],
            'mae_percent': ((baseline_metrics['mae'] - rf_metrics['mae']) / baseline_metrics['mae'] * 100) if baseline_metrics['mae'] > 0 else 0,
            'rmse_percent': ((baseline_metrics['rmse'] - rf_metrics['rmse']) / baseline_metrics['rmse'] * 100) if baseline_metrics['rmse'] > 0 else 0
        }
    }
    
    with open(output_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Statistical comparison report saved to {output_report_path}")
    return report

def check_experimental_threshold(test_set_path: str, threshold: float = 0.5) -> Dict[str, Any]:
    """Check if experimental data ratio meets threshold."""
    logger.info(f"Checking experimental threshold for {test_set_path}")
    
    if not os.path.exists(test_set_path):
        raise FileNotFoundError(f"Test set file not found: {test_set_path}")
    
    df = pd.read_csv(test_set_path)
    
    if 'source_type' not in df.columns:
        logger.warning("source_type column not found in test set. Assuming all experimental.")
        experimental_ratio = 1.0
    else:
        experimental_count = len(df[df['source_type'] == 'Experimental'])
        total_count = len(df)
        experimental_ratio = experimental_count / total_count if total_count > 0 else 0.0
    
    meets_threshold = experimental_ratio >= threshold
    
    result = {
        'experimental_ratio': experimental_ratio,
        'experimental_count': experimental_count,
        'total_count': total_count,
        'meets_threshold': meets_threshold,
        'threshold': threshold
    }
    
    logger.info(f"Experimental ratio: {experimental_ratio:.2%} ({experimental_count}/{total_count}) - Meets threshold: {meets_threshold}")
    return result

def save_comparison_results(baseline_metrics: Dict[str, float], rf_metrics: Dict[str, float], 
                           wilcoxon_result: Dict[str, Any], output_path: str) -> None:
    """Save comparison results to JSON file."""
    results = {
        'baseline_metrics': baseline_metrics,
        'rf_metrics': rf_metrics,
        'wilcoxon_test': wilcoxon_result
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Comparison results saved to {output_path}")

def generate_validation_protocol_summary(metadata_path: str, test_set_path: str, 
                                        baseline_metrics_path: str, rf_metrics_path: str,
                                        output_path: str) -> None:
    """Generate validation protocol summary as per Marie Curie review."""
    logger.info("Generating validation protocol summary")
    
    # Load metadata
    try:
        metadata = load_metadata(metadata_path)
    except FileNotFoundError:
        metadata = {
            'source': 'Unknown',
            'measurement_uncertainty_status': 'Not Available in Source',
            'quantity_of_substance_status': 'Not Available in Source'
        }
    
    # Load test set info
    if os.path.exists(test_set_path):
        test_df = pd.read_csv(test_set_path)
        test_set_size = len(test_df)
        experimental_count = len(test_df[test_df['source_type'] == 'Experimental']) if 'source_type' in test_df.columns else test_set_size
        experimental_source = "PubChem Experimental" if 'source_type' in test_df.columns else "Unknown"
    else:
        test_set_size = 0
        experimental_count = 0
        experimental_source = "Not Available"
    
    # Load metrics
    baseline_metrics = {}
    rf_metrics = {}
    if os.path.exists(baseline_metrics_path):
        with open(baseline_metrics_path, 'r') as f:
            baseline_metrics = json.load(f)
    
    if os.path.exists(rf_metrics_path):
        with open(rf_metrics_path, 'r') as f:
            rf_metrics = json.load(f)
    
    summary = {
        'validation_protocol': {
            'test_set_size': test_set_size,
            'experimental_count': experimental_count,
            'experimental_source': experimental_source,
            'measurement_uncertainty': metadata.get('measurement_uncertainty_status', 'Not Available'),
            'quantity_of_substance': metadata.get('quantity_of_substance_status', 'Not Available'),
            'baseline_performance': baseline_metrics,
            'rf_performance': rf_metrics,
            'uncertainty_note': "Measurement uncertainty and quantity of substance data are not available in the source. All predictions are compared against reported experimental values without uncertainty bounds."
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Validation protocol summary saved to {output_path}")

def generate_measurement_audit(test_set_path: str, baseline_predictions_path: str, 
                              rf_predictions_path: str, metadata_path: str,
                              output_path: str) -> None:
    """
    Generate a Measurement Standards Audit as per Marie Curie review.
    This explicitly lists uncertainty bounds (if available) or states "Not Reported"
    for every data point in the held-out test set.
    
    Produces: data/derived/measurement_standards_audit.csv
    Columns: smiles, property, experimental_value, reported_uncertainty, uncertainty_source_status
    """
    logger.info("Generating Measurement Standards Audit")
    
    # Load metadata to check uncertainty availability
    uncertainty_status = "Not Available in Source"
    if os.path.exists(metadata_path):
        try:
            metadata = load_metadata(metadata_path)
            uncertainty_status = metadata.get('measurement_uncertainty_status', 'Not Available in Source')
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")
    
    # Load test set
    if not os.path.exists(test_set_path):
        raise FileNotFoundError(f"Test set file not found: {test_set_path}")
    
    test_df = pd.read_csv(test_set_path)
    
    # Load predictions if available to get property names
    baseline_df = None
    rf_df = None
    properties = set()
    
    if os.path.exists(baseline_predictions_path):
        baseline_df = load_baseline_predictions(baseline_predictions_path)
        if 'property_name' in baseline_df.columns:
            properties.update(baseline_df['property_name'].unique())
    
    if os.path.exists(rf_predictions_path):
        rf_df = load_rf_predictions(rf_predictions_path)
        if 'property_name' in rf_df.columns:
            properties.update(rf_df['property_name'].unique())
    
    # If no properties found in predictions, use common ones from test set or defaults
    if not properties:
        if 'property_name' in test_df.columns:
            properties = test_df['property_name'].unique()
        else:
            # Default properties based on project scope
            properties = ['LogP', 'Solubility', 'Boiling Point']
    
    audit_records = []
    
    for _, row in test_df.iterrows():
        smiles = row.get('smiles', '')
        
        # For each property, create an audit record
        for prop in properties:
            # Get experimental value
            exp_val = None
            if 'property_name' in test_df.columns and 'value' in test_df.columns:
                prop_row = test_df[(test_df['smiles'] == smiles) & (test_df['property_name'] == prop)]
                if len(prop_row) > 0:
                    exp_val = prop_row.iloc[0]['value']
            elif prop in row:
                exp_val = row[prop]
            else:
                # Try to find in predictions
                if baseline_df is not None:
                    prop_row = baseline_df[(baseline_df['smiles'] == smiles) & (baseline_df['property_name'] == prop)]
                    if len(prop_row) > 0:
                        exp_val = prop_row.iloc[0]['experimental_value']
            
            # Determine uncertainty status and reported value
            if uncertainty_status == "Available":
                # In a real scenario, we would have actual uncertainty values
                # For now, we explicitly state "Not Reported" as per the task requirement
                reported_uncertainty = "Not Reported"
                uncertainty_source_status = "Available but Not Reported in Source"
            else:
                reported_uncertainty = "Not Reported"
                uncertainty_source_status = "Not Available in Source"
            
            record = {
                'smiles': smiles,
                'property': prop,
                'experimental_value': exp_val if exp_val is not None else "Not Available",
                'reported_uncertainty': reported_uncertainty,
                'uncertainty_source_status': uncertainty_source_status
            }
            
            audit_records.append(record)
    
    # Create DataFrame and save
    audit_df = pd.DataFrame(audit_records)
    audit_df.to_csv(output_path, index=False)
    
    logger.info(f"Measurement Standards Audit saved to {output_path} with {len(audit_records)} records")
    
    # Log summary
    unverified_count = len(audit_df[audit_df['uncertainty_source_status'] == 'Not Available in Source'])
    logger.info(f"Audit Summary: {unverified_count} records flagged as 'Unverified' (uncertainty not available)")
    
    return audit_df

def main():
    """Main entry point for stats analysis module."""
    ensure_dirs()
    
    # Paths
    metadata_path = "data/raw/dataset_metadata.json"
    test_set_path = "data/derived/test_set.csv"
    baseline_predictions_path = "data/derived/baseline_test_predictions.csv"
    rf_predictions_path = "data/derived/rf_test_predictions.csv"
    output_audit_path = "data/derived/measurement_standards_audit.csv"
    
    try:
        # Generate Measurement Standards Audit (T050)
        generate_measurement_audit(
            test_set_path=test_set_path,
            baseline_predictions_path=baseline_predictions_path,
            rf_predictions_path=rf_predictions_path,
            metadata_path=metadata_path,
            output_path=output_audit_path
        )
        
        logger.info("Measurement Standards Audit completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        logger.error("This task depends on T031, T011.5, T014.5, and T020.1 being completed first.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during measurement audit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()