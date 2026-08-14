import os
import sys
import pickle
import logging
from pathlib import Path

def load_and_prepare_data(data_path):
    """Loads data, handles missing values, and logs warnings."""
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        logging.error(f"Data file not found at {data_path}")
        return None

    # Handle NaN in effect_size or sample_size by dropping the row
    if df['effect_size'].isnull().any():
        for index in df[df['effect_size'].isnull()].index:
            logging.warning(f"Skipping row {index} due to NaN in effect_size")
            df = df.drop(index)

    if df['sample_size'].isnull().any():
        for index in df[df['sample_size'].isnull()].index:
            logging.warning(f"Skipping row {index} due to NaN in sample_size")
            df = df.drop(index)

    # Handle zero variance fields (avoid division by zero)
    if df['sample_size'].nunique() == 1 and df['sample_size'].iloc[0] == 0:  # Check for all zeros in sample_size
        logging.warning("Skipping data due to zero-variance sample_size")
        return None

    return df

def fit_mixed_linear_model(df):
    """Fits a Linear Mixed-Effects Model."""
    try:
        from statsmodels.formula.api import mixedlm
    except ImportError as e:
        logging.error(f"Statsmodels not found: {e}")
        return None

    if df is None:
      logging.warning("Dataframe is None, model fitting skipped.")
      return None

    try:
        model = mixedlm("power_est ~ year + effect_size + sample_size", df, groups=df["field"], re_formula="~1")
        result = model.fit()
        return result
    except Exception as e:  #Catch any other errors during modeling
      logging.error(f"Error fitting LMM: {e}")
      return None

def extract_year_statistics(model):
    """Extracts year slope, standard error, and confidence intervals."""
    if model is None:
        return None
    try:
        slope = model.params['year']
        se = model.bse['year']
        ci = model.conf_int(['year'])
        return slope, se, ci[0][0], ci[1][0]  # Lower and Upper CI bounds
    except KeyError as e:
        logging.error(f"KeyError extracting year statistics: {e}")
        return None

def save_results(slope, se, ci_lower, ci_upper):
    """Saves results to a CSV file."""
    import pandas as pd
    data = {'slope_year': [slope], 'se_year': [se], 'ci_lower': [ci_lower], 'ci_upper': [ci_upper]}
    df = pd.DataFrame(data)
    try:
        df.to_csv("data/derived/lmm_summary.csv", index=False)
    except Exception as e:
        logging.error(f"Error saving results to CSV: {e}")

def save_summary(model):
  try:  #Handle errors when pickling the model
      with open("data/derived/input_trends_models.pkl", "wb") as f:
          pickle.dump(model, f)
  except Exception as e:
      logging.error(f"Error saving model to pickle file : {e}")

def main():
    """Main function to load data, fit the model, and save results."""
    import pandas as pd

    # Configure logging
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    data_path = "data/raw/data.csv"  # Assuming data is in raw directory
    df = load_and_prepare_data(data_path)
    if df is None:
      logger.error("Data loading or preparation failed. Exiting.")
      sys.exit(1)

    model = fit_mixed_linear_model(df)

    if model is None:
        logger.error("Model fitting failed. Exiting")
        sys.exit(1)

    save_summary(model) #Save the full model as well

    year_stats = extract_year_statistics(model)

    if year_stats is not None:
      slope, se, ci_lower, ci_upper = year_stats
      save_results(slope, se, ci_lower, ci_upper)
      logger.info("Successfully fitted model and saved results.")
    else:
        logger.error("Failed to extract year statistics")

if __name__ == "__main__":
    main()