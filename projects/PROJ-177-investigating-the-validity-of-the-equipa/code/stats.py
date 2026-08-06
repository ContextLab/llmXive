"""
Statistical analysis module for granular system energy distributions.

Implements binning, Maxwell-Boltzmann comparison, KS tests, Chi-squared tests,
and FDR correction for the Equipartition Theorem validity investigation.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
import logging
import argparse
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def bin_energy_data(input_path: str = "data/derived/energy_samples.csv") -> Dict[str, pd.DataFrame]:
    """
    Bin energy data by driving frequency and material type.
    
    Reads input from data/derived/energy_samples.csv (Constitution Principle VII).
    
    Args:
        input_path: Path to the energy samples CSV file.
        
    Returns:
        Dictionary mapping (frequency, material) tuples to DataFrames.
        
    Raises:
        FileNotFoundError: If input file is missing or invalid.
        StatsError: If required columns are missing.
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file {input_path} not found or invalid. "
            "Ensure T019 completed successfully."
        )
    
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        raise FileNotFoundError(
            f"Input file {input_path} not found or invalid. "
            "Ensure T019 completed successfully. Read error: {e}"
        )
    
    required_columns = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete', 'driving_frequency', 'material_type']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        raise StatsError(
            f"Missing required columns in {input_path}: {missing_cols}. "
            "Ensure T019 output schema is correct."
        )
    
    # Filter out incomplete potential energy data if needed
    # (Optional: could filter based on pot_incomplete flag depending on analysis needs)
    # For now, we keep all data but note the flag
    
    # Group by frequency and material type
    bins = {}
    grouped = df.groupby(['driving_frequency', 'material_type'])
    
    for (freq, mat), group in grouped:
        key = (freq, mat)
        bins[key] = group.reset_index(drop=True)
        logger.info(f"Binned {len(group)} samples for freq={freq}, material={mat}")
    
    if not bins:
        logger.warning("No data bins created. Check input data content.")
    
    return bins

