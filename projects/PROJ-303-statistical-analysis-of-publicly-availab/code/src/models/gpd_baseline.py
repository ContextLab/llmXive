"""
GPD Baseline Model Implementation.

Fits an independent Generalized Pareto Distribution (GPD) for each station
using scipy.stats. This serves as the baseline model for comparison against
the Spatial-GPD model.

Dependencies:
    - scipy.stats (Gaussian/GPD distributions)
    - pandas (data handling)
    - src.config (configuration)
    - src.pipeline.logging_config (logging)
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, Any, List
from pathlib import Path
import logging

from scipy import stats
from scipy.optimize import minimize_scalar

from src.config import get_config
from src.pipeline.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)


class GPDBaseline:
    """
    Independent GPD model for extreme event modeling.

    Fits a separate GPD for each station's exceedances over a threshold.
    Parameters are estimated using Maximum Likelihood Estimation (MLE).

    Attributes:
        parameters (Dict[str, Dict[str, float]]): Fitted parameters per station
            { station_id: {'shape': float, 'scale': float, 'loc': float} }
        station_ids (List[str]): List of stations for which parameters were fitted.
        fit_status (Dict[str, str]): Status of the fit for each station
            ('success', 'failed', 'convergence_warning')
    """

    def __init__(self, method: str = "mle"):
        """
        Initialize the GPD Baseline model.

        Args:
            method (str): Fitting method. Currently only 'mle' is supported.
        """
        self.method = method
        self.parameters: Dict[str, Dict[str, float]] = {}
        self.station_ids: List[str] = []
        self.fit_status: Dict[str, str] = {}
        self._fitted = False

    def fit(self, exceedances_df: pd.DataFrame, threshold_col: str = 'threshold_value',
            magnitude_col: str = 'magnitude') -> 'GPDBaseline':
        """
        Fit independent GPD models for each station.

        Args:
            exceedances_df (pd.DataFrame): DataFrame containing extreme events.
                Expected columns: 'station_id', 'magnitude', 'threshold_value'.
            threshold_col (str): Column name for the threshold value.
            magnitude_col (str): Column name for the magnitude of exceedance.

        Returns:
            GPDBaseline: Self with fitted parameters.

        Raises:
            ValueError: If required columns are missing or data is invalid.
            RuntimeError: If no stations have sufficient data for fitting.
        """
        logger.info("Starting GPD baseline model fitting...")

        required_cols = {'station_id', magnitude_col, threshold_col}
        if not required_cols.issubset(exceedances_df.columns):
            missing = required_cols - set(exceedances_df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        # Group by station
        grouped = exceedances_df.groupby('station_id')
        self.station_ids = list(grouped.groups.keys())
        self.parameters = {}
        self.fit_status = {}

        if len(self.station_ids) == 0:
            raise RuntimeError("No stations found in the exceedances dataframe.")

        total_stations = len(self.station_ids)
        success_count = 0

        for i, station_id in enumerate(self.station_ids):
            station_data = grouped.get_group(station_id)
            magnitudes = station_data[magnitude_col].values

            if len(magnitudes) < 10:
                logger.warning(f"Station {station_id}: Only {len(magnitudes)} exceedances. "
                             "GPD fit may be unreliable.")
                self.fit_status[station_id] = 'insufficient_data'
                continue

            try:
                # GPD is typically defined for x > 0 (exceedances above threshold)
                # We assume 'magnitude' is already (value - threshold)
                # If magnitude can be negative or zero, we filter or shift.
                # Based on T014 logic, magnitude = value - threshold, so should be > 0.
                # We filter strictly positive exceedances for stability.
                valid_mags = magnitudes[magnitudes > 1e-8]

                if len(valid_mags) < 10:
                    logger.warning(f"Station {station_id}: After filtering non-positive, "
                                 f"only {len(valid_mags)} points. Skipping fit.")
                    self.fit_status[station_id] = 'insufficient_data'
                    continue

                # Fit GPD using scipy.stats.gpd.fit
                # gpd.fit returns (shape, loc, scale)
                # We fix loc=0 since magnitudes are already exceedances above threshold
                shape, loc, scale = stats.gpd.fit(valid_mags, floc=0)

                self.parameters[station_id] = {
                    'shape': float(shape),
                    'loc': float(loc), # Should be ~0
                    'scale': float(scale)
                }
                self.fit_status[station_id] = 'success'
                success_count += 1

            except Exception as e:
                logger.error(f"Station {station_id}: GPD fit failed with error: {e}")
                self.fit_status[station_id] = 'failed'
                continue

        if success_count == 0:
            raise RuntimeError("Failed to fit GPD for any station.")

        self._fitted = True
        logger.info(f"GPD baseline fitting complete. "
                  f"Successfully fitted {success_count}/{total_stations} stations.")

        return self

    def predict_probability(self, station_id: str, threshold_value: float,
                            value: float) -> float:
        """
        Predict the probability P(X > value | X > threshold_value) for a station.

        Uses the fitted GPD parameters to calculate the survival function.

        Args:
            station_id (str): The station identifier.
            threshold_value (float): The threshold used for exceedance.
            value (float): The value to evaluate the probability for.

        Returns:
            float: Probability P(X > value).

        Raises:
            ValueError: If the model is not fitted or station is unknown.
        """
        if not self._fitted:
            raise RuntimeError("Model has not been fitted yet. Call fit() first.")

        if station_id not in self.parameters:
            raise ValueError(f"Station {station_id} was not fitted or has insufficient data.")

        if value <= threshold_value:
            return 1.0

        params = self.parameters[station_id]
        shape = params['shape']
        scale = params['scale']
        loc = params['loc']

        # GPD survival function: P(X > x) = (1 + xi * (x - loc) / sigma)^(-1/xi)
        # Since we fitted with floc=0 on exceedances (x - threshold),
        # the 'x' in the formula is (value - threshold_value).
        exceedance = value - threshold_value

        # Handle edge case where shape is close to 0 (Exponential limit)
        if abs(shape) < 1e-8:
            prob = np.exp(-exceedance / scale)
        else:
            arg = 1 + shape * exceedance / scale
            if arg <= 0:
                # Value is beyond the finite upper bound of the distribution
                prob = 0.0
            else:
                prob = np.power(arg, -1.0 / shape)

        return float(prob)

    def predict_intensity(self, station_id: str, exceedance_prob: float,
                          threshold_value: float) -> float:
        """
        Predict the intensity (value) corresponding to a given exceedance probability.

        Inverts the CDF of the GPD.

        Args:
            station_id (str): The station identifier.
            exceedance_prob (float): The target exceedance probability P(X > x).
            threshold_value (float): The threshold used for exceedance.

        Returns:
            float: The predicted value x.

        Raises:
            ValueError: If the model is not fitted or station is unknown.
        """
        if not self._fitted:
            raise RuntimeError("Model has not been fitted yet. Call fit() first.")

        if station_id not in self.parameters:
            raise ValueError(f"Station {station_id} was not fitted or has insufficient data.")

        if not (0 < exceedance_prob <= 1):
            raise ValueError("Exceedance probability must be in (0, 1].")

        params = self.parameters[station_id]
        shape = params['shape']
        scale = params['scale']
        loc = params['loc']

        # Inverse CDF (Quantile function) for GPD
        # x = loc + (sigma / xi) * ((1 - p)^(-xi) - 1)
        # Here p is the CDF value, so 1 - p is the exceedance probability.
        # Let q = exceedance_prob = 1 - p.
        # x_exceedance = (scale / shape) * (q^(-shape) - 1)
        # value = threshold_value + x_exceedance

        if abs(shape) < 1e-8:
            # Exponential limit: x = -scale * ln(q)
            x_exceedance = -scale * np.log(exceedance_prob)
        else:
            x_exceedance = (scale / shape) * (np.power(exceedance_prob, -shape) - 1)

        predicted_value = threshold_value + x_exceedance
        return float(predicted_value)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the fitted model.

        Returns:
            Dict[str, Any]: Summary statistics including fitted station count,
                parameter ranges, and fit status counts.
        """
        if not self._fitted:
            return {"status": "not_fitted"}

        shape_values = [p['shape'] for p in self.parameters.values()]
        scale_values = [p['scale'] for p in self.parameters.values()]

        status_counts = {}
        for s in self.fit_status.values():
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "total_stations": len(self.station_ids),
            "fitted_stations": len(self.parameters),
            "shape_range": (min(shape_values), max(shape_values)),
            "scale_range": (min(scale_values), max(scale_values)),
            "status_counts": status_counts
        }


