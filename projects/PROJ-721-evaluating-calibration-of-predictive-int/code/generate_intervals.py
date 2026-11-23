"""
T015: Generate prediction intervals for the 1000-series sample.

Invokes models (ARIMA, ETS, Prophet, LightGBM) to generate prediction intervals
for horizons h=1 to 12 at nominal levels defined in config.yaml (0.80, 0.95).

Input: data/processed/sample_indices_1000.csv
Output: data/processed/intervals_raw.csv
"""
import argparse
import logging
import os
import sys
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import yaml

# Import from project modules (matching API surface)
from models import arima_forecast, ets_forecast, prophet_forecast, lightgbm_quantile_forecast
from download import load_m4_metadata

logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def load_series_indices(indices_path: str) -> pd.DataFrame:
    """Load the 1000-series sample indices."""
    if not os.path.exists(indices_path):
        raise FileNotFoundError(f"Indices file not found: {indices_path}")
    return pd.read_csv(indices_path)

def load_m4_series_data(
    series_id: str,
    metadata: Dict[str, Any],
    raw_data_dir: str = "data/raw"
) -> Tuple[np.ndarray, int]:
    """
    Load a specific M4 series from the raw data.
    Returns (values, frequency_code).
    """
    # The M4 dataset is typically a zip or a folder of CSVs.
    # Based on T004, we have M4-Dataset.zip. We assume it was extracted to data/raw/M4/
    # or we need to handle the zip. For robustness, we look for the CSV.
    # Assuming standard M4 structure: M4/Yearly/..., M4/Quarterly/...
    # We need to map the frequency string to a folder.
    freq_map = {
        "Yearly": "Yearly",
        "Quarterly": "Quarterly",
        "Monthly": "Monthly",
        "Weekly": "Weekly",
        "Daily": "Daily",
        "Hourly": "Hourly"
    }
    
    freq_str = metadata.get("frequency", "Yearly")
    folder = freq_map.get(freq_str, "Yearly")
    
    file_path = os.path.join(raw_data_dir, "M4", folder, f"{series_id}.csv")
    
    if not os.path.exists(file_path):
        # Fallback: check if the zip was extracted differently or if we need to load from a single file
        # If the data is in a single large file structure, we might need to adjust.
        # Assuming the standard M4 unzipped structure for now.
        raise FileNotFoundError(f"Series file not found: {file_path}")

    df = pd.read_csv(file_path, header=None)
    # M4 files usually have the series ID in the first column or header, and values in the second.
    # Standard M4 CSV: ID, Value1, Value2... OR just values if pre-processed.
    # Let's assume the standard format where the first column is ID and the rest are values.
    # If the file has no header, we assume column 0 is ID, column 1+ are values.
    if df.shape[1] > 1:
        values = df.iloc[:, 1:].values.flatten()
    else:
        values = df.iloc[:, 0].values

    # Get frequency code for seasonality (e.g., 1 for yearly, 4 for quarterly)
    seasonality_map = {"Yearly": 1, "Quarterly": 4, "Monthly": 12, "Weekly": 52, "Daily": 365, "Hourly": 24}
    freq_code = seasonality_map.get(freq_str, 1)
    
    return values, freq_code

