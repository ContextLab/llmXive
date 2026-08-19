"""Generate a comprehensive PDF report for the sustainable‑agriculture analysis.

The script pulls together:
  * Descriptive statistics from the cleaned survey data
  * The logistic‑regression summary
  * VIF diagnostics
  * ROC curve (with AUC)
  * Mediation‑analysis results
  * Validity‑metric summary (Cronbach’s α, factor loadings, convergent validity)

All artefacts are written under the ``results/`` directory; the final PDF is
``results/report.pdf``.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import yaml

from logging_config import log_operation, update_log_section
from config import (
    get_processed_data_path,
    get_results_path,
    get_figures_path,
)


# --------------------------------------------------------------------------- #
# Helper loading functions – each returns a concrete Python object
# --------------------------------------------------------------------------- #
@log_operation("load_cleaned_data")
def load_cleaned_data() -> pd.DataFrame:
    path = get_processed_data_path() / "cleaned_data.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned data not found at {path}")
    return pd.read_csv(path)


@log_operation("load_engineered_data")
def load_engineered_data() -> pd.DataFrame:
    path = get_processed_data_path() / "engineered_data.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Engineered data not found at {path}")
    return pd.read_csv(path)


@log_operation("load_model_results")
def load_model_results() -> dict:
    path = get_results_path() / "regression_summary.json"
    if not path.is_file():
        raise FileNotFoundError(f"Regression summary not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@log_operation("load_vif")
def load_vif() -> dict:
    path = get_results_path() / "vif.json"
    if not path.is_file():
        raise FileNotFoundError(f"VIF file not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@log_operation("load_roc")
def load_roc() -> dict:
    """Expected JSON structure: {'fpr': [...], 'tpr': [...], 'auc': float}."""
    path = get_results_path() / "roc_metrics.json"
    if not path.is_file():
        raise FileNotFoundError(f"ROC metrics not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@log_operation("load_mediation_results")
def load_mediation_results() -> dict:
    path = get_results_path() / "mediation_results.json"
    if not path.is_file():
        raise FileNotFoundError(f"Mediation results not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@log_operation("load_validity_metrics")
def load_validity_metrics() -> dict:
    path = get_results_path() / "validity_metrics.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Validity metrics not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------------------------------------------------------- #
# Report sections – each returns a string (or creates a figure) that can be
# embedded into the PDF.
# --------------------------------------------------------------------------- #
def generate_report_header() -> str:
    """Simple header containing project name and generation timestamp."""
    from datetime import datetime

    header = {
        "project": "Adoption of Sustainable Agricultural Practices",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    return json.dumps(header, indent=2)


def generate_descriptive_stats(df: pd.DataFrame) -> str:
    """Return a nicely formatted descriptive‑statistics table."""
    desc = df.describe(include="all")
    # Convert to string while preserving column alignment.
    return desc.to_string()


def generate_regression_table(reg_summary: dict) -> str:
    """Pretty‑print the regression summary (as stored in JSON)."""
    # The JSON is assumed to follow statsmodels' summary_json format.
    # We will flatten the most relevant fields for readability.
    lines = []
    lines.append("Logistic Regression Results")
    lines.append("-" * 30)
    for term in reg_summary.get("coefficients", []):
        name = term.get("name", "")
        coef = term.get("coef", "")
        std_err = term.get("std_err", "")
        z = term.get("z", "")
        p = term.get("pvalue", "")
        lines.append(
            f"{name:30s} {coef:>10.4f} {std_err:>10.4f} {z:>10.4f} {p:>10.4f}"
        )
    lines.append("")
    lines.append(f"Pseudo R-squared: {reg_summary.get('pseudo_r2', 'N/A')}")
    lines.append(f"Log‑likelihood : {reg_summary.get('llf', 'N/A')}")
    return "\n".join(lines)


def generate_vif_section(vif_dict: dict) -> str:
    lines = ["Variance Inflation Factor (VIF) Diagnostics", "-" * 40]
    for var, vif in vif_dict.items():
        lines.append(f"{var:30s}: {vif:.2f}")
    return "\n".join(lines)


def generate_roc_section(pdf: PdfPages, roc_dict: dict) -> None:
    """Add a ROC plot page to the PDF."""
    fpr = roc_dict.get("fpr", [])
    tpr = roc_dict.get("tpr", [])
    auc = roc_dict.get("auc", None)

    plt.figure(figsize=(6, 6))
    plt.plot(fpr, tpr, label=f"ROC curve (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], "k--", label="Random guess")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic")
    plt.legend(loc="lower right")
    pdf.savefig()
    plt.close()


def generate_mediation_section(med_dict: dict) -> str:
    """Render mediation analysis results as plain text."""
    lines = ["Mediation Analysis (Baron & Kenny)", "-" * 35]
    # Expected keys: 'total_effect', 'direct_effect', 'indirect_effect',
    # 'boot_ci_lower', 'boot_ci_upper', 'e_value', 'rosenbaum_gamma'.
    lines.append(f"Total effect      : {med_dict.get('total_effect', 'NA')}")
    lines.append(f"Direct effect     : {med_dict.get('direct_effect', 'NA')}")
    lines.append(f"Indirect effect   : {med_dict.get('indirect_effect', 'NA')}")
    lines.append(
        f"Bootstrap 95% CI : [{med_dict.get('boot_ci_lower', 'NA')}, {med_dict.get('boot_ci_upper', 'NA')}]"
    )
    lines.append(f"E‑value           : {med_dict.get('e_value', 'NA')}")
    lines.append(f"Rosenbaum gamma   : {med_dict.get('rosenbaum_gamma', 'NA')}")
    lines.append("")
    lines.append(
        "Interpretation: exploratory mediation – results should be treated as hypothesis‑generating."
    )
    return "\n".join(lines)


def generate_validity_section(validity_dict: dict) -> str:
    """Summarise reliability and factor‑analysis metrics."""
    lines = ["Validity Metrics", "-" * 20]
    alpha = validity_dict.get("cronbach_alpha")
    if alpha is not None:
        lines.append(f"Cronbach's α: {alpha:.3f}")

    efa = validity_dict.get("efa", {})
    if efa:
        lines.append("\nExploratory Factor Analysis (EFA)")
        loadings = efa.get("loadings", {})
        for factor, items in loadings.items():
            lines.append(f"Factor {factor}:")
            for var, loading in items.items():
                lines.append(f"  {var:30s} {loading:.3f}")
        eigenvalues = efa.get("eigenvalues", {})
        if eigenvalues:
            lines.append("\nEigenvalues > 1 (Kaiser’s rule):")
            for factor, ev in eigenvalues.items():
                lines.append(f"  Factor {factor}: {ev:.3f}")

    conv = validity_dict.get("convergent_validity")
    if conv:
        lines.append("\nConvergent Validity")
        for name, corr in conv.items():
            lines.append(f"{name:30s}: {corr:.3f}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main orchestration – builds the PDF page‑by‑page.
# --------------------------------------------------------------------------- #
@log_operation("generate_report")
def generate_report() -> None:
    """Create ``results/report.pdf`` with all required sections."""
    # Load all artefacts; any missing file will raise an informative error.
    cleaned_df = load_cleaned_data()
    engineered_df = load_engineered_data()
    reg_summary = load_model_results()
    vif = load_vif()
    roc = load_roc()
    mediation = load_mediation_results()
    validity = load_validity_metrics()

    report_path = get_results_path() / "report.pdf"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(report_path) as pdf:
        # 1. Header
        _add_text_page(pdf, "Report Header", generate_report_header())

        # 2. Descriptive statistics (cleaned data)
        _add_text_page(
            pdf,
            "Descriptive Statistics (Cleaned Data)",
            generate_descriptive_stats(cleaned_df),
        )

        # 3. Regression table
        _add_text_page(
            pdf, "Logistic Regression Results", generate_regression_table(reg_summary)
        )

        # 4. VIF diagnostics
        _add_text_page(pdf, "VIF Diagnostics", generate_vif_section(vif))

        # 5. ROC curve (figure)
        generate_roc_section(pdf, roc)

        # 6. Mediation analysis (text)
        _add_text_page(pdf, "Mediation Analysis", generate_mediation_section(mediation))

        # 7. Validity metrics (text)
        _add_text_page(pdf, "Validity Metrics", generate_validity_section(validity))

    # Record the successful creation in the modelling log.
    update_log_section("report_generated", {"path": str(report_path)})
    print(f"Report written to {report_path}", file=sys.stderr)


def _add_text_page(pdf: PdfPages, title: str, content: str) -> None:
    """Utility to add a single‑page text block to the PDF."""
    plt.figure(figsize=(8.5, 11))
    plt.axis("off")
    plt.title(title, fontsize=14, loc="left", weight="bold")
    # ``content`` may be long; we use ``text`` with multiline support.
    plt.text(
        0.01,
        0.95,
        content,
        fontsize=9,
        verticalalignment="top",
        wrap=True,
        family="monospace",
    )
    pdf.savefig()
    plt.close()


def main() -> None:
    """Entry‑point for ``python code/05_generate_report.py``."""
    generate_report()


if __name__ == "__main__":
    main()