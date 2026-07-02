"""
Module to compute observed statistical power and Minimum Detectable Effect Size (MDES).
Implements conversion of F-statistics to Cohen's d and power clamping.
"""
import json
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from statsmodels.stats.power import TTestIndPower

# Configure logging for this module if not already done
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def _convert_f_to_cohens_d(f_stat: float, df1: int, df2: int) -> float:
    """
    Convert F-statistic to Cohen's d for two-group comparison.
    
    Formula for independent samples t-test equivalent:
    For a one-way ANOVA with 2 groups, F = t^2.
    Cohen's d = t * sqrt(1/n1 + 1/n2) * sqrt(n1*n2/(n1+n2)) ... simplified for equal n
    
    Standard conversion for F(1, df2) to Cohen's d:
    d = 2 * sqrt(F / df2) * sqrt(df2 / (df2 + 1)) approx 2*sqrt(F/df2) for large df2
    
    More precise conversion assuming equal group sizes (n1=n2):
    F = t^2
    d = t * sqrt(2/n) where n is per group
    Also F = (d^2 * n) / 2  => d = sqrt(2*F/n) ... this depends on N.
    
    Alternative standard conversion from F(1, df) to Cohen's d:
    d = 2 * sqrt(F / (df + 1)) is not quite right.
    
    Correct relation for independent t-test (which F(1, df2) represents):
    t = sqrt(F)
    d = t * sqrt(1/n1 + 1/n2) * sqrt(n1*n2/(n1+n2))
    If n1=n2=n/2, then d = t * sqrt(4/n) = 2t/sqrt(n)
    Also F = t^2.
    
    A robust approximation often used when only F and df are known:
    d = 2 * sqrt(F / df2) * sqrt(df2 / (df2 + 1))
    Or simpler: d = sqrt( (4 * F) / (df2 + 1) ) ? No.
    
    Let's use the standard conversion for F(1, df2) to Cohen's d assuming equal sample sizes:
    d = 2 * sqrt(F / (df2 + 1)) is incorrect.
    
    Correct formula:
    d = 2 * sqrt(F / (df2 + 1)) * sqrt(df2 / (df2 + 1)) ... no.
    
    Actually, the most direct conversion for F(1, df2) to Cohen's d (assuming equal n):
    d = 2 * sqrt( F / (df2 + 1) ) is often cited but let's derive:
    F = (d^2 * N) / 4  (for equal groups, N total)
    df2 = N - 2
    So N = df2 + 2
    F = d^2 * (df2 + 2) / 4
    d = sqrt( 4 * F / (df2 + 2) )
    
    Let's use: d = 2 * sqrt(F / (df2 + 2))
    This assumes equal group sizes.
    """
    if df2 <= 0:
        logger.warning(f"Invalid degrees of freedom (df2={df2}) for F-conversion. Returning 0.")
        return 0.0
    
    # Conversion formula for F(1, df2) to Cohen's d (assuming equal group sizes)
    # d = 2 * sqrt(F / (df2 + 2))
    d = 2 * math.sqrt(f_stat / (df2 + 2))
    return d

