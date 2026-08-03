"""
Statistical analysis module for granular system energy distributions.
Implements binning, KS tests, Chi-squared tests, and FDR correction.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
import logging
import argparse
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def bin_energy_data(
    data_path: str,
    bin_by_frequency: bool = True,
    bin_by_material: bool = True
) -> pd.DataFrame:
    """
    Bin energy data by driving frequency and material type.

    Reads input from `data/derived/energy_samples.csv` and groups the data
    by the specified dimensions to prepare for statistical testing.

    Args:
        data_path: Path to the energy samples CSV file.
        bin_by_frequency: If True, group by the 'frequency' column.
        bin_by_material: If True, group by the 'material_type' column.

    Returns:
        A pandas DataFrame where each row represents a unique bin
        (frequency, material_type) containing the aggregated energy data
        or the groups ready for iteration. The function returns a DataFrame
        with columns: 'frequency', 'material_type', and 'energies' (list of
        energy values for that bin) to facilitate downstream testing.

    Raises:
        StatsError: If the input file is missing, empty, or lacks required columns.
        FileNotFoundError: If the input file does not exist.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Input file not found: {data_path}")

    df = pd.read_csv(data_path)

    required_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise StatsError(f"Missing required columns in {data_path}: {missing_cols}")

    # Ensure grouping columns exist
    if bin_by_frequency and 'frequency' not in df.columns:
        raise StatsError("Column 'frequency' not found in data. Ingestion may have failed to sync driving signals.")
    if bin_by_material and 'material_type' not in df.columns:
        raise StatsError("Column 'material_type' not found in data. Ingestion may have failed to apply material properties.")

    # Select grouping keys
    group_keys = []
    if bin_by_frequency:
        group_keys.append('frequency')
    if bin_by_material:
        group_keys.append('material_type')

    if not group_keys:
        # If no grouping requested, just return the energies column
        return df[['E_trans', 'E_rot', 'E_pot', 'E_vib']].copy()

    # Group and aggregate energies into lists for each bin
    # We aggregate all energy components into a single list or keep them separate?
    # The spec implies testing distributions. We will create a column 'energies'
    # that contains a list of the total energy (E_trans + E_rot + E_pot + E_vib)
    # or just the specific component being tested later.
    # For now, let's return the grouped data with a list of total energy.
    df['E_total'] = df['E_trans'] + df['E_rot'] + df['E_pot'] + df['E_vib']

    grouped = df.groupby(group_keys)['E_total'].apply(list).reset_index()
    grouped.columns = group_keys + ['energies']

    logger.info(f"Binned data into {len(grouped)} groups across {group_keys}.")
    return grouped

def calculate_maxwell_boltzmann_pdf(energies: np.ndarray, kT: float) -> np.ndarray:
    """
    Calculate the Maxwell-Boltzmann probability density function values
    for a given set of energies and temperature parameter kT.

    The 3D Maxwell-Boltzmann distribution for energy E is:
    f(E) = 2 * sqrt(E / (pi * (kT)^3)) * exp(-E / kT)

    Args:
        energies: Array of energy values.
        kT: The thermal energy scale (Boltzmann constant * temperature).

    Returns:
        Array of PDF values corresponding to the input energies.
    """
    if kT <= 0:
        raise StatsError("kT must be positive.")

    # Avoid division by zero or log of zero
    energies = np.array(energies)
    # Filter out zero or negative energies if any (though physical energies should be >= 0)
    valid_mask = energies > 0
    pdf_values = np.zeros_like(energies)

    if np.any(valid_mask):
        # f(E) = 2/sqrt(pi) * (1/kT)^(3/2) * sqrt(E) * exp(-E/kT)
        # Simplified: 2 * sqrt(E / (pi * kT^3)) * exp(-E/kT)
        factor = 2.0 / np.sqrt(np.pi) * (1.0 / kT)**1.5
        pdf_values[valid_mask] = factor * np.sqrt(energies[valid_mask]) * np.exp(-energies[valid_mask] / kT)

    return pdf_values