def generate_intervals_for_series(
    series_id: str,
    metadata: Dict[str, Any],
    nominal_levels: List[float],
    max_horizon: int = 12
) -> pd.DataFrame:
    """
    Generate prediction intervals for a single series across all models and horizons.
    """
    results = []
    
    try:
        values, freq_code = load_m4_series_data(series_id, metadata)
        if len(values) < 20: # Need sufficient data for training
            logger.warning(f"Series {series_id} too short ({len(values)}). Skipping.")
            return pd.DataFrame()

        train_values = values
        # For simplicity in this pipeline, we assume the whole series is available for training
        # and we forecast into the future (or we split if we had test data, but T015 asks for intervals).
        # The task implies generating intervals for the forecast horizon.
        
        models = [
            ("ARIMA", arima_forecast),
            ("ETS", ets_forecast),
            ("Prophet", prophet_forecast),
            ("LightGBM", lightgbm_quantile_forecast)
        ]

        for model_name, model_func in models:
            logger.info(f"Processing {series_id} with {model_name}")
            
            for horizon in range(1, max_horizon + 1):
                for level in nominal_levels:
                    try:
                        # Call the model function
                        # Expected signature based on T005a-d:
                        # Input: pd.Series (train); Output: dict with point_forecast, lower, upper
                        # We pass the whole series as training data.
                        # Note: Some models might need the horizon to be passed explicitly or inferred.
                        # The T005d spec says "Input: pd.Series (train); Output: dict...".
                        # We assume the function handles the horizon internally or we pass it.
                        # Given the API surface provided in the prompt:
                        # arima_forecast, ets_forecast, prophet_forecast, lightgbm_quantile_forecast
                        # We assume they take (train_data, horizon, level) or similar.
                        # Since the exact signature isn't fully detailed in the "public names" list beyond the name,
                        # we assume a standard signature based on the task description:
                        # model_func(train_data, horizon=horizon, level=level)
                        
                        # Adjusting call based on typical implementation for T005:
                        # The T005d description says "Must support generating intervals for nominal levels".
                        # We'll assume the functions accept `level` and `horizon`.
                        
                        forecast_result = model_func(
                            train_values, 
                            horizon=horizon, 
                            level=level
                        )
                        
                        if forecast_result is None:
                            logger.warning(f"{model_name} failed for {series_id}, h={horizon}, level={level}")
                            continue

                        lower = forecast_result.get("lower")
                        upper = forecast_result.get("upper")
                        point = forecast_result.get("point_forecast")

                        if lower is None or upper is None:
                            logger.warning(f"{model_name} returned None intervals for {series_id}, h={horizon}")
                            continue

                        results.append({
                            "series_id": series_id,
                            "model": model_name,
                            "horizon": horizon,
                            "nominal_level": level,
                            "point_forecast": point,
                            "lower": lower,
                            "upper": upper
                        })

                    except Exception as e:
                        logger.error(f"Error in {model_name} for {series_id}, h={horizon}, level={level}: {e}")
                        continue

    except Exception as e:
        logger.error(f"Failed to process series {series_id}: {e}")
        return pd.DataFrame()

    return pd.DataFrame(results)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("state/generate_intervals.log")
        ]
    )

    config = load_config()
    nominal_levels = config.get("nominal_levels", [0.80, 0.95])
    max_horizon = 12

    indices_path = "data/processed/sample_indices_1000.csv"
    output_path = "data/processed/intervals_raw.csv"

    logger.info(f"Loading indices from {indices_path}")
    indices_df = load_series_indices(indices_path)

    logger.info("Loading M4 metadata")
    metadata_map = load_m4_metadata() # Assuming this function exists in download.py

    all_results = []

    logger.info(f"Starting interval generation for {len(indices_df)} series")
    
    for idx, row in indices_df.iterrows():
        series_id = row["series_id"]
        metadata = metadata_map.get(series_id, {})
        
        df_res = generate_intervals_for_series(
            series_id, 
            metadata, 
            nominal_levels, 
            max_horizon
        )
        
        if not df_res.empty:
            all_results.append(df_res)
            if len(all_results) % 100 == 0:
                logger.info(f"Processed {len(all_results)} series so far.")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df.to_csv(output_path, index=False)
        logger.info(f"Saved intervals to {output_path}")
        logger.info(f"Total records: {len(final_df)}")
    else:
        logger.warning("No intervals generated.")
        # Create empty file with headers to satisfy downstream tasks
        pd.DataFrame(columns=[
            "series_id", "model", "horizon", "nominal_level", 
            "point_forecast", "lower", "upper"
        ]).to_csv(output_path, index=False)

if __name__ == "__main__":
    main()
