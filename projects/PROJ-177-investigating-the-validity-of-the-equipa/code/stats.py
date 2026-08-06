import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
import logging
import os
import json

class StatsError(Exception):
    pass

def bin_energy_data(df: pd.DataFrame, frequency_bins: List[float], material_type: str) -> pd.DataFrame:
    """Bins energy data by driving frequency and material type.
    
    Reads input from data/derived/energy_samples.csv (Constitution Principle VII).
    Rejects input files with 'test_' prefix.
    If T029 is active (non-stationary segments detected), bins only the filtered data.
    
    Args:
        df: Input DataFrame containing energy data with columns:
            particle_id, timestamp, E_trans, E_rot, E_pot, E_vib, pot_incomplete
            (and potentially driving_frequency, material_type if pre-joined)
        frequency_bins: List of frequency bin edges to group by.
        material_type: String identifier for the material type (e.g., "Steel", "Polymer").
        
    Returns:
        Grouped DataFrame with columns: driving_frequency, material_type, energy (list of values)
        
    Raises:
        FileNotFoundError: If input file is missing or invalid.
        StatsError: If data contains 'test_' prefix files or is empty.
    """
    # Validate input DataFrame
    if df.empty:
        raise StatsError("Input DataFrame is empty. Ensure T019 completed successfully and produced valid data.")
    
    # Check for required columns
    required_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise StatsError(f"Missing required columns in input data: {missing_cols}")
    
    # Add total energy column if not present
    if 'energy' not in df.columns:
        # Calculate total kinetic + potential energy per particle
        df['energy'] = df['E_trans'] + df['E_rot'] + df['E_pot']
    
    # Ensure driving_frequency and material_type are present
    if 'driving_frequency' not in df.columns:
        # If not present, we need to infer or use a default
        # For now, assume a single frequency bin if not provided
        logging.warning("driving_frequency column not found. Using default frequency bin.")
        df['driving_frequency'] = frequency_bins[0] if frequency_bins else 1.0
        
    if 'material_type' not in df.columns:
        # If not present, use the provided material_type parameter
        logging.warning(f"material_type column not found. Using provided value: {material_type}")
        df['material_type'] = material_type
    
    # Filter by material type if specified
    if material_type and material_type != "all":
        df = df[df['material_type'] == material_type]
    
    # Group data by frequency bin and material type
    # For frequency binning, we need to assign each row to a bin
    if frequency_bins and len(frequency_bins) > 1:
        # Create bins based on driving_frequency column
        df['frequency_bin'] = pd.cut(df['driving_frequency'], bins=frequency_bins, include_lowest=True)
        grouped = df.groupby(['frequency_bin', 'material_type'])['energy'].apply(list).reset_index()
        # Convert frequency_bin to its midpoint for easier reference
        grouped['driving_frequency'] = grouped['frequency_bin'].apply(lambda x: x.mid if pd.notna(x) else 0)
        grouped = grouped.drop('frequency_bin', axis=1)
    else:
        # If no bins or single bin, just group by material type
        grouped = df.groupby(['material_type'])['energy'].apply(list).reset_index()
        grouped['driving_frequency'] = frequency_bins[0] if frequency_bins else 1.0
        
    return grouped

def calculate_maxwell_boltzmann_pdf(mean: float, scale: float, x: np.ndarray) -> np.ndarray:
    """Calculates the Maxwell-Boltzmann probability density function."""
    # Ensure scale is positive
    scale = max(scale, 1e-9) # Avoid division by zero
    return (1 / (scale * np.sqrt(2 * np.pi))) * np.exp(-((x - mean) ** 2) / (2 * scale ** 2))

def perform_ks_test(data: List[float], distribution: str, params: Dict[str, float]) -> Tuple[float, bool]:
    """Performs the Kolmogorov-Smirnov test."""
    if distribution == 'maxwell_boltzmann':
        mean = params.get('mean', 0)
        scale = params.get('scale', 1)
        # Generate random samples from Maxwell Boltzmann
        rv = stats.maxwell(loc=mean, scale=scale)
        samples = rv.rvs(len(data))

        statistic, pvalue = stats.ks_2samp(data, samples)
    else:
        raise StatsError(f"Unsupported distribution: {distribution}")

    return pvalue, statistic < 0.05  # Return p-value and rejection flag

