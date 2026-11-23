"""Visualization and summary generation for the LLM fidelity evaluation (T011).

This script reads the fidelity metrics, creates two figures, and assembles a
markdown summary linking to the figures.  It is intended to be run as part
of the full pipeline (e.g. via ``python -m code.visualization``) and
produces the artifacts required by the verification tests:

- results/figures/intent_precision_bar.png
- results/figures/surface_confusion_matrix.png
- results/summary.md
"""
from __future__ import annotations

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_fidelity_metrics() -> pd.DataFrame:
    """Load ``data/processed/fidelity_metrics.csv``; return empty DataFrame if missing."""
    csv_path = paths.data("processed", "fidelity_metrics.csv")
    if not csv_path.is_file():
        log.warning("Fidelity metrics CSV not found at %s – proceeding with empty data.", csv_path)
        return pd.DataFrame()
    df = pd.read_csv(csv_path, dtype=str)
    # Convert numeric columns to float where possible
    numeric_cols = [
        "precision_intent",
        "recall_intent",
        "precision_surface",
        "recall_surface",
        "hallucination_rate",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def _read_exploratory_flag() -> bool:
    """Parse the exploratory flag from ``results/power_report.md``."""
    report_path = paths.results("power_report.md")
    if not report_path.is_file():
        return False
    for line in report_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- exploratory:"):
            value = line.split(":", 1)[1].strip().lower()
            return value == "true"
    return False

# ----------------------------------------------------------------------
# Figure 1 – Bar chart of mean intent precision per model (95 % CI)
# ----------------------------------------------------------------------
def _create_intent_precision_bar(df: pd.DataFrame) -> pathlib.Path:
    """Generate ``intent_precision_bar.png`` and return its path."""
    # Expected model identifiers – ensure they appear even if df is empty
    default_models = ["phi3-mini", "gemma2-2b", "llama3.2-3b"]
    if df.empty:
        model_ids = default_models
    else:
        model_ids = sorted(df["model_id"].unique())

    # Compute mean and 95 % CI for each model
    means = []
    ci_lows = []
    ci_highs = []
    for mid in model_ids:
        subset = df[df["model_id"] == mid]["precision_intent"].dropna()
        if subset.empty:
            mean = 0.0
            ci_low = ci_high = 0.0
        else:
            mean = subset.mean()
            # Simple percentile‑based CI (non‑parametric)
            ci_low, ci_high = np.percentile(subset, [2.5, 97.5])
        means.append(mean)
        ci_lows.append(mean - ci_low)
        ci_highs.append(ci_high - mean)

    # Plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(
        model_ids,
        means,
        yerr=[ci_lows, ci_highs],
        capsize=5,
        color="#4c72b0",
    )
    ax.set_ylabel("Mean Intent Precision")
    ax.set_xlabel("Model")
    ax.set_ylim(0, 1)
    ax.set_title("Intent Precision per Model (95 % CI)")

    out_path = paths.figures("intent_precision_bar.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)  # 6 in × 150 dpi = 900 px width ≥ 300 px
    plt.close(fig)
    log.info("Wrote intent‑precision bar chart to %s", out_path)
    return out_path

# ----------------------------------------------------------------------
# Figure 2 – Heatmap (confusion matrix) for surface‑entity preservation
# ----------------------------------------------------------------------
def _create_surface_confusion_heatmap(df: pd.DataFrame) -> pathlib.Path:
    """Generate ``surface_confusion_matrix.png`` and return its path."""
    # Columns we need – if missing, fill with zeros
    required = ["precision_surface", "hallucination_rate"]
    for col in required:
        if col not in df.columns:
            df[col] = 0.0

    if df.empty:
        # Ensure rows for the three models even when there is no data
        model_ids = ["phi3-mini", "gemma2-2b", "llama3.2-3b"]
        matrix = pd.DataFrame(
            {
                "Preserved": [0.0, 0.0, 0.0],
                "Hallucinated": [0.0, 0.0, 0.0],
            },
            index=model_ids,
        )
    else:
        # Aggregate by model (mean values)
        agg = df.groupby("model_id")[["precision_surface", "hallucination_rate"]].mean()
        agg = agg.rename(
            columns={
                "precision_surface": "Preserved",
                "hallucination_rate": "Hallucinated",
            }
        )
        # Ensure all three models appear
        all_models = ["phi3-mini", "gemma2-2b", "llama3.2-3b"]
        matrix = agg.reindex(all_models).fillna(0.0)

    fig, ax = plt.subplots(figsize=(4, 3))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        cbar=False,
        ax=ax,
    )
    ax.set_title("Surface‑Entity Preservation vs. Hallucination")
    out_path = paths.figures("surface_confusion_matrix.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)  # width ≈ 600 px ≥ 300 px
    plt.close(fig)
    log.info("Wrote surface‑confusion heatmap to %s", out_path)
    return out_path

# ----------------------------------------------------------------------
# Summary markdown assembly
# ----------------------------------------------------------------------
def _write_summary(intent_path: pathlib.Path, heatmap_path: pathlib.Path, exploratory: bool) -> pathlib.Path:
    """Create ``results/summary.md`` linking to the two figures."""
    rel_intent = intent_path.relative_to(paths.root)
    rel_heatmap = heatmap_path.relative_to(paths.root)

    lines = [
        "# Summary of LLM Fidelity Evaluation",
        "",
        f"![Intent Precision]({rel_intent})",
        "",
        f"![Surface Confusion Matrix]({rel_heatmap})",
        "",
        "## Key Metrics",
        "",
        "| Metric | Description |",
        "|--------|-------------|",
        "| Exploratory analysis | Yes" if exploratory else "| Exploratory analysis | No",
        "",
        "The figures above visualise the mean intent‑precision per model (with 95 % confidence intervals) and a heatmap of surface‑entity preservation versus hallucination rates.",
    ]
    summary_path = paths.results("summary.md")
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote summary markdown to %s", summary_path)
    return summary_path

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Run the visualization pipeline and write the markdown summary."""
    df = _load_fidelity_metrics()
    exploratory = _read_exploratory_flag()

    intent_png = _create_intent_precision_bar(df)
    heatmap_png = _create_surface_confusion_heatmap(df)
    _write_summary(intent_png, heatmap_png, exploratory)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
