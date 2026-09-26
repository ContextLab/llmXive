"""
Task T024: SC-002 Check - Kolmogorov-Smirnov test on p-value distribution.

If no significant taxa (q < 0.05) are found in the association results,
this script performs a Kolmogorov-Smirnov test to check if the p-value
distribution deviates from a uniform distribution (indicating potential
signal or bias).
"""

import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import kstest, uniform

from config import get_output_path
from utils.logging import get_logger

logger = get_logger(__name__)


def load_association_results() -> pd.DataFrame:
    """
    Load the association results from the previous analysis step.
    
    Returns:
        pd.DataFrame: DataFrame containing association results with columns
                     including 'taxon', 'pval' (unadjusted), and 'qval' (adjusted).
    
    Raises:
        FileNotFoundError: If the results file does not exist.
        ValueError: If required columns are missing.
    """
    input_path = get_output_path("data/processed/association_results.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Association results file not found at {input_path}. "
            "Ensure T025 (output association_results.csv) has been completed."
        )
    
    df = pd.read_csv(input_path)
    
    required_cols = ['pval', 'qval']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Association results missing required columns: {missing_cols}"
        )
    
    return df


def check_significant_taxa(df: pd.DataFrame, q_threshold: float = 0.05) -> bool:
    """
    Check if there are any significant taxa based on adjusted p-values.
    
    Args:
        df: DataFrame with association results.
        q_threshold: Threshold for adjusted p-value (q-value).
        
    Returns:
        bool: True if any significant taxa found, False otherwise.
    """
    significant = df[df['qval'] < q_threshold]
    return len(significant) > 0


def run_kolmogorov_smirnov_test(df: pd.DataFrame) -> dict:
    """
    Perform Kolmogorov-Smirnov test on the p-value distribution.
    
    The KS test checks if the observed p-values follow a uniform distribution
    (expected under the null hypothesis of no association).
    
    Args:
        df: DataFrame with association results.
        
    Returns:
        dict: Dictionary containing KS test statistics and p-value.
    """
    pvals = df['pval'].dropna()
    
    if len(pvals) == 0:
        logger.warning("No p-values found for KS test.")
        return {
            'statistic': np.nan,
            'pvalue': np.nan,
            'n_samples': 0,
            'message': 'No p-values available for testing'
        }
    
    # KS test against uniform distribution
    statistic, pvalue = kstest(pvals, 'uniform')
    
    return {
        'statistic': statistic,
        'pvalue': pvalue,
        'n_samples': len(pvals),
        'message': 'KS test completed'
    }


def save_ks_results(results: dict, significant_found: bool) -> str:
    """
    Save the KS test results to a text file.
    
    Args:
        results: Dictionary containing KS test results.
        significant_found: Whether significant taxa were found.
        
    Returns:
        str: Path to the output file.
    """
    output_path = get_output_path("results/ks_pvalue_check.txt")
    
    # Ensure results directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("SC-002 Check: Kolmogorov-Smirnov Test on P-value Distribution\n")
        f.write("=" * 70 + "\n\n")
        
        if significant_found:
            f.write("STATUS: Significant taxa (q < 0.05) were found.\n")
            f.write("        KS test not required per SC-002 specification.\n")
        else:
            f.write("STATUS: No significant taxa (q < 0.05) found.\n")
            f.write("        Performing KS test on p-value distribution.\n\n")
            
            f.write(f"Number of p-values tested: {results['n_samples']}\n")
            f.write(f"KS Test Statistic: {results['statistic']:.6f}\n")
            f.write(f"KS Test P-value: {results['pvalue']:.6f}\n")
            f.write(f"Null Hypothesis: P-values follow a uniform distribution\n\n")
            
            if results['n_samples'] > 0:
                if results['pvalue'] < 0.05:
                    f.write("INTERPRETATION: Reject null hypothesis (p < 0.05).\n")
                    f.write("                The p-value distribution deviates from uniform,\n")
                    f.write("                suggesting potential signal or systematic bias.\n")
                else:
                    f.write("INTERPRETATION: Fail to reject null hypothesis (p >= 0.05).\n")
                    f.write("                The p-value distribution is consistent with uniform,\n")
                    f.write("                suggesting no strong signal or systematic bias.\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write(f"Generated: {pd.Timestamp.now()}\n")
    
    return output_path


def main():
    """
    Main entry point for T024: SC-002 Check.
    
    This function:
    1. Loads the association results
    2. Checks if significant taxa exist
    3. If no significant taxa, performs KS test on p-value distribution
    4. Saves results to results/ks_pvalue_check.txt
    """
    logger.info("Starting SC-002 Check (T024)")
    
    try:
        # Load association results
        logger.info("Loading association results...")
        df = load_association_results()
        logger.info(f"Loaded {len(df)} association results")
        
        # Check for significant taxa
        logger.info("Checking for significant taxa (q < 0.05)...")
        significant_found = check_significant_taxa(df)
        
        if significant_found:
            logger.info("Significant taxa found. KS test not required.")
            results = {
                'statistic': np.nan,
                'pvalue': np.nan,
                'n_samples': len(df),
                'message': 'Skipped - significant taxa found'
            }
        else:
            logger.info("No significant taxa found. Performing KS test...")
            results = run_kolmogorov_smirnov_test(df)
            logger.info(f"KS Test completed: statistic={results['statistic']:.4f}, p={results['pvalue']:.4f}")
        
        # Save results
        output_path = save_ks_results(results, significant_found)
        logger.info(f"Results saved to {output_path}")
        
        print(f"SC-002 Check completed. Results written to: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()