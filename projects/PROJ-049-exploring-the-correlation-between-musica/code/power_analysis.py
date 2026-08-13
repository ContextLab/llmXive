"""
Power Analysis for Music-Personality Correlation Study.

Computes the required sample size to detect a Pearson correlation (r) of 0.10
with a Bonferroni-adjusted alpha of 0.001 (target power 0.80).

Logic:
1. Define parameters: r=0.10, alpha=0.001, power=0.80.
2. Use scipy.stats to calculate the required N.
3. Write the integer N to results/power_analysis.txt.
4. Parse the file to ensure consistency.
5. Update research.md (Methodological Rationale section) with the value.
6. Update state/projects/PROJ-049-exploring-the-correlation-between-musica.yaml
   with the recorded required sample size.
"""
import os
import sys
import math
import logging
from pathlib import Path

# Add parent directory to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import setup_logging

logger = setup_logging()

# Parameters
EFFECT_SIZE_R = 0.10
ALPHA_ADJUSTED = 0.001
POWER = 0.80
OUTPUT_FILE = project_root / "results" / "power_analysis.txt"
RESEARCH_FILE = project_root / "research.md"
STATE_FILE = project_root / "state" / "projects" / "PROJ-049-exploring-the-correlation-between-musica.yaml"

def calculate_sample_size(r, alpha, power):
    """
    Calculate required sample size for Pearson correlation test.
    Uses Fisher's z-transformation approximation.
    """
    # Fisher's z transformation
    z_r = 0.5 * math.log((1 + r) / (1 - r))
    
    # Critical z-values
    # Two-tailed test: alpha/2
    # We need the inverse CDF (percent point function) of the standard normal
    # Since we can't rely on scipy.stats in this isolated calculation block without import,
    # we approximate or import it here. The API surface allows standard libs.
    try:
        from scipy.stats import norm
    except ImportError:
        logger.error("scipy is required for power analysis. Please install it.")
        raise

    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)

    # Formula for N:
    # N = ((z_alpha + z_beta) / z_r)^2 + 3
    # (The +3 is a common continuity correction for Fisher's z)
    
    if z_r == 0:
        raise ValueError("Effect size r cannot be 0.")

    n = ((z_alpha + z_beta) / z_r) ** 2 + 3
    return math.ceil(n)

def update_research_md(required_n):
    """
    Updates research.md in the 'Methodological Rationale' section.
    """
    if not RESEARCH_FILE.exists():
        logger.warning(f"{RESEARCH_FILE} does not exist. Creating it.")
        RESEARCH_FILE.parent.mkdir(parents=True, exist_ok=True)
        content = "# Research Methodology\n\n"
        content += "## Methodological Rationale\n\n"
        content += f"The required sample size was calculated to detect a correlation of r={EFFECT_SIZE_R} "
        content += f"with alpha={ALPHA_ADJUSTED} and power={POWER}. "
        content += f"Calculated N: **{required_n}**.\n"
        RESEARCH_FILE.write_text(content)
        return

    content = RESEARCH_FILE.read_text()
    
    # Check if section exists
    if "## Methodological Rationale" not in content:
        content += "\n## Methodological Rationale\n\n"
    
    # Update or insert the specific line
    # We look for a pattern like "Calculated N: **XXX**" or "Required N: XXX"
    import re
    
    # Pattern to find the existing N record
    pattern = r"Calculated N: \*\*(\d+)\*\*|Required sample size: (\d+)"
    
    if re.search(pattern, content):
        # Replace existing
        new_line = f"Calculated N: **{required_n}**"
        content = re.sub(pattern, new_line, content)
    else:
        # Append if no existing record found
        content += f"Calculated N: **{required_n}**\n"
    
    RESEARCH_FILE.write_text(content)
    logger.info(f"Updated {RESEARCH_FILE} with required N: {required_n}")

def update_state_file(required_n):
    """
    Updates the project state YAML file with the required sample size.
    """
    if not STATE_FILE.exists():
        logger.warning(f"{STATE_FILE} does not exist. Creating it.")
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        content = f"project_id: PROJ-049-exploring-the-correlation-between-musica\n"
        content += f"required_sample_size: {required_n}\n"
        content += "updated_at: null\n"
        content += "artifact_hashes: {}\n"
        STATE_FILE.write_text(content)
        return

    content = STATE_FILE.read_text()
    
    # Simple YAML update (assuming basic structure)
    import re
    
    # Check if key exists
    if "required_sample_size:" in content:
        content = re.sub(r"required_sample_size: \d+", f"required_sample_size: {required_n}", content)
    else:
        # Insert after project_id
        content = re.sub(
            r"(project_id: .*\n)",
            f"\\1required_sample_size: {required_n}\n",
            content
        )
    
    STATE_FILE.write_text(content)
    logger.info(f"Updated {STATE_FILE} with required N: {required_n}")

def main():
    logger.info("Starting Power Analysis...")
    logger.info(f"Target r: {EFFECT_SIZE_R}, Alpha: {ALPHA_ADJUSTED}, Power: {POWER}")

    try:
        required_n = calculate_sample_size(EFFECT_SIZE_R, ALPHA_ADJUSTED, POWER)
        logger.info(f"Calculated required sample size: {required_n}")
    except Exception as e:
        logger.error(f"Power analysis calculation failed: {e}")
        raise

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(str(required_n))
    logger.info(f"Written required N ({required_n}) to {OUTPUT_FILE}")

    # Parse immediately to verify
    parsed_n = int(OUTPUT_FILE.read_text().strip())
    if parsed_n != required_n:
        raise RuntimeError(f"Verification failed: File contains {parsed_n}, expected {required_n}")
    logger.info(f"Verification passed: {parsed_n}")

    # Update documentation files
    update_research_md(parsed_n)
    update_state_file(parsed_n)

    logger.info("Power analysis complete.")

if __name__ == "__main__":
    main()