def perform_ks_test(energies: np.ndarray, kT: float) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov test against the theoretical Maxwell-Boltzmann distribution.

    Args:
        energies: Array of observed energy values.
        kT: The thermal energy scale for the theoretical distribution.

    Returns:
        Dictionary with 'statistic', 'pvalue', 'rejection' (bool), and 'method'.
    """
    if len(energies) < 2:
        raise StatsError("Need at least 2 data points for KS test.")

    # Define the CDF for the Maxwell-Boltzmann distribution
    # The CDF for 3D MB energy is: F(x) = erf(sqrt(x/kT)) - 2/sqrt(pi) * sqrt(x/kT) * exp(-x/kT)
    # However, scipy.stats.kstest accepts a CDF function.
    def mb_cdf(x):
        x = np.asarray(x)
        # Handle scalar or array
        if np.isscalar(x):
            x = np.array([x])
            scalar = True
        else:
            scalar = False

        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            sqrt_x_kt = np.sqrt(x / kT)
            # erf is available in scipy.special
            from scipy.special import erf
            cdf_vals = erf(sqrt_x_kt) - (2.0 / np.sqrt(np.pi)) * sqrt_x_kt * np.exp(-x / kT)
            # Clamp to [0, 1]
            cdf_vals = np.clip(cdf_vals, 0.0, 1.0)

        if scalar:
            return cdf_vals[0]
        return cdf_vals

    try:
        statistic, pvalue = stats.kstest(energies, mb_cdf)
    except Exception as e:
        raise StatsError(f"KS test failed: {e}")

    return {
        'statistic': float(statistic),
        'pvalue': float(pvalue),
        'rejection': pvalue < 0.05, # Default alpha, will be corrected later
        'method': 'KS'
    }

def perform_chisquared_test(energies: np.ndarray, kT: float, bins: int = 10) -> Dict[str, Any]:
    """
    Perform Chi-squared goodness-of-fit test.
    Bins observed counts and compares to expected counts from MB distribution.

    Args:
        energies: Array of observed energy values.
        kT: The thermal energy scale.
        bins: Number of bins for the histogram.

    Returns:
        Dictionary with 'statistic', 'pvalue', 'rejection', and 'method'.
    """
    if len(energies) < bins:
        raise StatsError(f"Not enough data points ({len(energies)}) for {bins} bins.")

    # Create histogram
    hist, bin_edges = np.histogram(energies, bins=bins)

    # Calculate expected probabilities for each bin
    # Integrate PDF over bin edges
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    # More accurate: integrate PDF
    # P(bin) = F(bin_right) - F(bin_left)
    from scipy.special import erf
    def cdf_mb(x, kT):
        if x <= 0: return 0.0
        sqrt_x_kt = np.sqrt(x / kT)
        return erf(sqrt_x_kt) - (2.0 / np.sqrt(np.pi)) * sqrt_x_kt * np.exp(-x / kT)

    expected_probs = []
    for i in range(len(bin_edges) - 1):
        left, right = bin_edges[i], bin_edges[i+1]
        p = cdf_mb(right, kT) - cdf_mb(left, kT)
        expected_probs.append(p)

    expected_probs = np.array(expected_probs)
    total_count = len(energies)
    expected_counts = total_count * expected_probs

    # Ensure no zero expected counts (combine bins if necessary)
    # Simple approach: skip bins with 0 expected count if they also have 0 observed
    # Or combine last bins. For simplicity, we filter.
    valid_mask = expected_counts > 0
    if not np.all(valid_mask):
        logger.warning(f"Chi-squared: {np.sum(~valid_mask)} bins have zero expected probability. Combining or ignoring.")
        # If we ignore, we must ignore observed too.
        if np.any((~valid_mask) & (hist > 0)):
            raise StatsError("Observed counts in bins with zero expected probability. Cannot perform Chi-squared test reliably.")
        hist = hist[valid_mask]
        expected_counts = expected_counts[valid_mask]

    if len(hist) < 2:
        raise StatsError("After bin filtering, less than 2 bins remain for Chi-squared test.")

    try:
        statistic, pvalue = stats.chisquare(f_obs=hist, f_exp=expected_counts)
    except Exception as e:
        raise StatsError(f"Chi-squared test failed: {e}")

    return {
        'statistic': float(statistic),
        'pvalue': float(pvalue),
        'rejection': pvalue < 0.05,
        'method': 'Chi-squared'
    }

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction.

    Args:
        p_values: List of raw p-values.
        alpha: Desired FDR level.

    Returns:
        Tuple of (rejection_flags, adjusted_p_values).
    """
    if not p_values:
        return [], []

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]

    # Calculate adjusted p-values
    # Rank i goes from 1 to n
    ranks = np.arange(1, n + 1)
    adjusted_p = sorted_p * n / ranks
    # Ensure monotonicity: adjusted p[i] <= adjusted p[i+1]
    # We do this by cummin from the back
    adjusted_p = np.minimum.accumulate(adjusted_p[::-1])[::-1]
    # Clamp to 1.0
    adjusted_p = np.clip(adjusted_p, 0, 1)

    # Reorder back to original
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted_p

    # Rejection flags
    rejection = final_adjusted < alpha

    return list(rejection), list(final_adjusted)

