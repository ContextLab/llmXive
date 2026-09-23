"""
Main entry point for the Imputation Impact Analysis Pipeline.

Orchestrates the full pipeline including data loading, imputation, variance estimation,
and reporting. Specifically implements the `write_psu1_warnings` functionality for T021.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Import from project modules
from data.loader import fetch_and_validate, check_design_columns
from data.synthetic import generate_synthetic_data
from imputation.psu1_warnings import detect_psu1_clusters, write_psu1_warnings
from imputation_pipeline import run_complete_case_pipeline
from variance.design import run_jackknife_analysis, apply_simplified_estimator
from metrics.bias import calculate_percentage_bias
from analysis import run_sensitivity_sweep, calculate_stability_score

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def load_json(path: str) -> dict:
    """Load a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def write_baseline_summary(results: dict, output_path: str) -> None:
    """
    Serialize baseline results to JSON.
    Schema: { "mean": float, "variance": float, "status": "success"|"failed", "design_type": str }
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Baseline summary written to {output_path}")


def calculate_baseline_stats(data_path: str, output_path: str) -> dict:
    """
    Calculate baseline statistics (mean, variance) for a dataset.
    """
    import pandas as pd
    df = pd.read_csv(data_path)
    # Assuming a numeric column 'value' or similar exists for synthetic data
    # For real data, this would be more complex.
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns found in data.")
        return {"mean": None, "variance": None, "status": "failed", "design_type": "none"}

    col = numeric_cols[0]
    mean_val = df[col].mean()
    var_val = df[col].var()

    result = {
        "mean": float(mean_val),
        "variance": float(var_val),
        "status": "success",
        "design_type": "simple"
    }
    write_baseline_summary(result, output_path)
    return result


def generate_report(results: dict, output_path: str) -> None:
    """Generate a markdown report."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write("# Analysis Report\n\n")
        f.write(f"Generated at: {datetime.now().isoformat()}\n\n")
        f.write("## Findings\n\n")
        f.write("All findings are associational; no causal claims are made.\n")
    logger.info(f"Report written to {output_path}")


def run_psu_check_stage(input_path: str, output_path: str, psu_col: str = "psu") -> int:
    """
    Implement T021: Write PSU=1 Warnings.

    Reads a dataset, detects clusters with PSU size = 1,
    and writes the warnings to a JSON file.
    """
    logger.info(f"Starting PSU=1 check stage on {input_path}")

    try:
        import pandas as pd
        df = pd.read_csv(input_path)

        if psu_col not in df.columns:
            logger.error(f"Missing column: {psu_col}. Cannot perform PSU check.")
            write_psu1_warnings([], output_path, variable_name="unknown")
            return 0

        # Detect
        warnings = detect_psu1_clusters(df, psu_col=psu_col)

        # Write
        var_name = "survey_variable"
        write_psu1_warnings(warnings, output_path, variable_name=var_name)

        return 0

    except Exception as e:
        logger.error(f"PSU check stage failed: {e}")
        return 1


def run_psu_fallback_stage(input_path: str, output_path: str, psu_col: str = "psu", value_col: str = "value") -> int:
    """
    Implement T021b: Apply Simplified Estimator Fallback for PSU=1 clusters.

    Reads a dataset, detects PSU=1 clusters, applies the simplified estimator,
    and logs the result with action_taken: "fallback" in the warnings file.
    """
    logger.info(f"Starting PSU=1 Fallback stage on {input_path}")

    try:
        import pandas as pd
        df = pd.read_csv(input_path)

        if psu_col not in df.columns:
            logger.error(f"Missing column: {psu_col}. Cannot perform fallback.")
            # Write a fallback record indicating failure to apply
            fallback_record = {
                "variable": value_col,
                "psu_count": 0,
                "action_taken": "fallback_failed",
                "reason": f"Missing column: {psu_col}"
            }
            # Append to existing or create new
            warnings_list = []
            if os.path.exists(output_path):
                with open(output_path, "r") as f:
                    try:
                        warnings_list = json.load(f)
                    except json.JSONDecodeError:
                        warnings_list = []
            warnings_list.append(fallback_record)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(warnings_list, f, indent=2)
            return 1

        # Detect PSU=1 clusters
        psu_counts = df[psu_col].value_counts()
        psu_1_clusters = psu_counts[psu_counts == 1].index.tolist()

        if not psu_1_clusters:
            logger.info("No PSU=1 clusters detected. No fallback needed.")
            # Ensure output file exists even if empty
            if not os.path.exists(output_path):
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w") as f:
                    json.dump([], f)
            return 0

        # Apply simplified estimator
        result = apply_simplified_estimator(df, value_col=value_col, psu_col=psu_col)

        if result["status"] != "success":
            logger.warning(f"Simplified estimator failed: {result.get('reason', 'Unknown error')}")
            return 1

        # Prepare warning record
        fallback_record = {
            "variable": value_col,
            "psu_count": len(psu_1_clusters),
            "action_taken": "fallback",
            "variance_estimate": result["variance"],
            "method": result["method"],
            "flag": result.get("flag", "estimated_with_fallback")
        }

        # Append to existing warnings or create new
        warnings_list = []
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                try:
                    warnings_list = json.load(f)
                except json.JSONDecodeError:
                    warnings_list = []

        warnings_list.append(fallback_record)

        # Write back
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(warnings_list, f, indent=2)

        logger.info(f"Fallback applied. Variance estimate: {result['variance']}")
        logger.info(f"Warning record written to {output_path}")

        return 0

    except Exception as e:
        logger.error(f"PSU fallback stage failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Main pipeline orchestrator.")
    parser.add_argument("--stage", type=str, help="Specific stage to run (e.g., baseline, psu_check, psu_fallback).")
    parser.add_argument("--input", type=str, help="Input data path.")
    parser.add_argument("--output", type=str, help="Output path for results.")
    parser.add_argument("--psu-col", type=str, default="psu", help="PSU column name.")
    parser.add_argument("--var-name", type=str, default="value", help="Variable name for analysis.")

    args = parser.parse_args()

    if args.stage == "psu_check":
        if not args.input:
            logger.error("--input is required for psu_check stage.")
            return 1
        if not args.output:
            args.output = "data/processed/psu1_warnings.json"
        return run_psu_check_stage(args.input, args.output, args.psu_col)

    elif args.stage == "psu_fallback":
        if not args.input:
            logger.error("--input is required for psu_fallback stage.")
            return 1
        if not args.output:
            args.output = "data/processed/psu1_warnings.json"
        return run_psu_fallback_stage(args.input, args.output, args.psu_col, args.var_name)

    elif args.stage == "baseline":
        if not args.input:
            logger.error("--input is required for baseline stage.")
            return 1
        if not args.output:
            args.output = "data/processed/baseline_results.json"
        calculate_baseline_stats(args.input, args.output)
        return 0

    else:
        # Default full pipeline or help
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())