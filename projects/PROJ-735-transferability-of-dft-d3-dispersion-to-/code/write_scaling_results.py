"""
write_scaling_results.py

Implements T025: Read the optimal scaling factor `s` and its CI from the output
of T022/T023 (derived by `derive_scaling.py`) and write to `data/derived/scaling_factor.txt`.

This module provides the `write_scaling_file` function to generate the human-readable,
parsable text artifact required by the task. It also exposes `load_scaling_results`
to read this artifact back into the pipeline (used by T026 and T027).
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from logger import get_logger, info, error
from derive_scaling import fit_scaling_factor, bootstrap_scaling_analysis, load_raw_energies

logger = get_logger(__name__)

def write_scaling_file(
    output_path: str,
    optimal_s: float,
    ci_lower: float,
    ci_upper: float,
    p_value: Optional[float] = None,
    hypothesis_rejected: Optional[bool] = None
) -> None:
    """
    Writes the optimal scaling factor and confidence interval to a text file.

    The format is human-readable and parsable:
    ```
    Scaling Factor: <value>
    95% CI: [<lower>, <upper>]
    Hypothesis Test (s=1.0): <rejected/failed/not_tested>
    P-value: <value or N/A>
    ```

    Args:
        output_path: Path to the output text file (e.g., 'data/derived/scaling_factor.txt').
        optimal_s: The optimal scaling factor found by optimization.
        ci_lower: Lower bound of the 95% confidence interval.
        ci_upper: Upper bound of the 95% confidence interval.
        p_value: Optional p-value from the hypothesis test.
        hypothesis_rejected: Optional boolean indicating if H0 (s=1.0) was rejected.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    info(f"Writing scaling results to {output_path}")

    status = "Not Tested"
    if hypothesis_rejected is not None:
        status = "Rejected" if hypothesis_rejected else "Failed to Reject"

    p_val_str = f"{p_value:.6f}" if p_value is not None else "N/A"

    content = (
        f"Scaling Factor: {optimal_s:.6f}\n"
        f"95% CI: [{ci_lower:.6f}, {ci_upper:.6f}]\n"
        f"Hypothesis Test (s=1.0): {status}\n"
        f"P-value: {p_val_str}\n"
    )

    with open(output_path, 'w') as f:
        f.write(content)

    info(f"Successfully wrote scaling results to {output_path}")

def load_scaling_results(input_path: str) -> Dict[str, Any]:
    """
    Reads the scaling factor text file and returns a dictionary with the values.

    Args:
        input_path: Path to the text file (e.g., 'data/derived/scaling_factor.txt').

    Returns:
        Dict containing 'optimal_s', 'ci_lower', 'ci_upper', 'hypothesis_rejected', 'p_value'.
        Raises FileNotFoundError if the file does not exist.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Scaling results file not found: {input_path}")

    logger.info(f"Loading scaling results from {input_path}")

    data = {}
    with open(path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("Scaling Factor:"):
            data['optimal_s'] = float(line.split(":")[1].strip())
        elif line.startswith("95% CI:"):
            # Format: 95% CI: [0.9, 1.1]
            parts = line.split(":")[1].strip()
            parts = parts.strip("[]").split(",")
            data['ci_lower'] = float(parts[0].strip())
            data['ci_upper'] = float(parts[1].strip())
        elif line.startswith("Hypothesis Test"):
            # Format: Hypothesis Test (s=1.0): Rejected
            status = line.split(":")[1].strip()
            data['hypothesis_rejected'] = status == "Rejected"
        elif line.startswith("P-value:"):
            val = line.split(":")[1].strip()
            data['p_value'] = float(val) if val != "N/A" else None

    return data

def main():
    """
    Main entry point to execute the full scaling derivation and write results.
    This function orchestrates T022, T023, T024, and T025.
    """
    logger.info("Starting scaling factor derivation and export (T022-T025)...")

    # 1. Load raw energies (T022 input)
    raw_energies_path = "data/derived/raw_energies.csv"
    logger.info(f"Loading raw energies from {raw_energies_path}")
    df = load_raw_energies(raw_energies_path)

    if df is None or df.empty:
        error("Failed to load raw energies. Aborting.")
        return

    # 2. Fit scaling factor (T022)
    optimal_s, _ = fit_scaling_factor(df)
    logger.info(f"Optimal scaling factor found: {optimal_s:.6f}")

    # 3. Bootstrap analysis for CI and Hypothesis Test (T023, T024)
    ci_lower, ci_upper, p_value, hypothesis_rejected = bootstrap_scaling_analysis(df)
    logger.info(f"95% CI: [{ci_lower:.6f}, {ci_upper:.6f}]")
    logger.info(f"Hypothesis Test (s=1.0): {'Rejected' if hypothesis_rejected else 'Failed to Reject'}")

    # 4. Write results to file (T025)
    output_path = "data/derived/scaling_factor.txt"
    write_scaling_file(
        output_path=output_path,
        optimal_s=optimal_s,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_value=p_value,
        hypothesis_rejected=hypothesis_rejected
    )

    logger.info("Scaling factor derivation and export complete.")

if __name__ == "__main__":
    main()