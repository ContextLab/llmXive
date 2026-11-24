"""
Visualization module for the solar wind – geomagnetic correlation project.

Generates:
  1. Time‑series overlay plots for each composition parameter vs. each
     geomagnetic index at each lag (0, 1, 2, 3, 6 h) over the validation
     period (2018‑01‑01 → 2020‑12‑31).
  2. Heatmaps of Pearson correlation magnitude (rows = composition
     parameters, columns = lags) for the full analysis results and for the
     validation results.

All PNGs are written under the project ``figures/`` directory and are
constrained to ≤ 5 MB by using a moderate DPI.
"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from llmxive_toolkit import paths, get_logger
from code.config import (
    ACE_VARS,
    NOAA_VARS,
    LAGS_HOURS,
    TEST_START,
    TEST_END,
)
from code.analysis.correlation import (
    load_synced_data,
    shift_series,
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _ensure_figures_dir() -> Path:
    """Return the Path to the figures directory, creating it if needed."""
    fig_dir = paths.figures()
    fig_dir.mkdir(parents=True, exist_ok=True)
    return fig_dir


def _filter_validation_period(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows whose timestamp falls within the validation window."""
    # ``timestamp`` column is timezone‑aware ISO‑8601 strings in the CSV.
    # pandas reads them as ``datetime64[ns, tz]`` when ``parse_dates`` is used.
    if not pd.api.types.is_datetime64tz_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    mask = (df["timestamp"] >= TEST_START) & (df["timestamp"] <= TEST_END)
    return df.loc[mask].reset_index(drop=True)


