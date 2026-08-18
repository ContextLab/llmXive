"""
Statistical analysis module for BES experiments.

Implements:
- Two-proportion z-test for success rates (FR-005)
- TOST (Two One-Sided Tests) for equivalence (SC-001)
- Pre-registration logic for statistical framework selection (SC-001)
"""
import math
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass
import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

@dataclass
class ZTestResult:
    """Result of a two-proportion z-test."""
    z_statistic: float
    p_value: float
    significant: bool
    alpha: float
    p1: float
    p2: float
    n1: int
    n2: int
    framework: str = "non-inferiority"  # Default framework

@dataclass
class TOSTResult:
    """Result of a TOST equivalence test."""
    t_low: float
    t_high: float
    p_low: float
    p_high: float
    significant: bool
    alpha: float
    delta: float
    mean_diff: float
    std_diff: float
    n: int
    framework: str = "equivalence"

@dataclass
class PreRegistration:
    """
    Pre-registration record for statistical analysis.
    Satisfies SC-001 requirement to define framework choice before testing.
    """
    experiment_id: str
    framework_choice: str  # 'equivalence' (TOST) or 'non-inferiority'
    alpha: float
    delta: Optional[float]  # Equivalence margin for TOST
    timestamp: str
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "framework_choice": self.framework_choice,
            "alpha": self.alpha,
            "delta": self.delta,
            "timestamp": self.timestamp,
            "notes": self.notes
        }
    
    def to_json(self, filepath: Path) -> None:
        """Write pre-registration to a JSON file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Pre-registration saved to {filepath}")

def two_proportion_z_test(
    x1: int, n1: int, x2: int, n2: int, 
    alpha: float = 0.05, 
    alternative: str = "two-sided"
) -> ZTestResult:
    """
    Perform a two-proportion z-test.
    
    H0: p1 = p2
    HA: p1 != p2 (two-sided), p1 > p2, or p1 < p2
    
    Args:
        x1: Number of successes in sample 1
        n1: Total trials in sample 1
        x2: Number of successes in sample 2
        n2: Total trials in sample 2
        alpha: Significance level
        alternative: 'two-sided', 'greater', or 'less'
        
    Returns:
        ZTestResult with statistics and significance decision
    """
    if n1 == 0 or n2 == 0:
        raise ValueError("Sample sizes must be positive")
        
    p1 = x1 / n1
    p2 = x2 / n2
    
    # Pooled proportion
    p_pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se == 0:
        z_stat = 0.0
    else:
        z_stat = (p1 - p2) / se
        
    # Calculate p-value
    if alternative == "two-sided":
        p_value = 2 * (1 - abs(math.erf(z_stat / math.sqrt(2)) / 2) if z_stat >= 0 else 2 * (1 - abs(math.erf(-z_stat / math.sqrt(2)) / 2)))
        # More accurate approximation using standard normal CDF
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_stat) / math.sqrt(2))))
    elif alternative == "greater":
        p_value = 1 - 0.5 * (1 + math.erf(z_stat / math.sqrt(2)))
    elif alternative == "less":
        p_value = 0.5 * (1 + math.erf(z_stat / math.sqrt(2)))
    else:
        raise ValueError(f"Unknown alternative: {alternative}")
        
    significant = p_value < alpha
    
    return ZTestResult(
        z_statistic=z_stat,
        p_value=p_value,
        significant=significant,
        alpha=alpha,
        p1=p1,
        p2=p2,
        n1=n1,
        n2=n2,
        framework="non-inferiority"
    )

def tost_equivalence_test(
    x: List[float], 
    y: List[float], 
    delta: float, 
    alpha: float = 0.05
) -> TOSTResult:
    """
    Perform TOST (Two One-Sided Tests) for equivalence.
    
    H0: |mean(x) - mean(y)| >= delta
    HA: |mean(x) - mean(y)| < delta
    
    Args:
        x: Sample 1 data
        y: Sample 2 data
        delta: Equivalence margin
        alpha: Significance level
        
    Returns:
        TOSTResult with test statistics and equivalence decision
    """
    if not x or not y:
        raise ValueError("Samples must be non-empty")
        
    n1 = len(x)
    n2 = len(y)
    
    mean_x = sum(x) / n1
    mean_y = sum(y) / n2
    mean_diff = mean_x - mean_y
    
    # Sample variances
    var_x = sum((xi - mean_x) ** 2 for xi in x) / (n1 - 1) if n1 > 1 else 0
    var_y = sum((yi - mean_y) ** 2 for yi in y) / (n2 - 1) if n2 > 1 else 0
    
    # Pooled standard error
    se = math.sqrt(var_x / n1 + var_y / n2)
    
    if se == 0:
        # If no variance, check if means are exactly equal
        t_low = float('inf') if mean_diff > -delta else -float('inf')
        t_high = float('inf') if mean_diff < delta else -float('inf')
    else:
        # TOST statistics
        t_low = (mean_diff + delta) / se
        t_high = (mean_diff - delta) / se
        
    # Approximate p-values using normal distribution for large samples
    # For small samples, t-distribution with Welch-Satterthwaite df would be better
    # Using normal approximation for simplicity
    p_low = 1 - 0.5 * (1 + math.erf(t_low / math.sqrt(2)))
    p_high = 1 - 0.5 * (1 + math.erf(t_high / math.sqrt(2)))
    
    # Equivalence is established if both one-sided tests are significant
    significant = (p_low < alpha) and (p_high < alpha)
    
    # Calculate pooled std for reporting
    pooled_var = ((n1 - 1) * var_x + (n2 - 1) * var_y) / (n1 + n2 - 2)
    std_diff = math.sqrt(pooled_var)
    
    return TOSTResult(
        t_low=t_low,
        t_high=t_high,
        p_low=p_low,
        p_high=p_high,
        significant=significant,
        alpha=alpha,
        delta=delta,
        mean_diff=mean_diff,
        std_diff=std_diff,
        n=len(x) + len(y),
        framework="equivalence"
    )

def register_statistical_framework(
    experiment_id: str,
    framework_choice: str,
    alpha: float = 0.05,
    delta: Optional[float] = None,
    notes: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> PreRegistration:
    """
    Pre-register the statistical framework choice before running tests.
    
    This satisfies SC-001 requirement to define the choice between
    'equivalence' (TOST) and 'non-inferiority' frameworks before analysis.
    
    Args:
        experiment_id: Unique identifier for the experiment
        framework_choice: 'equivalence' for TOST or 'non-inferiority' for z-test
        alpha: Significance level (default 0.05)
        delta: Equivalence margin (required for 'equivalence', optional for 'non-inferiority')
        notes: Optional notes about the choice
        output_dir: Directory to save the pre-registration file
        
    Returns:
        PreRegistration object with the recorded choice
        
    Raises:
        ValueError: If framework_choice is invalid or delta is missing for equivalence
    """
    valid_choices = ['equivalence', 'non-inferiority']
    if framework_choice not in valid_choices:
        raise ValueError(f"framework_choice must be one of {valid_choices}")
        
    if framework_choice == 'equivalence' and delta is None:
        raise ValueError("delta (equivalence margin) is required for 'equivalence' framework")
        
    timestamp = datetime.now().isoformat()
    
    pre_reg = PreRegistration(
        experiment_id=experiment_id,
        framework_choice=framework_choice,
        alpha=alpha,
        delta=delta,
        timestamp=timestamp,
        notes=notes
    )
    
    # Log the pre-registration
    logger.info(f"Pre-registered framework: {framework_choice} for experiment {experiment_id}")
    logger.info(f"  Alpha: {alpha}, Delta: {delta}")
    if notes:
        logger.info(f"  Notes: {notes}")
        
    # Save to file if output_dir provided
    if output_dir:
        filepath = output_dir / f"pre_registration_{experiment_id}.json"
        pre_reg.to_json(filepath)
        
    return pre_reg

def main():
    """
    Demo of statistical framework pre-registration and testing.
    """
    # Example 1: Pre-register non-inferiority framework
    print("=== Non-Inferiority Framework Registration ===")
    pre_reg_1 = register_statistical_framework(
        experiment_id="EXP-001",
        framework_choice="non-inferiority",
        alpha=0.05,
        notes="Testing if new method is not worse than baseline"
    )
    print(f"Framework: {pre_reg_1.framework_choice}")
    print(f"Alpha: {pre_reg_1.alpha}")
    
    # Run a z-test
    result_z = two_proportion_z_test(x1=80, n1=100, x2=70, n2=100)
    print(f"\nZ-test result: z={result_z.z_statistic:.3f}, p={result_z.p_value:.3f}")
    print(f"Significant: {result_z.significant}")
    
    # Example 2: Pre-register equivalence framework
    print("\n=== Equivalence Framework Registration ===")
    pre_reg_2 = register_statistical_framework(
        experiment_id="EXP-002",
        framework_choice="equivalence",
        alpha=0.05,
        delta=0.1,
        notes="Testing if two methods are equivalent within margin"
    )
    print(f"Framework: {pre_reg_2.framework_choice}")
    print(f"Delta: {pre_reg_2.delta}")
    
    # Run TOST
    sample_x = [0.85, 0.82, 0.88, 0.84, 0.86]
    sample_y = [0.84, 0.83, 0.85, 0.86, 0.84]
    result_tost = tost_equivalence_test(sample_x, sample_y, delta=0.1)
    print(f"\nTOST result: t_low={result_tost.t_low:.3f}, t_high={result_tost.t_high:.3f}")
    print(f"p_low={result_tost.p_low:.3f}, p_high={result_tost.p_high:.3f}")
    print(f"Equivalence established: {result_tost.significant}")
    
    # Save pre-registrations
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pre_reg_1.to_json(output_dir / "pre_registration_EXP-001.json")
    pre_reg_2.to_json(output_dir / "pre_registration_EXP-002.json")
    
    print(f"\nPre-registrations saved to {output_dir}")

if __name__ == "__main__":
    main()