def fit_gpd_baseline(exceedances_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main function to fit the GPD baseline and save parameters.

    Args:
        exceedances_path (str): Path to the parquet file with extreme events.
        output_path (str): Path to save the fitted parameters (JSON).

    Returns:
        Dict[str, Any]: Summary of the fitting process.
    """
    logger.info(f"Loading exceedances from {exceedances_path}")
    df = pd.read_parquet(exceedances_path)

    logger.info(f"Loaded {len(df)} extreme events.")

    model = GPDBaseline()
    model.fit(df)

    # Save parameters
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert parameters to a serializable format
    params_dict = {
        "model_type": "Independent GPD",
        "fitted_stations": model.parameters,
        "fit_status": model.fit_status,
        "summary": model.get_summary()
    }

    import json
    with open(output_path, 'w') as f:
        json.dump(params_dict, f, indent=2)

    logger.info(f"GPD baseline parameters saved to {output_path}")
    return model.get_summary()


def main():
    """Entry point for the GPD baseline script."""
    config = get_config()
    exceedances_path = config.get('paths', {}).get('extreme_events_parquet',
                                                   'data/processed/extreme_events.parquet')
    output_path = config.get('paths', {}).get('gpd_baseline_params',
                                              'outputs/models/gpd_baseline_params.json')

    try:
        summary = fit_gpd_baseline(exceedances_path, output_path)
        print(f"Model fitting successful. Summary: {summary}")
    except Exception as e:
        logger.critical(f"Failed to fit GPD baseline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
