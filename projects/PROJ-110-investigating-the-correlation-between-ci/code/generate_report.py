"""
generate_report.py

This script generates the final diagnostic report (`docs/report.md`) summarising
the key scientific compliance (SC) outcomes for the project:

- SC‑001: Classification proportion (from T018)
- SC‑002: Number of significant differentially expressed (DE) genes (from T026)
- SC‑003: Cross‑validation performance (average AUC with 95 % CI) (from T036)
- SC‑004: Number of significant correlations (from T050)
- SC‑005: Classification agreement rate (from T042)

The script reads the artefacts produced by the respective pipeline stages,
aggregates the required metrics and writes a human‑readable markdown report to
`docs/report.md`.

It is intended to be executed as:
    python code/generate_report.py

The script will raise a clear exception if any required input file is missing,
ensuring that the pipeline fails loudly rather than silently fabricating results.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from utils.logging import get_logger

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its content."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def find_file(pattern: str, base_dir: Path) -> Path:
    """Return the first file matching *pattern* under *base_dir*.

    Raises:
        FileNotFoundError: if no matching file is found.
    """
    matches = list(base_dir.rglob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file matching pattern '{pattern}' under {base_dir}")
    # deterministic: sort and pick first
    matches.sort()
    return matches[0]

# --------------------------------------------------------------------------- #
# Main report generation
# --------------------------------------------------------------------------- #

def generate_report() -> None:
    logger = get_logger(__name__)

    # Base directories
    processed_dir = Path("data/processed")
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------- #
    # SC‑001 – Classification proportion
    # ------------------------------------------------------------------- #
    proportion_path = processed_dir / "classification_proportion.json"
    if not proportion_path.is_file():
        raise FileNotFoundError(f"Expected classification proportion file not found: {proportion_path}")
    prop_data = load_json(proportion_path)
    proportion = prop_data.get("proportion")
    total_donors = prop_data.get("total_donors")
    classified_donors = prop_data.get("classified_donors")

    logger.info("Loaded classification proportion: %.3f ( %d / %d )",
                proportion, classified_donors, total_donors)

    # ------------------------------------------------------------------- #
    # SC‑005 – Classification agreement rate (from sensitivity analysis)
    # ------------------------------------------------------------------- #
    sensitivity_path = processed_dir / "sensitivity_metric.json"
    if not sensitivity_path.is_file():
        raise FileNotFoundError(f"Sensitivity metric file not found: {sensitivity_path}")
    sensitivity_data = load_json(sensitivity_path)
    agreement_rate = sensitivity_data.get("classification_agreement_rate")
    delta_prevalence = sensitivity_data.get("delta_prevalence")

    logger.info("Loaded agreement rate: %.2f%%, delta prevalence: %.4f",
                agreement_rate * 100 if agreement_rate is not None else None,
                delta_prevalence)

    # ------------------------------------------------------------------- #
    # SC‑002 – Significant DE genes (FDR < 0.05)
    # ------------------------------------------------------------------- #
    # T026 writes a FDR‑corrected DE table; we look for a CSV file containing
    # the term "de" and "fdr" in its name.
    try:
        de_fdr_path = find_file("*de*fdr*.csv", processed_dir)
    except FileNotFoundError as e:
        raise FileNotFoundError("DE FDR‑corrected results not found. Ensure T026 has run.") from e

    de_df = pd.read_csv(de_fdr_path)
    if "fdr" not in de_df.columns:
        raise KeyError(f"The DE results file {de_fdr_path} must contain an 'fdr' column.")
    sig_de_genes = de_df[de_df["fdr"] < 0.05]
    n_sig_de = sig_de_genes.shape[0]

    logger.info("Found %d significant DE genes (FDR < 0.05) in %s", n_sig_de, de_fdr_path.name)

    # ------------------------------------------------------------------- #
    # SC‑004 – Significant correlations (FDR < 0.05)
    # ------------------------------------------------------------------- #
    try:
        corr_fdr_path = find_file("*correlation*fdr*.csv", processed_dir)
    except FileNotFoundError as e:
        raise FileNotFoundError("Correlation FDR‑corrected results not found. Ensure T050 has run.") from e

    corr_df = pd.read_csv(corr_fdr_path)
    if "fdr" not in corr_df.columns:
        raise KeyError(f"The correlation results file {corr_fdr_path} must contain an 'fdr' column.")
    sig_corr = corr_df[corr_df["fdr"] < 0.05]
    n_sig_corr = sig_corr.shape[0]

    logger.info("Found %d significant correlations (FDR < 0.05) in %s", n_sig_corr, corr_fdr_path.name)

    # ------------------------------------------------------------------- #
    # SC‑003 – Cross‑validation AUC (mean and 95 % CI)
    # ------------------------------------------------------------------- #
    cv_metrics_path = processed_dir / "cv_metrics.json"
    if not cv_metrics_path.is_file():
        raise FileNotFoundError(f"Cross‑validation metrics file not found: {cv_metrics_path}")
    cv_metrics = load_json(cv_metrics_path)
    mean_auc = cv_metrics.get("mean_auc")
    ci_lower = cv_metrics.get("ci_lower")
    ci_upper = cv_metrics.get("ci_upper")

    logger.info("CV performance: mean AUC = %.3f (95 %% CI: %.3f‑%.3f)",
                mean_auc, ci_lower, ci_upper)

    # ------------------------------------------------------------------- #
    # Assemble markdown report
    # ------------------------------------------------------------------- #
    report_lines: List[str] = [
        "# Final Diagnostic Report",
        "",
        "This report summarises the key scientific compliance (SC) outcomes "
        "required for the project **PROJ‑110 – Investigating the Correlation "
        "Between Circadian Gene Expression and Metabolic Syndrome Risk**.",
        "",
        "## Summary of Outcomes",
        "",
        "### SC‑001 – Classification Proportion",
        f"- **Proportion of donors classified:** {proportion:.3%} "
        f"({classified_donors} / {total_donors})",
        "",
        "### SC‑002 – Differential Expression (DE) Findings",
        f"- **Number of core circadian genes with significant differential expression** "
        f"(FDR < 0.05): **{n_sig_de}**",
        "",
        "### SC‑003 – Predictive Modeling Performance",
        f"- **Mean AUC (5‑fold CV):** {mean_auc:.3f}",
        f"- **95 % Confidence Interval:** [{ci_lower:.3f}, {ci_upper:.3f}]",
        "",
        "### SC‑004 – Correlation Analysis",
        f"- **Significant gene–trait correlations (FDR < 0.05):** **{n_sig_corr}**",
        "",
        "### SC‑005 – Sensitivity Analysis – Classification Agreement",
        f"- **Agreement Rate:** {agreement_rate:.2%}",
        f"- **Delta in MetS prevalence between baseline and varied thresholds:** "
        f"{delta_prevalence:.4f}",
        "",
        "---",
        "",
        "*All metrics are derived from the latest pipeline run. "
        "Any missing or unexpected values indicate a failure in the corresponding "
        "pipeline stage and should be investigated.*",
        "",
    ]

    report_path = docs_dir / "report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    logger.info("Diagnostic report written to %s", report_path)

# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    generate_report()
