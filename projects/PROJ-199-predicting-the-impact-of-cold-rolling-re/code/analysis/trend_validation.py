"""
Trend Validation Module for FCC Texture Evolution.

This module implements validation logic to flag samples where texture evolution
deviates from standard FCC trends (Edge Case). It ensures that the pipeline
identifies anomalous behavior rather than forcing a fit to statistical noise.

Standard FCC trends (based on metallurgical literature for Al, Cu, Ni):
- Brass component generally increases with cold rolling reduction.
- Copper component generally increases with cold rolling reduction.
- S component generally increases with cold rolling reduction.
- Goss component behavior is more variable but often increases or remains stable.
- Random fraction generally decreases as texture sharpens.

Deviations from these trends are flagged as potential outliers or anomalous samples.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set

import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Standard FCC trend expectations (direction of change with increasing reduction)
# Positive = expected to increase, Negative = expected to decrease
STANDARD_TRENDS = {
    'Brass': 1,
    'Copper': 1,
    'S': 1,
    'Goss': 0,  # Variable, treat as neutral for strict deviation detection
    'Random': -1
}

# Threshold for deviation detection (percentage change from expected trend)
DEVIATION_THRESHOLD = 0.15  # 15% deviation from expected trend direction

def load_descriptors(path: str = "data/processed/descriptors.csv") -> pd.DataFrame:
    """
    Load descriptors from the processed CSV file.

    Args:
        path: Path to the descriptors CSV file.

    Returns:
        DataFrame containing descriptors.

    Raises:
        FileNotFoundError: If the descriptors file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Descriptors file not found: {path}")

    df = pd.read_csv(path)

    required_columns = ['material', 'reduction', 'Brass', 'Copper', 'S', 'Goss', 'Random']
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns in descriptors: {missing}")

    logger.info(f"Loaded {len(df)} samples from {path}")
    return df

def calculate_trend_direction(df: pd.DataFrame, material: str) -> Dict[str, float]:
    """
    Calculate the actual trend direction for each component within a material.

    Uses linear regression slope to determine if a component increases or decreases
    with reduction.

    Args:
        df: DataFrame filtered by material.
        material: Material name (Al, Cu, Ni).

    Returns:
        Dictionary mapping component names to their trend slope.
    """
    if df.empty:
        return {}

    trends = {}
    components = ['Brass', 'Copper', 'S', 'Goss', 'Random']

    for component in components:
        # Simple linear regression: slope = cov(x,y) / var(x)
        x = df['reduction'].values
        y = df[component].values

        # Handle constant reduction (single point or all same)
        if len(np.unique(x)) < 2:
            trends[component] = 0.0
            continue

        slope = np.polyfit(x, y, 1)[0]
        trends[component] = slope

    return trends

