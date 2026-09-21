import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
import json
from logger import get_logger, info, warning, error, critical
from config import get_config, set_random_seed
from utils import calculate_metrics, bootstrap_mae, bootstrap_mean

def load_scaling_factor(path: Path) -> float:
    """Load the scaling factor from a text file."""
    logger = get_logger(__name__)
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Scaling factor file not found: {path}")
    with open(path, "r") as f:
        content = f.read().strip()
        # Parse the value assuming format like "s = 1.234" or just "1.234"
        if "=" in content:
            value = float(content.split("=")[1].strip())
        else:
            value = float(content)
    logger.info(f"Loaded scaling factor: {value}")
    return value

def extract_psi4_energies(output_file: Path) -> Dict[str, float]:
    """
    Extract total energy and D3 dispersion contribution from a Psi4 output file.

    Args:
        output_file: Path to the Psi4 output file.

    Returns:
        Dictionary with keys 'total_energy' and 'd3_dispersion_energy'.
    """
    logger = get_logger(__name__)
    with open(output_file, "r") as f:
        content = f.read()

    # Simple parsing logic (assumes standard Psi4 output format)
    # In a real scenario, this would be more robust
    total_energy = None
    d3_energy = None

    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "Final Energy" in line or "E(" in line and ")" in line:
            # Try to find the final energy value
            parts = line.split()
            for part in parts:
                try:
                    val = float(part)
                    if val < 0:  # Energies are typically negative
                        total_energy = val
                        break
                except ValueError:
                    continue
            if total_energy is not None:
                break

    # Look for D3 dispersion contribution
    # Psi4 usually prints "Dispersion energy" or similar
    for line in lines:
        if "Dispersion" in line and "energy" in line.lower():
            parts = line.split()
            for part in parts:
                try:
                    val = float(part)
                    d3_energy = val
                    break
                except ValueError:
                    continue
            if d3_energy is not None:
                break

    if total_energy is None:
        error(f"Could not find total energy in {output_file}")
        raise ValueError(f"Total energy not found in {output_file}")
    if d3_energy is None:
        warning(f"D3 dispersion energy not found in {output_file}, defaulting to 0.0")
        d3_energy = 0.0

    return {
        "total_energy": total_energy,
        "d3_dispersion_energy": d3_energy,
    }

def compute_statistics(
    reference_energies: List[float],
    dft_energies: List[float],
    d3_energies: List[float],
    scaling_factor: Optional[float] = None,
) -> Dict[str, float]:
    """
    Compute error statistics between DFT and reference energies.

    Args:
        reference_energies: List of reference (CCSD(T)/CBS) energies.
        dft_energies: List of DFT total energies.
        d3_energies: List of D3 dispersion energies.
        scaling_factor: Optional scaling factor for D3 term.

    Returns:
        Dictionary with MAE, RMSE, MSE, MSE, and Mean Signed Error.
    """
    logger = get_logger(__name__)
    if len(reference_energies) != len(dft_energies):
        raise ValueError("Reference and DFT energy lists must have the same length")

    errors = np.array(dft_energies) - np.array(reference_energies)

    if scaling_factor is not None:
        # Corrected DFT energy = E_base + (s - 1) * E_D3 ?
        # Or E_corrected = E_DFT_base + s * E_D3?
        # Assuming the task implies: E_corrected = E_DFT_without_D3 + s * E_D3
        # But we only have E_DFT_total and E_D3.
        # Let's assume E_DFT_total = E_base + E_D3 (raw)
        # Then E_corrected = E_base + s * E_D3 = (E_DFT_total - E_D3) + s * E_D3
        # = E_DFT_total + (s - 1) * E_D3
        corrected_errors = np.array(dft_energies) + (scaling_factor - 1) * np.array(d3_energies) - np.array(reference_energies)
        metrics = calculate_metrics(corrected_errors)
        logger.info(f"Computed metrics with scaling factor {scaling_factor}")
    else:
        metrics = calculate_metrics(errors)
        logger.info("Computed raw metrics (no scaling)")

    return metrics