def detect_non_stationary_segments(energies: np.ndarray, window_size: int = 10) -> List[int]:
    """
    Detect non-stationary segments by checking variance changes.
    Returns indices where significant shifts occur.
    """
    if len(energies) < window_size * 2:
        return []

    # Simple moving variance comparison
    variances = []
    for i in range(0, len(energies) - window_size, window_size):
        chunk = energies[i:i+window_size]
        variances.append(np.var(chunk))

    variances = np.array(variances)
    if len(variances) < 2:
        return []

    # Detect large jumps in variance
    diffs = np.abs(np.diff(variances))
    threshold = np.mean(diffs) + 2 * np.std(diffs)
    change_indices = np.where(diffs > threshold)[0]

    # Map back to original indices (approximate)
    segment_indices = [i * window_size for i in change_indices]
    return segment_indices

def handle_non_stationary_segments(energies: np.ndarray, segment_indices: List[int]) -> np.ndarray:
    """
    Remove or flag non-stationary segments.
    For now, simply removes data around detected change points.
    """
    if not segment_indices:
        return energies

    mask = np.ones(len(energies), dtype=bool)
    margin = 5 # Remove 5 points around change
    for idx in segment_indices:
        start = max(0, idx - margin)
        end = min(len(energies), idx + margin)
        mask[start:end] = False

    return energies[mask]