def validate_sample_trends(df: pd.DataFrame, threshold: float = DEVIATION_THRESHOLD) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Validate individual samples against expected FCC trends.

    Flags samples that contribute to anomalous trend directions.

    Args:
        df: Full descriptors DataFrame.
        threshold: Deviation threshold for flagging.

    Returns:
        Tuple of (flagged_samples_df, list_of_flag_reasons)
    """
    flagged_samples = []
    materials = df['material'].unique()

    for material in materials:
        material_df = df[df['material'] == material].copy()
        material_df = material_df.sort_values('reduction')

        if len(material_df) < 3:
            logger.warning(f"Insufficient data points for {material} to validate trends. Skipping.")
            continue

        # Calculate expected trend direction
        trends = calculate_trend_direction(material_df, material)

        # Check each component against standard trends
        for component in ['Brass', 'Copper', 'S', 'Goss', 'Random']:
            expected_direction = STANDARD_TRENDS.get(component, 0)
            actual_slope = trends.get(component, 0)

            # Determine if trend is anomalous
            if expected_direction == 0:
                continue  # Skip components with no strict expectation

            # Check if actual trend opposes expected direction
            if expected_direction > 0 and actual_slope < -threshold:
                # Expected increase, but significant decrease
                logger.warning(f"Anomalous trend detected for {material} {component}: "
                             f"Expected increase, observed slope {actual_slope:.4f}")
                # Flag samples with lowest reduction values in this material
                low_reduction_samples = material_df[
                    material_df['reduction'] <= material_df['reduction'].quantile(0.25)
                ]
                for _, row in low_reduction_samples.iterrows():
                    flagged_samples.append({
                        'sample_id': row.get('sample_id', f"{material}_{row['reduction']}"),
                        'material': material,
                        'reduction': row['reduction'],
                        'component': component,
                        'reason': f"Anomalous trend: {component} decreases (slope={actual_slope:.4f}) while expected to increase",
                        'severity': 'high'
                    })

            elif expected_direction < 0 and actual_slope > threshold:
                # Expected decrease, but significant increase
                logger.warning(f"Anomalous trend detected for {material} {component}: "
                             f"Expected decrease, observed slope {actual_slope:.4f}")
                high_reduction_samples = material_df[
                    material_df['reduction'] >= material_df['reduction'].quantile(0.75)
                ]
                for _, row in high_reduction_samples.iterrows():
                    flagged_samples.append({
                        'sample_id': row.get('sample_id', f"{material}_{row['reduction']}"),
                        'material': material,
                        'reduction': row['reduction'],
                        'component': component,
                        'reason': f"Anomalous trend: {component} increases (slope={actual_slope:.4f}) while expected to decrease",
                        'severity': 'high'
                    })

    if flagged_samples:
        flagged_df = pd.DataFrame(flagged_samples)
        logger.info(f"Flagged {len(flagged_samples)} samples with anomalous texture evolution")
        return flagged_df, flagged_samples
    else:
        logger.info("No anomalous trends detected. All samples follow standard FCC evolution.")
        return pd.DataFrame(), []

def aggregate_deviation_report(flagged_samples: List[Dict], output_path: str) -> Dict:
    """
    Generate a summary report of flagged samples.

    Args:
        flagged_samples: List of flagged sample dictionaries.
        output_path: Path to save the JSON report.

    Returns:
        Report dictionary.
    """
    report = {
        'total_flagged': len(flagged_samples),
        'by_material': {},
        'by_component': {},
        'flagged_samples': flagged_samples
    }

    if flagged_samples:
        df = pd.DataFrame(flagged_samples)
        report['by_material'] = df['material'].value_counts().to_dict()
        report['by_component'] = df['component'].value_counts().to_dict()

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Trend validation report saved to {output_path}")
    return report

def run_trend_validation(
    input_path: str = "data/processed/descriptors.csv",
    output_path: str = "data/processed/trend_validation_report.json"
) -> Dict:
    """
    Main entry point for trend validation.

    Args:
        input_path: Path to descriptors CSV.
        output_path: Path for output JSON report.

    Returns:
        Validation report dictionary.
    """
    logger.info("Starting trend validation for FCC texture evolution...")

    try:
        df = load_descriptors(input_path)
        flagged_df, flagged_samples = validate_sample_trends(df)
        report = aggregate_deviation_report(flagged_samples, output_path)

        if flagged_samples:
            logger.warning(f"Found {len(flagged_samples)} samples with anomalous texture evolution. "
                         f"Review the report at {output_path}")
        else:
            logger.info("All samples conform to standard FCC texture evolution trends.")

        return report

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during trend validation: {e}")
        raise

def main():
    """Command-line entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate texture evolution trends against standard FCC behavior."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/descriptors.csv",
        help="Path to input descriptors CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/trend_validation_report.json",
        help="Path for output validation report"
    )

    args = parser.parse_args()

    try:
        report = run_trend_validation(args.input, args.output)
        print(f"Trend validation complete. Report saved to {args.output}")
        print(f"Total flagged samples: {report['total_flagged']}")
    except Exception as e:
        logger.error(f"Failed to complete trend validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()