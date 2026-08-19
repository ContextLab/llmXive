"""
TDP Constant Generation Script.

Reads the calibration run results from data/processed/calibration_run.json
and generates data/processed/calibrated_tdp.json with the estimated TDP,
source, error margin, and confidence interval.

Constraint: This script MUST fail loudly if calibration data is missing,
malformed, or indicates a failed calibration. NO fallback to constant values.
"""

import json
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "calibration_run.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "calibrated_tdp.json"


class CalibrationDataError(Exception):
    """Raised when calibration data is missing, invalid, or indicates failure."""
    pass


def load_calibration_data(path: Path) -> Dict[str, Any]:
    """
    Load and validate the calibration run JSON.

    Raises:
        CalibrationDataError: If file not found, malformed, or indicates failure.
    """
    if not path.exists():
        raise CalibrationDataError(
            f"Calibration file not found: {path}. "
            "Ensure T008a (calibrate_tdp.py) has been executed successfully."
        )

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise CalibrationDataError(f"Invalid JSON in calibration file: {e}")

    # Validate required fields
    required_fields = ["workload_type", "cpu_percent", "duration", "estimated_tdp_watts"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise CalibrationDataError(
            f"Calibration data missing required fields: {missing}"
        )

    # Check for explicit failure indicators if any (e.g., from T008a logic)
    if data.get("status") == "failed" or data.get("success") is False:
        raise CalibrationDataError(
            "Calibration run reported failure. Cannot generate TDP constant."
        )

    # Validate numeric fields
    if not isinstance(data["estimated_tdp_watts"], (int, float)):
        raise CalibrationDataError("estimated_tdp_watts must be a number")
    if data["estimated_tdp_watts"] <= 0:
        raise CalibrationDataError(
            f"estimated_tdp_watts must be positive, got {data['estimated_tdp_watts']}"
        )

    return data


def calculate_error_margin_and_ci(
    tdp_watts: float,
    cpu_percent: float,
    duration: float
) -> tuple[float, float]:
    """
    Calculate a conservative error margin and 95% confidence interval width.

    Since we only have a single calibration run, we estimate uncertainty based on
    CPU utilization variance proxy. A higher CPU% variance (proxy: 100 - cpu_percent)
    suggests more noise.

    Note: In a production setting with multiple runs, this would use standard deviation.
    Here we use a heuristic based on the single run's CPU utilization stability.
    """
    # Heuristic: assume ~5% relative error base, scaled by CPU stability
    base_relative_error = 0.05
    stability_factor = 1.0 + (100.0 - cpu_percent) / 200.0  # More error if CPU not saturated

    relative_error = base_relative_error * stability_factor
    error_margin = tdp_watts * relative_error

    # 95% CI is approx +/- 1.96 * SE. With single sample, we use error_margin as half-width
    confidence_interval_width = 2 * error_margin

    return error_margin, confidence_interval_width


def generate_calibrated_tdp(calibration_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the calibrated TDP output structure.
    """
    tdp_watts = calibration_data["estimated_tdp_watts"]
    cpu_percent = calibration_data["cpu_percent"]
    duration = calibration_data["duration"]

    error_margin, ci_width = calculate_error_margin_and_ci(
        tdp_watts, cpu_percent, duration
    )

    return {
        "tdp_watts": round(tdp_watts, 2),
        "source": "calibration",
        "error_margin": round(error_margin, 4),
        "confidence_interval": round(ci_width, 4),
        "calibration_source": {
            "workload_type": calibration_data["workload_type"],
            "cpu_percent": cpu_percent,
            "duration_seconds": duration
        }
    }


def save_calibrated_tdp(data: Dict[str, Any], path: Path) -> None:
    """Save the calibrated TDP data to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def main() -> int:
    """
    Main entry point for TDP constant generation.

    Returns:
        0 on success, 1 on failure (with error message printed to stderr).
    """
    try:
        # Load calibration data (fails loudly if missing/invalid)
        calibration_data = load_calibration_data(CALIBRATION_INPUT_PATH)

        # Generate calibrated TDP structure
        calibrated_tdp = generate_calibrated_tdp(calibration_data)

        # Save output
        save_calibrated_tdp(calibrated_tdp, OUTPUT_PATH)

        print(f"Successfully generated: {OUTPUT_PATH}")
        print(f"  TDP: {calibrated_tdp['tdp_watts']} W")
        print(f"  Source: {calibrated_tdp['source']}")
        print(f"  Error Margin: ±{calibrated_tdp['error_margin']} W")
        print(f"  95% CI Width: {calibrated_tdp['confidence_interval']} W")

        return 0

    except CalibrationDataError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
