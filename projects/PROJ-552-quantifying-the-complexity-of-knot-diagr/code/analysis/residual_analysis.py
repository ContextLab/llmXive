"""Residual analysis utilities for the knot‑complexity regression pipeline.

Provides logic for grouping knots whose residuals deviate by ≥ 2 SD
from the fitted linear model and for writing a reproducibility report.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from reproducibility.logs import get_logger, log_operation


@dataclass
class ResidualFamily:
    family_name: str
    knots: List[str]
    mean_residual: float
    std_residual: float


@log_operation
def identify_residual_families(
    linear_result: Any,  # LinearModelResult from model_fitting
    df: pd.DataFrame,
    sigma: float = 2.0,
) -> List[ResidualFamily]:
    """Return families of knots whose residuals lie ≥ *sigma* standard deviations."""
    residuals = df.copy()
    residuals["predicted"] = linear_result.predictions
    residuals["residual"] = residuals["hyperbolic_volume"] - residuals["predicted"]

    mu = residuals["residual"].mean()
    sigma_val = residuals["residual"].std()

    outliers = residuals[
        (residuals["residual"] > mu + sigma * sigma_val)
        | (residuals["residual"] < mu - sigma * sigma_val)
    ]

    families: List[ResidualFamily] = []
    for family, group in outliers.groupby("family"):
        families.append(
            ResidualFamily(
                family_name=str(family),
                knots=group["knot_id"].tolist(),
                mean_residual=float(group["residual"].mean()),
                std_residual=float(group["residual"].std()),
            )
        )
    return families


@log_operation
def write_residual_analysis_report(
    families: List[ResidualFamily],
    output_md: Path,
) -> None:
    """Write a markdown report summarising the identified residual families."""
    logger = get_logger(__name__)
    logger.info("Writing residual analysis report to %s", output_md)

    lines = [
        "# Residual Analysis Report",
        "",
        "Families of knots whose residuals deviate by ≥ 2 SD from the linear model:",
        "",
    ]
    if not families:
        lines.append("_No families exceeded the threshold._")
    else:
        for fam in families:
            lines.extend(
                [
                    f"## Family: {fam.family_name}",
                    f"- Number of knots: {len(fam.knots)}",
                    f"- Mean residual: {fam.mean_residual:.4f}",
                    f"- Std residual: {fam.std_residual:.4f}",
                    "",
                    "### Knot identifiers",
                    "",
                    "\n".join(f"- {kid}" for kid in fam.knots),
                    "",
                ]
            )
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Residual analysis report written")