import json
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Constants
PAIRED_SCORES_PATH = Path("results/paired_scores.json")
STATISTICAL_REPORT_PATH = Path("results/statistical_report.json")
DEFAULT_MARGIN = 5.0
DEFAULT_ALPHA = 0.05
LOW_POWER_THRESHOLD = 0.4

def load_ppaired_scores() -> Tuple[Optional[list], str]:
    """
    Load paired scores from results/paired_scores.json.
    Returns (scores_list, error_message). If successful, error_message is empty.
    """
    if not PAIRED_SCORES_PATH.exists():
        return None, f"File not found: {PAIRED_SCORES_PATH}"
    
    try:
        with open(PAIRED_SCORES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return None, "Invalid format: expected a list of score objects."
        
        # Extract scientific_core scores for both conditions
        zero_shot_scores = []
        scaffolded_scores = []
        
        for entry in data:
            if entry.get("condition") == "zero_shot":
                zero_shot_scores.append(entry["scores"]["scientific_core"])
            elif entry.get("condition") == "scaffolded":
                scaffolded_scores.append(entry["scores"]["scientific_core"])
        
        if len(zero_shot_scores) != len(scaffolded_scores):
            return None, f"Mismatched counts: {len(zero_shot_scores)} zero-shot vs {len(scaffolded_scores)} scaffolded."
        
        if len(zero_shot_scores) == 0:
            return None, "No paired scores found."
        
        return list(zip(zero_shot_scores, scaffolded_scores)), ""
    
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def calculate_mean_diff(paired_data: list) -> float:
    """Calculate the mean difference (Scaffolded - Zero-Shot)."""
    if not paired_data:
        return 0.0
    diffs = [s - z for z, s in paired_data]
    return sum(diffs) / len(diffs)

def calculate_std_dev(data: list) -> float:
    """Calculate sample standard deviation."""
    if len(data) < 2:
        return 0.0
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
    return math.sqrt(variance)

def calculate_effect_size_cohen_d(paired_data: list) -> float:
    """
    Calculate Cohen's d for paired samples.
    d = mean_diff / std_diff
    """
    if not paired_data:
        return 0.0
    
    diffs = [s - z for z, s in paired_data]
    mean_diff = sum(diffs) / len(diffs)
    std_diff = calculate_std_dev(diffs)
    
    if std_diff == 0:
        return 0.0
    
    return mean_diff / std_diff

def calculate_power_t_test(
    effect_size: float,
    n: int,
    alpha: float = DEFAULT_ALPHA,
    margin: float = DEFAULT_MARGIN
) -> float:
    """
    Estimate statistical power for a paired t-test (approximation).
    
    Uses the non-central t-distribution approximation:
    Power = P(t > t_crit | non-centrality parameter)
    
    For simplicity in this environment without scipy.stats, we use a standard
    approximation formula for power based on effect size and sample size.
    
    Power ~ Phi( sqrt(n) * |d| - z_{1-alpha/2} )
    where Phi is the CDF of the standard normal distribution.
    
    Note: This is an approximation. In a full implementation, scipy.stats would be used.
    """
    if n < 2:
        return 0.0
    
    # Standard normal critical value for two-tailed test (approx z=1.96 for alpha=0.05)
    z_critical = 1.96 
    
    # Non-centrality parameter (NCP)
    ncp = math.sqrt(n) * abs(effect_size)
    
    # Approximate power using normal CDF
    # We approximate Phi(x) using the error function
    # Phi(x) = 0.5 * (1 + erf(x / sqrt(2)))
    
    # Power is the probability that the test statistic exceeds the critical value
    # under the alternative hypothesis.
    # Approximation: Power = P(Z > z_critical - ncp) + P(Z < -z_critical - ncp)
    # Since we are looking for equivalence, we focus on the upper tail usually,
    # but for a standard t-test power calculation:
    # Power = 1 - Phi(z_critical - ncp) + Phi(-z_critical - ncp)
    # For large ncp, the second term is negligible.
    
    # Let's use a robust approximation for Phi
    def normal_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    # Power = P(reject H0 | H1 is true)
    # In a two-sided test, we reject if |t| > t_crit.
    # Under H1, t is distributed as non-central t with ncp.
    # Approximation: Power = 1 - Phi(z_crit - ncp) + Phi(-z_crit - ncp)
    
    term1 = 1 - normal_cdf(z_critical - ncp)
    term2 = normal_cdf(-z_critical - ncp)
    
    power = term1 + term2
    
    return min(max(power, 0.0), 1.0)

def calculate_power_report(paired_data: list) -> Dict[str, Any]:
    """
    Calculate statistical power and generate a warning if low.
    
    Returns a dictionary containing:
    - n: sample size
    - mean_diff: calculated mean difference
    - effect_size: Cohen's d
    - power: estimated power
    - power_warning: present if power < 0.4
    """
    n = len(paired_data)
    mean_diff = calculate_mean_diff(paired_data)
    effect_size = calculate_effect_size_cohen_d(paired_data)
    power = calculate_power_t_test(effect_size, n)
    
    report = {
        "n": n,
        "mean_diff": mean_diff,
        "effect_size": effect_size,
        "power": power
    }
    
    if power < LOW_POWER_THRESHOLD:
        report["power_warning"] = {
            "value": power,
            "threshold": LOW_POWER_THRESHOLD,
            "recommendation": "interpret results as 'inconclusive' rather than 'validated'",
            "reason": f"Statistical power ({power:.3f}) is below the threshold ({LOW_POWER_THRESHOLD}). With N={n}, the sample size is insufficient to reliably detect the observed effect size."
        }
    
    return report

def update_statistical_report(power_info: Dict[str, Any]) -> None:
    """
    Read the existing statistical_report.json, add the power warning if present,
    and write it back. If the file does not exist, create it with the power info.
    """
    report_path = STATISTICAL_REPORT_PATH
    
    existing_data = {}
    if report_path.exists():
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, Exception):
            existing_data = {}
    
    # Add power info
    if "power_info" not in existing_data:
        existing_data["power_info"] = {}
    
    existing_data["power_info"] = {
        "n": power_info["n"],
        "mean_diff": power_info["mean_diff"],
        "effect_size": power_info["effect_size"],
        "power": power_info["power"]
    }
    
    if "power_warning" in power_info:
        existing_data["power_warning"] = power_info["power_warning"]
        # Update interpreted_status if warning exists
        if "interpreted_status" in existing_data:
            if existing_data["interpreted_status"] == "safe" and "power_warning" in power_info:
                existing_data["interpreted_status"] = "inconclusive"
                existing_data["interpretation_note"] = "Results marked inconclusive due to low statistical power."
    
    # Write back
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)

def main():
    """Main entry point for power calculation."""
    print("Starting power calculation...")
    
    # Load data
    paired_data, error = load_ppaired_scores()
    if error:
        print(f"ERROR: {error}")
        return 1
    
    # Calculate power
    power_info = calculate_power_report(paired_data)
    
    # Update report
    try:
        update_statistical_report(power_info)
        print(f"Power calculation complete. Report updated at {STATISTICAL_REPORT_PATH}")
        if "power_warning" in power_info:
            print(f"WARNING: Low power detected ({power_info['power']:.3f}).")
            print(f"Recommendation: {power_info['power_warning']['recommendation']}")
    except Exception as e:
        print(f"ERROR updating report: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())