def run_statistical_analysis(
    data_path: str,
    output_path: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline:
    1. Bin energy data.
    2. For each bin, estimate kT (mean energy / 3/2 k_B? or just mean for scaling).
       Spec says: "using sample mean to estimate scale parameter".
       For MB energy in 3D, mean E = 3/2 kT. So kT = 2/3 * mean(E).
    3. Perform KS and Chi-squared tests.
    4. Apply FDR correction.
    5. Save results to JSON.

    Args:
        data_path: Path to energy_samples.csv.
        output_path: Path to write statistical_results.json.
        alpha: Significance level for FDR.

    Returns:
        Dictionary of results.
    """
    logger.info(f"Running statistical analysis on {data_path}")

    # 1. Bin data
    binned_data = bin_energy_data(data_path)

    results = []
    all_p_values = []
    test_configs = []

    for _, row in binned_data.iterrows():
        freq = row.get('frequency', 'unknown')
        mat = row.get('material_type', 'unknown')
        energies = np.array(row['energies'])

        if len(energies) < 10:
            logger.warning(f"Skipping bin (freq={freq}, mat={mat}) due to insufficient data ({len(energies)}).")
            continue

        # Estimate kT: Mean E = 1.5 kT => kT = E_mean / 1.5
        kT = np.mean(energies) / 1.5

        # 2. KS Test
        try:
            ks_res = perform_ks_test(energies, kT)
            results.append({
                'frequency': str(freq),
                'material_type': str(mat),
                'n_samples': len(energies),
                'kT_est': float(kT),
                'ks_statistic': ks_res['statistic'],
                'ks_pvalue': ks_res['pvalue'],
                'ks_rejection_raw': ks_res['rejection']
            })
            all_p_values.append(ks_res['pvalue'])
            test_configs.append({'method': 'KS', 'bin': f"{freq}_{mat}"})
        except StatsError as e:
            logger.error(f"KS test failed for {freq}_{mat}: {e}")

        # 3. Chi-squared Test
        try:
            chi_res = perform_chisquared_test(energies, kT)
            results[-1]['chi_statistic'] = chi_res['statistic']
            results[-1]['chi_pvalue'] = chi_res['pvalue']
            results[-1]['chi_rejection_raw'] = chi_res['rejection']
            all_p_values.append(chi_res['pvalue'])
            test_configs.append({'method': 'Chi-squared', 'bin': f"{freq}_{mat}"})
        except StatsError as e:
            logger.error(f"Chi-squared test failed for {freq}_{mat}: {e}")

    # 4. FDR Correction
    if all_p_values:
        rejection_flags, adjusted_p_values = apply_benjamini_hochberg(all_p_values, alpha)
        for i, res in enumerate(results):
            # We have mixed KS and Chi results in 'results'.
            # We need to map back carefully.
            # Let's rebuild the mapping logic or store indices.
            # Simpler: re-iterate or store indices in the loop.
            # Since we appended to 'results' and 'all_p_values' in pairs (KS then Chi),
            # we can assume:
            # index 0 -> KS of row 0
            # index 1 -> Chi of row 0
            # index 2 -> KS of row 1
            # ...
            # But if a test failed, the counts might differ.
            # Better: Store indices in the loop.
            pass

        # Re-do with explicit indexing
        final_results = []
        p_counter = 0
        for _, row in binned_data.iterrows():
            freq = row.get('frequency', 'unknown')
            mat = row.get('material_type', 'unknown')
            energies = np.array(row['energies'])
            if len(energies) < 10: continue

            kT = np.mean(energies) / 1.5
            entry = {
                'frequency': str(freq),
                'material_type': str(mat),
                'n_samples': len(energies),
                'kT_est': float(kT)
            }

            # KS
            if p_counter < len(rejection_flags):
                ks_res = perform_ks_test(energies, kT)
                entry['ks_statistic'] = ks_res['statistic']
                entry['ks_pvalue'] = ks_res['pvalue']
                entry['ks_rejection_fdr'] = rejection_flags[p_counter]
                entry['ks_pvalue_adjusted'] = adjusted_p_values[p_counter]
                p_counter += 1
            else:
                entry['ks_rejection_fdr'] = False # Default

            # Chi
            if p_counter < len(rejection_flags):
                chi_res = perform_chisquared_test(energies, kT)
                entry['chi_statistic'] = chi_res['statistic']
                entry['chi_pvalue'] = chi_res['pvalue']
                entry['chi_rejection_fdr'] = rejection_flags[p_counter]
                entry['chi_pvalue_adjusted'] = adjusted_p_values[p_counter]
                p_counter += 1
            else:
                entry['chi_rejection_fdr'] = False

            final_results.append(entry)

        results = final_results

    # Save to JSON
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_params': {'alpha': alpha},
            'results': results
        }, f, indent=2)

    logger.info(f"Statistical results written to {output_path}")
    return {'results': results}

def main():
    parser = argparse.ArgumentParser(description="Run statistical analysis on granular energy data.")
    parser.add_argument("--input", type=str, default="data/derived/energy_samples.csv",
                        help="Path to energy_samples.csv")
    parser.add_argument("--output", type=str, default="artifacts/statistical_results.json",
                        help="Path for output JSON")
    parser.add_argument("--alpha", type=float, default=0.05,
                        help="Significance level for FDR correction")

    args = parser.parse_args()

    try:
        run_statistical_analysis(args.input, args.output, args.alpha)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
