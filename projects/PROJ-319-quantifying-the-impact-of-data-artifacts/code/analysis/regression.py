"""
Regression module for calibration functions.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats

def fit_calibration_models(root: Path) -> None:
    """
    Fit calibration models (linear/polynomial) linking artifact intensity to bias.
    Uses AIC for model selection.
    Outputs data/processed/calibration_functions.json.
    """
    logger = logging.getLogger("regression")
    logger.info("Fitting Calibration Models...")

    noise_stats_path = root / "data" / "processed" / "noise_stats.csv"
    sat_stats_path = root / "data" / "processed" / "saturation_stats.csv"
    output_path = root / "data" / "processed" / "calibration_functions.json"

    models = {}

    # Fit Noise Model
    if noise_stats_path.exists():
        # Read data
        data = []
        with open(noise_stats_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        x = np.array([float(row['sigma']) for row in data])
        y = np.array([float(row['mean_bias']) for row in data])

        if len(x) > 1:
            # Linear fit
            slope, intercept, r, p, std_err = stats.linregress(x, y)
            y_pred = slope * x + intercept
            rss = np.sum((y - y_pred)**2)
            n = len(x)
            k = 2 # slope, intercept
            aic_linear = n * np.log(rss/n) + 2*k

            # Quadratic fit
            coeffs = np.polyfit(x, y, 2)
            p = np.poly1d(coeffs)
            y_pred_q = p(x)
            rss_q = np.sum((y - y_pred_q)**2)
            k_q = 3
            aic_quad = n * np.log(rss_q/n) + 2*k_q

            if aic_linear < aic_quad:
                models['ellipticity_model'] = {
                    "type": "linear",
                    "slope": slope,
                    "intercept": intercept,
                    "aic": aic_linear
                }
            else:
                models['ellipticity_model'] = {
                    "type": "quadratic",
                    "coefficients": coeffs.tolist(),
                    "aic": aic_quad
                }
        else:
            models['ellipticity_model'] = {"type": "insufficient_data"}

    # Fit Saturation Model
    if sat_stats_path.exists():
        data = []
        with open(sat_stats_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        x = np.array([float(row['saturation_fraction']) for row in data])
        y = np.array([float(row['mean_bias']) for row in data])

        if len(x) > 1:
            slope, intercept, r, p, std_err = stats.linregress(x, y)
            y_pred = slope * x + intercept
            rss = np.sum((y - y_pred)**2)
            n = len(x)
            k = 2
            aic_linear = n * np.log(rss/n) + 2*k

            coeffs = np.polyfit(x, y, 2)
            p = np.poly1d(coeffs)
            y_pred_q = p(x)
            rss_q = np.sum((y - y_pred_q)**2)
            k_q = 3
            aic_quad = n * np.log(rss_q/n) + 2*k_q

            if aic_linear < aic_quad:
                models['asymmetry_model'] = {
                    "type": "linear",
                    "slope": slope,
                    "intercept": intercept,
                    "aic": aic_linear
                }
            else:
                models['asymmetry_model'] = {
                    "type": "quadratic",
                    "coefficients": coeffs.tolist(),
                    "aic": aic_quad
                }
        else:
            models['asymmetry_model'] = {"type": "insufficient_data"}

    # Save
    with open(output_path, 'w') as f:
        json.dump(models, f, indent=2)

    logger.info(f"Calibration models saved to {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, required=True)
    args = parser.parse_args()
    root = Path(args.root)
    fit_calibration_models(root)

if __name__ == "__main__":
    main()
