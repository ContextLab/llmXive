import os
import sys
import logging
import pandas as pd
import numpy as np
from scipy import stats
from logging_config import setup_logging, get_module_logger

def calculate_power_cohen_d(effect_size, sample_size, alpha=0.05):
    """Calculates statistical power for a given effect size and sample size."""
    try:
        result = stats.norm.cdf(effect_size / np.sqrt(2)) * (1 - stats.norm.cdf(-effect_size / np.sqrt(2)))
        if result < 0 or result > 1:
            return None  # Handle invalid power values
    except Exception as e:
        logging.warning(f"Error calculating power: {e}")
        return None

def load_and_validate_data(file_path):
    """Loads data from a CSV file and validates required columns."""
    try:
        df = pd.read_csv(file_path)
        required_columns = ['study_id', 'year', 'field', 'original_study_id', 'effect_size', 'sample_size']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns")
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return None
    except pd.errors.EmptyDataError:
        logging.error(f"File is empty: {file_path}")
        return None
    except ValueError as e:
        logging.error(f"Validation error: {e}")
        return None

def filter_and_log_invalid_rows(df):
    """Filters out invalid rows and logs warnings."""
    valid_rows = []
    for index, row in df.iterrows():
        if pd.isna(row['effect_size']) or pd.isna(row['sample_size']):
            logging.warning(f"Skipping row {index} due to missing effect_size or sample_size")
            continue

        if row['sample_size'] <= 0:
            logging.warning(f"Skipping row {index} due to non-positive sample size")
            continue

        valid_rows.append(row)

    return pd.DataFrame(valid_rows)

def compute_power_estimates(df):
    """Computes power estimates for each study."""
    df['power_est'] = df.apply(lambda row: calculate_power_cohen_d(row['effect_size'], row['sample_size']), axis=1)
    return df

def validate_output(file_path):
  """Validates the output file."""
  try:
      df = pd.read_csv(file_path)
      if 'power_est' not in df.columns:
          raise ValueError("Missing power_est column")
      if df['power_est'].isnull().any():
          raise ValueError("Contains null values in power_est column")
      return True
  except Exception as e:
      logging.error(f"Output validation failed: {e}")
      return False

def main():
    """Main function to load data, compute power estimates, and save the results."""
    setup_logging()
    logger = get_module_logger(__name__)
    input_file = 'data/raw/data.csv'
    output_file = 'data/derived/power_estimates.csv'

    df = load_and_validate_data(input_file)
    if df is None:
        sys.exit(1)

    df = filter_and_log_invalid_rows(df)
    df = compute_power_estimates(df)

    if validate_output(output_file):
      logger.info("Output file already exists, skipping save.")
    else:
      df.to_csv(output_file, index=False)
      logger.info(f"Power estimates saved to {output_file}")


if __name__ == "__main__":
    main()
