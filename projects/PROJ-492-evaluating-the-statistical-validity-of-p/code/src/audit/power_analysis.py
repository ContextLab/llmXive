"""
Power analysis utility for A/B test audit.

Implements FR-025: Computes minimum sample size N given baseline conversion,
detectable effect size, alpha, and power. Validates corpus size against
statistical power requirements from claim c_21f3e400 (arXiv:2510.17487).
"""
import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set random seed for reproducibility in power analysis."""
    set_rng_seed(seed)

def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0
) -> int:
    """
    Calculate minimum sample size per group for a two-proportion z-test.
    
    Args:
        baseline_rate: Expected baseline conversion rate (0-1)
        detectable_effect: Minimum detectable effect size (absolute difference)
        alpha: Significance level (Type I error rate)
        power: Statistical power (1 - Type II error rate)
        ratio: Ratio of sample sizes between groups (n2/n1)
        
    Returns:
        Minimum sample size per group (integer)
        
    Raises:
        ValueError: If parameters are out of valid range
    """
    if not 0 < baseline_rate < 1:
        raise ValueError(f"baseline_rate must be between 0 and 1, got {baseline_rate}")
    if not 0 < detectable_effect < 1:
        raise ValueError(f"detectable_effect must be between 0 and 1, got {detectable_effect}")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be between 0 and 1, got {alpha}")
    if not 0 < power < 1:
        raise ValueError(f"power must be between 0 and 1, got {power}")
    if not 0 < ratio:
        raise ValueError(f"ratio must be positive, got {ratio}")
        
    # Calculate effect size (Cohen's h for proportions)
    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect
    
    if p2 <= 0 or p2 >= 1:
        raise ValueError(f"Resulting rate p2={p2} must be in (0, 1)")
        
    # Cohen's h for proportions
    h = 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2))
    h = abs(h)
    
    if h == 0:
        raise ValueError("Effect size is zero; cannot compute sample size")
        
    # Critical values
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula for two proportions
    # n = (z_alpha + z_beta)^2 * (p1*(1-p1) + p2*(1-p2)/ratio) / (p1-p2)^2
    # Simplified using effect size approximation:
    n_per_group = ((z_alpha + z_beta) ** 2) / (h ** 2)
    
    # Adjust for ratio if not 1:1
    if ratio != 1.0:
        n_per_group = n_per_group * (1 + ratio) / (2 * np.sqrt(ratio))
        
    return max(1, int(np.ceil(n_per_group)))

def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0
) -> int:
    """
    Calculate minimum sample size per group for a Welch's t-test.
    
    Args:
        baseline_mean: Expected baseline mean
        detectable_effect: Minimum detectable difference in means
        std_dev: Expected standard deviation (assumed equal for both groups)
        alpha: Significance level
        power: Statistical power
        ratio: Ratio of sample sizes between groups
        
    Returns:
        Minimum sample size per group (integer)
    """
    if std_dev <= 0:
        raise ValueError(f"std_dev must be positive, got {std_dev}")
        
    # Cohen's d (effect size)
    d = abs(detectable_effect) / std_dev
    
    if d == 0:
        raise ValueError("Effect size is zero; cannot compute sample size")
        
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula for two means
    n_per_group = ((z_alpha + z_beta) ** 2) / (d ** 2)
    
    if ratio != 1.0:
        n_per_group = n_per_group * (1 + ratio) / (2 * np.sqrt(ratio))
        
    return max(1, int(np.ceil(n_per_group)))

def count_corpus_size(corpus_path: Path) -> int:
    """
    Count the number of records in the audit corpus.
    
    Args:
        corpus_path: Path to the audit report JSON file
        
    Returns:
        Number of records in the corpus
    """
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")
        
    with open(corpus_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict) and 'records' in data:
        return len(data['records'])
    else:
        # Try to count keys or items
        return len(data) if isinstance(data, dict) else 0

def run_power_analysis(
    baseline_rate: float = 0.05,
    detectable_effect: float = 0.01,
    alpha: float = 0.05,
    power: float = 0.80,
    corpus_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    logger: Optional[AuditLogger] = None
) -> Dict[str, Any]:
    """
    Run power analysis and validate corpus size against requirements.
    
    This function:
    1. Calculates minimum sample size per group for binary outcomes
    2. Counts actual corpus size if provided
    3. Validates against the requirement from claim c_21f3e400
       (arXiv:2510.17487) which suggests a minimum corpus size for
       statistically meaningful prevalence estimates
    
    Args:
        baseline_rate: Expected baseline conversion rate
        detectable_effect: Minimum detectable effect size
        alpha: Significance level
        power: Statistical power
        corpus_path: Path to audit report JSON (optional)
        output_path: Path to write results JSON (optional)
        logger: AuditLogger instance (optional)
        
    Returns:
        Dictionary with power analysis results and validation status
    """
    if logger is None:
        logger = get_default_logger(__name__)
        
    set_rng_seed_for_power_analysis()
    
    # Calculate minimum sample size per group
    min_n_per_group = calculate_sample_size_binary(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power
    )
    
    # Total minimum sample size (two groups)
    min_total_n = min_n_per_group * 2
    
    result = {
        "baseline_rate": baseline_rate,
        "detectable_effect": detectable_effect,
        "alpha": alpha,
        "power": power,
        "min_sample_size_per_group": min_n_per_group,
        "min_total_sample_size": min_total_n,
        "corpus_size": None,
        "corpus_valid": None,
        "requirement_reference": "c_21f3e400",
        "requirement_source": "https://arxiv.org/abs/2510.17487",
        "timestamp": str(datetime.now())
    }
    
    # Validate against corpus size if provided
    if corpus_path is not None:
        try:
            corpus_size = count_corpus_size(corpus_path)
            result["corpus_size"] = corpus_size
            
            # According to claim c_21f3e400 (arXiv:2510.17487),
            # the audited corpus must meet a minimum size threshold
            # for statistical validity. The paper suggests a minimum
            # of ~2,500 summaries for reliable prevalence estimation.
            # We use min_total_n as the threshold.
            min_required_size = min_total_n
            
            is_valid = corpus_size >= min_required_size
            result["corpus_valid"] = is_valid
            result["min_required_corpus_size"] = min_required_size
            
            if is_valid:
                logger.info(
                    f"Corpus size {corpus_size} meets minimum requirement "
                    f"of {min_required_size} (claim c_21f3e400)"
                )
            else:
                logger.warning(
                    f"Corpus size {corpus_size} is below minimum requirement "
                    f"of {min_required_size} (claim c_21f3e400)"
                )
        except Exception as e:
            logger.error(f"Failed to validate corpus size: {e}")
            result["corpus_valid"] = False
            result["corpus_error"] = str(e)
    
    # Write output if path provided
    if output_path is not None:
        write_power_analysis_result(result, output_path, logger)
        
    return result

def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path,
    logger: Optional[AuditLogger] = None
) -> None:
    """
    Write power analysis results to JSON file.
    
    Args:
        result: Power analysis result dictionary
        output_path: Path to write JSON file
        logger: AuditLogger instance (optional)
    """
    if logger is None:
        logger = get_default_logger(__name__)
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
        
    logger.info(f"Power analysis results written to {output_path}")

def main() -> int:
    """
    Main entry point for power analysis utility.
    
    Reads configuration from environment or defaults, runs power analysis,
    validates against corpus, and writes results to output/power_analysis.json.
    
    Returns:
        0 on success, 1 on failure
    """
    logger = get_default_logger(__name__)
    
    try:
        # Default parameters (can be overridden via environment)
        baseline_rate = float(
            Path("config/power_analysis_baseline_rate.txt").read_text().strip()
        ) if Path("config/power_analysis_baseline_rate.txt").exists() else 0.05
        
        detectable_effect = float(
            Path("config/power_analysis_effect.txt").read_text().strip()
        ) if Path("config/power_analysis_effect.txt").exists() else 0.01
        
        alpha = 0.05
        power = 0.80
        
        # Determine corpus path
        corpus_path = Path("output/audit_report.json")
        if not corpus_path.exists():
            # Try alternative location
            corpus_path = Path("code/output/audit_report.json")
        
        output_path = Path("output/power_analysis.json")
        
        logger.info(f"Running power analysis with baseline={baseline_rate}, "
                   f"effect={detectable_effect}, alpha={alpha}, power={power}")
        
        # Run analysis
        result = run_power_analysis(
            baseline_rate=baseline_rate,
            detectable_effect=detectable_effect,
            alpha=alpha,
            power=power,
            corpus_path=corpus_path if corpus_path.exists() else None,
            output_path=output_path,
            logger=logger
        )
        
        # Verify required fields
        if "min_sample_size_per_group" not in result:
            logger.error("Missing min_sample_size_per_group in result")
            return 1
            
        if result["min_sample_size_per_group"] is None:
            logger.error("min_sample_size_per_group is None")
            return 1
            
        # Verify output file exists and contains numeric N
        if not output_path.exists():
            logger.error(f"Output file not created: {output_path}")
            return 1
            
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
            
        if "min_sample_size_per_group" not in saved_result:
            logger.error("Output JSON missing min_sample_size_per_group")
            return 1
            
        if not isinstance(saved_result["min_sample_size_per_group"], (int, float)):
            logger.error("min_sample_size_per_group is not numeric")
            return 1
        
        logger.info("Power analysis completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())
