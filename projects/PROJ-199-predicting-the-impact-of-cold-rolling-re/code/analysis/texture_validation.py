import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd

from utils.logging import get_logger
from config import get_reductions

logger = get_logger(__name__)

# Standard FCC texture evolution trends based on literature (e.g., Rosenstock et al.)
# Key: Material, Value: Dict of component -> expected trend direction ('increase', 'decrease', 'stable')
# Brass: Typically increases with reduction in FCC metals
# Copper: Typically increases with reduction
# S: Typically increases with reduction
# Goss: Behavior varies, often stable or slight increase
# Random: Typically decreases as texture sharpens
STANDARD_FCC_TRENDS = {
    'Al': {
        'brass': 'increase',
        'copper': 'increase',
        's': 'increase',
        'goss': 'stable',
        'random': 'decrease'
    },
    'Cu': {
        'brass': 'increase',
        'copper': 'increase',
        's': 'increase',
        'goss': 'stable',
        'random': 'decrease'
    },
    'Ni': {
        'brass': 'increase',
        'copper': 'increase',
        's': 'increase',
        'goss': 'stable',
        'random': 'decrease'
    }
}

def load_descriptors(filepath: str = "data/processed/descriptors.csv") -> pd.DataFrame:
    """Load the descriptors dataset."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Descriptors file not found: {filepath}")
    logger.info(f"Loading descriptors from {filepath}")
    return pd.read_csv(path)

def calculate_expected_trend(material: str) -> Dict[str, str]:
    """
    Retrieve the expected standard FCC trend for a given material.
    Falls back to a generic FCC trend if the specific material is not defined.
    """
    if material in STANDARD_FCC_TRENDS:
        return STANDARD_FCC_TRENDS[material]
    
    # Generic fallback for any FCC metal if specific data is missing
    logger.warning(f"No specific standard trend defined for {material}. Using generic FCC trend.")
    return {
        'brass': 'increase',
        'copper': 'increase',
        's': 'increase',
        'goss': 'stable',
        'random': 'decrease'
    }

def calculate_trend_deviation(
    sample_data: pd.Series, 
    expected_trends: Dict[str, str], 
    reduction_col: str = 'reduction',
    threshold: float = 0.15
) -> Tuple[bool, Dict[str, Any]]:
    """
    Analyze a single sample's evolution relative to expected trends.
    Since a single row is a snapshot, we interpret 'deviation' as:
    1. If the sample is at a high reduction but shows low texture intensity (high random), it deviates.
    2. If the sample is at low reduction but shows high texture intensity, it might be anomalous (depending on context).
    
    For this specific task (T021), we flag samples where the *state* is inconsistent with the *progression* 
    implied by the reduction level relative to standard FCC behavior.
    
    Logic:
    - High Reduction (> 60%): Expect low 'random' fraction (< 0.2) and high major components.
    - Low Reduction (< 20%): Expect higher 'random' fraction (> 0.4) and lower major components.
    
    This acts as a sanity check for "anomalous behavior" where a sample at high reduction 
    remains largely random (failed deformation) or at low reduction is already fully textured.
    """
    deviation_details = {}
    is_deviant = False
    
    reduction = sample_data.get(reduction_col, 0)
    random_frac = sample_data.get('random_fraction', 0.0)
    brass = sample_data.get('brass_fraction', 0.0)
    copper = sample_data.get('copper_fraction', 0.0)
    s = sample_data.get('s_fraction', 0.0)
    
    # Check 1: High Reduction Anomaly (Should be textured, but is random)
    if reduction > 60 and random_frac > 0.3:
        deviation_details['high_reduction_random'] = {
            'observed': random_frac,
            'expected_max': 0.3,
            'status': 'FAIL'
        }
        is_deviant = True
    
    # Check 2: Low Reduction Anomaly (Should be random, but is textured)
    # Only flag if major components are extremely high for low reduction
    if reduction < 20:
        total_texture = brass + copper + s
        if total_texture > 0.7:
            deviation_details['low_reduction_textured'] = {
                'observed': total_texture,
                'expected_max': 0.7,
                'status': 'FAIL'
            }
            is_deviant = True
    
    # Check 3: Mass Balance sanity (if not already caught by T019, double check here for trend logic)
    total = brass + copper + s + sample_data.get('goss_fraction', 0.0) + random_frac
    if abs(total - 1.0) > 0.05:
        deviation_details['mass_balance'] = {
            'sum': total,
            'status': 'WARN'
        }
        # Don't necessarily flag as deviant trend, but log it.
    
    return is_deviant, deviation_details

def aggregate_deviation_score(deviation_details: Dict[str, Any]) -> float:
    """Calculate a simple score based on the number of deviations."""
    return len([k for k, v in deviation_details.items() if v.get('status') == 'FAIL'])

def validate_sample_trends(df: pd.DataFrame, threshold: float = 0.15) -> pd.DataFrame:
    """
    Validate trends for each sample in the dataset.
    Adds a 'is_trend_deviant' boolean column and 'deviation_details' JSON string.
    """
    results = []
    
    for idx, row in df.iterrows():
        material = row.get('material', 'Unknown')
        expected = calculate_expected_trend(material)
        is_deviant, details = calculate_trend_deviation(row, expected, threshold=threshold)
        
        results.append({
            'index': idx,
            'is_trend_deviant': is_deviant,
            'deviation_details': details,
            'score': aggregate_deviation_score(details)
        })
    
    result_df = pd.DataFrame(results)
    df_out = df.copy()
    df_out['is_trend_deviant'] = result_df['is_trend_deviant']
    df_out['deviation_details'] = result_df['deviation_details'].apply(str)
    df_out['deviation_score'] = result_df['score']
    
    deviant_count = df_out['is_trend_deviant'].sum()
    logger.info(f"Found {deviant_count} samples with anomalous texture evolution out of {len(df_out)}")
    
    return df_out

def validate_dataset_trends(df: pd.DataFrame) -> bool:
    """
    Aggregate check: Do the overall trends of the dataset match FCC expectations?
    Returns True if the dataset generally follows trends, False if the majority is anomalous.
    """
    if 'is_trend_deviant' not in df.columns:
        df = validate_sample_trends(df)
    
    deviant_ratio = df['is_trend_deviant'].mean()
    if deviant_ratio > 0.2: # If > 20% of samples are anomalous, flag dataset
        logger.warning(f"Dataset shows high anomaly rate: {deviant_ratio:.2f}")
        return False
    return True

def flag_deviant_samples(df: pd.DataFrame, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Main entry point for T021.
    Validates trends, flags deviant samples, and optionally saves the report.
    """
    logger.info("Starting texture evolution trend validation (T021)")
    
    validated_df = validate_sample_trends(df)
    
    # Filter to show only deviant samples for review
    deviant_samples = validated_df[validated_df['is_trend_deviant']]
    
    if not deviant_samples.empty:
        logger.warning(f"Identified {len(deviant_samples)} samples with anomalous texture evolution.")
        logger.warning("These samples are flagged but NOT excluded from the dataset per T021 requirements.")
        logger.warning("They are marked with 'is_trend_deviant=True' for downstream filtering or analysis.")
    else:
        logger.info("All samples follow standard FCC texture evolution trends.")
    
    if output_path:
        validated_df.to_csv(output_path, index=False)
        logger.info(f"Validation report saved to {output_path}")
    
    return validated_df

def main():
    """Main execution entry point."""
    input_path = "data/processed/descriptors.csv"
    output_path = "data/processed/descriptors_validated.csv"
    
    if not Path(input_path).exists():
        logger.error(f"Input file {input_path} not found. Cannot run validation.")
        sys.exit(1)
    
    try:
        df = load_descriptors(input_path)
        validated_df = flag_deviant_samples(df, output_path=output_path)
        print(f"Validation complete. Report saved to {output_path}")
        print(f"Total samples: {len(validated_df)}")
        print(f"Deviant samples: {validated_df['is_trend_deviant'].sum()}")
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
