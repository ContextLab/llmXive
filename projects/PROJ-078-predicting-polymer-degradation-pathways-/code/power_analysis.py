"""
Statistical power analysis for the filtered polymer degradation dataset.

Performs power analysis to determine if the dataset size is sufficient for
detecting meaningful effect sizes in degradation pathway predictions.

Uses Cohen's d effect size metric with alpha=0.05 and beta=0.20 (power=0.80).
"""
import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from statsmodels.stats.power import TTestIndPower
from statsmodels.stats.effect_size import CoefCohenD

from data_models import PolymerRecord
from utils import get_logger, get_project_paths

# Constants for power analysis
ALPHA = 0.05  # Significance level
BETA = 0.20   # Type II error rate (power = 1 - beta = 0.80)
MIN_DATASET_SIZE = 150  # Minimum instances required
EFFECT_SIZE_SMALL = 0.2
EFFECT_SIZE_MEDIUM = 0.5
EFFECT_SIZE_LARGE = 0.8

def check_dataset_power(
    records: List[PolymerRecord],
    target_variable: str = 'degradation_rate',
    group_variable: str = 'degradation_pathway'
) -> Dict[str, Any]:
    """
    Perform power analysis on the dataset.
    
    Args:
        records: List of PolymerRecord objects
        target_variable: Name of the target variable for effect size calculation
        group_variable: Name of the grouping variable (e.g., degradation pathway)
        
    Returns:
        Dictionary containing power analysis results
    """
    logger = get_logger(__name__)
    
    if len(records) < 2:
        return {
            'error': 'Insufficient records for power analysis',
            'sample_size': len(records),
            'power': 0.0,
            'effect_size': 0.0,
            'sufficient': False
        }
    
    # Extract values for analysis
    # Group records by the group_variable
    groups = {}
    for record in records:
        group_val = getattr(record, group_variable, None)
        if group_val is None:
            continue
        target_val = getattr(record, target_variable, None)
        if target_val is None:
            continue
        
        if group_val not in groups:
            groups[group_val] = []
        groups[group_val].append(target_val)
    
    # Need at least 2 groups for t-test based power analysis
    if len(groups) < 2:
        logger.warning(f"Only {len(groups)} group(s) found, cannot perform power analysis")
        return {
            'error': 'Insufficient groups for power analysis',
            'sample_size': len(records),
            'power': 0.0,
            'effect_size': 0.0,
            'sufficient': False,
            'groups_found': list(groups.keys())
        }
    
    # Calculate effect size (Cohen's d) between first two groups
    group_names = list(groups.keys())
    group1 = np.array(groups[group_names[0]])
    group2 = np.array(groups[group_names[1]])
    
    if len(group1) < 2 or len(group2) < 2:
        logger.warning("One or more groups have insufficient samples for effect size calculation")
        return {
            'error': 'Insufficient samples in groups',
            'sample_size': len(records),
            'power': 0.0,
            'effect_size': 0.0,
            'sufficient': False
        }
    
    # Calculate Cohen's d
    pooled_std = np.sqrt((np.var(group1, ddof=1) + np.var(group2, ddof=1)) / 2)
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = abs(np.mean(group1) - np.mean(group2)) / pooled_std
    
    # Calculate power using TTestIndPower
    power_analysis = TTestIndPower()
    
    try:
        power = power_analysis.solve_power(
            effect_size=cohens_d,
            nobs1=len(group1),
            ratio=len(group2)/len(group1),
            alpha=ALPHA,
            power=None  # We're solving for power
        )
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}")
        power = 0.0
    
    # Determine sufficiency
    sufficient = (
        len(records) >= MIN_DATASET_SIZE and
        power >= (1 - BETA) and
        cohens_d >= EFFECT_SIZE_SMALL
    )
    
    result = {
        'sample_size': len(records),
        'group_sizes': {k: len(v) for k, v in groups.items()},
        'effect_size': float(cohens_d),
        'effect_size_interpretation': interpret_effect_size(cohens_d),
        'power': float(power),
        'alpha': ALPHA,
        'beta': BETA,
        'target_power': 1 - BETA,
        'sufficient': sufficient,
        'min_dataset_size': MIN_DATASET_SIZE,
        'warnings': []
    }
    
    # Add warnings if not sufficient
    if len(records) < MIN_DATASET_SIZE:
        result['warnings'].append(f"Dataset size ({len(records)}) is below minimum threshold ({MIN_DATASET_SIZE})")
    
    if power < (1 - BETA):
        result['warnings'].append(f"Statistical power ({power:.3f}) is below target ({1 - BETA:.3f})")
    
    if cohens_d < EFFECT_SIZE_SMALL:
        result['warnings'].append(f"Effect size ({cohens_d:.3f}) is smaller than expected minimum ({EFFECT_SIZE_SMALL})")
    
    logger.info(f"Power analysis complete: n={len(records)}, power={power:.3f}, effect_size={cohens_d:.3f}")
    
    return result

