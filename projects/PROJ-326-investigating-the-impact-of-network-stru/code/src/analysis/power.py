"""
Statistical power analysis module.
Calculates achieved power and provides design validation.
"""
import json
import logging
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from statsmodels.stats.power import TTestIndPower
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logger.warning("statsmodels not installed. Power analysis will be limited.")

logger = logging.getLogger(__name__)

class PowerAnalysisError(Exception):
    """Custom exception for power analysis errors."""
    pass

def calculate_effect_size_r_to_cohen_d(r: float) -> float:
    """Convert correlation coefficient to Cohen's d."""
    if abs(r) >= 1.0:
        raise PowerAnalysisError("Correlation must be in (-1, 1)")
    return (2 * r) / math.sqrt(1 - r**2)

def calculate_power_t_test_two_tailed(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """Calculate power for two-sample t-test."""
    if not HAS_STATSMODELS:
        logger.warning("statsmodels not available. Returning placeholder power.")
        return 0.5
        
    try:
        power_analysis = TTestIndPower()
        power = power_analysis.solve_power(
            effect_size=effect_size,
            nobs1=n1,
            alpha=alpha,
            ratio=n2/n1 if n1 > 0 else 1.0
        )
        return float(power)
    except Exception as e:
        logger.error(f"Power calculation failed: {e}")
        return 0.0

def load_regression_results(path: str) -> Optional[Dict]:
    """Load regression results from file."""
    p = Path(path)
    if not p.exists():
        return None
    with open(p, 'r') as f:
        return json.load(f)

def load_anova_results(path: str) -> Optional[Dict]:
    """Load ANOVA results from file."""
    p = Path(path)
    if not p.exists():
        return None
    with open(p, 'r') as f:
        return json.load(f)

def compute_power_analysis(regression_results: Dict, anova_results: Dict, sample_size: int, target_power: float = 0.8) -> Dict[str, Any]:
    """Compute power analysis based on results."""
    # Estimate effect size from regression R-squared
    r_squared = regression_results.get("linear", {}).get("r_squared", 0.0)
    r = math.sqrt(r_squared)
    
    try:
        effect_size = calculate_effect_size_r_to_cohen_d(r)
    except PowerAnalysisError:
        effect_size = 0.5  # Default medium effect
        
    # Assume equal group sizes for simplicity
    n_per_group = sample_size // 2
    achieved_power = calculate_power_t_test_two_tailed(effect_size, n_per_group, n_per_group)
    
    shortfall = 0
    recommendation = "Sample size is sufficient."
    
    if achieved_power < target_power:
        # Estimate required sample size
        if HAS_STATSMODELS:
            try:
                power_analysis = TTestIndPower()
                required_n = power_analysis.solve_power(
                    effect_size=effect_size,
                    power=target_power,
                    alpha=0.05,
                    ratio=1.0
                )
                shortfall = int(required_n * 2) - sample_size
                if shortfall > 0:
                    recommendation = f"Increase sample size by {shortfall} to achieve {target_power} power."
            except:
                recommendation = "Could not calculate required sample size. Manual review needed."
        else:
            recommendation = "Install statsmodels for accurate power calculations."
            
    return {
        "achieved_power": round(achieved_power, 4),
        "effect_size": round(effect_size, 4),
        "sample_size": sample_size,
        "target_power": target_power,
        "sample_size_shortfall": max(0, shortfall),
        "recommendation": recommendation
    }

def generate_power_report(power_data: Dict[str, Any], output_path: str) -> None:
    """Generate and save power analysis report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": "Statistical Power Analysis",
        "results": power_data
    }
    
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Power analysis report saved to {output_path}")

def main():
    """Main entry point for power analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run power analysis")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    output_path = Path(args.output)
    stats_path = output_path / "analysis" / "statistical_outputs.json"
    results_path = output_path / "analysis" / "simulation_results.json"
    report_path = output_path / "analysis" / "power_analysis_report.json"
    
    stats_data = load_json_file(str(stats_path))
    
    if not stats_data:
        logger.warning("No statistical outputs found. Creating placeholder report.")
        placeholder = {
            "achieved_power": 0.0,
            "sample_size_shortfall": 0,
            "recommendation": "No data available for analysis."
        }
        generate_power_report(placeholder, str(report_path))
        return
        
    # Get sample size
    if results_path.exists():
        with open(results_path, 'r') as f:
            sim_data = json.load(f)
            sample_size = len(sim_data) if isinstance(sim_data, list) else 1
    else:
        sample_size = 0
        
    power_data = compute_power_analysis(
        regression_results=stats_data.get("regression", {}),
        anova_results=stats_data.get("anova", {}),
        sample_size=sample_size
    )
    
    generate_power_report(power_data, str(report_path))

if __name__ == "__main__":
    main()
