"""
Multiple comparison correction for statistical tests.

Implements Bonferroni and False Discovery Rate (FDR) corrections
to control family-wise error rate (FWER) and false discovery rate respectively.
"""

import numpy as np
from typing import List, Tuple, Dict, Union
from statsmodels.stats.multitest import multipletests


def bonferroni_correction(p_values: Union[List[float], np.ndarray], 
                           alpha: float = 0.05) -> Dict[str, Union[np.ndarray, List[bool]]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    The Bonferroni correction controls the Family-Wise Error Rate (FWER) by 
    dividing the significance threshold alpha by the number of tests.
    
    Parameters
    ----------
    p_values : list or np.ndarray
        Array of uncorrected p-values from statistical tests.
    alpha : float, optional
        Significance threshold (default: 0.05).
        
    Returns
    -------
    dict
        Dictionary containing:
        - 'corrected_p_values': np.ndarray of Bonferroni-corrected p-values
        - 'reject': List[bool] indicating which hypotheses are rejected
        - 'alpha_corrected': The adjusted alpha threshold (alpha / n_tests)
        - 'n_tests': Number of tests performed
        
    Raises
    ------
    ValueError
        If p_values is empty or contains invalid values.
    """
    if not p_values:
        raise ValueError("p_values cannot be empty")
        
    p_values = np.asarray(p_values)
    
    if np.any(p_values < 0) or np.any(p_values > 1):
        raise ValueError("p_values must be between 0 and 1")
        
    n_tests = len(p_values)
    if n_tests == 0:
        raise ValueError("Number of tests cannot be zero")
        
    # Bonferroni correction: multiply p-values by number of tests
    # Cap at 1.0
    corrected_p_values = np.minimum(p_values * n_tests, 1.0)
    
    # Determine which hypotheses are rejected
    alpha_corrected = alpha / n_tests
    reject = corrected_p_values <= alpha_corrected
    
    return {
        'corrected_p_values': corrected_p_values,
        'reject': reject,
        'alpha_corrected': alpha_corrected,
        'n_tests': n_tests
    }


def fdr_correction(p_values: Union[List[float], np.ndarray], 
                  alpha: float = 0.05,
                  method: str = 'fdr_bh') -> Dict[str, Union[np.ndarray, List[bool], float]]:
    """
    Apply False Discovery Rate (FDR) correction using the Benjamini-Hochberg procedure.
    
    FDR controls the expected proportion of false positives among rejected hypotheses.
    This is less conservative than Bonferroni and provides more power when testing
    many hypotheses.
    
    Parameters
    ----------
    p_values : list or np.ndarray
        Array of uncorrected p-values from statistical tests.
    alpha : float, optional
        Significance threshold (default: 0.05).
    method : str, optional
        FDR method to use. Options:
        - 'fdr_bh': Benjamini-Hochberg (default, assumes independence or positive dependence)
        - 'fdr_by': Benjamini-Yekutieli (valid for arbitrary dependence)
        
    Returns
    -------
    dict
        Dictionary containing:
        - 'corrected_p_values': np.ndarray of FDR-corrected p-values
        - 'reject': List[bool] indicating which hypotheses are rejected
        - 'q_values': np.ndarray of q-values (minimum FDR at which test is significant)
        - 'n_tests': Number of tests performed
        - 'method': The FDR method used
        
    Raises
    ------
    ValueError
        If p_values is empty or contains invalid values.
    """
    if not p_values:
        raise ValueError("p_values cannot be empty")
        
    p_values = np.asarray(p_values)
    
    if np.any(p_values < 0) or np.any(p_values > 1):
        raise ValueError("p_values must be between 0 and 1")
        
    n_tests = len(p_values)
    if n_tests == 0:
        raise ValueError("Number of tests cannot be zero")
        
    # Use statsmodels for FDR correction
    # multipletests returns: (reject, pvals_corrected, alphac_Sidak, alphac_Bonf)
    reject, corrected_p_values, _, _ = multipletests(
        p_values, 
        alpha=alpha, 
        method=method
    )
    
    # Calculate q-values (minimum FDR at which the test would be rejected)
    # For BH procedure, q-values can be derived from corrected p-values
    q_values = corrected_p_values.copy()
    
    return {
        'corrected_p_values': corrected_p_values,
        'reject': reject,
        'q_values': q_values,
        'n_tests': n_tests,
        'method': method
    }


def compare_corrections(p_values: Union[List[float], np.ndarray], 
                       alpha: float = 0.05) -> Dict[str, Dict]:
    """
    Apply both Bonferroni and FDR corrections and compare results.
    
    Parameters
    ----------
    p_values : list or np.ndarray
        Array of uncorrected p-values from statistical tests.
    alpha : float, optional
        Significance threshold (default: 0.05).
        
    Returns
    -------
    dict
        Dictionary containing results from both correction methods:
        - 'bonferroni': Results from Bonferroni correction
        - 'fdr_bh': Results from Benjamini-Hochberg FDR correction
        - 'summary': Comparison summary including number of rejections for each method
    """
    bonf_result = bonferroni_correction(p_values, alpha)
    fdr_result = fdr_correction(p_values, alpha, method='fdr_bh')
    
    summary = {
        'n_tests': len(p_values),
        'alpha': alpha,
        'bonferroni_rejections': int(sum(bonf_result['reject'])),
        'fdr_rejections': int(sum(fdr_result['reject'])),
        'bonferroni_threshold': bonf_result['alpha_corrected'],
        'fdr_method': fdr_result['method']
    }
    
    return {
        'bonferroni': bonf_result,
        'fdr_bh': fdr_result,
        'summary': summary
    }


def apply_correction_to_results(correlation_results: List[Dict], 
                               metric_name: str,
                               outcome_name: str,
                               alpha: float = 0.05,
                               method: str = 'fdr_bh') -> Dict:
    """
    Apply multiple comparison correction to a list of correlation results.
    
    This function extracts p-values from correlation results, applies the specified
    correction method, and adds the corrected values back to the results.
    
    Parameters
    ----------
    correlation_results : list of dict
        List of dictionaries containing correlation results with 'p_value' key.
    metric_name : str
        Name of the network metric being tested.
    outcome_name : str
        Name of the outcome variable (e.g., 'age', 'cognitive_score').
    alpha : float, optional
        Significance threshold (default: 0.05).
    method : str, optional
        Correction method: 'bonferroni' or 'fdr' (default: 'fdr').
        
    Returns
    -------
    dict
        Dictionary containing:
        - 'corrected_results': List of results with corrected p-values and significance flags
        - 'correction_info': Metadata about the correction applied
    """
    if not correlation_results:
        return {
            'corrected_results': [],
            'correction_info': {
                'metric': metric_name,
                'outcome': outcome_name,
                'n_tests': 0,
                'method': method,
                'alpha': alpha
            }
        }
    
    # Extract p-values
    p_values = [r.get('p_value', np.nan) for r in correlation_results]
    valid_indices = [i for i, p in enumerate(p_values) if not np.isnan(p)]
    
    if not valid_indices:
        return {
            'corrected_results': correlation_results,
            'correction_info': {
                'metric': metric_name,
                'outcome': outcome_name,
                'n_tests': 0,
                'method': method,
                'alpha': alpha,
                'note': 'No valid p-values found'
            }
        }
    
    valid_p_values = [p_values[i] for i in valid_indices]
    
    # Apply correction
    if method.lower() == 'bonferroni':
        correction_result = bonferroni_correction(valid_p_values, alpha)
    elif method.lower() == 'fdr':
        correction_result = fdr_correction(valid_p_values, alpha, 'fdr_bh')
    else:
        raise ValueError(f"Unknown correction method: {method}. Use 'bonferroni' or 'fdr'.")
    
    # Update results with corrected values
    corrected_results = []
    for i, result in enumerate(correlation_results):
        new_result = result.copy()
        if i in valid_indices:
          idx_in_valid = valid_indices.index(i)
          new_result['p_value_corrected'] = float(correction_result['corrected_p_values'][idx_in_valid])
          new_result['is_significant_corrected'] = bool(correction_result['reject'][idx_in_valid])
        else:
          new_result['p_value_corrected'] = np.nan
          new_result['is_significant_corrected'] = False
        corrected_results.append(new_result)
    
    correction_info = {
        'metric': metric_name,
        'outcome': outcome_name,
        'n_tests': len(valid_p_values),
        'method': method,
        'alpha': alpha,
        'n_rejected': int(sum(correction_result['reject']))
    }
    
    if method.lower() == 'bonferroni':
        correction_info['alpha_corrected'] = correction_result['alpha_corrected']
    else:
        correction_info['fdr_method'] = 'fdr_bh'
    
    return {
        'corrected_results': corrected_results,
        'correction_info': correction_info
    }

def main():
    """
    Main function to demonstrate correction methods.
    This is primarily for testing and documentation purposes.
    """
    # Example usage
    sample_p_values = [0.001, 0.01, 0.03, 0.04, 0.06, 0.1, 0.2, 0.5]
    
    print("Multiple Comparison Correction Demo")
    print("=" * 50)
    print(f"Original p-values: {sample_p_values}")
    print()
    
    # Bonferroni
    bonf_result = bonferroni_correction(sample_p_values)
    print("Bonferroni Correction:")
    print(f"  Corrected p-values: {bonf_result['corrected_p_values']}")
    print(f"  Rejected: {bonf_result['reject']}")
    print(f"  Adjusted alpha: {bonf_result['alpha_corrected']:.6f}")
    print()
    
    # FDR
    fdr_result = fdr_correction(sample_p_values)
    print("FDR (Benjamini-Hochberg) Correction:")
    print(f"  Corrected p-values: {fdr_result['corrected_p_values']}")
    print(f"  Rejected: {fdr_result['reject']}")
    print(f"  Q-values: {fdr_result['q_values']}")
    print()
    
    # Comparison
    comparison = compare_corrections(sample_p_values)
    print("Comparison Summary:")
    print(f"  Bonferroni rejections: {comparison['summary']['bonferroni_rejections']}")
    print(f"  FDR rejections: {comparison['summary']['fdr_rejections']}")
    print(f"  Bonferroni threshold: {comparison['summary']['bonferroni_threshold']:.6f}")

if __name__ == "__main__":
    main()