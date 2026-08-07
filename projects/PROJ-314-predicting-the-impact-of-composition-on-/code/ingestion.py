import pandas as pd
import logging
import re
import json
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_url_for_fetch(url):
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")
    # Add more sophisticated validation if needed (e.g., check scheme)
    pass

def validate_source_citations(sources):
    """Validates source URLs/DOIs against primary sources."""
    valid_count = 0
    for source in sources:
        try:
            validate_url_for_fetch(source['url'])
            # Placeholder for more robust title overlap check
            title_overlap = 0.8  # Replace with actual logic
            if title_overlap >= 0.7:
                valid_count += 1
        except Exception as e:
            logger.warning(f"Citation validation failed for {source['url']}: {e}")
    return valid_count

def fetch_data(url):
    """Fetches data from a URL (placeholder)."""
    # Replace with actual data fetching logic
    try:
        # This is just a placeholder.  Replace it with real code that fetches
        # and parses the necessary data.
        df = pd.DataFrame({'composition': ['Mg2SiO4'], 'weibull_modulus': [100]}) # dummy dataframe for now

        return df

    except Exception as e:
        logger.error(f"Error fetching data from {url}: {e}")
        raise

def generate_data_availability_report(total_sources, valid_entries):
    """Generates a report on data availability.
    
    Creates the data/reports directory if it doesn't exist and writes
    the JSON report file before halting the process.
    """
    # Ensure the output directory exists
    report_dir = Path("data/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = report_dir / "data_availability_report.json"
    
    report = {
        'total_sources': total_sources,
        'valid_entries': valid_entries,
        'reason_code': 'InsufficientData',
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Data availability report written to {report_path}")

def validate_data_gap(df):
    """Checks for data gaps and halts if necessary."""
    N = len(df)
    if N < 30:
        # Pass 0 for total_sources as we don't have that context here, 
        # but the function signature requires it. 
        # In a real flow, this would be passed from the fetch stage.
        generate_data_availability_report(total_sources=0, valid_entries=N)
        logger.info("PROJECT_HALTED: Insufficient data (N={})".format(N))
        raise ValueError("Insufficient data")
    return df

def clean_data(df):
    """Cleans and filters the ceramic entry data."""
    initial_len = len(df)
    excluded_indices = []

    # Filter for N >= 30 (already handled in validate_data_gap, but kept here for clarity)
    if len(df) < 30:
        raise ValueError("Dataframe size is less than 30 after filtering")

    # Handle range values
    def extract_range_values(row):
      value = row['weibull_modulus']
      if isinstance(value, str) and '-' in value:
          try:
              min_val, max_val = map(float, value.split('-'))
              return (min_val + max_val) / 2 , True, value
          except ValueError:
              return None, False, None  # Handle invalid range format

      else:
          return float(value), False, None


    df[['weibull_modulus', 'is_range_flag', 'range_original']] = df.apply(extract_range_values, axis=1, result_type='expand')
    df['weibull_modulus'] = pd.to_numeric(df['weibull_modulus'], errors='coerce') # convert to numeric after range extraction

    # Filter out rows with missing stoichiometry (composition is NaN or empty)
    # Assuming 'composition' is the column to check for stoichiometry
    missing_stoich_mask = df['composition'].isna() | (df['composition'].astype(str).str.strip() == '')
    missing_stoich_indices = df[missing_stoich_mask].index.tolist()
    for idx in missing_stoich_indices:
        excluded_indices.append((idx, 'missing_stoichiometry'))
    df = df[~missing_stoich_mask]

    # Handle non-stoichiometric phases (placeholder logic for exclusion)
    # In a real implementation, this would involve checking a specific column or flag
    # For this task, we assume there's a column 'is_non_stoichiometric' or similar logic
    # If such a column exists and is True, exclude the row.
    if 'is_non_stoichiometric' in df.columns:
        non_stoich_mask = df['is_non_stoichiometric'] == True
        non_stoich_indices = df[non_stoich_mask].index.tolist()
        for idx in non_stoich_indices:
            excluded_indices.append((idx, 'non_stoichiometric_phase'))
        df = df[~non_stoich_mask]
    
    # Log all exclusions
    for idx, reason in excluded_indices:
        logger.info(f"Excluded row {idx} due to {reason}")

    # Impute missing processing parameters (group median -> global median) - Placeholder for now
    # In a real implementation, this would involve calculating the medians and applying them
    df = df.fillna(df.median())


    return df

def compute_descriptors(df):
    """Computes elemental descriptors."""
    # Replace with actual descriptor calculation logic
    # This is just a placeholder
    df['mean_atomic_radius'] = 10  # Dummy value
    df['electronegativity_std'] = 2.5 # dummy value
    return df

def validate_no_missing_predictors(df):
    """Validates that no primary predictors contain NaN values.
    
    Args:
        df: DataFrame containing the computed descriptors.
        
    Raises:
        ValueError: If any of the primary predictor columns contain NaN values.
    """
    required_columns = ['mean_atomic_radius', 'electronegativity_std', 'valence_electron_concentration']
    
    # Check which columns are missing or contain NaN
    missing_cols = []
    for col in required_columns:
        if col not in df.columns:
            missing_cols.append(col)
        elif df[col].isnull().any():
            missing_cols.append(col)

    if missing_cols:
        raise ValueError(f"Missing values in primary predictors: {missing_cols}")
    
    logger.info("Validation passed: No missing values in primary predictors.")

def main():
    """Main function to demonstrate the data cleaning process."""
    # This is a placeholder. Replace with your actual data loading and processing logic.
    try:
      df = fetch_data("http://example.com/ceramic_data.csv") # replace with real URL

      validated_df = validate_data_gap(df)

      cleaned_df = clean_data(validated_df)

      computed_df = compute_descriptors(cleaned_df)
      validate_no_missing_predictors(computed_df)
      computed_df.to_csv("data/processed/ceramic_entries.csv", index=False)
      logger.info("Data cleaning and descriptor computation complete.")

    except Exception as e:
      logger.error(f"Error during data processing: {e}")
      raise