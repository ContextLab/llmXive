"""
power_analysis.py
-----------------
Computes the required sample size for detecting a Pearson correlation
coefficient of r = 0.10 with a Bonferroni‑adjusted significance level
α = 0.001 and a target statistical power of 0.80.

The script performs three actions:

1. Calculates the sample size using statsmodels' FTestPower (which is
   equivalent to a correlation test via the relationship
   f² = r² / (1‑r²)).
2. Writes the integer sample size to ``results/power_analysis.txt``.
3. Immediately reads back the written file and updates two project‑wide
   artefacts:
      * ``research.md`` – inserts a line in the *Methodological Rationale*
        section reporting the required sample size.
      * ``state/projects/PROJ-049-exploring-the-correlation-between-musica.yaml``
        – stores the value under the key ``required_sample_size``.
The script is deliberately self‑contained and can be executed directly:

    python code/power_analysis.py

It will create any missing parent directories, and it uses the shared
``setup_logging`` utility for consistent log handling.
"""

import math
import logging
from pathlib import Path

import yaml
from statsmodels.stats.power import FTestPower

from utils import setup_logging


# ----------------------------------------------------------------------
# Configuration constants (these are part of the scientific specification)
# ----------------------------------------------------------------------
TARGET_R = 0.10                 # effect size we wish to detect
BONFERRONI_ALPHA = 0.001        # family‑wise error rate after correction
TARGET_POWER = 0.80             # conventional statistical power

# Paths – relative to the repository root
RESULTS_DIR = Path("results")
POWER_ANALYSIS_TXT = RESULTS_DIR / "power_analysis.txt"

RESEARCH_MD_PATH = Path("research.md")
STATE_FILE_PATH = Path(
    "state/projects/PROJ-049-exploring-the-correlation-between-musica.yaml"
)


def calculate_sample_size(
    r: float = TARGET_R,
    alpha: float = BONFERRONI_ALPHA,
    power: float = TARGET_POWER,
) -> int:
    """
    Compute the required total sample size (N) for a two‑tailed Pearson
    correlation test using the F‑test power approximation.

    Parameters
    ----------
    r: float
        Target correlation coefficient.
    alpha: float
        Desired significance level (already Bonferroni‑adjusted).
    power: float
        Desired statistical power.

    Returns
    -------
    int
        The smallest integer N that satisfies the power requirement.
    """
    # Convert correlation to Cohen's f² for a simple linear regression with
    # one predictor (the equivalence holds for testing a single correlation).
    f_squared = r ** 2 / (1 - r ** 2)

    # statsmodels expects the *effect size* f (square‑root of f²)
    effect_size_f = math.sqrt(f_squared)

    # df_num = number of numerator degrees of freedom = 1 for a single
    # predictor; df_denom is solved internally.
    power_analysis = FTestPower()
    nobs = power_analysis.solve_power(
        effect_size=effect_size_f,
        df_num=1,
        alpha=alpha,
        power=power,
        alternative="two-sided",
    )

    # ``solve_power`` returns a float; we need the ceiling to guarantee
    # sufficient observations.
    required_n = math.ceil(nobs)
    return required_n


def write_power_analysis_file(sample_size: int, path: Path = POWER_ANALYSIS_TXT) -> None:
    """
    Persist the required sample size to ``results/power_analysis.txt``.
    The file contains a single integer on the first line.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{sample_size}\\n")
    logging.info("Required sample size (%d) written to %s", sample_size, path)


def read_power_analysis_file(path: Path = POWER_ANALYSIS_TXT) -> int:
    """
    Read back the sample size from the file written by ``write_power_analysis_file``.
    """
    content = path.read_text().strip()
    try:
        value = int(content.splitlines()[0])
    except Exception as exc:
        raise ValueError(f"Unable to parse integer from {path}") from exc
    logging.debug("Read sample size %d from %s", value, path)
    return value


def update_research_md(sample_size: int, md_path: Path = RESEARCH_MD_PATH) -> None:
    """
    Insert (or replace) a line reporting the required sample size in the
    *Methodological Rationale* section of ``research.md``.

    The function is tolerant of missing headings – if the heading cannot be
    found it appends a new section at the end of the file.
    """
    if not md_path.is_file():
        raise FileNotFoundError(f"{md_path} does not exist")

    lines = md_path.read_text().splitlines()
    new_lines = []
    inserted = False

    for idx, line in enumerate(lines):
        new_lines.append(line)
        # Detect the start of the methodological rationale section.
        if line.strip().lower().startswith("## methodological rationale"):
            # Insert a blank line then the required‑size line.
            insertion = (
                f"Required sample size (detect r={TARGET_R:.2f}, "
                f"α={BONFERRONI_ALPHA:.3f}, power={TARGET_POWER:.2f}): {sample_size}"
            )
            new_lines.append("")
            new_lines.append(insertion)
            inserted = True
            # Continue copying the rest of the file unchanged.

    if not inserted:
        # Fallback – add a new section at the end.
        new_lines.append("")
        new_lines.append("## Methodological Rationale")
        new_lines.append(
            f"Required sample size (detect r={TARGET_R:.2f}, "
            f"α={BONFERRONI_ALPHA:.3f}, power={TARGET_POWER:.2f}): {sample_size}"
        )

    md_path.write_text("\\n".join(new_lines) + "\\n")
    logging.info("research.md updated with required sample size %d", sample_size)


def update_state_file(sample_size: int, state_path: Path = STATE_FILE_PATH) -> None:
    """
    Store the required sample size in the project's state YAML file.
    If the file already exists, the key ``required_sample_size`` is added
    or overwritten; all other keys are preserved.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if state_path.is_file():
        with state_path.open("r") as f:
            try:
                data = yaml.safe_load(f) or {}
            except yaml.YAMLError as exc:
                raise ValueError(f"Malformed YAML in {state_path}") from exc
    else:
        data = {}

    data["required_sample_size"] = sample_size
    with state_path.open("w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    logging.info("State file %s updated with required_sample_size=%d", state_path, sample_size)


def main() -> None:
    """
    Orchestrates the full power‑analysis workflow.
    """
    # Initialise a consistent logger (writes to ``logs/app.log`` via utils).
    logger = setup_logging()
    logger.info("Starting power analysis computation")

    # 1️⃣  Compute the required N.
    required_n = calculate_sample_size()
    logger.debug("Calculated required sample size: %d", required_n)

    # 2️⃣  Persist the result.
    write_power_analysis_file(required_n)

    # 3️⃣  Immediately read it back (as required by the spec).
    parsed_n = read_power_analysis_file()
    if parsed_n != required_n:
        logger.error(
            "Mismatch between written (%d) and parsed (%d) sample size",
            required_n,
            parsed_n,
        )
        raise RuntimeError("Inconsistent sample size after write/read")

    # 4️⃣  Update ancillary artefacts.
    update_research_md(parsed_n)
    update_state_file(parsed_n)

    logger.info("Power analysis completed successfully")


if __name__ == "__main__":
    main()
