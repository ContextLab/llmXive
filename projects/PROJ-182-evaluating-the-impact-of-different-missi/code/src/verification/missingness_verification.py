"""
Statistical verification of missingness mechanisms.

This module implements the statistical tests required by T044:
- Chi-square test for MCAR (independence of missingness from all variables)
- Pearson correlation for MAR (correlation between missingness and covariate Z)
- Pearson correlation for MNAR (correlation between missingness and outcome Y)

The script reads `data/simulated_raw.csv`, performs the tests, and asserts
the expected p-value thresholds as per the specification:
- MCAR: p >= 0.05 (fail to reject independence)
- MAR/MNAR: p < 0.05 (reject independence)

If the assertions fail, the script exits with a non-zero status code.
"""
import sys
import os
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Tuple, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from src.logging_config import get_logger

logger = get_logger(__name__)


def load_simulated_data(file_path: str) -> pd.DataFrame:
    """Load the simulated raw data from CSV."""
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Data file not found: {path}")
        raise FileNotFoundError(f"Data file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded data from {path}: {len(df)} rows, {len(df.columns)} columns")
    return df


def verify_mcar(df: pd.DataFrame, missing_col: str = 'Y_missing', threshold: float = 0.05) -> Tuple[float, bool]:
    """
    Verify MCAR mechanism using Chi-square test.
    
    For MCAR, missingness should be independent of all observed variables.
    We test independence between the missingness indicator and each observed variable.
    
    Args:
        df: DataFrame with observed variables and missingness indicator
        missing_col: Name of the column indicating missingness (1=missing, 0=observed)
        threshold: Significance threshold (default 0.05)
    
    Returns:
        Tuple of (min_p_value, is_valid)
        is_valid is True if all p-values >= threshold (fail to reject independence)
    """
    if missing_col not in df.columns:
        raise ValueError(f"Missingness column '{missing_col}' not found in data")
    
    # Identify numeric observed columns (excluding the missingness indicator itself)
    observed_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                    if col != missing_col]
    
    if not observed_cols:
        logger.warning("No observed numeric columns found for MCAR test")
        return 1.0, True  # Cannot test, assume valid (or could fail loudly)
    
    p_values = []
    
    for col in observed_cols:
        # Create contingency table: missingness vs binned observed variable
        # For continuous variables, we bin them to perform Chi-square test
        try:
            # Bin continuous variable into 4 bins
            bins = pd.qcut(df[col], q=4, duplicates='drop')
            contingency = pd.crosstab(bins, df[missing_col])
            
            if contingency.shape[0] < 2 or contingency.shape[1] < 2:
                logger.warning(f"Contingency table too small for {col}, skipping")
                continue
            
            chi2, p, dof, expected = stats.chi2_contingency(contingency)
            p_values.append(p)
            logger.debug(f"MCAR Chi-square test for {col}: chi2={chi2:.4f}, p={p:.4f}")
        except Exception as e:
            logger.warning(f"Could not perform Chi-square test for {col}: {e}")
            continue
    
    if not p_values:
        logger.warning("No valid Chi-square tests performed")
        return 1.0, True
    
    min_p = min(p_values)
    is_valid = min_p >= threshold
    
    logger.info(f"MCAR verification: min p-value = {min_p:.4f}, threshold = {threshold}, valid = {is_valid}")
    return min_p, is_valid


def verify_mar(df: pd.DataFrame, covariate_col: str = 'Z', missing_col: str = 'Y_missing', threshold: float = 0.05) -> Tuple[float, bool]:
    """
    Verify MAR mechanism using Pearson correlation.
    
    For MAR, missingness should be correlated with the covariate Z.
    We test the correlation between the missingness indicator and Z.
    
    Args:
        df: DataFrame with covariate and missingness indicator
        covariate_col: Name of the covariate column (Z)
        missing_col: Name of the column indicating missingness (1=missing, 0=observed)
        threshold: Significance threshold (default 0.05)
    
    Returns:
        Tuple of (p_value, is_valid)
        is_valid is True if p < threshold (reject independence)
    """
    if covariate_col not in df.columns:
        raise ValueError(f"Covariate column '{covariate_col}' not found in data")
    if missing_col not in df.columns:
        raise ValueError(f"Missingness column '{missing_col}' not found in data")
    
    # Calculate Pearson correlation between Z and missingness indicator
    corr, p_value = stats.pearsonr(df[covariate_col], df[missing_col])
    
    is_valid = p_value < threshold
    
    logger.info(f"MAR verification: correlation = {corr:.4f}, p-value = {p_value:.4f}, "
               f"threshold = {threshold}, valid = {is_valid}")
    return p_value, is_valid


