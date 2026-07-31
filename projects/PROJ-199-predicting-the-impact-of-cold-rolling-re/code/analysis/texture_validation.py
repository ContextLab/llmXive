"""
T022: Texture Evolution Deviation Validator

Validates samples where texture evolution deviates from standard FCC trends.
Standard FCC trends for cold rolling include:
- Increase in Brass component (B)
- Increase in Copper component (C)
- Decrease in Cube component
- S component typically increases then stabilizes

This module flags samples that deviate significantly from these expected trends
based on material type and reduction level.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# Import from existing API surface
from utils.logging import get_logger
from config import get_reductions, ConfigurationError
from features.descriptors import calculate_texture_index, calculate_component_volume_fractions

# Configure logger
logger = get_logger(__name__)

# Standard FCC trend expectations (direction of change with increasing reduction)
# Positive = expected to increase, Negative = expected to decrease
STANDARD_FCC_TRENDS = {
    'Al': {
        'Brass': 1.0,      # Brass increases with reduction
        'Copper': 1.0,     # Copper increases with reduction
        'S': 0.5,          # S increases moderately
        'Goss': -0.3,      # Goss typically decreases
        'Cube': -1.0,      # Cube decreases significantly
    },
    'Cu': {
        'Brass': 1.0,
        'Copper': 1.0,
        'S': 0.5,
        'Goss': -0.2,
        'Cube': -0.8,
    },
    'Ni': {
        'Brass': 0.8,
        'Copper': 0.9,
        'S': 0.4,
        'Goss': -0.1,
        'Cube': -0.7,
    }
}

# Threshold for deviation detection (standard deviations from expected trend)
DEVIATION_THRESHOLD = 2.0

def load_descriptors(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed descriptors from the data directory.

    Args:
        data_path: Optional path to the descriptors file. If None, uses default.

    Returns:
        DataFrame with texture descriptors.

    Raises:
        FileNotFoundError: If descriptors file not found.
        ConfigurationError: If data path configuration is invalid.
    """
    if data_path is None:
        try:
            base_path = Path(get_data_path())
            data_path = base_path / "processed" / "descriptors.csv"
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            raise

    if not data_path.exists():
        raise FileNotFoundError(f"Descriptors file not found at: {data_path}")

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} samples from {data_path}")
    return df

def calculate_expected_trend(material: str, reduction: float) -> Dict[str, float]:
    """
    Calculate expected trend values for a given material and reduction level.

    Args:
        material: Material type (Al, Cu, Ni)
        reduction: Cold rolling reduction percentage

    Returns:
        Dictionary mapping component names to expected trend values.
    """
    base_trends = STANDARD_FCC_TRENDS.get(material, STANDARD_FCC_TRENDS['Al'])

    # Normalize reduction to 0-1 scale for trend calculation
    # Assuming max reduction is around 90%
    normalized_reduction = min(reduction / 90.0, 1.0)

    expected = {}
    for component, trend_factor in base_trends.items():
        # Trend scales with reduction level
        expected[component] = trend_factor * normalized_reduction

    return expected

