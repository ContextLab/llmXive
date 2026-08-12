"""
Statistical analysis module for the BES pipeline.
Implements significance testing (z-test) and equivalence testing (TOST).
"""
import math
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass
import sys
import os

# Add parent to path for imports if run as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@dataclass
class ZTestResult:
    """Result of a two-proportion z-test."""
    z_statistic: float
    p_value: float
    significant: bool
    p1: float
    p2: float
    n1: int
    n2: int
    null_hypothesis: str = "H0: p1 = p2"
    alpha: float = 0.05

@dataclass
class TOSTResult:
    """Result of the Two One-Sided Tests (TOST) for equivalence."""
    t1_statistic: float
    t2_statistic: float
    p1_value: float  # p-value for H01: p1 - p2 <= -delta
    p2_value: float  # p-value for H02: p1 - p2 >= delta
    lower_bound: float
    upper_bound: float
    equivalence_margin: float
    significant: bool  # True if both p-values < alpha (equivalence established)
    alpha: float = 0.05
    delta: float = 0.0  # Equivalence margin

def two_proportion_z_test(
    successes1: int,
    n1: int,
    successes2: int,
    n2: int,
    alpha: float = 0.05
) -> ZTestResult:
    """
    Perform a two-tailed two-proportion z-test.
    
    H0: p1 = p2
    H1: p1 != p2
    
    Args:
        successes1: Number of successes in sample 1
        n1: Total sample size 1
        successes2: Number of successes in sample 2
        n2: Total sample size 2
        alpha: Significance level
        
    Returns:
        ZTestResult object
    """
    if n1 == 0 or n2 == 0:
        raise ValueError("Sample sizes must be greater than 0")
        
    p1 = successes1 / n1
    p2 = successes2 / n2
    
    # Pooled proportion
    p_pooled = (successes1 + successes2) / (n1 + n2)
    
    # Standard error
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se == 0:
        # If pooled proportion is 0 or 1, z is undefined (or infinite)
        # If p1 == p2, z=0, p=1.0
        if p1 == p2:
            z_stat = 0.0
            p_val = 1.0
        else:
            z_stat = float('inf') if (p1 - p2) > 0 else float('-inf')
            p_val = 0.0
    else:
        z_stat = (p1 - p2) / se
        # Two-tailed p-value using standard normal approximation
        # Using math.erfc for 2 * (1 - Phi(|z|))
        p_val = 2 * (1 - 0.5 * (1 + math.erf(abs(z_stat) / math.sqrt(2))))
        
    significant = p_val < alpha
    
    return ZTestResult(
        z_statistic=z_stat,
        p_value=p_val,
        significant=significant,
        p1=p1,
        p2=p2,
        n1=n1,
        n2=n2,
        null_hypothesis="H0: p1 = p2",
        alpha=alpha
    )

def tost_equivalence_test(
    successes1: int,
    n1: int,
    successes2: int,
    n2: int,
    equivalence_margin: float,
    alpha: float = 0.05
) -> TOSTResult:
    """
    Perform the Two One-Sided Tests (TOST) for equivalence.
    
    Tests:
    H01: p1 - p2 <= -delta  (Alternative: p1 - p2 > -delta)
    H02: p1 - p2 >= delta   (Alternative: p1 - p2 < delta)
    
    Equivalence is established if BOTH null hypotheses are rejected.
    
    Args:
        successes1: Number of successes in sample 1
        n1: Total sample size 1
        successes2: Number of successes in sample 2
        n2: Total sample size 2
        equivalence_margin: The delta (delta) for equivalence margin
        alpha: Significance level
        
    Returns:
        TOSTResult object
    """
    if n1 == 0 or n2 == 0:
        raise ValueError("Sample sizes must be greater than 0")
    if equivalence_margin <= 0:
        raise ValueError("Equivalence margin must be positive")
        
    p1 = successes1 / n1
    p2 = successes2 / n2
    diff = p1 - p2
    
    # Standard error for the difference (unpooled)
    se = math.sqrt((p1 * (1 - p1) / n1) + (p2 * (1 - p2) / n2))
    
    if se == 0:
        # If both proportions are 0 or 1, se is 0
        # If diff is within margin, we might consider it equivalent, 
        # but statistically we can't compute t.
        # If diff is exactly 0 and margin > 0, we treat as equivalent.
        if abs(diff) < equivalence_margin:
            t1_stat = float('inf') # Reject H01
            t2_stat = float('-inf') # Reject H02
            p1_val = 0.0
            p2_val = 0.0
        else:
            t1_stat = float('-inf')
            t2_stat = float('inf')
            p1_val = 1.0
            p2_val = 1.0
    else:
        # Test 1: H01: p1 - p2 <= -delta
        # t1 = (diff - (-delta)) / se = (diff + delta) / se
        t1_stat = (diff + equivalence_margin) / se
        # One-tailed p-value (right tail for H01 rejection)
        p1_val = 1 - 0.5 * (1 + math.erf(t1_stat / math.sqrt(2)))
        
        # Test 2: H02: p1 - p2 >= delta
        # t2 = (diff - delta) / se
        t2_stat = (diff - equivalence_margin) / se
        # One-tailed p-value (left tail for H02 rejection)
        p2_val = 0.5 * (1 + math.erf(t2_stat / math.sqrt(2)))
        
    # Equivalence is established if both p-values < alpha
    significant = (p1_val < alpha) and (p2_val < alpha)
    
    return TOSTResult(
        t1_statistic=t1_stat,
        t2_statistic=t2_stat,
        p1_value=p1_val,
        p2_value=p2_val,
        lower_bound=diff - equivalence_margin,
        upper_bound=diff + equivalence_margin,
        equivalence_margin=equivalence_margin,
        significant=significant,
        alpha=alpha,
        delta=equivalence_margin
    )

def main():
    """
    Main function to demonstrate TOST and z-test functionality.
    Reads experiment logs if available, or runs with dummy data for verification.
    """
    from pathlib import Path
    
    # Example usage with dummy data for verification
    # In a real scenario, this would load data from logs
    n1, s1 = 1000, 850  # 85% success rate
    n2, s2 = 1000, 845  # 84.5% success rate
    margin = 0.05       # 5% equivalence margin
    
    print("=== Statistical Analysis Module ===")
    print(f"Sample 1: {s1}/{n1} ({s1/n1:.2%})")
    print(f"Sample 2: {s2}/{n2} ({s2/n2:.2%})")
    print(f"Equivalence Margin: {margin}")
    print()
    
    # Z-Test
    z_result = two_proportion_z_test(s1, n1, s2, n2)
    print(f"Z-Test Result:")
    print(f"  Z-statistic: {z_result.z_statistic:.4f}")
    print(f"  P-value: {z_result.p_value:.4f}")
    print(f"  Significant (p < {z_result.alpha}): {z_result.significant}")
    print()
    
    # TOST
    tost_result = tost_equivalence_test(s1, n1, s2, n2, margin)
    print(f"TOST Result:")
    print(f"  T1 Statistic: {tost_result.t1_statistic:.4f} (p={tost_result.p1_value:.4f})")
    print(f"  T2 Statistic: {tost_result.t2_statistic:.4f} (p={tost_result.p2_value:.4f})")
    print(f"  Equivalence Margin: {tost_result.equivalence_margin}")
    print(f"  Significant (Equivalence Established): {tost_result.significant}")
    
    if tost_result.significant:
        print("  -> Conclusion: The two methods are statistically equivalent within the margin.")
    else:
        print("  -> Conclusion: Equivalence cannot be established (or difference is significant).")

if __name__ == "__main__":
    main()