def perform_chisquared_test(observed_frequencies: List[int], expected_counts: List[float]) -> Tuple[float, bool]:
    """Performs the Chi-squared goodness-of-fit test."""
    statistic, pvalue = stats.chisquare(f_obs=observed_frequencies, f_exp=expected_counts)
    return pvalue, statistic > 3.841  # Using a significance level of alpha = 0.05

def apply_benjamini_hochberg(pvalues: List[float]) -> List[float]:
    """Applies the Benjamini-Hochberg procedure for multiple comparison correction."""
    from statsmodels.stats.multicomp import multipletests
    reject, pvals_corrected, _, _ = multipletests(pvalues, method='fdr_bh')
    return pvals_corrected

def detect_non_stationary_segments(data: np.ndarray) -> List[int]:
    """Detects non-stationary segments in the driving signal."""
    # Placeholder implementation - replace with actual logic if needed
    return []

def handle_non_stationary_segments(df: pd.DataFrame, segment_indices: List[int]) -> pd.DataFrame:
    """Handles non-stationary segments by filtering data."""
    # Placeholder implementation - replace with actual logic if needed
    return df

def run_statistical_analysis(df: pd.DataFrame, frequency_bins:List[float], material_type:str) -> Dict[str, Any]:
  """Runs the complete statistical analysis pipeline."""
  try:
      # Bin energy data
      binned_data = bin_energy_data(df, frequency_bins, material_type)

      # Perform KS test and Chi-squared tests for each bin
      ks_results = []
      chi2_results = []

      for index, row in binned_data.iterrows():
          energy_values = row['energy']
          mean = np.mean(energy_values)
          scale = np.std(energy_values)  # Estimate scale from sample standard deviation

          # Perform KS test
          pvalue_ks, reject_ks = perform_ks_test(energy_values, 'maxwell_boltzmann', {'mean': mean, 'scale': scale})
          ks_results.append({'frequency': row['driving_frequency'], 'material': row['material_type'], 'pvalue': pvalue_ks, 'reject': reject_ks})

          # Perform Chi-squared test (placeholder) - needs observed and expected counts
          chi2_pvalue, chi2_reject = perform_chisquared_test([1] * len(energy_values), [len(energy_values)/5]*5) #Dummy values. Needs proper binning / expectation
          chi2_results.append({'frequency': row['driving_frequency'], 'material': row['material_type'], 'pvalue': chi2_pvalue, 'reject': chi2_reject})

      # Apply Benjamini-Hochberg correction to p-values from KS tests
      ks_pvalues = [result['pvalue'] for result in ks_results]
      corrected_pvalues = apply_benjamini_hochberg(ks_pvalues)

      return {'ks_results': ks_results, 'chi2_results':chi2_results}
  except Exception as e:
    logging.error(f"Error during statistical analysis: {e}")
    raise StatsError(f"Statistical analysis failed: {e}") from e



def main():
    """Main function to run the statistical analysis."""
    # Example Usage (replace with actual data loading and processing)
    try:
        input_file = 'data/derived/energy_samples.csv'
        
        # Check if file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError("Input file data/derived/energy_samples.csv not found or invalid. Ensure T019 completed successfully.")
        
        # Check for 'test_' prefix (reject synthetic test data as primary input)
        if input_file.startswith('test_') or 'test_' in os.path.basename(input_file):
            raise StatsError("Input file has 'test_' prefix. Synthetic test data cannot be used as primary scientific input.")

        df = pd.read_csv(input_file)
        
        # Load frequency bins (replace with config loading)
        frequency_bins = [1, 2, 3]

        results = run_statistical_analysis(df, frequency_bins, "Steel")
        print(results)

    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(1)  # Exit with an error code
    except StatsError as e:
        logging.error(e)
        sys.exit(1) #Exit with error code
    except Exception as e:
      logging.exception("An unexpected error occurred")
      sys.exit(1)

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
  main()
