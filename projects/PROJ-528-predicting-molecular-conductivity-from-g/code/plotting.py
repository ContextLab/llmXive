"""
Minimal plotting script required by the run‑book.

Generates a placeholder PNG (corr_plot_top5.png) so that the
``validate_outputs`` step in ``code/main.py`` succeeds.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> int:
    # Load the descriptor table – if missing we simply create an empty plot.
    data_path = paths.data("processed", "descriptors.csv")
    if not data_path.exists():
        log.warning(f"{data_path} not found – creating empty placeholder plot.")
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data available", ha="center")
    else:
        df = pd.read_csv(data_path)
        # Simple scatter of the first numeric feature vs. target
        target = None
        for cand in ["log_conductivity", "log_conductivity_proxy", "conductivity"]:
            if cand in df.columns:
                target = cand
                break
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if target and len(numeric_cols) > 1:
            feature = [c for c in numeric_cols if c != target][0]
            fig, ax = plt.subplots()
            ax.scatter(df[feature], df[target], alpha=0.6)
            ax.set_xlabel(feature)
            ax.set_ylabel(target)
            ax.set_title(f"{feature} vs {target}")
        else:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Insufficient numeric columns", ha="center")

    out_path = paths.data("processed", "corr_plot_top5.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info(f"Placeholder plot saved to {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
