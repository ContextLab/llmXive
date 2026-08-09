"""
Post-hoc power analysis for predicting individual differences in sensory processing speed.

Task: T023
Description: Perform post-hoc power analysis to estimate the required sample size (N)
for R²=0.10 with power ≥ 0.80 and report in `data/processed/model_results.json` (FR-011).

Dependencies:
  - code/config.py (get_path, ensure_dirs)
  - code/utils/stats_helpers.py (calculate_sample_size_for_r2)
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, ensure_dirs
from utils.stats_helpers import calculate_sample_size_for_r2


def load_model_results() -> Dict[str, Any]:
    """
    Load existing model results from the JSON file.
    
    Returns:
        Dictionary containing model results.
        
    Raises:
        FileNotFoundError: If the model results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    results_path = get_path("processed", "model_results.json")
    
    if not results_path.exists():
        raise FileNotFoundError(
            f"Model results file not found: {results_path}. "
            "Ensure T019 (modeling) has completed successfully."
        )
    
    with open(results_path, 'r') as f:
        return json.load(f)


def perform_power_analysis(
    current_n: int,
    current_r2: float,
    target_r2: float = 0.10,
    target_power: float = 0.80,
    alpha: float = 0.05,
    num_predictors: int = 6
) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis to estimate required sample size.
    
    Args:
        current_n: Current number of participants in the study.
        current_r2: Observed R² value from the model.
        target_r2: Target R² value to detect (default 0.10).
        target_power: Target statistical power (default 0.80).
        alpha: Significance level (default 0.05).
        num_predictors: Number of predictors in the model (default 6 bands).
        
    Returns:
        Dictionary containing power analysis results including:
          - current_n: Current sample size
          - current_r2: Observed R²
          - target_r2: Target R²
          - target_power: Target power
          - alpha: Significance level
          - required_n: Estimated required sample size for target power
          - achieved_power: Power achieved with current N and observed R²
          - effect_size_f2: Cohen's f² effect size
    """
    # Calculate Cohen's f² from observed R²
    # f² = R² / (1 - R²)
    if current_r2 >= 1.0:
        # Avoid division by zero or infinite effect size
        current_f2 = 10.0  # Very large effect
    else:
        current_f2 = current_r2 / (1 - current_r2)
    
    # Calculate required sample size for target R²
    # Target f² = target_r2 / (1 - target_r2)
    target_f2 = target_r2 / (1 - target_r2)
    
    required_n = calculate_sample_size_for_r2(
        f2=target_f2,
        power=target_power,
        alpha=alpha,
        num_predictors=num_predictors
    )
    
    # Calculate achieved power with current sample size and observed effect
    achieved_power = calculate_achieved_power(
        n=current_n,
        f2=current_f2,
        alpha=alpha,
        num_predictors=num_predictors
    )
    
    return {
        "current_n": current_n,
        "current_r2": round(current_r2, 4),
        "target_r2": target_r2,
        "target_power": target_power,
        "alpha": alpha,
        "required_n": required_n,
        "achieved_power": round(achieved_power, 4),
        "effect_size_f2": round(current_f2, 4),
        "target_effect_size_f2": round(target_f2, 4),
        "adequate_power": achieved_power >= target_power,
        "recommendation": (
            "Sample size is adequate" if achieved_power >= target_power 
            else f"Consider increasing sample size to at least {required_n}"
        )
    }


def calculate_achieved_power(
    n: int,
    f2: float,
    alpha: float,
    num_predictors: int
) -> float:
    """
    Calculate achieved statistical power given sample size and effect size.
    
    Uses the non-central F-distribution approach for multiple regression.
    
    Args:
        n: Sample size
        f2: Cohen's f² effect size
        alpha: Significance level
        num_predictors: Number of predictors (k)
        
    Returns:
        Achieved power (0-1)
    """
    try:
        from scipy import stats
        
        # Degrees of freedom
        df1 = num_predictors
        df2 = n - num_predictors - 1
        
        if df2 <= 0:
            return 0.0
        
        # Non-centrality parameter
        ncp = f2 * n
        
        # Critical F value
        f_critical = stats.f.ppf(1 - alpha, df1, df2)
        
        # Power = P(F > f_critical | ncp)
        power = 1 - stats.ncf.cdf(f_critical, df1, df2, ncp)
        
        return max(0.0, min(1.0, power))
        
    except ImportError:
        # Fallback if scipy not available (should not happen given requirements)
        return 0.5


def save_results(
    model_results: Dict[str, Any],
    power_analysis_results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Append power analysis results to model results and save.
    
    Args:
        model_results: Existing model results dictionary
        power_analysis_results: Power analysis results dictionary
        output_path: Path to save the updated results
    """
    # Ensure power analysis section exists
    if "power_analysis" not in model_results:
        model_results["power_analysis"] = {}
    
    # Update with new power analysis results
    model_results["power_analysis"].update(power_analysis_results)
    
    # Ensure output directory exists
    ensure_dirs(output_path)
    
    # Save updated results
    with open(output_path, 'w') as f:
        json.dump(model_results, f, indent=2)
    
    print(f"Power analysis results saved to: {output_path}")


def main():
    """Main entry point for post-hoc power analysis."""
    parser = argparse.ArgumentParser(
        description="Perform post-hoc power analysis for EEG-RT prediction model"
    )
    parser.add_argument(
        "--target-r2",
        type=float,
        default=0.10,
        help="Target R² value to detect (default: 0.10)"
    )
    parser.add_argument(
        "--target-power",
        type=float,
        default=0.80,
        help="Target statistical power (default: 0.80)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)"
    )
    parser.add_argument(
        "--num-predictors",
        type=int,
        default=6,
        help="Number of predictors (default: 6 bands)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load existing model results
        print("Loading model results...")
        model_results = load_model_results()
        
        # Extract current sample size and R²
        # Try to get from modeling results
        current_n = model_results.get("n", 0)
        current_r2 = model_results.get("adjusted_r2", model_results.get("r2", 0.0))
        
        if current_n == 0:
            # Try to infer from features if available
            features_path = get_path("processed", "features.csv")
            if features_path.exists():
                import pandas as pd
                features_df = pd.read_csv(features_path)
                current_n = len(features_df)
                print(f"Inferred sample size from features: {current_n}")
            else:
                raise ValueError(
                    "Could not determine sample size. "
                    "Ensure 'n' is present in model_results.json or "
                    "features.csv exists."
                )
        
        if current_r2 == 0.0:
            raise ValueError(
                "Could not determine R² value from model results. "
                "Ensure 'adjusted_r2' or 'r2' is present in model_results.json."
            )
        
        print(f"Current sample size: {current_n}")
        print(f"Current adjusted R²: {current_r2:.4f}")
        
        # Perform power analysis
        print(f"Performing power analysis for target R²={args.target_r2}, "
              f"power={args.target_power}...")
        
        power_results = perform_power_analysis(
            current_n=current_n,
            current_r2=current_r2,
            target_r2=args.target_r2,
            target_power=args.target_power,
            alpha=args.alpha,
            num_predictors=args.num_predictors
        )
        
        print(f"Required sample size for target power: {power_results['required_n']}")
        print(f"Achieved power with current sample: {power_results['achieved_power']:.4f}")
        
        # Save results
        output_path = get_path("processed", "model_results.json")
        save_results(model_results, power_results, output_path)
        
        print("\nPower analysis completed successfully!")
        print(f"Recommendation: {power_results['recommendation']}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
