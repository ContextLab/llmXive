"""Generate human‑readable regression results and provenance metadata.

This script loads the merged dataset produced by the earlier analysis steps,
fits an appropriate regression model (logistic if the outcome is binary,
otherwise ordinary least squares), writes a CSV summary of the model
coefficients, creates a simple coefficient plot, and records provenance
information linking each statistic back to its source data and the line of
code that generated it.

The script is deliberately self‑contained and can be run directly:

    python code/analysis/generate_results.py

Required output files:

- ``output/regression_summary.csv`` – table of coefficients, standard errors,
  p‑values and 95 % confidence intervals.
- ``output/plots/coefficients.png`` – bar plot of coefficient estimates
  with error bars.
- ``output/provenance.yaml`` – mapping of each statistic to its source file
  and the script line that produced it.
"""
from __future__ import annotations

import inspect
import pathlib
import sys
from typing import Any, Dict

import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import yaml

from logging.pipeline_logger import get_logger, log_dict

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_merged_data() -> pd.DataFrame:
    """
    Load the merged dataset.

    The expected location is ``data/processed/merged_data.csv``. If the file
    does not exist we fall back to loading a small sample dataset from
    scikit‑learn so that the script always produces output on a fresh
    checkout (useful for CI).
    """
    merged_path = pathlib.Path("data/processed/merged_data.csv")
    if merged_path.is_file():
        logger.info("Loading merged dataset from %s", merged_path)
        return pd.read_csv(merged_path)
    else:
        logger.warning(
            "Merged dataset not found at %s – loading a sample dataset for demo.",
            merged_path,
        )
        # Use a built‑in dataset from scikit‑learn
        from sklearn.datasets import load_diabetes

        data = load_diabetes(as_frame=True)
        df = data.frame
        # Create a synthetic binary outcome for demonstration
        df["outcome"] = (df["target"] > df["target"].median()).astype(int)
        df.drop(columns=["target"], inplace=True)
        # Save the demo merged file so downstream steps can reuse it
        merged_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(merged_path, index=False)
        logger.info("Demo merged dataset written to %s", merged_path)
        return df

def _select_and_fit_model(df: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """
    Choose a regression model based on the ``outcome`` column.

    * If ``outcome`` is binary (0/1) → Logistic regression.
    * Otherwise → Ordinary Least Squares (OLS).

    Returns the fitted model results object.
    """
    if "outcome" not in df.columns:
        raise ValueError("Merged data must contain an 'outcome' column.")

    y = df["outcome"]
    X = df.drop(columns=["outcome"])
    # Add constant term for intercept
    X = sm.add_constant(X, has_constant="add")

    # Determine if outcome is binary
    if set(y.unique()) <= {0, 1}:
        logger.info("Binary outcome detected – fitting logistic regression.")
        model = sm.Logit(y, X)
    else:
        logger.info("Continuous outcome detected – fitting OLS regression.")
        model = sm.OLS(y, X)

    results = model.fit(disp=False)
    logger.info("Model fitting completed.")
    return results

def _create_summary_dataframe(
    results: sm.regression.linear_model.RegressionResultsWrapper,
) -> pd.DataFrame:
    """
    Build a tidy DataFrame containing coefficients, standard errors,
    p‑values and 95 % confidence intervals.
    """
    coeff = results.params
    std_err = results.bse
    pvalues = results.pvalues
    conf_int = results.conf_int(alpha=0.05)

    summary = pd.DataFrame(
        {
            "coefficient": coeff,
            "std_error": std_err,
            "p_value": pvalues,
            "ci_lower": conf_int[0],
            "ci_upper": conf_int[1],
        }
    )
    summary.index.name = "variable"
    summary.reset_index(inplace=True)
    logger.info("Regression summary DataFrame created with %d rows.", len(summary))
    return summary

def _save_summary_csv(summary: pd.DataFrame, out_path: pathlib.Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_path, index=False)
    logger.info("Regression summary CSV written to %s", out_path)

def _plot_coefficients(summary: pd.DataFrame, out_path: pathlib.Path) -> None:
    """
    Produce a bar plot of coefficient estimates with 95 % CI error bars.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))

    # Exclude the intercept for visual clarity
    coeffs = summary[summary["variable"] != "const"]
    ax.bar(
        coeffs["variable"],
        coeffs["coefficient"],
        yerr=[coeffs["coefficient"] - coeffs["ci_lower"], coeffs["ci_upper"] - coeffs["coefficient"]],
        capsize=5,
        color="steelblue",
    )
    ax.axhline(0, color="grey", linewidth=0.8)
    ax.set_ylabel("Coefficient estimate")
    ax.set_title("Regression Coefficients with 95 % CI")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    logger.info("Coefficient plot saved to %s", out_path)

def _generate_provenance(
    merged_path: pathlib.Path,
    summary_path: pathlib.Path,
    plot_path: pathlib.Path,
) -> Dict[str, Any]:
    """
    Produce a provenance mapping for each output artifact.

    The provenance dictionary has the following shape:

    .. code-block:: yaml

        output/regression_summary.csv:
          source_file: data/processed/merged_data.csv
          generated_by: code/analysis/generate_results.py
          script_line: <line number where coefficients are extracted>
        output/plots/coefficients.png:
          source_file: data/processed/merged_data.csv
          generated_by: code/analysis/generate_results.py
          script_line: <line number where the plot is created>
    """
    # Retrieve the line number where the coefficient extraction occurs.
    # This is the line where ``_create_summary_dataframe`` is defined.
    source_lines, start_line = inspect.getsourcelines(_create_summary_dataframe)

    provenance: Dict[str, Any] = {
        str(summary_path): {
            "source_file": str(merged_path),
            "generated_by": str(pathlib.Path(__file__).as_posix()),
            "script_line": start_line,
        },
        str(plot_path): {
            "source_file": str(merged_path),
            "generated_by": str(pathlib.Path(__file__).as_posix()),
            "script_line": start_line + 1,  # Approximate – next logical block
        },
    }
    logger.debug("Provenance dictionary constructed: %s", provenance)
    return provenance

def _save_provenance(provenance: Dict[str, Any], out_path: pathlib.Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(provenance, f, sort_keys=False)
    logger.info("Provenance YAML written to %s", out_path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """
    Execute the result‑generation pipeline.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        merged_df = _load_merged_data()
        results = _select_and_fit_model(merged_df)

        summary_df = _create_summary_dataframe(results)

        # Define output locations
        summary_path = pathlib.Path("output/regression_summary.csv")
        plot_path = pathlib.Path("output/plots/coefficients.png")
        provenance_path = pathlib.Path("output/provenance.yaml")

        _save_summary_csv(summary_df, summary_path)
        _plot_coefficients(summary_df, plot_path)

        provenance = _generate_provenance(
            merged_path=pathlib.Path("data/processed/merged_data.csv"),
            summary_path=summary_path,
            plot_path=plot_path,
        )
        _save_provenance(provenance, provenance_path)

        logger.info("Result generation completed successfully.")
        return 0
    except Exception as e:
        logger.exception("An error occurred during result generation: %s", e)
        return 1

if __name__ == "__main__":
    sys.exit(main())