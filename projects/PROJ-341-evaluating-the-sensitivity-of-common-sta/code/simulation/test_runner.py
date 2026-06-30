import numpy as np
from scipy import stats
from typing import Tuple, List, Dict, Any, Optional, Union
import warnings
import json
import os
from code.simulation import get_rng
from code.simulation.chi_squared_utils import calculate_expected_counts, check_low_expected_counts, run_chi_squared_with_fallback

def run_t_test(
    data_group1: np.ndarray,
    data_group2: np.ndarray,
    alpha: float = 0.05,
    sample_size: int = 0,
    rng: Optional[np.random.Generator] = None
) -> Dict[str, Any]:
    """
    Perform an independent two-sample t-test.
    
    Args:
        data_group1: First group of data points.
        data_group2: Second group of data points.
        alpha: Significance level.
        sample_size: Total sample size (n1 + n2) for small sample warning.
        rng: Random number generator (unused for t-test but kept for API consistency).
        
    Returns:
        Dictionary containing p-value, statistic, and warnings.
    """
    warnings_list = []
    
    # Small sample warning (T013b)
    if sample_size < 30:
        warnings_list.append(
            f"Small sample warning (n={sample_size} < 30): Normality assumptions may be severely violated."
        )
    
    # Perform t-test assuming unequal variances (Welch's t-test)
    try:
        statistic, p_value = stats.ttest_ind(data_group1, data_group2, equal_var=False)
    except Exception as e:
        return {
            "p_value": None,
            "statistic": None,
            "test_type": "t-test",
            "error": str(e),
            "warnings": warnings_list
        }
        
    return {
        "p_value": p_value,
        "statistic": statistic,
        "test_type": "t-test",
        "warnings": warnings_list
    }

def run_anova(
    groups: List[np.ndarray],
    alpha: float = 0.05,
    sample_size: int = 0,
    rng: Optional[np.random.Generator] = None
) -> Dict[str, Any]:
    """
    Perform a one-way ANOVA test.
    
    Args:
        groups: List of arrays, each representing a group.
        alpha: Significance level.
        sample_size: Total sample size for small sample warning.
        rng: Random number generator.
        
    Returns:
        Dictionary containing p-value, statistic, and warnings.
    """
    warnings_list = []
    
    # Small sample warning (T013b)
    if sample_size < 30:
        warnings_list.append(
            f"Small sample warning (n={sample_size} < 30): Normality assumptions may be severely violated."
        )
        
    # Filter out empty groups if any
    valid_groups = [g for g in groups if len(g) > 0]
    
    if len(valid_groups) < 2:
        return {
            "p_value": None,
            "statistic": None,
            "test_type": "anova",
            "error": "Need at least two non-empty groups for ANOVA",
            "warnings": warnings_list
        }
        
    try:
        statistic, p_value = stats.f_oneway(*valid_groups)
    except Exception as e:
        return {
            "p_value": None,
            "statistic": None,
            "test_type": "anova",
            "error": str(e),
            "warnings": warnings_list
        }
        
    return {
        "p_value": p_value,
        "statistic": statistic,
        "test_type": "anova",
        "warnings": warnings_list
    }

def run_chi_squared(
    observed: np.ndarray,
    alpha: float = 0.05,
    sample_size: int = 0,
    rng: Optional[np.random.Generator] = None
) -> Dict[str, Any]:
    """
    Perform a chi-squared test with fallback logic for low expected counts.
    
    Args:
        observed: Observed contingency table (2D array).
        alpha: Significance level.
        sample_size: Total sample size for small sample warning.
        rng: Random number generator.
        
    Returns:
        Dictionary containing p-value, statistic, test method, and warnings.
    """
    warnings_list = []
    
    # Small sample warning (T013b)
    if sample_size < 30:
        warnings_list.append(
            f"Small sample warning (n={sample_size} < 30): Normality assumptions may be severely violated."
        )
        
    # Use existing fallback logic from chi_squared_utils
    result = run_chi_squared_with_fallback(observed, alpha)
    result["warnings"] = warnings_list + result.get("warnings", [])
    return result

