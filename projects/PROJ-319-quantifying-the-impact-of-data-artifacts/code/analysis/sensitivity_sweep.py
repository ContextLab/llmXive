"""
Sensitivity analysis sweep for saturation-induced bias on asymmetry.

This module implements the saturation sweep logic to quantify how varying
saturation levels bias asymmetry measurements. It processes a clean synthetic
image, applies saturation clipping across a defined range, measures asymmetry,
and outputs statistical summaries to CSV.

The sweep range is 0.0 to 0.5 in 0.05 increments as per T024 requirements.
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

# Local imports from existing API surface
from code.config import get_project_root, SATURATION_LEVELS
from code.synthetic.generator import generate_nebula_base, calculate_true_asymmetry
from code.synthetic.artifacts import clip_saturation
from code.metrics.asymmetry import calculate_asymmetry
from code.io.writer import compute_array_checksum, save_metadata_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_sensitivity_sweep(
    base_image: np.ndarray,
    true_asymmetry: float,
    saturation_levels: List[float],
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Run the saturation sensitivity sweep on a single base image.

    Args:
        base_image: Clean synthetic nebula image (2D numpy array).
        true_asymmetry: Ground truth asymmetry value.
        saturation_levels: List of saturation fractions to test (e.g., 0.0, 0.05, ... 0.5).
        seed: Random seed for reproducibility.

    Returns:
        List of dictionaries containing sweep results.
    """
    rng = np.random.default_rng(seed)
    results = []
    base_checksum = compute_array_checksum(base_image)

    logger.info(f"Starting saturation sweep on image with checksum {base_checksum[:8]}...")
    logger.info(f"True asymmetry: {true_asymmetry:.6f}")
    logger.info(f"Testing {len(saturation_levels)} saturation levels: {saturation_levels}")

    for sat_frac in saturation_levels:
        try:
            # Apply saturation clipping
            clipped_image, clipped_stats = clip_saturation(
                base_image,
                saturation_fraction=sat_frac,
                rng=rng
            )

            # Measure asymmetry on clipped image
            measured_asymmetry = calculate_asymmetry(clipped_image)

            # Calculate bias
            bias = measured_asymmetry - true_asymmetry

            # Validate that clipping actually occurred (unless sat_frac is 0)
            if sat_frac > 0.0:
                original_max = float(np.max(base_image))
                clipped_max = float(np.max(clipped_image))
                if clipped_max == original_max and sat_frac > 0.001:
                    logger.warning(
                        f"Saturation level {sat_frac:.2f} produced no clipping. "
                        f"Original max: {original_max}, Clipped max: {clipped_max}. "
                        "This may indicate a very bright image or edge case."
                    )

            result_entry = {
                "saturation_fraction": float(sat_frac),
                "asymmetry_mean": float(measured_asymmetry),
                "asymmetry_std": 0.0,  # Single measurement, std is 0
                "bias": float(bias),
                "true_asymmetry": float(true_asymmetry),
                "image_checksum": base_checksum,
                "valid": True
            }

            results.append(result_entry)
            logger.info(
                f"Saturation {sat_frac:.2f}: Asymmetry={measured_asymmetry:.6f}, "
                f"Bias={bias:.6f}"
            )

        except Exception as e:
            logger.error(f"Error at saturation level {sat_frac}: {e}", exc_info=True)
            results.append({
                "saturation_fraction": float(sat_frac),
                "asymmetry_mean": None,
                "asymmetry_std": None,
                "bias": None,
                "true_asymmetry": float(true_asymmetry),
                "image_checksum": base_checksum,
                "valid": False,
                "error": str(e)
            })

    return results

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save sweep results to CSV.

    Args:
        results: List of result dictionaries from run_sensitivity_sweep.
        output_path: Path to save the CSV file.
    """
    if not results:
        raise ValueError("No results to save.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "saturation_fraction",
        "asymmetry_mean",
        "asymmetry_std",
        "bias",
        "true_asymmetry",
        "image_checksum",
        "valid"
    ]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results saved to {output_path}")

def generate_statistical_summary(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a statistical summary JSON file verifying monotonic trends.

    Args:
        results: List of result dictionaries.
        output_path: Path to save the summary JSON.
    """
    valid_results = [r for r in results if r.get("valid", False) and r["asymmetry_mean"] is not None]

    if not valid_results:
        logger.warning("No valid results to summarize.")
        return

    saturation_fractions = [r["saturation_fraction"] for r in valid_results]
    asymmetry_means = [r["asymmetry_mean"] for r in valid_results]
    biases = [r["bias"] for r in valid_results]

    # Check for monotonic trend (asymmetry should generally increase with saturation)
    increasing_count = sum(
        1 for i in range(1, len(asymmetry_means))
        if asymmetry_means[i] >= asymmetry_means[i-1]
    )
    monotonic_ratio = increasing_count / (len(asymmetry_means) - 1) if len(asymmetry_means) > 1 else 1.0

    # Check if bias is positive (indicating saturation inflates asymmetry)
    positive_bias_count = sum(1 for b in biases if b > 0)
    bias_trend = "positive" if positive_bias_count > len(biases) / 2 else "mixed/negative"

    summary = {
        "total_points": len(valid_results),
        "saturation_range": [min(saturation_fractions), max(saturation_fractions)],
        "asymmetry_range": [min(asymmetry_means), max(asymmetry_means)],
        "monotonic_trend_ratio": float(monotonic_ratio),
        "bias_trend": bias_trend,
        "mean_bias": float(np.mean(biases)),
        "std_bias": float(np.std(biases)),
        "conclusion": (
            "Saturation appears to induce a " + bias_trend + " bias on asymmetry. "
            f"Monotonic trend ratio: {monotonic_ratio:.2f}"
        )
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Statistical summary saved to {output_path}")
    logger.info(f"Conclusion: {summary['conclusion']}")

def main() -> None:
    """
    Main entry point for the sensitivity sweep analysis.
    """
    project_root = get_project_root()
    output_csv = project_root / "data" / "processed" / "saturation_sweep.csv"
    output_summary = project_root / "data" / "processed" / "saturation_sweep_summary.json"

    logger.info(f"Project root: {project_root}")

    # 1. Generate a clean synthetic nebula as the base image
    # We use a single representative image for the sweep to ensure consistency
    # across saturation levels.
    logger.info("Generating base synthetic nebula image...")
    seed = 42
    base_image, true_params = generate_nebula_base(seed=seed)

    true_asymmetry = calculate_true_asymmetry(base_image)
    logger.info(f"Base image generated. True asymmetry: {true_asymmetry:.6f}")

    # 2. Define saturation levels (0.0 to 0.5, step 0.05)
    saturation_levels = [0.0 + i * 0.05 for i in range(11)]  # 0.0, 0.05, ..., 0.5

    # 3. Run the sweep
    results = run_sensitivity_sweep(
        base_image=base_image,
        true_asymmetry=true_asymmetry,
        saturation_levels=saturation_levels,
        seed=seed
    )

    # 4. Save CSV results
    save_results(results, output_csv)

    # 5. Generate statistical summary
    generate_statistical_summary(results, output_summary)

    logger.info("Sensitivity sweep analysis complete.")

if __name__ == "__main__":
    main()