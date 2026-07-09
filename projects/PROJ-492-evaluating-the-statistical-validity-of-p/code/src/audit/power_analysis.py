import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger = get_default_logger(__name__)

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set the random seed for reproducibility in power analysis."""
    set_rng_seed(seed)
    logger.debug(f"Power analysis RNG seed set to {seed}")

def calculate_sample_size_binary(
    p0: float,
    p1: float,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided"
) -> float:
    """
    Calculate minimum sample size per group for a two-proportion z-test.
    
    Args:
        p0: Baseline proportion (control group)
        p1: Expected proportion in treatment group
        alpha: Significance level (Type I error rate)
        power: Desired statistical power (1 - Type II error rate)
        alternative: 'two-sided', 'larger', or 'smaller'
    
    Returns:
        Minimum sample size per group (n)
    """
    if not (0 < p0 < 1):
        raise ValueError(f"Baseline proportion p0 must be between 0 and 1, got {p0}")
    if not (0 < p1 < 1):
        raise ValueError(f"Treatment proportion p1 must be between 0 and 1, got {p1}")
    if not (0 < alpha < 1):
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
    if not (0 < power < 1):
        raise ValueError(f"Power must be between 0 and 1, got {power}")
    
    delta = abs(p1 - p0)
    if delta == 0:
        raise ValueError("Effect size (delta) cannot be zero")
    
    # Pooled proportion under null
    p_pooled = p0
    # Standard normal quantiles
    z_alpha = stats.norm.ppf(1 - alpha / 2) if alternative == "two-sided" else stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Variance components
    var0 = p0 * (1 - p0)
    var1 = p1 * (1 - p1)
    
    # Sample size formula for two-proportion z-test
    # n = ( (z_alpha * sqrt(2*p_pooled*(1-p_pooled)) + z_beta * sqrt(p0*(1-p0) + p1*(1-p1)))^2 ) / delta^2
    numerator = (z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) + z_beta * np.sqrt(var0 + var1)) ** 2
    n = numerator / (delta ** 2)
    
    return float(np.ceil(n))

def calculate_sample_size_continuous(
    mu0: float,
    mu1: float,
    sigma: float,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided"
) -> float:
    """
    Calculate minimum sample size per group for a Welch's t-test (approximated).
    
    Args:
        mu0: Baseline mean (control group)
        mu1: Expected mean in treatment group
        sigma: Standard deviation (assumed equal for both groups for this approximation)
        alpha: Significance level
        power: Desired statistical power
        alternative: 'two-sided', 'larger', or 'smaller'
    
    Returns:
        Minimum sample size per group (n)
    """
    if sigma <= 0:
        raise ValueError(f"Standard deviation must be positive, got {sigma}")
    
    delta = abs(mu1 - mu0)
    if delta == 0:
        raise ValueError("Effect size (delta) cannot be zero")
    
    # Effect size (Cohen's d)
    d = delta / sigma
    
    z_alpha = stats.norm.ppf(1 - alpha / 2) if alternative == "two-sided" else stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula for t-test (approximated with normal)
    # n = 2 * ( (z_alpha + z_beta) / d )^2
    n = 2 * ((z_alpha + z_beta) / d) ** 2
    
    return float(np.ceil(n))

def count_corpus_size(audit_records_path: Path) -> int:
    """
    Count the number of audit records in the corpus.
    
    Args:
        audit_records_path: Path to the audit_report.json file
    
    Returns:
        Number of records in the corpus
    """
    if not audit_records_path.exists():
        logger.warning(f"Audit report not found at {audit_records_path}, assuming corpus size 0")
        return 0
    
    try:
        with open(audit_records_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict) and 'records' in data:
            return len(data['records'])
        else:
            logger.warning(f"Unexpected audit report format at {audit_records_path}")
            return 0
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse audit report JSON: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error reading audit report: {e}")
        return 0

def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write power analysis results to a JSON file.
    
    Args:
        result: Dictionary containing power analysis results
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    logger.info(f"Power analysis results written to {output_path}")

def run_power_analysis(
    output_dir: Path,
    audit_report_path: Optional[Path] = None,
    baseline_conversion: float = 0.10,
    detectable_effect: float = 0.05,
    alpha: float = 0.05,
    power: float = 0.80,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Run power analysis for the audit corpus.
    
    Args:
        output_dir: Directory to write output files
        audit_report_path: Path to the audit report JSON (optional)
        baseline_conversion: Baseline conversion rate for binary outcomes
        detectable_effect: Minimum detectable effect size (absolute difference)
        alpha: Significance level
        power: Desired statistical power
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing power analysis results
    """
    set_rng_seed_for_power_analysis(seed)
    
    # Calculate required sample size per group for binary outcome
    p0 = baseline_conversion
    p1 = baseline_conversion + detectable_effect
    n_required = calculate_sample_size_binary(p0, p1, alpha, power)
    
    # Count actual corpus size if audit report is provided
    corpus_size = 0
    if audit_report_path and audit_report_path.exists():
        corpus_size = count_corpus_size(audit_report_path)
    
    # Check if corpus meets the requirement (Claim c_21f3e400 reference)
    # The claim references a specific sample size requirement (2510.17487)
    # We interpret this as a requirement that the corpus size must be >= the calculated N
    # Since the claim is unresolved, we perform the check against the calculated N
    meets_requirement = corpus_size >= n_required if corpus_size > 0 else False
    
    result = {
        "parameters": {
            "baseline_conversion": baseline_conversion,
            "detectable_effect": detectable_effect,
            "alpha": alpha,
            "power": power,
            "seed": seed
        },
        "calculated_sample_size_per_group": n_required,
        "corpus_size": corpus_size,
        "meets_sample_size_requirement": meets_requirement,
        "sample_size_gap": max(0, n_required - corpus_size) if corpus_size > 0 else None,
        "timestamp": str(Path(output_dir).parent.stat().st_mtime) if output_dir.exists() else str(Path.cwd().stat().st_mtime)
    }
    
    output_path = output_dir / "power_analysis.json"
    write_power_analysis_result(result, output_path)
    
    if not meets_requirement and corpus_size > 0:
        logger.warning(
            f"Corpus size ({corpus_size}) is below required sample size ({n_required}). "
            f"Gap: {n_required - corpus_size} samples."
        )
    elif meets_requirement:
        logger.info(f"Corpus size ({corpus_size}) meets required sample size ({n_required}).")
    else:
        logger.info("No audit report provided to compare against calculated sample size.")
    
    return result

def main() -> int:
    """Main entry point for power analysis utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Power analysis for A/B test audit corpus")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to write output files"
    )
    parser.add_argument(
        "--audit-report",
        type=Path,
        default=None,
        help="Path to audit_report.json"
    )
    parser.add_argument(
        "--baseline",
        type=float,
        default=0.10,
        help="Baseline conversion rate"
    )
    parser.add_argument(
        "--effect",
        type=float,
        default=0.05,
        help="Detectable effect size"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.80,
        help="Desired power"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help="Random seed"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_power_analysis(
            output_dir=args.output_dir,
            audit_report_path=args.audit_report,
            baseline_conversion=args.baseline,
            detectable_effect=args.effect,
            alpha=args.alpha,
            power=args.power,
            seed=args.seed
        )
        
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