def run_simulation_condition(
    test_type: str,
    n: int,
    effect_size: float,
    hypothesis: str,
    alpha: float = 0.05,
    rng: Optional[np.random.Generator] = None
) -> Dict[str, Any]:
    """
    Run a single simulation condition for a specific test type, sample size, 
    effect size, and hypothesis state.
    
    Args:
        test_type: One of 't-test', 'anova', 'chi-squared'.
        n: Sample size per group (for t-test/anova) or total N (for chi-squared).
        effect_size: Effect size parameter (Cohen's d for t-test, etc.).
        hypothesis: 'null' or 'alternative'.
        alpha: Significance level.
        rng: Random number generator instance.
        
    Returns:
        Dictionary with p-value, decision, and metadata.
    """
    if rng is None:
        rng = get_rng()
        
    warnings_list = []
    
    # T013b: Flag small sample sizes
    if n < 30:
        warnings_list.append(
            f"Small sample warning (n={n} < 30): Normality assumptions may be severely violated."
        )
    
    result = {
        "test_type": test_type,
        "n": n,
        "effect_size": effect_size,
        "hypothesis": hypothesis,
        "p_value": None,
        "decision": None,
        "warnings": warnings_list
    }
    
    try:
        if test_type == "t-test":
            # Generate two groups
            if hypothesis == "null":
                # No effect: same mean
                mean1, mean2 = 0.0, 0.0
            else:
                # Alternative: different means based on effect size
                # Assuming equal variance and n per group
                mean1 = 0.0
                mean2 = effect_size * np.std([0, 1]) * np.sqrt(2) # Simplified scaling
                
            data1 = rng.normal(mean1, 1.0, n)
            data2 = rng.normal(mean2, 1.0, n)
            
            res = run_t_test(data1, data2, alpha, sample_size=2*n, rng=rng)
            result["p_value"] = res["p_value"]
            result["warnings"].extend(res.get("warnings", []))
            
        elif test_type == "anova":
            # Generate 3 groups for ANOVA
            if hypothesis == "null":
                means = [0.0, 0.0, 0.0]
            else:
                # Spread means based on effect size
                base = 0.0
                spread = effect_size * 0.5
                means = [base - spread, base, base + spread]
                
            groups = [rng.normal(m, 1.0, n) for m in means]
            res = run_anova(groups, alpha, sample_size=3*n, rng=rng)
            result["p_value"] = res["p_value"]
            result["warnings"].extend(res.get("warnings", []))
            
        elif test_type == "chi-squared":
            # Generate contingency table
            # For null: uniform distribution
            # For alt: skewed distribution
            if hypothesis == "null":
                # 2x2 table with roughly equal counts
                total = n
                # Ensure at least some counts
                p = 0.25
                counts = rng.multinomial(total, [p, p, p, p])
            else:
                # Skewed distribution
                total = n
                p = [0.1, 0.4, 0.4, 0.1] # Skewed
                counts = rng.multinomial(total, p)
                
            observed = np.array(counts).reshape(2, 2)
            res = run_chi_squared(observed, alpha, sample_size=n, rng=rng)
            result["p_value"] = res["p_value"]
            result["warnings"].extend(res.get("warnings", []))
        else:
            raise ValueError(f"Unknown test type: {test_type}")
            
    except Exception as e:
        result["error"] = str(e)
        
    # Determine decision
    if result["p_value"] is not None and result["p_value"] < alpha:
        result["decision"] = "reject"
    elif result["p_value"] is not None:
        result["decision"] = "fail_to_reject"
    else:
        result["decision"] = "error"
        
    return result

def aggregate_results(
    results: List[Dict[str, Any]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Aggregate simulation results to calculate empirical error rates.
    
    Args:
        results: List of result dictionaries from run_simulation_condition.
        alpha: Significance level.
        
    Returns:
        Dictionary with aggregated statistics.
    """
    if not results:
        return {"error": "No results to aggregate"}
        
    total = len(results)
    rejects = 0
    errors = 0
    warnings_count = 0
    warning_types = {}
    
    for r in results:
        if r.get("error"):
            errors += 1
            continue
            
        if r.get("decision") == "reject":
            rejects += 1
            
        # Count warnings
        if "warnings" in r:
            for w in r["warnings"]:
                warnings_count += 1
                if "Small sample warning" in w:
                    warning_types["small_sample"] = warning_types.get("small_sample", 0) + 1
                
    return {
        "total_conditions": total,
        "successful_conditions": total - errors,
        "total_rejections": rejects,
        "empirical_rejection_rate": rejects / (total - errors) if (total - errors) > 0 else 0.0,
        "alpha": alpha,
        "total_warnings": warnings_count,
        "warning_breakdown": warning_types
    }