def calculate_maxwell_boltzmann_pdf(energies: np.ndarray, temperature: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate theoretical Maxwell-Boltzmann PDF for given energy data.
    
    The Maxwell-Boltzmann distribution for energy in 3D is:
    f(E) = 2 * sqrt(E / (pi * (kT)^3)) * exp(-E / (kT))
    
    For granular systems, we often use an effective temperature T_eff estimated
    from the mean energy: <E> = (3/2) * kT_eff  =>  kT_eff = (2/3) * <E>
    
    Args:
        energies: Array of energy values.
        temperature: Optional known temperature. If None, estimated from mean.
        
    Returns:
        Tuple of (bin_edges, pdf_values)
    """
    if len(energies) == 0:
        return np.array([]), np.array([])
    
    if temperature is None:
        mean_energy = np.mean(energies)
        # kT_eff = (2/3) * <E>
        kT = (2.0 / 3.0) * mean_energy
    else:
        kT = temperature
    
    if kT <= 0:
        raise StatsError("Invalid temperature parameter: must be positive.")
    
    # Use Freedman-Diaconis rule for bin edges (consistent with T026)
    # But for PDF calculation, we generate a smooth curve
    E_max = np.max(energies) * 1.2
    E_min = 0.0
    E_range = np.linspace(E_min, max(E_max, 1e-6), 200)
    
    # Maxwell-Boltzmann PDF for energy (3D)
    # f(E) = 2 * sqrt(E / (pi * (kT)^3)) * exp(-E / (kT))
    pdf_values = 2.0 * np.sqrt(E_range / (np.pi * (kT ** 3))) * np.exp(-E_range / kT)
    
    # Normalize to ensure integral ~ 1 over the range
    # (Discrete approximation)
    integral = np.trapz(pdf_values, E_range)
    if integral > 0:
        pdf_values = pdf_values / integral
    
    return E_range, pdf_values

def perform_ks_test(energies: np.ndarray, temperature: Optional[float] = None) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov test against Maxwell-Boltzmann distribution.
    
    Uses Lilliefors correction approach: estimate scale parameter from sample mean.
    
    Args:
        energies: Array of energy values.
        temperature: Optional known temperature.
        
    Returns:
        Dictionary with test statistic, p-value, and rejection flag.
    """
    if len(energies) < 2:
        return {
            'statistic': np.nan,
            'p_value': np.nan,
            'rejected': False,
            'n_samples': len(energies),
            'message': 'Insufficient samples for KS test'
        }
    
    try:
        # Estimate kT from mean energy
        mean_energy = np.mean(energies)
        kT = (2.0 / 3.0) * mean_energy
        
        if kT <= 0:
            return {
                'statistic': np.nan,
                'p_value': np.nan,
                'rejected': False,
                'n_samples': len(energies),
                'message': 'Invalid estimated temperature'
            }
        
        # Define the theoretical CDF for Maxwell-Boltzmann
        def mb_cdf(x):
            if x <= 0:
                return 0.0
            # CDF of Maxwell-Boltzmann for energy
            # F(E) = erf(sqrt(E/(kT))) - 2*sqrt(E/(pi*kT)) * exp(-E/(kT))
            # Simplified using scipy's chi-square (3 degrees of freedom)
            # E/(kT) ~ chi^2(3) / 2  =>  2*E/(kT) ~ chi^2(3)
            return stats.chi.cdf(2.0 * x / kT, df=3)
        
        # Perform KS test
        # We use the 'kstest' with a callable CDF
        statistic, p_value = stats.kstest(energies, mb_cdf)
        
        return {
            'statistic': float(statistic),
            'p_value': float(p_value),
            'rejected': p_value < 0.05,  # Default alpha
            'n_samples': len(energies),
            'estimated_kT': float(kT),
            'message': 'KS test completed'
        }
        
    except Exception as e:
        logger.error(f"KS test failed: {e}")
        return {
            'statistic': np.nan,
            'p_value': np.nan,
            'rejected': False,
            'n_samples': len(energies),
            'message': f'KS test error: {e}'
        }

def perform_chisquared_test(energies: np.ndarray, temperature: Optional[float] = None, n_bins: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform Chi-squared goodness-of-fit test against Maxwell-Boltzmann.
    
    Uses Freedman-Diaconis rule for bin edges.
    
    Args:
        energies: Array of energy values.
        temperature: Optional known temperature.
        n_bins: Optional number of bins (if None, uses Freedman-Diaconis).
        
    Returns:
        Dictionary with test statistic, p-value, and rejection flag.
    """
    if len(energies) < 5:
        return {
            'statistic': np.nan,
            'p_value': np.nan,
            'rejected': False,
            'n_samples': len(energies),
            'message': 'Insufficient samples for Chi-squared test'
        }
    
    try:
        # Estimate kT
        mean_energy = np.mean(energies)
        kT = (2.0 / 3.0) * mean_energy
        
        if kT <= 0:
            return {
                'statistic': np.nan,
                'p_value': np.nan,
                'rejected': False,
                'n_samples': len(energies),
                'message': 'Invalid estimated temperature'
            }
        
        # Determine bin edges using Freedman-Diaconis rule
        if n_bins is None:
            iqr = np.subtract(*np.percentile(energies, [75, 25]))
            n = len(energies)
            bin_width = 2.0 * iqr / (n ** (1/3)) if iqr > 0 else 1.0
            if bin_width <= 0:
                bin_width = (np.max(energies) - np.min(energies)) / 10
            n_bins = max(5, int((np.max(energies) - np.min(energies)) / bin_width))
        
        # Create bins
        bin_edges = np.linspace(0, np.max(energies) * 1.1, n_bins + 1)
        
        # Observed counts
        observed, _ = np.histogram(energies, bins=bin_edges)
        
        # Expected counts: integrate MB PDF over each bin
        expected = []
        for i in range(len(bin_edges) - 1):
            bin_min, bin_max = bin_edges[i], bin_edges[i+1]
            # CDF difference
            cdf_max = stats.chi.cdf(2.0 * bin_max / kT, df=3)
            cdf_min = stats.chi.cdf(2.0 * bin_min / kT, df=3)
            prob = cdf_max - cdf_min
            expected.append(prob * len(energies))
        
        expected = np.array(expected)
        
        # Avoid zero expected counts
        mask = expected > 0
        if np.sum(mask) < 2:
            return {
                'statistic': np.nan,
                'p_value': np.nan,
                'rejected': False,
                'n_samples': len(energies),
                'message': 'Too many empty bins'
            }
        
        observed_filtered = observed[mask]
        expected_filtered = expected[mask]
        
        # Chi-squared statistic
        chi2_stat = np.sum((observed_filtered - expected_filtered) ** 2 / expected_filtered)
        df = len(observed_filtered) - 1 - 1  # -1 for estimated parameter
        p_value = 1.0 - stats.chi2.cdf(chi2_stat, df)
        
        return {
            'statistic': float(chi2_stat),
            'p_value': float(p_value),
            'rejected': p_value < 0.05,
            'n_samples': len(energies),
            'n_bins': len(observed_filtered),
            'estimated_kT': float(kT),
            'message': 'Chi-squared test completed'
        }
        
    except Exception as e:
        logger.error(f"Chi-squared test failed: {e}")
        return {
            'statistic': np.nan,
            'p_value': np.nan,
            'rejected': False,
            'n_samples': len(energies),
            'message': f'Chi-squared test error: {e}'
        }

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (rejection flags, adjusted p-values)
    """
    if not p_values:
        return [], []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]
    
    # BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha
    
    # Find largest k where p(k) <= critical(k)
    # Rejection: all p <= p(k) are rejected
    reject = np.zeros(n, dtype=bool)
    adjusted = np.ones(n)
    
    # Calculate adjusted p-values
    for i in range(n - 1, -1, -1):
        if i == n - 1:
            adjusted[sorted_indices[i]] = min(1.0, sorted_pvals[i] * n / (i + 1))
        else:
            adjusted[sorted_indices[i]] = min(
                adjusted[sorted_indices[i + 1]],
                sorted_pvals[i] * n / (i + 1)
            )
    
    # Determine rejections
    for i in range(n):
        if adjusted[sorted_indices[i]] <= alpha:
            reject[sorted_indices[i]] = True
    
    return reject.tolist(), adjusted.tolist()

def detect_non_stationary_segments(driving_signal_path: str, threshold: float = 0.05) -> List[Dict[str, Any]]:
    """
    Detect non-stationary segments in driving signal using Hilbert transform.
    
    Args:
        driving_signal_path: Path to driving signal CSV.
        threshold: Frequency variance threshold (fraction of mean).
        
    Returns:
        List of segment info dictionaries.
    """
    # Placeholder: implementation depends on driving signal format
    # This would extract instantaneous frequency and check variance
    logger.warning("Non-stationary detection not fully implemented")
    return []

def handle_non_stationary_segments(df: pd.DataFrame, segments: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Filter out non-stationary segments from data.
    
    Args:
        df: Input DataFrame.
        segments: List of non-stationary segment definitions.
        
    Returns:
        Filtered DataFrame.
    """
    # Placeholder: filter based on segment definitions
    return df

def run_statistical_analysis(
    input_path: str = "data/derived/energy_samples.csv",
    output_path: str = "artifacts/statistical_results.json",
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run full statistical analysis pipeline: binning, KS, Chi-squared, FDR.
    
    Args:
        input_path: Path to energy samples CSV.
        output_path: Path to output JSON results.
        alpha: Significance level for tests.
        
    Returns:
        Dictionary of results.
    """
    logger.info(f"Starting statistical analysis on {input_path}")
    
    # Bin data
    bins = bin_energy_data(input_path)
    
    results = {
        'bins': {},
        'summary': [],
        'fdr_corrected': []
    }
    
    all_pvalues_ks = []
    all_pvalues_chi2 = []
    bin_keys = []
    
    for key, data in bins.items():
        freq, mat = key
        energies = data['E_trans'].values  # Use translational energy
        
        ks_result = perform_ks_test(energies)
        chi2_result = perform_chisquared_test(energies)
        
        bin_key_str = f"{freq}_{mat}"
        results['bins'][bin_key_str] = {
            'frequency': freq,
            'material': mat,
            'n_samples': len(energies),
            'mean_energy': float(np.mean(energies)),
            'ks_test': ks_result,
            'chi2_test': chi2_result
        }
        
        if not np.isnan(ks_result['p_value']):
            all_pvalues_ks.append(ks_result['p_value'])
            bin_keys.append(bin_key_str)
        if not np.isnan(chi2_result['p_value']):
            all_pvalues_chi2.append(chi2_result['p_value'])
    
    # Apply FDR
    if all_pvalues_ks:
        reject_ks, adj_ks = apply_benjamini_hochberg(all_pvalues_ks, alpha)
        for i, key in enumerate(bin_keys):
            results['fdr_corrected'].append({
                'bin': key,
                'test': 'KS',
                'raw_pvalue': all_pvalues_ks[i],
                'adjusted_pvalue': adj_ks[i],
                'rejected': reject_ks[i]
            })
    
    if all_pvalues_chi2:
        reject_chi2, adj_chi2 = apply_benjamini_hochberg(all_pvalues_chi2, alpha)
        for i, key in enumerate(bin_keys):
            results['fdr_corrected'].append({
                'bin': key,
                'test': 'Chi-squared',
                'raw_pvalue': all_pvalues_chi2[i],
                'adjusted_pvalue': adj_chi2[i],
                'rejected': reject_chi2[i]
            })
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Statistical analysis complete. Results written to {output_path}")
    return results

def main():
    """CLI entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description='Statistical analysis of granular energy data')
    parser.add_argument('--input', type=str, default='data/derived/energy_samples.csv',
                        help='Input energy samples CSV')
    parser.add_argument('--output', type=str, default='artifacts/statistical_results.json',
                        help='Output JSON results file')
    parser.add_argument('--alpha', type=float, default=0.05,
                        help='Significance level for tests')
    
    args = parser.parse_args()
    
    try:
        results = run_statistical_analysis(args.input, args.output, args.alpha)
        print(f"Analysis complete. Results: {len(results['bins'])} bins processed.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