def plot_time_series_overlay(
    df: pd.DataFrame,
    composition: str,
    geomagnetic: str,
    lag_hours: int,
    output_path: Path,
) -> None:
    """
    Plot a composition parameter together with a geomagnetic index,
    applying the requested lag to the composition series.

    The composition series is shifted **forward** by ``lag_hours`` so that
    the value at time *t* aligns with the geomagnetic response at *t+lag*.
    """
    logger.info(
        f"Creating TS overlay: {composition} vs {geomagnetic} (lag={lag_hours}h)"
    )

    # Shift composition series; the shift introduces NaNs at the start.
    comp_series = shift_series(df[composition], lag_hours)
    geo_series = df[geomagnetic]

    # Align both series, dropping rows where either is NaN (the shift may
    # create leading NaNs).
    plot_df = pd.DataFrame(
        {
            "timestamp": df["timestamp"],
            composition: comp_series,
            geomagnetic: geo_series,
        }
    ).dropna()

    plt.figure(figsize=(12, 6))
    ax1 = plt.gca()
    ax1.plot(
        plot_df["timestamp"],
        plot_df[composition],
        label=composition,
        color="tab:blue",
        linewidth=1,
    )
    ax1.set_ylabel(composition, color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(
        plot_df["timestamp"],
        plot_df[geomagnetic],
        label=geomagnetic,
        color="tab:red",
        linestyle="--",
        linewidth=1,
    )
    ax2.set_ylabel(geomagnetic, color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    plt.title(
        f"{composition.replace('_', ' ').title()} vs {geomagnetic} (lag {lag_hours} h)"
    )
    plt.xlabel("Time")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved time‑series overlay to {output_path}")


def plot_correlation_heatmap(
    corr_df: pd.DataFrame,
    output_path: Path,
    title: str = "Correlation Heatmap",
) -> None:
    """
    Create a heatmap where rows are composition parameters, columns are
    lag values, and cell colour encodes the Pearson correlation coefficient.
    The DataFrame must contain the columns ``ace_var``, ``noaa_var``,
    ``lag_hours`` and ``pearson_r``.
    """
    if corr_df.empty:
        logger.warning(f"No correlation data to plot for {output_path}. Skipping.")
        return

    logger.info(f"Generating heatmap: {output_path}")

    # Build a multi‑index label "ACE – NOAA" for the rows.
    corr_df = corr_df.copy()
    corr_df["pair_label"] = (
        corr_df["ace_var"].astype(str) + " vs " + corr_df["noaa_var"].astype(str)
    )
    # Ensure numeric lag ordering.
    corr_df["lag_hours"] = pd.to_numeric(corr_df["lag_hours"], errors="coerce")

    heatmap_data = corr_df.pivot_table(
        index="pair_label",
        columns="lag_hours",
        values="pearson_r",
        aggfunc="first",
    )
    # Sort columns (lags) numerically.
    heatmap_data = heatmap_data.sort_index(axis=1, key=lambda x: x.astype(float))

    plt.figure(figsize=(12, max(6, 0.5 * len(heatmap_data))))
    cmap = plt.cm.RdBu_r
    im = plt.imshow(
        heatmap_data.values,
        cmap=cmap,
        aspect="auto",
        vmin=-1,
        vmax=1,
        origin="upper",
    )

    plt.yticks(
        range(len(heatmap_data.index)),
        heatmap_data.index,
        fontsize=9,
    )
    plt.xticks(
        range(len(heatmap_data.columns)),
        [f"{int(l)}h" for l in heatmap_data.columns],
        fontsize=9,
    )
    cbar = plt.colorbar(im, shrink=0.8)
    cbar.set_label("Pearson r", rotation=270, labelpad=15)

    plt.title(title, fontsize=14)
    plt.xlabel("Lag (hours)")
    plt.ylabel("Variable pair")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved heatmap to {output_path}")


# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------


def run_viz_pipeline(
    synced_path: str = "data/processed/synced.csv",
    full_corr_path: str = "results/correlations.csv",
    val_corr_path: str = "results/validation_correlations.csv",
) -> None:
    """
    Execute the complete visualization pipeline required by US3.

    Steps
    -----
    1. Load the synchronized dataset.
    2. Restrict it to the held‑out validation period.
    3. For every (composition, geomagnetic, lag) combination create a
       time‑series overlay PNG named ``ts_overlay_<comp>_lag<h>.png``.
    4. Load the full‑series correlation results and generate
       ``heatmap_full.png``.
    5. Load the validation‑period correlation results and generate
       ``heatmap_validation.png``.
    """
    logger.info("Starting visualization pipeline...")

    # ------------------------------------------------------------------
    # 1‑2. Load and filter synced data
    # ------------------------------------------------------------------
    df_synced = load_synced_data(synced_path)
    df_val = _filter_validation_period(df_synced)

    figs_dir = _ensure_figures_dir()

    # ------------------------------------------------------------------
    # 3. Time‑series overlay plots for each lag
    # ------------------------------------------------------------------
    for comp in ACE_VARS:
        if comp not in df_val.columns:
            logger.warning(f"Composition variable '{comp}' missing in synced data.")
            continue
        for geo in NOAA_VARS:
            if geo not in df_val.columns:
                logger.warning(f"Geomagnetic variable '{geo}' missing in synced data.")
                continue
            for lag in LAGS_HOURS:
                out_file = figs_dir / f"ts_overlay_{comp}_lag{lag}.png"
                plot_time_series_overlay(
                    df_val, comp, geo, lag, out_file
                )

    # ------------------------------------------------------------------
    # 4. Heatmap for the full correlation results
    # ------------------------------------------------------------------
    if os.path.exists(full_corr_path):
        full_corr_df = pd.read_csv(full_corr_path)
        # The correlation CSV produced by the pipeline uses the column
        # names ``composition_parameter`` and ``geomagnetic_index``.
        # Rename them to match the expectations of ``plot_correlation_heatmap``.
        full_corr_df = full_corr_df.rename(
            columns={
                "composition_parameter": "ace_var",
                "geomagnetic_index": "noaa_var",
                "lag_hours": "lag_hours",
                "pearson_r": "pearson_r",
            }
        )
        heatmap_full_path = figs_dir / "heatmap_full.png"
        plot_correlation_heatmap(
            full_corr_df,
            heatmap_full_path,
            title="Correlation Heatmap (Full 1998‑2020 Series)",
        )
    else:
        logger.error(f"Full correlation file not found at {full_corr_path}")

    # ------------------------------------------------------------------
    # 5. Heatmap for the validation correlation results
    # ------------------------------------------------------------------
    if os.path.exists(val_corr_path):
        val_corr_df = pd.read_csv(val_corr_path)
        if not val_corr_df.empty:
            val_corr_df = val_corr_df.rename(
                columns={
                    "composition_parameter": "ace_var",
                    "geomagnetic_index": "noaa_var",
                    "lag_hours": "lag_hours",
                    "pearson_r": "pearson_r",
                }
            )
            heatmap_val_path = figs_dir / "heatmap_validation.png"
            plot_correlation_heatmap(
                val_corr_df,
                heatmap_val_path,
                title="Correlation Heatmap (Validation 2018‑2020)",
            )
        else:
            logger.warning(
                f"Validation correlation file {val_corr_path} is empty – "
                "skipping validation heatmap."
            )
    else:
        logger.error(f"Validation correlation file not found at {val_corr_path}")

    logger.info("Visualization pipeline completed.")


if __name__ == "__main__":
    # When executed directly ``python -m code.viz.plots`` the pipeline runs.
    run_viz_pipeline()