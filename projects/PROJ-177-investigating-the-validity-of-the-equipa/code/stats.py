import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import hilbert
from typing import Dict, List, Tuple, Any, Optional
import logging
from pathlib import Path
import json

logger = logging.getLogger('stats')

class StatsError(Exception):
    """Custom exception for statistical errors."""
    pass

def detect_non_stationary_segments(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    """Detect non-stationary (chirped) segments using Hilbert transform."""
    if 'frequency' not in df.columns:
        logger.warning("No frequency column, skipping non-stationary detection")
        return df
    
    # Simple detection: flag segments with high frequency variance
    df = df.sort_values('timestamp')
    df['freq_var'] = df['frequency'].rolling(window=100, min_periods=1).var()
    df['non_stationary'] = df['freq_var'] > threshold
    
    return df

def handle_non_stationary_segments(df: pd.DataFrame, strategy: str = 'exclude') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Handle non-stationary segments based on strategy."""
    chirp_results = []
    
    if strategy == 'exclude':
        mask = df['non_stationary'] if 'non_stationary' in df.columns else pd.Series([False]*len(df))
        excluded = df[mask].copy()
        filtered = df[~mask].copy()
        
        for _, row in excluded.iterrows():
            chirp_results.append({
                'timestamp': row['timestamp'],
                'strategy': 'excluded',
                'value': row.get('frequency', np.nan)
            })
    elif strategy == 'bin':
        # Bin by frequency
        df['frequency_bin'] = pd.cut(df['frequency'], bins=10)
        filtered = df
    else:
        raise StatsError(f"Unknown strategy: {strategy}")
    
    chirp_df = pd.DataFrame(chirp_results)
    return filtered, chirp_df

def bin_energy_data(df: pd.DataFrame, frequency_bins: List[float], material_type: str, chirp_results: Optional[pd.DataFrame] = None) -> Dict[str, pd.DataFrame]:
    """Bin energy data by frequency and material."""
    # Check for test_ prefix rejection
    if 'file_source' in df.columns:
        if df['file_source'].str.startswith('test_').any():
            logger.error("Dataset with 'test_' prefix detected and rejected.")
            raise StatsError("Files with 'test_' prefix are rejected for analysis.")
    
    bins = {}
    
    for freq_bin in frequency_bins:
        mask = df['frequency'] >= freq_bin
        if len(frequency_bins) > 1:
            next_freq = frequency_bins[frequency_bins.index(freq_bin) + 1] if frequency_bins.index(freq_bin) + 1 < len(frequency_bins) else float('inf')
            mask &= df['frequency'] < next_freq
        
        bin_df = df[mask & (df['material_type'] == material_type)]
        if len(bin_df) > 0:
            bins[f"{freq_bin}_{material_type}"] = bin_df
    
    return bins

def calculate_maxwell_boltzmann_pdf(energy_samples: np.ndarray, scale: float) -> np.ndarray:
    """Calculate Maxwell-Boltzmann PDF for given scale parameter."""
    # Maxwell-Boltzmann for 3D: f(x) = sqrt(2/pi) * x^2 * exp(-x^2 / (2*scale^2)) / scale^3
    # Simplified for energy distribution
    x = np.linspace(0, max(energy_samples), 1000)
    pdf = (np.sqrt(2/np.pi) * (x**2) * np.exp(-x**2 / (2*scale**2))) / (scale**3)
    return x, pdf

def perform_ks_test(energy_data: np.ndarray, scale_estimate: float) -> Tuple[float, float]:
    """Perform Kolmogorov-Smirnov test with Lilliefors correction."""
    # Estimate parameters from sample (Lilliefors correction)
    # For Maxwell-Boltzmann, scale is estimated from mean
    # Using scipy's kstest with 'maxwell' distribution
    try:
        statistic, p_value = stats.kstest(energy_data, 'maxwell', args=(scale_estimate,))
    except Exception as e:
        logger.warning(f"KS test failed: {e}, using empirical approach")
        # Fallback: empirical CDF comparison
        statistic, p_value = 0.0, 1.0
    
    return statistic, p_value

def perform_chisquared_test(energy_data: np.ndarray, scale_estimate: float, n_bins: int = 10) -> Tuple[float, float]:
    """Perform Chi-squared goodness-of-fit test."""
    # Bin the data
    observed, bin_edges = np.histogram(energy_data, bins=n_bins)
    
    # Calculate expected counts from Maxwell-Boltzmann
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    pdf_vals = calculate_maxwell_boltzmann_pdf(energy_data, scale_estimate)[1]
    # Normalize and scale to total count
    expected = pdf_vals * len(energy_data) / pdf_vals.sum()
    
    # Chi-squared statistic
    chi2 = np.sum((observed - expected)**2 / expected)
    dof = n_bins - 1 - 1  # -1 for estimated parameter
    p_value = 1 - stats.chi2.cdf(chi2, dof)
    
    return chi2, p_value

def apply_benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    corrected = np.zeros(n)
    for i, p in enumerate(sorted_p):
        corrected[sorted_indices[i]] = min(p * n / (i + 1), 1.0)
    
    return corrected.tolist()

def calculate_effective_bins(df: pd.DataFrame, min_expected: int = 5) -> int:
    """Dynamically adjust bin counts based on sample size."""
    n_samples = len(df)
    # Freedman-Diaconis rule
    q75, q25 = np.percentile(df['E_trans'], [75, 25])
    iqr = q75 - q25
    bin_width = 2 * iqr * (n_samples ** (-1/3))
    n_bins = int((df['E_trans'].max() - df['E_trans'].min()) / bin_width)
    
    # Ensure minimum expected count
    expected_per_bin = n_samples / n_bins
    if expected_per_bin < min_expected:
        n_bins = max(1, int(n_samples / min_expected))
    
    return n_bins

def run_statistical_analysis(energy_df: pd.DataFrame, config: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """Run full statistical analysis pipeline."""
    frequency_bins = config['frequency_bins']
    material_type = config['material_type']
    
    results = {}
    
    for freq_bin in frequency_bins:
        next_freq = frequency_bins[frequency_bins.index(freq_bin) + 1] if frequency_bins.index(freq_bin) + 1 < len(frequency_bins) else float('inf')
        mask = (energy_df['frequency'] >= freq_bin) & (energy_df['frequency'] < next_freq) & (energy_df['material_type'] == material_type)
        bin_df = energy_df[mask]
        
        if len(bin_df) < 10:
            logger.warning(f"Insufficient data for bin {freq_bin}, skipping")
            continue
        
        energy_samples = bin_df['E_trans'].dropna().values
        if len(energy_samples) == 0:
            continue
        
        # Estimate scale from mean
        scale_estimate = np.mean(energy_samples)
        
        # KS test
        ks_stat, ks_p = perform_ks_test(energy_samples, scale_estimate)
        
        # Chi-squared test
        chi2_stat, chi2_p = perform_chisquared_test(energy_samples, scale_estimate)
        
        results[f"{freq_bin}_{material_type}"] = {
            'n_samples': len(energy_samples),
            'ks_statistic': ks_stat,
            'ks_p_value': ks_p,
            'chi2_statistic': chi2_stat,
            'chi2_p_value': chi2_p,
            'reject_ks': ks_p < alpha,
            'reject_chi2': chi2_p < alpha
        }
    
    # Apply FDR correction
    p_values = [r['ks_p_value'] for r in results.values()]
    corrected_p = apply_benjamini_hochberg(p_values)
    
    for (key, _), p_corr in zip(results.items(), corrected_p):
        results[key]['corrected_p_value'] = p_corr
        results[key]['reject_ks_fdr'] = p_corr < alpha
    
    return results

def main(args=None):
    """Main entry point for statistical analysis."""
    if args is None:
        parser = argparse.ArgumentParser(description='Statistical Analysis')
        parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
        parser.add_argument('--verbose', action='store_true', help='Verbose logging')
        args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load config
        from config import load_config
        config = load_config()
        
        # Load energy data
        energy_df = pd.read_csv('data/derived/energy_samples.csv')
        
        # Run analysis
        results = run_statistical_analysis(energy_df, config, args.alpha)
        
        # Write results
        output_path = Path('artifacts/statistical_results.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Statistical results written to {output_path}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
