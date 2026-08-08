import math
from typing import Dict, List, Tuple, Any

def anova_test(accuracies: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Perform a one-way ANOVA test on the provided accuracy groups.
    
    Args:
        accuracies: Dictionary mapping group names (e.g., 'high', 'low', 'target')
                    to lists of float accuracy values.
    
    Returns:
        Dictionary containing 'f_statistic' and 'p_value'.
    """
    groups = list(accuracies.values())
    k = len(groups)  # number of groups
    
    if k < 2:
        raise ValueError("ANOVA requires at least two groups.")
    
    # Flatten all data and calculate overall mean
    all_data = [val for group in groups for val in group]
    n_total = len(all_data)
    grand_mean = sum(all_data) / n_total
    
    # Calculate Sum of Squares Between (SSB) and Within (SSW)
    ssw = 0.0
    ssb = 0.0
    
    for group in groups:
        n_i = len(group)
        group_mean = sum(group) / n_i
        
        # SSW: Sum of squared deviations from group mean
        ssw += sum((x - group_mean) ** 2 for x in group)
        
        # SSB: Sum of squared deviations of group mean from grand mean
        ssb += n_i * ((group_mean - grand_mean) ** 2)
    
    # Degrees of freedom
    df_between = k - 1
    df_within = n_total - k
    
    if df_within == 0:
        raise ValueError("ANOVA requires at least one degree of freedom within groups.")
    
    # Mean Squares
    msb = ssb / df_between
    msw = ssw / df_within
    
    # F-statistic
    f_stat = msb / msw if msw != 0 else float('inf')
    
    # Approximate p-value using the F-distribution survival function
    # Since we don't want to import scipy, we use a rough approximation
    # or a simplified logic. However, for a real scientific pipeline,
    # scipy is a standard dependency (listed in requirements.txt).
    # We will attempt to import scipy.stats for accurate p-value calculation.
    try:
        from scipy.stats import f as f_dist
        p_value = f_dist.sf(f_stat, df_between, df_within)
    except ImportError:
        # Fallback: If scipy is missing, we cannot accurately compute p-value.
        # We raise an error to enforce dependency compliance.
        raise ImportError("scipy is required for accurate ANOVA p-value calculation.")
    
    return {
        'f_statistic': float(f_stat),
        'p_value': float(p_value)
    }

def pairwise_t_test(convergence_epochs: Dict[str, List[int]]) -> Dict[str, Dict[str, float]]:
    """
    Perform pairwise t-tests between all groups in the dictionary.
    
    Args:
        convergence_epochs: Dictionary mapping group names to lists of int epochs.
    
    Returns:
        Dictionary with keys as 'group1_vs_group2' and values as dicts containing
        't_statistic' and 'p_value'.
    """
    group_names = list(convergence_epochs.keys())
    results = {}
    
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            g1_name = group_names[i]
            g2_name = group_names[j]
            x = convergence_epochs[g1_name]
            y = convergence_epochs[g2_name]
            
            n1, n2 = len(x), len(y)
            mean1, mean2 = sum(x)/n1, sum(y)/n2
            
            var1 = sum((val - mean1)**2 for val in x) / (n1 - 1) if n1 > 1 else 0
            var2 = sum((val - mean2)**2 for val in y) / (n2 - 1) if n2 > 1 else 0
            
            # Pooled standard error for independent samples t-test
            se = math.sqrt((var1 / n1) + (var2 / n2))
            
            if se == 0:
                t_stat = 0.0
            else:
                t_stat = (mean1 - mean2) / se
            
            # Approximate degrees of freedom (Welch's t-test approximation)
            num = (var1/n1 + var2/n2)**2
            den = (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1)
            df = num / den if den != 0 else (n1 + n2 - 2)
            
            # Calculate two-tailed p-value
            try:
                from scipy.stats import t as t_dist
                p_value = t_dist.sf(abs(t_stat), df) * 2
            except ImportError:
                raise ImportError("scipy is required for accurate t-test p-value calculation.")
            
            key = f"{g1_name}_vs_{g2_name}"
            results[key] = {
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'group1': g1_name,
                'group2': g2_name
            }
    
    return results

def bonferroni_correction(p_values: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Apply Bonferroni correction to a dictionary of p-values.
    
    This function adjusts p-values to control the family-wise error rate (FWER)
    by multiplying each p-value by the number of tests performed.
    Values exceeding 1.0 are capped at 1.0.
    
    Args:
        p_values: Dictionary mapping test names (e.g., 'anova', 'group1_vs_group2')
                  to their raw p-values (float).
    
    Returns:
        Dictionary with the same keys, where each value is a dict containing:
            - 'raw_p_value': The original p-value
            - 'corrected_p_value': The Bonferroni-corrected p-value
            - 'is_significant': Boolean indicating if corrected p < 0.05
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {}
    
    corrected_results = {}
    alpha = 0.05
    
    for test_name, raw_p in p_values.items():
        # Bonferroni correction: p_corrected = p_raw * n_tests
        corrected_p = raw_p * n_tests
        
        # Cap at 1.0
        corrected_p = min(corrected_p, 1.0)
        
        is_sig = corrected_p < alpha
        
        corrected_results[test_name] = {
            'raw_p_value': raw_p,
            'corrected_p_value': corrected_p,
            'is_significant': is_sig
        }
    
    return corrected_results