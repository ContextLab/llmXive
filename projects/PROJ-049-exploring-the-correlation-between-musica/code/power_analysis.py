import seed
import math
import logging
from pathlib import Path
import yaml
from statsmodels.stats.power import FTestPower
from utils import setup_logging

logger = logging.getLogger(__name__)

# Constants (could be moved to config)
R_TARGET = 0.10  # Desired correlation coefficient to detect
ALPHA_BONFERRONI = 0.001  # Bonferroni‑adjusted significance level (two‑tailed)
POWER_TARGET = 0.80  # Desired statistical power

RESULT_PATH = Path("results") / "power_analysis.txt"
RESEARCH_MD_PATH = Path("research.md")
STATE_YAML_PATH = Path("state") / "projects" / "PROJ-049.yaml"

def calculate_sample_size(r: float = R_TARGET, alpha: float = ALPHA_BONFERRONI, power: float = POWER_TARGET) -> int:
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
    f2 = r**2 / (1 - r**2)
    effect_size = math.sqrt(f2)  # Cohen's f for the F‑test
    analysis = FTestPower()
    # For a simple correlation (single predictor) the numerator df = 1
    n = analysis.solve_power(effect_size=effect_size, df_num=1, alpha=alpha, power=power, nobs=None)
    sample_size = int(math.ceil(n))
    logger.info(f"Calculated sample size: {sample_size} (r={r}, alpha={alpha}, power={power})")
    return sample_size

def write_power_analysis_file(sample_size: int, path: Path = RESULT_PATH) -> None:
    """
    Write the computed sample size to ``results/power_analysis.txt``.
    The file contains a single integer on the first line.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(f"{sample_size}\\n")
    logger.info(f"Wrote power analysis result to {path}")

def read_power_analysis_file(path: Path = RESULT_PATH) -> int:
    """
    Read the sample size back from ``results/power_analysis.txt``.
    Raises ``FileNotFoundError`` if the file does not exist or the contents
    cannot be parsed as an integer.
    """
    with open(path, "r") as f:
        line = f.readline().strip()
        try:
            value = int(line)
            logger.info(f"Read power analysis sample size {value} from {path}")
            return value
        except ValueError as e:
            logger.error(f"Invalid integer in {path}: {line}")
            raise

def update_research_md(sample_size: int, path: Path = RESEARCH_MD_PATH) -> None:
    """
    Ensure that ``research.md`` contains a single line
    ``Required sample size: <sample_size>``. If the file does not exist,
    it is created with that line. Any existing line that starts with
    ``Required sample size:`` is replaced.
    """
    line_needed = f"Required sample size: {sample_size}"
    if not path.exists():
        with open(path, "w") as f:
            f.write(line_needed + "\\n")
        logger.info(f"Created {path} with required sample size line.")
        return

    # Read existing lines
    with open(path, "r") as f:
        lines = f.readlines()

    # Replace or append the line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("Required sample size:"):
            lines[i] = line_needed + "\\n"
            updated = True
            break

    if not updated:
        lines.append(line_needed + "\\n")

    # Write back
    with open(path, "w") as f:
        f.writelines(lines)
    logger.info(f"Updated {path} with required sample size line.")

def update_state_file(sample_size: int, path: Path = STATE_YAML_PATH) -> None:
    """
    Record the required sample size in the project's state YAML file.
    The key ``required_sample_size`` is added/updated at the top level.
    If the file does not exist, a new one is created.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    if path.exists():
        with open(path, "r") as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML in {path}: {e}")
                state = {}

    state["required_sample_size"] = sample_size
    with open(path, "w") as f:
        yaml.safe_dump(state, f)
    logger.info(f"Updated state file {path} with required_sample_size={sample_size}")

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
    sample_size = calculate_sample_size()
    write_power_analysis_file(sample_size)
    # Verify round‑trip
    read_back = read_power_analysis_file()
    if read_back != sample_size:
        logger.error(f"Round‑trip mismatch: wrote {sample_size}, read back {read_back}")
        raise ValueError("Power analysis round‑trip verification failed")

    update_research_md(sample_size)
    update_state_file(sample_size)
    logger.info("Power analysis workflow completed successfully.")

if __name__ == "__main__":
    main()