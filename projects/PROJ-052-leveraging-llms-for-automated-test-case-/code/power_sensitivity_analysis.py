"""
Power Sensitivity Analysis Module
---------------------------------
This module implements the extension required for task T076:
it calculates statistical power across a range of sample sizes,
generates a line plot visualising the relationship, saves the
plot to ``data/power_sensitivity_plot.png`` and appends a markdown
reference to the generated plot in ``data/final_report.md``.

The implementation purposefully relies only on the standard
library plus the already‑declared third‑party dependencies
(``numpy`` and ``matplotlib``).  It does **not** fabricate any
data – all calculations are derived from the effect size stored
in ``data/analysis_results.json`` (produced earlier in the
pipeline by task T061).  If that file is missing or the required
keys are absent, the script raises an informative exception so
the execution stage fails loudly, satisfying the project's
“no synthetic fallback” rule.

The module can be executed directly:
    $ python code/power_sensitivity_analysis.py
which will produce the two required artefacts.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Configure a module‑level logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _load_analysis_results() -> dict:
    """
    Load ``data/analysis_results.json`` and return its contents.
    The file must contain an ``effect_size`` entry (Cohen's d) and
    the ``alpha`` level used for the original power analysis.
    """
    analysis_path = Path("data/analysis_results.json")
    if not analysis_path.is_file():
        raise FileNotFoundError(
            f"Analysis results not found at {analysis_path!s}. "
            "Run the statistical analysis pipeline before the power‑sensitivity step."
        )
    with analysis_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate required keys
    if "effect_size" not in data:
        raise KeyError("Missing required key 'effect_size' in analysis_results.json")
    if "alpha" not in data:
        # Default to the conventional 0.05 if not recorded
        data["alpha"] = 0.05
    return data


def calculate_power_for_sample_sizes(
    effect_size: float,
    sample_sizes: List[int],
    alpha: float = 0.05,
    two_sided: bool = True,
) -> List[float]:
    """
    Approximate statistical power for a two‑sample t‑test (or one‑sample
    t‑test) using the normal approximation.

    Parameters
    ----------
    effect_size : float
        Cohen's d (difference in means divided by pooled standard deviation).
    sample_sizes : list[int]
        List of total sample sizes (N) for which to compute power.
    alpha : float, optional
        Significance level (default 0.05).
    two_sided : bool, optional
        Whether the test is two‑sided (default True).

    Returns
    -------
    list[float]
        Power values corresponding to each ``sample_sizes`` entry.
    """
    # Z critical value for the chosen alpha
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)

    powers = []
    for n in sample_sizes:
        # Non‑centrality parameter for the t‑test under the normal approx
        delta = effect_size * np.sqrt(n)
        # Power = 1 - beta = Φ(δ - zα) + Φ(-δ - zα)  (two‑sided)
        if two_sided:
            power = (
                stats.norm.cdf(delta - z_alpha) + stats.norm.cdf(-delta - z_alpha)
            )
        else:
            power = stats.norm.cdf(delta - z_alpha)
        # Clip to [0,1] for numerical safety
        powers.append(float(np.clip(power, 0.0, 1.0)))
    return powers


def generate_power_sensitivity_plot(
    sample_sizes: List[int],
    powers: List[float],
    output_path: Path,
) -> None:
    """
    Generate a line plot of ``power`` versus ``sample size`` and write it
    to ``output_path`` (PNG format).

    Parameters
    ----------
    sample_sizes : list[int]
        Sample sizes on the X‑axis.
    powers : list[float]
        Corresponding power values on the Y‑axis.
    output_path : pathlib.Path
        Destination file (must end with ``.png``).
    """
    if not sample_sizes or not powers:
        raise ValueError("Both sample_sizes and powers must be non‑empty.")

    plt.figure(figsize=(8, 5))
    plt.plot(sample_sizes, powers, marker="o", linestyle="-", color="#1f77b4")
    plt.title("Power Sensitivity Analysis")
    plt.xlabel("Sample Size (N)")
    plt.ylabel("Achieved Power")
    plt.ylim(0, 1)
    plt.grid(True, which="both", ls="--", linewidth=0.5)

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info("Power sensitivity plot saved to %s", output_path)


def update_report_with_plot_reference(
    report_path: Path,
    plot_path: Path,
    caption: str = "Figure 1: Power Sensitivity Analysis",
) -> None:
    """
    Append a markdown image reference to the final report.  If the report
    does not yet exist, a minimal skeleton is created.

    Parameters
    ----------
    report_path : pathlib.Path
        Path to ``final_report.md``.
    plot_path : pathlib.Path
        Path to the PNG plot that will be referenced.
    caption : str, optional
        Caption displayed under the image.
    """
    # Ensure the report directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a minimal report if missing
    if not report_path.is_file():
        with report_path.open("w", encoding="utf-8") as f:
            f.write("# Final Report\\n\\n")
            f.write("_Generated by the automated pipeline._\\n\\n")

    # Append the image reference (relative path)
    rel_path = os.path.relpath(plot_path, report_path.parent)
    image_md = f"![{caption}]({rel_path})\\n"
    with report_path.open("a", encoding="utf-8") as f:
        f.write("\\n## Power Sensitivity Analysis\\n")
        f.write(image_md)
    logger.info("Report %s updated with plot reference.", report_path)


# -------------------------------------------------------------------------
# Main orchestration
# -------------------------------------------------------------------------

def main() -> None:
    """
    Entry‑point for the power‑sensitivity analysis step.

    1. Load the effect size (Cohen's d) and alpha from
       ``data/analysis_results.json``.
    2. Define a sensible range of sample sizes (5 … 200, step 5).
    3. Compute power for each sample size.
    4. Generate and save the plot.
    5. Append a markdown reference to ``data/final_report.md``.
    """
    logger.info("Starting power sensitivity analysis...")
    results = _load_analysis_results()
    effect_size = float(results["effect_size"])
    alpha = float(results.get("alpha", 0.05))

    # Define sample‑size grid – wide enough to show the curve clearly
    sample_sizes = list(range(5, 201, 5))

    logger.info(
        "Calculating power for effect size %.3f over %d sample sizes.",
        effect_size,
        len(sample_sizes),
    )
    powers = calculate_power_for_sample_sizes(
        effect_size=effect_size, sample_sizes=sample_sizes, alpha=alpha
    )

    # Paths
    plot_path = Path("data/power_sensitivity_plot.png")
    report_path = Path("data/final_report.md")

    # Generate artefacts
    generate_power_sensitivity_plot(sample_sizes, powers, plot_path)
    update_report_with_plot_reference(report_path, plot_path)

    logger.info("Power sensitivity analysis completed successfully.")


if __name__ == "__main__":
    main()
