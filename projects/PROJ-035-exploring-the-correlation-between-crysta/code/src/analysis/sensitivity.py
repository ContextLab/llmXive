"""
Sensitivity Analysis Module for P-value Threshold Evaluation.

Performs sensitivity analysis across varying significance levels
to assess robustness of correlation findings.
"""
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.seed_manager import init_seed, add_seed_argument, get_seed
from src.utils.validation import setup_logger

logger = setup_logger("sensitivity")


def setup_logger_module(name: str = "sensitivity") -> logging.Logger:
    """Setup module logger."""
    return setup_logger(name)


def run_sensitivity_analysis(
    df: pd.DataFrame,
    predictors: List[str],
    target: str = "thermal_conductivity",
    p_thresholds: List[float] = [0.01, 0.05, 0.1],
    seed: Optional[int] = None
) -> Dict[str, Dict[str, float]]:
    """
    Run sensitivity analysis across different p-value thresholds.

    Args:
        df: Input DataFrame
        predictors: Predictor variables
        target: Target variable
        p_thresholds: List of p-value thresholds to test
        seed: Random seed

    Returns:
        Dictionary of sensitivity results keyed by threshold
    """
    if seed is not None:
        init_seed(seed)

    logger.info(f"Running sensitivity analysis with thresholds {p_thresholds}, seed={get_seed()}")

    results = {}

    for threshold in p_thresholds:
        # Compute correlations with p-values
        data = df[predictors + [target]].dropna()
        pearson_corr = data.corr(method='pearson')

        # Approximate p-values (simplified - in real implementation use scipy.stats)
        # This is a placeholder for actual p-value computation
        n = len(data)
        p_values = {}

        for pred in predictors:
            r = pearson_corr.loc[target, pred]
            if not np.isnan(r):
                # t-statistic approximation
                t_stat = r * np.sqrt((n - 2) / (1 - r**2 + 1e-10))
                # Two-tailed p-value approximation
                from scipy import stats
                p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
                p_values[pred] = float(p_val)
            else:
                p_values[pred] = np.nan

        significant = {k: v for k, v in p_values.items() if v < threshold and not np.isnan(v)}

        results[str(threshold)] = {
            "p_values": p_values,
            "significant_count": len(significant),
            "significant_predictors": list(significant.keys())
        }

    return results


def save_sensitivity_report(results: Dict, output_path: Path) -> None:
    """
    Save sensitivity analysis report to JSON.

    Args:
        results: Results dictionary
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved sensitivity report to {output_path}")


def main():
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on p-value thresholds"
    )
    parser = add_seed_argument(parser)
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help="Input CSV file"
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path("data/results/sensitivity_analysis.json"),
        help="Output JSON file"
    )
    parser.add_argument(
        '--predictors',
        nargs='+',
        default=['tolerance_factor', 'bond_length_variance', 'unit_cell_volume'],
        help="Predictor columns"
    )
    parser.add_argument(
        '--target',
        default='thermal_conductivity',
        help="Target column"
    )

    args = parser.parse_args()

    # Initialize seed
    init_seed(args.seed)
    logger.info(f"Initialized seed: {get_seed()}")

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    df = pd.read_csv(args.input)

    results = run_sensitivity_analysis(
        df,
        predictors=args.predictors,
        target=args.target,
        seed=args.seed
    )

    save_sensitivity_report(results, args.output)
    logger.info("Sensitivity analysis complete")


if __name__ == "__main__":
    main()
