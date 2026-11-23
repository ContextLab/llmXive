"""
Reporter module for generating evaluation_report.json.

Implements T024: Generate evaluation_report.json including data_source_type,
per-family metrics, and missing confounds warning.

Logic for data_source_type:
- "Synthetic" if synthetic generator was invoked OR real data count < threshold
- "Real" otherwise
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import from existing API surface
from code.models.evaluator import compute_metrics_per_family, load_model_predictions
from code.utils.logging import get_logger, log_warning_structured

# Constants
MIN_SAMPLES_PER_FAMILY = 50
REAL_DATA_THRESHOLD = 100  # Threshold to consider real data sufficient

def load_evaluation_metrics(predictions_path: Path) -> Dict[str, Any]:
    """Load metrics computed by the evaluator module."""
    # Compute metrics per family using existing evaluator functions
    predictions_df = load_model_predictions(predictions_path)
    
    if predictions_df is None or predictions_df.empty:
        logger = get_logger()
        logger.error(f"Could not load predictions from {predictions_path}")
        return {}
    
    # Compute metrics per alloy family
    metrics_per_family = compute_metrics_per_family(predictions_df)
    
    return metrics_per_family

def determine_data_source_type(predictions_df: pd.DataFrame, real_data_count: int = 0) -> str:
    """
    Determine data_source_type based on task requirements:
    - "Synthetic" if synthetic generator was invoked or real data count < threshold
    - "Real" otherwise
    
    We infer synthetic invocation by checking if real_data_count is below threshold
    or if the dataset contains synthetic markers.
    """
    if real_data_count < REAL_DATA_THRESHOLD:
        return "Synthetic"
    
    # Check for synthetic data markers in the dataframe
    if 'is_synthetic' in predictions_df.columns:
        synthetic_count = predictions_df['is_synthetic'].sum()
        if synthetic_count > 0:
            return "Synthetic"
    
    # If we have substantial real data, consider it Real
    if real_data_count >= REAL_DATA_THRESHOLD:
        return "Real"
    
    # Default to Synthetic if uncertain
    return "Synthetic"

def check_missing_confounds(predictions_df: pd.DataFrame) -> List[str]:
    """
    Check for missing confounds as per SC-004 and FR-012.
    Returns list of warnings about missing confounds.
    """
    warnings_list = []
    
    # Check for common confounds that should be present
    expected_confounds = ['temperature', 'strain_rate', 'alloy_composition']
    
    for confound in expected_confounds:
        if confound not in predictions_df.columns:
            warnings_list.append(f"Missing confound: {confound}")
    
    # Check for sufficient sample diversity
    if 'alloy_family' in predictions_df.columns:
        family_counts = predictions_df['alloy_family'].value_counts()
        for family, count in family_counts.items():
            if count < MIN_SAMPLES_PER_FAMILY:
                warnings_list.append(
                    f"Insufficient samples for alloy family '{family}': {count} < {MIN_SAMPLES_PER_FAMILY}"
                )
    
    return warnings_list

def generate_evaluation_report(
    predictions_path: Path,
    output_path: Path,
    real_data_count: int = 0
) -> Dict[str, Any]:
    """
    Generate evaluation_report.json with:
    - data_source_type (Real/Synthetic)
    - per-family metrics
    - missing confounds warning
    
    Args:
        predictions_path: Path to predictions.csv
        output_path: Path to save evaluation_report.json
        real_data_count: Count of real data samples (0 if synthetic only)
    
    Returns:
        Dictionary containing the evaluation report
    """
    logger = get_logger()
    
    # Load predictions
    predictions_df = load_model_predictions(predictions_path)
    
    if predictions_df is None or predictions_df.empty:
        error_msg = f"Failed to load predictions from {predictions_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Determine data source type
    data_source_type = determine_data_source_type(predictions_df, real_data_count)
    logger.info(f"Determined data source type: {data_source_type}")
    
    # Compute metrics per family
    metrics_per_family = compute_metrics_per_family(predictions_df)
    
    # Check for missing confounds
    missing_confounds_warnings = check_missing_confounds(predictions_df)
    
    # Build report
    report = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_source_type": data_source_type,
            "real_data_count": real_data_count,
            "total_samples": len(predictions_df)
        },
        "per_family_metrics": metrics_per_family,
        "warnings": {
            "missing_confounds": missing_confounds_warnings,
            "sc004_status": "WARNING" if missing_confounds_warnings else "PASS"
        },
        "summary": {
            "data_source": data_source_type,
            "families_evaluated": list(metrics_per_family.keys()) if metrics_per_family else [],
            "total_families": len(metrics_per_family) if metrics_per_family else 0
        }
    }
    
    # Add per-texture metrics if available
    if 'texture_metrics' in predictions_df.columns or any(
        col.startswith('texture_') for col in predictions_df.columns
    ):
        # Compute texture-specific metrics
        texture_columns = [col for col in predictions_df.columns if col.startswith('texture_')]
        if texture_columns:
            report["texture_performance"] = {
                "texture_coefficients_evaluated": texture_columns,
                "note": "Per-texture coefficient metrics available in per_family_metrics"
            }
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Evaluation report saved to {output_path}")
    
    # Log structured warning if SC-004 violated
    if missing_confounds_warnings:
        log_warning_structured(
            "SC-004_VIOLATION",
            "Missing confounds detected in dataset",
            {
                "missing_confounds": missing_confounds_warnings,
                "data_source_type": data_source_type
            }
        )
    
    return report

def main():
    """Main entry point for generating evaluation report."""
    logger = get_logger()
    logger.info("Starting evaluation report generation (T024)")
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    predictions_path = base_dir / "data" / "processed" / "predictions.csv"
    output_path = base_dir / "data" / "processed" / "evaluation_report.json"
    
    # Check if predictions exist
    if not predictions_path.exists():
        error_msg = f"Predictions file not found at {predictions_path}. Run the pipeline first."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Load predictions to estimate real data count
    predictions_df = pd.read_csv(predictions_path)
    
    # Estimate real data count (simplified: assume all non-synthetic markers are real)
    real_data_count = 0
    if 'is_synthetic' in predictions_df.columns:
        real_data_count = len(predictions_df) - predictions_df['is_synthetic'].sum()
    else:
        # If no marker, assume all are synthetic (conservative)
        real_data_count = 0
    
    # Generate report
    report = generate_evaluation_report(
        predictions_path=predictions_path,
        output_path=output_path,
        real_data_count=real_data_count
    )
    
    logger.info(f"Evaluation report generated successfully: {output_path}")
    print(f"Evaluation report saved to: {output_path}")
    
    return report

if __name__ == "__main__":
    main()