def calculate_metrics(errors: np.ndarray) -> Dict[str, float]:
    """
    Calculate error metrics (MAE, RMSE, MSE, MSE, MSE).
    This is a wrapper for utils.calculate_metrics to ensure compatibility.
    """
    return calculate_metrics(errors)

def bootstrap_analysis(
    reference_energies: List[float],
    dft_energies: List[float],
    d3_energies: List[float],
    n_replicates: int = 1000,
    scaling_factor: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to compute confidence intervals for MAE.

    Args:
        reference_energies: List of reference energies.
        dft_energies: List of DFT energies.
        d3_energies: List of D3 energies.
        n_replicates: Number of bootstrap replicates.
        scaling_factor: Optional scaling factor.

    Returns:
        Dictionary with MAE, 95% CI for MAE.
    """
    logger = get_logger(__name__)
    config = get_config()
    set_random_seed(config.seed)

    errors = np.array(dft_energies) - np.array(reference_energies)
    if scaling_factor is not None:
        errors = errors + (scaling_factor - 1) * np.array(d3_energies)

    mae_values = []
    for _ in range(n_replicates):
        indices = np.random.choice(len(errors), size=len(errors), replace=True)
        sample_errors = errors[indices]
        mae = np.mean(np.abs(sample_errors))
        mae_values.append(mae)

    mae_values = np.array(mae_values)
    mae_mean = np.mean(mae_values)
    ci_lower = np.percentile(mae_values, 2.5)
    ci_upper = np.percentile(mae_values, 97.5)

    logger.info(f"Bootstrap MAE: {mae_mean:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

    return {
        "mae": mae_mean,
        "mae_ci_lower": ci_lower,
        "mae_ci_upper": ci_upper,
        "n_replicates": n_replicates,
    }

def analyze_and_export(
    raw_energies_path: Path,
    output_dir: Path,
    scaling_factor_path: Optional[Path] = None,
) -> None:
    """
    Analyze energies and export results to CSV and JSON.

    Args:
        raw_energies_path: Path to raw energies CSV.
        output_dir: Directory for output files.
        scaling_factor_path: Optional path to scaling factor file.
    """
    logger = get_logger(__name__)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(raw_energies_path)

    reference_energies = df["reference_energy"].tolist()
    dft_energies = df["dft_total_energy"].tolist()
    d3_energies = df["d3_dispersion_energy"].tolist()

    scaling_factor = None
    if scaling_factor_path and scaling_factor_path.exists():
        scaling_factor = load_scaling_factor(scaling_factor_path)

    metrics = compute_statistics(
        reference_energies,
        dft_energies,
        d3_energies,
        scaling_factor=scaling_factor,
    )

    bootstrap_results = bootstrap_analysis(
        reference_energies,
        dft_energies,
        d3_energies,
        scaling_factor=scaling_factor,
    )

    # Export metrics to JSON
    metrics_path = output_dir / "statistics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    # Export bootstrap results
    bootstrap_path = output_dir / "bootstrap_results.json"
    with open(bootstrap_path, "w") as f:
        json.dump(bootstrap_results, f, indent=2)
    logger.info(f"Bootstrap results saved to {bootstrap_path}")

    # Update raw_energies.csv with metrics if needed
    # (Optional: add columns for corrected errors if scaling is applied)
    if scaling_factor is not None:
        df["corrected_error"] = (
            np.array(dft_energies) + (scaling_factor - 1) * np.array(d3_energies)
            - np.array(reference_energies)
        )
        corrected_csv_path = output_dir / "corrected_energies.csv"
        df.to_csv(corrected_csv_path, index=False)
        logger.info(f"Corrected energies saved to {corrected_csv_path}")

def main() -> None:
    """Main entry point for energy analysis."""
    logger = get_logger(__name__)
    config = get_config()
    set_random_seed(config.seed)

    # Example usage:
    # analyze_and_export(
    #     Path("data/derived/raw_energies.csv"),
    #     Path("data/derived"),
    #     scaling_factor_path=Path("data/derived/scaling_factor.txt"),
    # )

    logger.info("Energy analyzer ready. Call analyze_and_export() with your files.")

if __name__ == "__main__":
    main()