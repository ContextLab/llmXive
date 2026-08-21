"""
Texture Validation Module

Implements validation logic to flag samples where texture evolution deviates
from standard FCC trends. This serves as an edge case handler for User Story 2.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# Ensure project root is in path for imports if running as script
if "code" not in sys.path:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from config import get_reductions

logger = get_logger(__name__)

# Standard FCC Texture Evolution Trends (Approximate)
# Based on literature for FCC metals (Al, Cu, Ni) under cold rolling:
# - Brass (θ) typically increases or remains dominant in the Copper component region initially,
#   but in many FCC metals, the Brass component increases significantly with reduction.
# - Copper (Cu) component often increases then stabilizes or decreases at very high reductions.
# - S component increases.
# - Goss component behavior varies but is often less dominant.
#
# For this validation, we define "Standard Trends" as monotonic increases for Brass and S,
# and a specific trajectory for Copper.
# Deviation is flagged if the sign of the derivative (trend) contradicts the expected physics
# for the majority of the reduction range.

EXPECTED_TRENDS = {
    "Brass": "increasing",
    "Copper": "increasing",  # Often increases then plateaus, but initial trend is up
    "S": "increasing",
    "Goss": "variable"  # No strict monotonic requirement
}

def load_descriptors() -> pd.DataFrame:
    """
    Load the processed descriptors from the standard location.
    Raises FileNotFoundError if the file does not exist.
    """
    data_path = Path("data/processed/descriptors.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {data_path}. "
                                "Ensure T021 has been completed successfully.")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} descriptor records from {data_path}")
    return df

def calculate_expected_trend(component: str) -> str:
    """
    Retrieve the expected trend direction for a given texture component.
    """
    return EXPECTED_TRENDS.get(component, "variable")

def calculate_trend_deviation(df: pd.DataFrame, component: str, material: str) -> float:
    """
    Calculate a deviation score for a specific component and material.
    
    Logic:
    1. Group by sample_id and sort by reduction.
    2. Calculate the slope (change in volume fraction vs reduction) for each sample.
    3. Compare the sign of the slope to the expected trend.
    4. Return a score: 0.0 if fully compliant, increasing if deviating.
    
    A simple heuristic: 
    - If expected is "increasing", and the average slope is negative, score = 1.0 (max deviation).
    - If expected is "increasing", and slope is positive, score = 0.0.
    - We can refine this by magnitude: score = max(0, -slope / expected_max_slope)
    """
    expected = calculate_expected_trend(component)
    
    if expected == "variable":
        return 0.0

    # Filter for this material
    material_df = df[df['material'] == material].copy()
    if material_df.empty:
        return 0.0

    # Ensure reduction is numeric
    material_df['reduction'] = pd.to_numeric(material_df['reduction'], errors='coerce')
    material_df = material_df.dropna(subset=['reduction'])

    if material_df.empty:
        return 0.0

    # Group by sample_id to track individual sample evolution
    sample_groups = material_df.groupby('sample_id')
    
    deviation_scores = []

    for sample_id, group in sample_groups:
        if len(group) < 2:
            # Not enough points to determine a trend
            continue
        
        # Sort by reduction
        group = group.sort_values('reduction')
        
        # Calculate slope using linear regression (simple)
        x = group['reduction'].values
        y = group[component].values
        
        # Simple linear regression slope
        # slope = (n*sum(xy) - sum(x)*sum(y)) / (n*sum(x^2) - (sum(x))^2)
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x**2)
        
        denom = n * sum_x2 - sum_x**2
        if denom == 0:
            continue
        
        slope = (n * sum_xy - sum_x * sum_y) / denom
        
        # Determine deviation
        if expected == "increasing":
            if slope < 0:
                # Negative slope when expecting increase
                # Normalize by a typical expected slope (e.g., 0.01 per % reduction)
                # If slope is -0.05, deviation is high.
                deviation = abs(slope) / 0.01 
                deviation_scores.append(min(1.0, deviation))
            else:
                deviation_scores.append(0.0)
        elif expected == "decreasing":
            if slope > 0:
                deviation = abs(slope) / 0.01
                deviation_scores.append(min(1.0, deviation))
            else:
                deviation_scores.append(0.0)

    if not deviation_scores:
        return 0.0
        
    return np.mean(deviation_scores)

def aggregate_deviation_score(df: pd.DataFrame) -> Dict[str, float]:
    """
    Aggregate deviation scores across all components and materials.
    Returns a dictionary mapping sample_id to a total deviation score.
    """
    # We need to calculate per-sample deviation, not per-material.
    # The previous function calculated per-material trend. 
    # Let's refactor the logic to be per-sample.
    
    df['reduction'] = pd.to_numeric(df['reduction'], errors='coerce')
    df = df.dropna(subset=['reduction'])
    
    sample_ids = df['sample_id'].unique()
    sample_scores = {}
    
    for sample_id in sample_ids:
        group = df[df['sample_id'] == sample_id].sort_values('reduction')
        if len(group) < 2:
            sample_scores[sample_id] = 0.0
            continue
        
        total_deviation = 0.0
        count = 0
        
        for component in ["Brass", "Copper", "S"]:
            expected = calculate_expected_trend(component)
            if expected == "variable":
                continue
            
            y = group[component].values
            x = group['reduction'].values
            
            n = len(x)
            sum_x = np.sum(x)
            sum_y = np.sum(y)
            sum_xy = np.sum(x * y)
            sum_x2 = np.sum(x**2)
            
            denom = n * sum_x2 - sum_x**2
            if denom == 0:
                continue
            
            slope = (n * sum_xy - sum_x * sum_y) / denom
            
            if expected == "increasing" and slope < 0:
                total_deviation += abs(slope) / 0.01
                count += 1
            elif expected == "decreasing" and slope > 0:
                total_deviation += abs(slope) / 0.01
                count += 1
        
        # Average deviation across checked components
        if count > 0:
            sample_scores[sample_id] = min(1.0, total_deviation / count)
        else:
            sample_scores[sample_id] = 0.0
            
    return sample_scores

def validate_sample_trends(df: pd.DataFrame, threshold: float = 0.5) -> List[str]:
    """
    Identify samples that deviate significantly from expected FCC trends.
    
    Args:
        df: DataFrame with columns ['sample_id', 'material', 'reduction', 'Brass', 'Copper', 'S', ...]
        threshold: Deviation score threshold (0.0 to 1.0) above which a sample is flagged.
        
    Returns:
        List of sample_ids that are flagged as deviant.
    """
    scores = aggregate_deviation_score(df)
    deviant_samples = [sid for sid, score in scores.items() if score > threshold]
    
    if deviant_samples:
        logger.warning(f"Found {len(deviant_samples)} samples deviating from standard FCC trends: {deviant_samples}")
    else:
        logger.info("No samples deviated significantly from standard FCC trends.")
        
    return deviant_samples

def validate_dataset_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the overall dataset trends and return a summary report.
    """
    scores = aggregate_deviation_score(df)
    avg_score = np.mean(list(scores.values())) if scores else 0.0
    max_score = max(scores.values()) if scores else 0.0
    deviant_count = len([s for s in scores.values() if s > 0.5])
    
    report = {
        "total_samples": len(scores),
        "deviant_samples_count": deviant_count,
        "average_deviation_score": avg_score,
        "max_deviation_score": max_score,
        "deviant_sample_ids": [sid for sid, score in scores.items() if score > 0.5]
    }
    
    return report

def flag_deviant_samples(df: pd.DataFrame, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Main entry point to flag deviant samples.
    Adds a 'is_deviant' column to the dataframe.
    Optionally writes the flagged samples to a file.
    """
    deviant_ids = validate_sample_trends(df)
    df['is_deviant'] = df['sample_id'].isin(deviant_ids)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Flagged samples written to {output_path}")
        
    return df

def main():
    """
    Main execution function to run texture validation.
    """
    logger.info("Starting Texture Validation (T022)...")
    
    try:
        df = load_descriptors()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Validate trends
    deviant_ids = validate_sample_trends(df)
    
    if deviant_ids:
        logger.warning(f"WARNING: {len(deviant_ids)} samples flagged for deviation from FCC trends.")
        logger.warning("These samples should be reviewed for data quality or anomalous physical behavior.")
    else:
        logger.info("All samples conform to standard FCC texture evolution trends.")
        
    # Optional: Write results
    output_file = Path("data/processed/descriptors_validated.csv")
    df_validated = flag_deviant_samples(df, output_path=output_file)
    
    print(f"\nValidation Report:")
    print(f"Total Samples: {len(df_validated)}")
    print(f"Deviant Samples: {df_validated['is_deviant'].sum()}")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    main()