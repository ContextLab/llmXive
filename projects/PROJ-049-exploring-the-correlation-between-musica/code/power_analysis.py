"""
Power Analysis Script for Project PROJ-049

This script computes the required sample size to detect a Pearson correlation
coefficient of r = 0.10 with a Bonferroni‑adjusted significance level α = 0.001
(two‑sided) and a target statistical power of 0.80. The resulting sample size
is written to ``results/power_analysis.txt``. The script then updates the
``research.md`` file with a simple line ``Required sample size: <n>`` and records
the same value in the project state YAML file located at
``state/projects/PROJ-049-exploring-the-correlation-between-musica.yaml``.
"""

import math
import logging
from pathlib import Path

import yaml
from statsmodels.stats.power import FTestPower

from utils import setup_logging

# --------------------------------------------------------------------------- #
# Configuration constants (can be tweaked if the study design changes)
# --------------------------------------------------------------------------- #
R_TARGET = 0.10               # Desired detectable Pearson correlation
ALPHA_BONFERRONI = 0.001      # Bonferroni‑adjusted two‑sided significance level
POWER_TARGET = 0.80           # Desired statistical power (1 - β)

# Output locations
RESULT_PATH = Path("results/power_analysis.txt")
RESEARCH_MD_PATH = Path("research.md")
STATE_YAML_PATH = Path(
    "state/projects/PROJ-049-exploring-the-correlation-between-musica.yaml"
)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def calculate_sample_size(
    r: float = R_TARGET,
    alpha: float = ALPHA_BONFERRONI,
    power: float = POWER_TARGET,
) -> int:
    """
    Compute the required total sample size for a two‑sided correlation test.

    The relationship between Pearson r and Cohen's f² for a simple linear
    regression (single predictor) is:

        f² = r² / (1 - r²)

    ``statsmodels.stats.power.FTestPower`` solves for the total number of
    observations needed to achieve the specified power.

    Parameters
    ----------
    r: float
        Target correlation coefficient.
    alpha: float
        Significance level (two‑sided).
    power: float
        Desired statistical power.

    Returns
    -------
    int
        Rounded‑up required sample size.
    """
    if not (-1 < r < 1):
        raise ValueError("Correlation coefficient must be between -1 and 1 (exclusive).")
    effect_size_f2 = r ** 2 / (1 - r ** 2)

    ftest = FTestPower()
    nobs = ftest.solve_power(
        effect_size=effect_size_f2,
        df_num=1,
        alpha=alpha,
        power=power,
        alternative="two-sided",
    )
    return math.ceil(nobs)

def write_power_analysis_file(sample_size: int, path: Path = RESULT_PATH) -> None:
    """
    Write the computed sample size to ``results/power_analysis.txt``.
    The file contains a single integer on the first line.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{sample_size}\n", encoding="utf-8")

def read_power_analysis_file(path: Path = RESULT_PATH) -> int:
    """
    Read the sample size back from ``results/power_analysis.txt``.
    Raises ``FileNotFoundError`` if the file does not exist or the contents
    cannot be parsed as an integer.
    """
    content = path.read_text(encoding="utf-8").strip()
    try:
        return int(content)
    except ValueError as exc:
        raise ValueError(f"Unable to parse sample size from {path}") from exc

def update_research_md(sample_size: int, path: Path = RESEARCH_MD_PATH) -> None:
    """
    Ensure that ``research.md`` contains a single line
    ``Required sample size: <sample_size>``. If the file does not exist,
    it is created with that line. Any existing line that starts with
    ``Required sample size:`` is replaced.
    """
    line_to_write = f"Required sample size: {sample_size}"
    if not path.exists():
        path.write_text(line_to_write + "\n", encoding="utf-8")
        return

    lines = path.read_text(encoding="utf-8").splitlines()
    # Remove any existing line that starts with the required prefix
    prefix = "Required sample size:"
    new_lines = [ln for ln in lines if not ln.lstrip().startswith(prefix)]
    # Append the required line at the end of the file
    new_lines.append(line_to_write)
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

def update_state_file(sample_size: int, path: Path = STATE_YAML_PATH) -> None:
    """
    Record the required sample size in the project's state YAML file.
    The key ``required_sample_size`` is added/updated at the top level.
    If the file does not exist, a new one is created.
    """
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    state["required_sample_size"] = sample_size

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, sort_keys=False)

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Execute the full power‑analysis workflow:
    1. Compute the required sample size.
    2. Persist it to ``results/power_analysis.txt``.
    3. Verify the write/read round‑trip.
    4. Update ``research.md`` with a plain ``Required sample size: <n>`` line.
    5. Record the same value in the project state YAML file.
    """
    logger = setup_logging(__name__)

    logger.info("Starting power analysis for Pearson r = %.3f", R_TARGET)
    sample_size = calculate_sample_size()
    logger.info("Calculated required sample size: %d", sample_size)

    write_power_analysis_file(sample_size)
    logger.info("Wrote sample size to %s", RESULT_PATH)

    # Verify round‑trip integrity.
    read_back = read_power_analysis_file()
    if read_back != sample_size:
        logger.error(
            "Mismatch after reading back the sample size: wrote %d, read %d",
            sample_size,
            read_back,
        )
        raise RuntimeError("Power analysis file integrity check failed.")
    logger.info("Verified sample size written correctly.")

    # Update auxiliary documentation/artifacts.
    update_research_md(sample_size)
    logger.info("Updated research.md with required sample size line.")

    update_state_file(sample_size)
    logger.info("Recorded required sample size in project state file %s", STATE_YAML_PATH)

    logger.info("Power analysis workflow completed successfully.")

if __name__ == "__main__":
    main()