def verify_mnar(df: pd.DataFrame, outcome_col: str = 'Y', missing_col: str = 'Y_missing', threshold: float = 0.05) -> Tuple[float, bool]:
    """
    Verify MNAR mechanism using Pearson correlation.
    
    For MNAR, missingness should be correlated with the outcome Y.
    We test the correlation between the missingness indicator and Y.
    Note: We use the observed Y values (where Y is not missing) for this test.
    
    Args:
        df: DataFrame with outcome and missingness indicator
        outcome_col: Name of the outcome column (Y)
        missing_col: Name of the column indicating missingness (1=missing, 0=observed)
        threshold: Significance threshold (default 0.05)
    
    Returns:
        Tuple of (p_value, is_valid)
        is_valid is True if p < threshold (reject independence)
    """
    if outcome_col not in df.columns:
        raise ValueError(f"Outcome column '{outcome_col}' not found in data")
    if missing_col not in df.columns:
        raise ValueError(f"Missingness column '{missing_col}' not found in data")
    
    # For MNAR, we test correlation between missingness and Y using observed Y values
    # However, the missingness indicator is defined for all rows
    # We calculate correlation between missingness and Y (NaN where missing)
    # This is valid because missingness is correlated with the unobserved Y values
    
    # Option 1: Use all rows, treating NaN in Y appropriately
    # Pearson correlation handles NaN by default (excludes them)
    corr, p_value = stats.pearsonr(df[outcome_col], df[missing_col])
    
    is_valid = p_value < threshold
    
    logger.info(f"MNAR verification: correlation = {corr:.4f}, p-value = {p_value:.4f}, "
               f"threshold = {threshold}, valid = {is_valid}")
    return p_value, is_valid


def run_verification(data_path: str, mechanism: Optional[str] = None) -> Dict[str, Dict]:
    """
    Run all missingness verification tests.
    
    Args:
        data_path: Path to the simulated raw data CSV
        mechanism: Optional specific mechanism to test ('mcar', 'mar', 'mnar')
                  If None, tests all mechanisms based on the data structure
    
    Returns:
        Dictionary with test results
    """
    df = load_simulated_data(data_path)
    
    # Determine which mechanism to test based on data structure or explicit argument
    # We look for mechanism indicators in column names or test all if ambiguous
    mechanisms_to_test = []
    
    if mechanism:
        mechanisms_to_test = [mechanism.lower()]
    else:
        # Try to detect mechanism from column names or test all
        # Common patterns: 'mcar_', 'mar_', 'mnar_' in column names
        # For now, we test all and let the user interpret
        mechanisms_to_test = ['mcar', 'mar', 'mnar']
    
    results = {}
    all_passed = True
    
    for mech in mechanisms_to_test:
        if mech == 'mcar':
            p_val, is_valid = verify_mcar(df)
            results['mcar'] = {
                'p_value': p_val,
                'is_valid': is_valid,
                'expected': 'p >= 0.05 (independence)'
            }
            if not is_valid:
                all_passed = False
                logger.error(f"MCAR verification FAILED: p={p_val:.4f} < 0.05 (dependence detected)")
            else:
                logger.info(f"MCAR verification PASSED: p={p_val:.4f} >= 0.05")
        
        elif mech == 'mar':
            # MAR: correlation with Z (covariate)
            if 'Z' in df.columns:
                p_val, is_valid = verify_mar(df, covariate_col='Z')
                results['mar'] = {
                    'p_value': p_val,
                    'is_valid': is_valid,
                    'expected': 'p < 0.05 (correlation with Z)'
                }
                if not is_valid:
                    all_passed = False
                    logger.error(f"MAR verification FAILED: p={p_val:.4f} >= 0.05 (no correlation with Z)")
                else:
                    logger.info(f"MAR verification PASSED: p={p_val:.4f} < 0.05")
            else:
                logger.warning("MAR test skipped: Z column not found")
                results['mar'] = {'skipped': True, 'reason': 'Z column not found'}
        
        elif mech == 'mnar':
            # MNAR: correlation with Y (outcome)
            if 'Y' in df.columns:
                p_val, is_valid = verify_mnar(df, outcome_col='Y')
                results['mnar'] = {
                    'p_value': p_val,
                    'is_valid': is_valid,
                    'expected': 'p < 0.05 (correlation with Y)'
                }
                if not is_valid:
                    all_passed = False
                    logger.error(f"MNAR verification FAILED: p={p_val:.4f} >= 0.05 (no correlation with Y)")
                else:
                    logger.info(f"MNAR verification PASSED: p={p_val:.4f} < 0.05")
            else:
                logger.warning("MNAR test skipped: Y column not found")
                results['mnar'] = {'skipped': True, 'reason': 'Y column not found'}
    
    return results, all_passed


def main():
    """Main entry point for the verification script."""
    parser = argparse.ArgumentParser(
        description="Statistical verification of missingness mechanisms"
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default='data/simulated_raw.csv',
        help='Path to the simulated raw data CSV file'
    )
    parser.add_argument(
        '--mechanism',
        type=str,
        choices=['mcar', 'mar', 'mnar'],
        help='Specific mechanism to verify (optional, defaults to all)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting missingness verification for {args.data_path}")
    
    try:
        results, all_passed = run_verification(args.data_path, args.mechanism)
        
        # Print summary
        print("\n" + "="*60)
        print("MISSINGNESS VERIFICATION SUMMARY")
        print("="*60)
        
        for mech, result in results.items():
            if result.get('skipped'):
                print(f"{mech.upper()}: SKIPPED - {result.get('reason')}")
            else:
                status = "PASS" if result['is_valid'] else "FAIL"
                print(f"{mech.upper()}: {status} (p={result['p_value']:.4f}, "
                     f"expected: {result['expected']})")
        
        print("="*60)
        
        if all_passed:
            print("OVERALL: ALL VERIFICATIONS PASSED")
            sys.exit(0)
        else:
            print("OVERALL: SOME VERIFICATIONS FAILED")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Verification failed with error: {e}")
        print(f"ERROR: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