def compute_observed_power(params: Dict[str, Any]) -> float:
    """
    Compute observed statistical power given sample size and effect size.
    
    Args:
        params: Dictionary containing 'sample_size', 'effect_size', 'metric_type', 
                and optionally 'degrees_of_freedom'.
                
    Returns:
        Computed power value (clamped between 0 and 1).
    """
    n = params.get('sample_size')
    d = params.get('effect_size')
    metric_type = params.get('metric_type')
    df = params.get('degrees_of_freedom')
    
    if n is None or d is None:
        logger.warning(f"Missing sample_size or effect_size in params: {params}")
        return 0.0
    
    # Handle F-statistic conversion to Cohen's d
    if metric_type == 'F' and df is not None:
        try:
            # Extract F value from effect_size if it's stored as a tuple or string?
            # Based on T020, extract_effect_size returns (float, str, Optional[Tuple[int,int]])
            # But here 'effect_size' in params might be the float value if it was Cohen's d.
            # If metric_type is 'F', the 'effect_size' field likely holds the F value.
            # Let's assume 'effect_size' holds the F value when metric_type is 'F'.
            f_val = float(d)
            d_converted = _convert_f_to_cohens_d(f_val, 1, df) # df1 is 1 for F(1, df2)
            
            if d_converted != d:
                logger.info(f"Converted F-statistic {f_val} (df={df}) to Cohen's d: {d_converted:.4f}")
            d = d_converted
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert F-statistic to Cohen's d: {e}")
            return 0.0
    
    if d < 0:
        d = abs(d) # Power calculation usually uses absolute effect size
    
    if n <= 2:
        logger.warning(f"Sample size too small for power calculation: {n}")
        return 0.0
    
    # statsmodels TTestIndPower expects nobs1 (per group) for equal groups
    # Total N = n. Assuming equal groups, n_per_group = n / 2.
    n_per_group = n / 2.0
    
    power_analysis = TTestIndPower()
    try:
        power = power_analysis.power(effect_size=d, nobs1=n_per_group, alpha=0.05, ratio=1.0)
    except Exception as e:
        logger.error(f"Power calculation failed: {e}")
        return 0.0
    
    # Clamp power to [0, 1]
    if power > 1.0:
        logger.warning(f"Computed power {power} > 1.0. Clamping to 1.0.")
        power = 1.0
    if power < 0.0:
        power = 0.0
        
    return float(power)

def compute_mdes(params: Dict[str, Any], alpha: float = 0.05, target_power: float = 0.8) -> float:
    """
    Compute Minimum Detectable Effect Size (MDES) for a given sample size and target power.
    
    Args:
        params: Dictionary containing 'sample_size'.
        alpha: Significance level.
        target_power: Desired power (default 0.8).
        
    Returns:
        MDES value.
    """
    n = params.get('sample_size')
    if n is None or n <= 2:
        logger.warning(f"Invalid sample size for MDES: {n}")
        return float('inf')
    
    n_per_group = n / 2.0
    power_analysis = TTestIndPower()
    
    try:
        mdes = power_analysis.solve_power(effect_size=None, nobs1=n_per_group, alpha=alpha, power=target_power, ratio=1.0)
    except Exception as e:
        logger.error(f"MDES calculation failed: {e}")
        return float('inf')
        
    if mdes is None:
        return float('inf')
        
    return float(mdes)

def process_extracted_params(input_path: str, output_path: str) -> List[Dict[str, Any]]:
    """
    Process extracted parameters from JSON, compute power and MDES, and save results.
    
    Args:
        input_path: Path to input JSON file with extracted parameters.
        output_path: Path to output JSON file for results.
        
    Returns:
        List of result dictionaries.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    results = []
    total = len(data)
    success_count = 0
    
    for idx, item in enumerate(data):
        dataset_id = item.get('dataset_id', f'unknown_{idx}')
        try:
            power = compute_observed_power(item)
            mdes = compute_mdes(item)
            
            threshold_met = power >= 0.8
            status = 'success'
            success_count += 1
            
            result = {
                'dataset_id': dataset_id,
                'observed_power': power,
                'mdes': mdes,
                'threshold_met': threshold_met,
                'status': status,
                'original_params': {
                    'sample_size': item.get('sample_size'),
                    'effect_size': item.get('effect_size'),
                    'metric_type': item.get('metric_type'),
                    'degrees_of_freedom': item.get('degrees_of_freedom')
                }
            }
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {e}")
            result = {
                'dataset_id': dataset_id,
                'observed_power': None,
                'mdes': None,
                'threshold_met': None,
                'status': 'error',
                'error_message': str(e)
            }
        
        results.append(result)
        
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{total} datasets")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Processed {total} datasets. Saved results to {output_path}")
    return results

def main():
    """Main entry point for the script."""
    # Define paths relative to project root
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'data' / 'processed' / 'extracted_params.json'
    output_file = base_dir / 'data' / 'processed' / 'power_audit_results.json'
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.info("Please run code/02_parse_publications.py first to generate extracted_params.json")
        sys.exit(1)
    
    logger.info(f"Starting sensitivity analysis on {input_file}")
    process_extracted_params(str(input_file), str(output_file))
    logger.info("Sensitivity analysis complete.")

if __name__ == '__main__':
    main()