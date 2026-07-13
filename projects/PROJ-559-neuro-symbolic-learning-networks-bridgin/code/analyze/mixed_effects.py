"""
Mixed-effects regression analysis for neuro-symbolic learning experiments.

Implements FR-006 and FR-011:
- Fixed effects: condition, prior_knowledge, difficulty, data_source
- Random intercepts: student_id
- CPU-only execution using statsmodels
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# Project relative imports (assuming run from project root or code/)
try:
    from utils.validation import validate_batch
except ImportError:
    # Fallback for direct execution testing
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.validation import validate_batch

logger = logging.getLogger(__name__)

# Constants
DEFAULT_INPUT_PATH = "data/derived/simulation_logs.csv"
DEFAULT_OUTPUT_PATH = "data/derived/mixed_effects_results.json"
DEFAULT_RESULTS_TABLE_PATH = "data/derived/mixed_effects_table.csv"

# Required columns for the input data
REQUIRED_COLUMNS = [
    'student_id', 'condition', 'prior_knowledge', 'difficulty',
    'data_source', 'correct', 'rt_seconds', 'comprehension_rating'
]

def load_data(input_path: str) -> pd.DataFrame:
    """
    Load simulation logs from CSV.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        DataFrame containing the simulation logs.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Validate columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Validate data types
    df['prior_knowledge'] = pd.to_numeric(df['prior_knowledge'], errors='coerce')
    df['difficulty'] = pd.to_numeric(df['difficulty'], errors='coerce')
    df['correct'] = pd.to_numeric(df['correct'], errors='coerce')
    df['rt_seconds'] = pd.to_numeric(df['rt_seconds'], errors='coerce')
    df['comprehension_rating'] = pd.to_numeric(df['comprehension_rating'], errors='coerce')

    # Drop rows with NaN in critical columns
    df = df.dropna(subset=['prior_knowledge', 'difficulty', 'correct', 'rt_seconds', 'comprehension_rating'])

    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def run_mixed_effects_model(
    df: pd.DataFrame,
    dependent_var: str = 'comprehension_rating',
    output_path: Optional[str] = None,
    table_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run mixed-effects regression analysis.

    Model formula:
    dependent_var ~ condition + prior_knowledge + difficulty + data_source + (1|student_id)

    Args:
        df: Input DataFrame.
        dependent_var: The dependent variable for the regression.
        output_path: Path to save the full results JSON.
        table_path: Path to save the regression table CSV.

    Returns:
        Dictionary containing model results and statistics.
    """
    # Ensure categorical variables are treated as such
    df['condition'] = df['condition'].astype('category')
    df['data_source'] = df['data_source'].astype('category')
    df['student_id'] = df['student_id'].astype('category')

    # Formula for mixed-effects model
    # Using 'C()' to explicitly treat condition and data_source as categorical
    formula = f"{dependent_var} ~ C(condition) + prior_knowledge + difficulty + C(data_source) + (1|student_id)"

    logger.info(f"Running mixed-effects model: {formula}")

    try:
        # Fit the model using statsmodels
        # Note: statsmodels MixedLM requires the group column to be in the data
        model = smf.mixedlm(formula, df, groups=df["student_id"])
        result = model.fit()

    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

    # Extract results
    results_dict = {
        "model_formula": formula,
        "dependent_variable": dependent_var,
        "num_observations": len(df),
        "num_groups": df['student_id'].nunique(),
        "converged": result.converged,
        "log_likelihood": result.llf,
        "aic": result.aic,
        "bic": result.bic,
        "fixed_effects": {},
        "random_effects": {},
        "p_values": {}
    }

    # Process fixed effects
    for param_name, param_val in result.params.items():
        if param_name.startswith("C(condition)"):
            results_dict["fixed_effects"][param_name] = float(param_val)
            results_dict["p_values"][param_name] = float(result.pvalues[param_name])
        elif param_name.startswith("C(data_source)"):
            results_dict["fixed_effects"][param_name] = float(param_val)
            results_dict["p_values"][param_name] = float(result.pvalues[param_name])
        elif param_name in ["prior_knowledge", "difficulty", "Intercept"]:
            results_dict["fixed_effects"][param_name] = float(param_val)
            results_dict["p_values"][param_name] = float(result.pvalues[param_name])

    # Process random effects (variance components)
    if hasattr(result, 'var_re') and result.var_re is not None:
        results_dict["random_effects"] = {k: float(v) for k, v in result.var_re.items()}

    # Save full results to JSON if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)
        logger.info(f"Saved full results to {output_path}")

    # Save regression table to CSV if path provided
    if table_path:
        os.makedirs(os.path.dirname(table_path), exist_ok=True)
        # Create a summary DataFrame for the table
        table_data = []
        for param_name, param_val in result.params.items():
            table_data.append({
                "parameter": param_name,
                "estimate": float(param_val),
                "std_err": float(result.bse[param_name]),
                "z_value": float(result.tvalues[param_name]),
                "p_value": float(result.pvalues[param_name]),
                "conf_int_lower": float(result.conf_int().loc[param_name, 0]),
                "conf_int_upper": float(result.conf_int().loc[param_name, 1])
            })

        table_df = pd.DataFrame(table_data)
        table_df.to_csv(table_path, index=False)
        logger.info(f"Saved regression table to {table_path}")

    return results_dict

def run_pairwise_comparisons(
    df: pd.DataFrame,
    dependent_var: str = 'comprehension_rating',
    group_var: str = 'condition'
) -> Dict[str, Any]:
    """
    Run Tukey HSD pairwise comparisons for conditions.

    Args:
        df: Input DataFrame.
        dependent_var: The dependent variable.
        group_var: The grouping variable (condition).

    Returns:
        Dictionary containing pairwise comparison results.
    """
    logger.info(f"Running pairwise comparisons for {group_var} on {dependent_var}")

    try:
        tukey = pairwise_tukeyhsd(endog=df[dependent_var], groups=df[group_var], alpha=0.05)
        results = {
            "method": "Tukey HSD",
            "alpha": 0.05,
            "comparisons": []
        }

        # Extract comparison data
        for row in tukey.result_frame:
            results["comparisons"].append({
                "group1": str(row[0]),
                "group2": str(row[1]),
                "mean_diff": float(row[2]),
                "lower": float(row[3]),
                "upper": float(row[4]),
                "reject": bool(row[5])
            })

        return results
    except Exception as e:
        logger.error(f"Pairwise comparison failed: {e}")
        return {"error": str(e)}

def main():
    """Main entry point for the mixed effects analysis."""
    parser = argparse.ArgumentParser(description="Run mixed-effects regression analysis")
    parser.add_argument(
        "--input",
        type=str,
        default=DEFAULT_INPUT_PATH,
        help=f"Path to input CSV (default: {DEFAULT_INPUT_PATH})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to output JSON (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--table",
        type=str,
        default=DEFAULT_RESULTS_TABLE_PATH,
        help=f"Path to output table CSV (default: {DEFAULT_RESULTS_TABLE_PATH})"
    )
    parser.add_argument(
        "--dependent-var",
        type=str,
        default="comprehension_rating",
        help="Dependent variable for the model (default: comprehension_rating)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Load data
        df = load_data(args.input)

        # Run mixed effects model
        results = run_mixed_effects_model(
            df,
            dependent_var=args.dependent_var,
            output_path=args.output,
            table_path=args.table
        )

        # Run pairwise comparisons
        pairwise_results = run_pairwise_comparisons(df, args.dependent_var)

        # Combine results
        final_results = {
            "mixed_effects": results,
            "pairwise_comparisons": pairwise_results
        }

        # Save combined results
        combined_output_path = args.output.replace('.json', '_full.json')
        with open(combined_output_path, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)

        print(f"Analysis complete. Results saved to:")
        print(f"  - {args.output}")
        print(f"  - {args.table}")
        print(f"  - {combined_output_path}")

        return 0

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