def calculate_trend_deviation(
    sample_data: Dict[str, Any],
    expected_trends: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate deviation of sample's texture evolution from expected trends.

    Args:
        sample_data: Dictionary with component volume fractions and metadata
        expected_trends: Expected trend values for the material/reduction

    Returns:
        Dictionary mapping component names to deviation scores.
    """
    deviations = {}

    for component in expected_trends.keys():
        actual_value = sample_data.get(component, 0.0)
        expected_value = expected_trends.get(component, 0.0)

        # Calculate normalized deviation
        # Using a simple difference normalized by expected magnitude
        if abs(expected_value) > 0.01:
            deviation = (actual_value - expected_value) / abs(expected_value)
        else:
            # If expected is near zero, use absolute deviation
            deviation = actual_value - expected_value

        deviations[component] = deviation

    return deviations

def aggregate_deviation_score(
    component_deviations: Dict[str, float],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Aggregate component deviations into a single score.

    Args:
        component_deviations: Deviation scores for each component
        weights: Optional weights for each component (defaults to equal)

    Returns:
        Aggregate deviation score (higher = more deviation).
    """
    if weights is None:
        weights = {comp: 1.0 for comp in component_deviations.keys()}

    total_weight = sum(weights.values())
    weighted_sum = 0.0

    for component, deviation in component_deviations.items():
        weight = weights.get(component, 1.0)
        weighted_sum += abs(deviation) * weight

    return weighted_sum / total_weight if total_weight > 0 else 0.0

def validate_sample_trends(
    sample_data: Dict[str, Any],
    deviation_threshold: float = DEVIATION_THRESHOLD
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a single sample against standard FCC texture evolution trends.

    Args:
        sample_data: Sample data including material, reduction, and component fractions
        deviation_threshold: Threshold for flagging deviations

    Returns:
        Tuple of (is_valid, details_dict)
        - is_valid: True if sample follows expected trends
        - details_dict: Contains deviation scores and flag information
    """
    material = sample_data.get('material', 'Al')
    reduction = sample_data.get('reduction', 0.0)

    # Get expected trends
    expected_trends = calculate_expected_trend(material, reduction)

    # Calculate deviations
    component_deviations = calculate_trend_deviation(sample_data, expected_trends)

    # Aggregate deviation score
    aggregate_score = aggregate_deviation_score(component_deviations)

    # Determine if sample is flagged
    is_valid = aggregate_score <= deviation_threshold

    details = {
        'material': material,
        'reduction': reduction,
        'expected_trends': expected_trends,
        'component_deviations': component_deviations,
        'aggregate_deviation_score': aggregate_score,
        'is_valid': is_valid,
        'flagged': not is_valid,
        'deviation_reasons': []
    }

    # Collect specific reasons for flagging
    if not is_valid:
        for component, deviation in component_deviations.items():
            if abs(deviation) > deviation_threshold:
                direction = "higher" if deviation > 0 else "lower"
                details['deviation_reasons'].append(
                    f"{component} component is {direction} than expected "
                    f"(deviation: {deviation:.2f})"
                )

    return is_valid, details

def validate_dataset_trends(
    df: pd.DataFrame,
    deviation_threshold: float = DEVIATION_THRESHOLD
) -> pd.DataFrame:
    """
    Validate all samples in a dataset against standard FCC texture evolution trends.

    Args:
        df: DataFrame with texture descriptors
        deviation_threshold: Threshold for flagging deviations

    Returns:
        DataFrame with validation results appended.
    """
    results = []

    for idx, row in df.iterrows():
        sample_data = row.to_dict()
        is_valid, details = validate_sample_trends(sample_data, deviation_threshold)

        # Append validation results to row
        result_row = {
            'sample_id': row.get('sample_id', f'sample_{idx}'),
            'material': row.get('material', 'Unknown'),
            'reduction': row.get('reduction', 0.0),
            'follows_fcc_trend': is_valid,
            'deviation_score': details['aggregate_deviation_score'],
            'flagged': not is_valid,
            'deviation_reasons': '; '.join(details['deviation_reasons']) if details['deviation_reasons'] else ''
        }

        results.append(result_row)

    validation_df = pd.DataFrame(results)
    return validation_df

def flag_deviant_samples(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    deviation_threshold: float = DEVIATION_THRESHOLD
) -> pd.DataFrame:
    """
    Flag samples that deviate from standard FCC texture evolution trends.

    Args:
        df: DataFrame with texture descriptors
        output_path: Optional path to save flagged samples report
        deviation_threshold: Threshold for flagging deviations

    Returns:
        DataFrame with flagged samples.
    """
    validation_results = validate_dataset_trends(df, deviation_threshold)

    # Filter to only flagged samples
    flagged_samples = validation_results[validation_results['flagged'] == True]

    logger.info(
        f"Flagged {len(flagged_samples)} out of {len(validation_results)} samples "
        f"for deviating from standard FCC trends"
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        flagged_samples.to_csv(output_path, index=False)
        logger.info(f"Flagged samples report saved to: {output_path}")

    return flagged_samples

def main():
    """
    Main entry point for texture trend validation.

    Reads descriptors from data/processed/descriptors.csv, validates against
    standard FCC trends, and outputs a report of flagged samples.
    """
    try:
        # Load descriptors
        descriptors_path = Path(get_data_path()) / "processed" / "descriptors.csv"
        df = load_descriptors(descriptors_path)

        # Validate and flag deviant samples
        flagged_path = Path(get_data_path()) / "processed" / "flagged_trend_deviations.csv"
        flagged_samples = flag_deviant_samples(df, flagged_path)

        # Print summary
        print(f"\nTexture Trend Validation Summary:")
        print(f"  Total samples: {len(df)}")
        print(f"  Flagged samples: {len(flagged_samples)}")
        print(f"  Flagged percentage: {100*len(flagged_samples)/len(df):.1f}%")

        if len(flagged_samples) > 0:
            print(f"\nFlagged sample IDs:")
            for _, row in flagged_samples.iterrows():
                print(f"  - {row['sample_id']} ({row['material']}, {row['reduction']}% reduction)")
                if row['deviation_reasons']:
                    print(f"    Reasons: {row['deviation_reasons']}")

        print(f"\nReport saved to: {flagged_path}")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
