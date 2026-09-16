import json
import logging
from pathlib import Path
from typing import Dict, Any

from logger import get_logger, info, error
from derive_scaling import fit_scaling_factor, bootstrap_scaling_analysis, load_raw_energies

# Configure logger
logger = get_logger(__name__)

SCALING_RESULTS_PATH = Path("data/derived/scaling_results.json")
SCALING_FACTOR_TXT_PATH = Path("data/derived/scaling_factor.txt")
RAW_ENERGIES_PATH = Path("data/raw/IL-Benchmark-local.zip")

def write_scaling_file(results: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the optimal scaling factor 's' and its 95% confidence interval
    to a text file in a human-readable format.

    Args:
        results: Dictionary containing 'optimal_s', 'ci_lower', 'ci_upper', etc.
        output_path: Path where the text file will be written.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    s_opt = results.get("optimal_s")
    ci_lower = results.get("ci_lower")
    ci_upper = results.get("ci_upper")
    hypothesis_rejected = results.get("hypothesis_rejected", False)

    if s_opt is None or ci_lower is None or ci_upper is None:
        error(f"Missing required scaling results to write file: {results}")
        raise ValueError("Cannot write scaling file: missing required metrics.")

    content = (
        f"Optimal Scaling Factor (s): {s_opt:.6f}\n"
        f"95% Confidence Interval: [{ci_lower:.6f}, {ci_upper:.6f}]\n"
        f"Hypothesis Test (s=1.0): {'Rejected' if hypothesis_rejected else 'Not Rejected'}\n"
        f"Note: CI excludes 1.0 implies significant deviation from standard D3.\n"
    )

    output_path.write_text(content)
    info(f"Scaling factor written to {output_path}")

def load_scaling_results(path: Path) -> Dict[str, Any]:
    """
    Loads scaling results from a JSON file.
    """
    if not path.exists():
        error(f"Scaling results file not found: {path}")
        raise FileNotFoundError(f"Scaling results file not found: {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def main():
    """
    Orchestrates the derivation of the scaling factor, bootstrapping,
    and writing the final results to disk.
    """
    logger.info("Starting scaling factor derivation and output generation...")
    
    # 1. Load raw energies
    if not RAW_ENERGIES_PATH.exists():
        error(f"Raw energies file not found: {RAW_ENERGIES_PATH}")
        raise FileNotFoundError(f"Raw energies file not found: {RAW_ENERGIES_PATH}")
    
    df = load_raw_energies(RAW_ENERGIES_PATH)
    
    # 2. Fit scaling factor
    s_opt, mae_opt = fit_scaling_factor(df)
    logger.info(f"Optimal scaling factor s = {s_opt:.6f}, MAE = {mae_opt:.6f}")

    # 3. Bootstrap analysis for CI
    ci_lower, ci_upper, hypothesis_rejected = bootstrap_scaling_analysis(df, n_replicates=1000)
    logger.info(f"95% CI for s: [{ci_lower:.6f}, {ci_upper:.6f}]")
    logger.info(f"Hypothesis s=1.0 rejected: {hypothesis_rejected}")

    # 4. Prepare results dictionary
    results = {
        "optimal_s": s_opt,
        "mae_opt": mae_opt,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "hypothesis_rejected": hypothesis_rejected,
        "n_replicates": 1000
    }

    # 5. Write JSON results (for programmatic use)
    SCALING_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SCALING_RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Scaling results JSON written to {SCALING_RESULTS_PATH}")

    # 6. Write human-readable text file (T025 requirement)
    write_scaling_file(results, SCALING_FACTOR_TXT_PATH)

    logger.info("Scaling factor derivation complete.")

if __name__ == "__main__":
    main()