def interpret_effect_size(effect_size: float) -> str:
    """Interpret Cohen's d effect size."""
    if effect_size < EFFECT_SIZE_SMALL:
        return "negligible"
    elif effect_size < EFFECT_SIZE_MEDIUM:
        return "small"
    elif effect_size < EFFECT_SIZE_LARGE:
        return "medium"
    else:
        return "large"

def run_power_analysis_from_csv(
    csv_path: str,
    output_dir: Optional[str] = None,
    target_variable: str = 'degradation_rate',
    group_variable: str = 'degradation_pathway'
) -> Dict[str, Any]:
    """
    Run power analysis from a CSV file containing polymer records.
    
    Args:
        csv_path: Path to the CSV file with processed data
        output_dir: Directory to save the power analysis report
        target_variable: Target variable for effect size calculation
        group_variable: Grouping variable for comparison
        
    Returns:
        Dictionary containing power analysis results
    """
    import pandas as pd
    
    logger = get_logger(__name__)
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} records from {csv_path}")
    
    # Convert to PolymerRecord-like objects for consistency
    records = []
    for _, row in df.iterrows():
        record = PolymerRecord(
            smiles=row.get('smiles', ''),
            degradation_pathway=row.get(group_variable, None),
            degradation_rate=row.get(target_variable, None),
            temperature=row.get('temperature', None),
            ph=row.get('ph', None),
            uv_exposure=row.get('uv_exposure', None),
            molecular_weight=row.get('molecular_weight', None),
            functional_groups=row.get('functional_groups', None)
        )
        records.append(record)
    
    # Perform power analysis
    results = check_dataset_power(
        records,
        target_variable=target_variable,
        group_variable=group_variable
    )
    
    # Save report if output_dir specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, 'power_analysis_report.json')
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Power analysis report saved to {report_path}")
        
        # Generate warning if dataset is insufficient
        if not results['sufficient']:
            logger.warning("⚠️ WARNING: Dataset insufficient for reliable statistical power!")
            for warning in results['warnings']:
                logger.warning(f"  - {warning}")
    
    return results

def main():
    """Main entry point for power analysis."""
    logger = get_logger(__name__)
    logger.info("Starting power analysis for polymer degradation dataset")
    
    # Get project paths
    paths = get_project_paths()
    processed_data_path = paths['processed'] / 'polyester_filtered.csv'
    reports_dir = paths['reports']
    
    if not processed_data_path.exists():
        logger.error(f"Processed data not found at {processed_data_path}")
        logger.error("Please run preprocess.py first to generate the filtered dataset")
        return
    
    # Run power analysis
    results = run_power_analysis_from_csv(
        str(processed_data_path),
        output_dir=str(reports_dir),
        target_variable='degradation_rate',
        group_variable='degradation_pathway'
    )
    
    # Print summary
    logger.info("=" * 60)
    logger.info("POWER ANALYSIS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Sample size: {results['sample_size']}")
    logger.info(f"Effect size (Cohen's d): {results['effect_size']:.3f} ({results['effect_size_interpretation']})")
    logger.info(f"Statistical power: {results['power']:.3f}")
    logger.info(f"Target power: {results['target_power']:.3f}")
    logger.info(f"Minimum dataset size: {results['min_dataset_size']}")
    logger.info(f"Sufficient for analysis: {'YES' if results['sufficient'] else 'NO'}")
    
    if results['warnings']:
        logger.warning("Warnings:")
        for warning in results['warnings']:
            logger.warning(f"  - {warning}")
    
    logger.info("=" * 60)
    
    # Return exit code based on sufficiency
    if not results['sufficient']:
        logger.error("⚠️ Dataset insufficient for reliable statistical analysis!")
        return 1
    
    logger.info("Power analysis completed successfully")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
