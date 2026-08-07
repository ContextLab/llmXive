import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from scipy.special import gamma

# Import from local modules as per API surface
from dickman import rho, DickmanFunction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_density_data(filepath: str) -> List[Dict[str, Any]]:
    """
    Load density measurement data from a CSV file.
    Expects columns: x, y, h, count, density, d_dickman (optional), r_deviation (optional)
    """
    data = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        # Skip header
        header = f.readline().strip().split(',')
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < len(header):
                continue
            row = {}
            for i, col in enumerate(header):
                val = parts[i].strip()
                if val == '':
                    row[col] = None
                elif col in ['x', 'y', 'h', 'count']:
                    row[col] = int(val)
                else:
                    try:
                        row[col] = float(val)
                    except ValueError:
                        row[col] = val
            data.append(row)
    return data

def power_law(x: np.ndarray, c: float, beta: float) -> np.ndarray:
    """
    Power law function: f(x) = c * x^beta
    """
    return c * np.power(x, beta)

def fit_power_law_deviation(data: List[Dict[str, Any]], y_val: int) -> Optional[Dict[str, Any]]:
    """
    Fit power law to deviation ratio R = rho_obs / rho_dickman for a specific y.
    Model: R = c * h^beta
    """
    subset = [d for d in data if d.get('y') == y_val and d.get('r_deviation') is not None and d.get('r_deviation') > 0]
    if not subset:
        return None
    
    h_vals = np.array([d['h'] for d in subset])
    r_vals = np.array([d['r_deviation'] for d in subset])
    
    # Log-log transformation for linear regression
    log_h = np.log(h_vals)
    log_r = np.log(r_vals)
    
    # Weighted least squares (optional, using 1/h as weight if needed, here simple OLS)
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_h, log_r)
    
    c_est = np.exp(intercept)
    beta_est = slope
    
    return {
        'y': y_val,
        'c': c_est,
        'beta': beta_est,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err': std_err,
        'n_points': len(subset)
    }

def fit_power_law_raw_density(data: List[Dict[str, Any]], y_val: int) -> Optional[Dict[str, Any]]:
    """
    Fit power law to raw density rho = count/h for a specific y.
    Model: rho = c * h^beta
    """
    subset = [d for d in data if d.get('y') == y_val and d.get('density') is not None and d.get('density') > 0]
    if not subset:
        return None
    
    h_vals = np.array([d['h'] for d in subset])
    rho_vals = np.array([d['density'] for d in subset])
    
    log_h = np.log(h_vals)
    log_rho = np.log(rho_vals)
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_h, log_rho)
    
    c_est = np.exp(intercept)
    beta_est = slope
    
    return {
        'y': y_val,
        'c': c_est,
        'beta': beta_est,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err': std_err,
        'n_points': len(subset)
    }

def run_plan_primary_analysis(data: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """
    Plan-Primary Analysis:
    1. Power-law regression on deviation ratio R (T026a).
    2. Kolmogorov-Smirnov (KS) test comparing observed vs. Dickman distributions (T027a).
    """
    logger.info("Starting Plan-Primary Analysis...")
    results = {
        'power_law_deviation': {},
        'ks_tests': {}
    }
    
    # 1. Power-law regression on deviation ratio
    y_values = sorted(list(set(d['y'] for d in data if 'y' in d)))
    for y_val in y_values:
        fit = fit_power_law_deviation(data, y_val)
        if fit:
            results['power_law_deviation'][str(y_val)] = fit
            logger.info(f"  Y={y_val}: beta={fit['beta']:.4f}, R^2={fit['r_squared']:.4f}")
    
    # 2. Kolmogorov-Smirnov Test (T027a)
    # We compare the distribution of observed deviations from the Dickman prediction.
    # Null Hypothesis: The observed deviations are consistent with the Dickman function's theoretical distribution.
    # Since Dickman is a single value for a given u, we interpret this as testing the "goodness of fit"
    # of the observed counts against the expected counts derived from Dickman(u) * h.
    # However, the KS test is typically for continuous distributions.
    # To adapt: We can treat the "standardized residual" or the ratio R as the variable.
    # But a more direct interpretation for "Observed vs Dickman" in a discrete count context
    # often involves comparing the empirical CDF of the counts to a theoretical CDF.
    # Given the data structure (x, y, h, count), we can construct a sample of "observed densities"
    # and compare it to a "theoretical density" sample generated by the Dickman function 
    # (with added noise or just the theoretical value as a degenerate distribution, which KS doesn't like).
    
    # Alternative robust interpretation for T027a:
    # We test if the distribution of the *ratio* R = observed/dickman follows a specific pattern.
    # If the Dickman function is the perfect predictor, R should be centered around 1.
    # We can perform a one-sample KS test against a theoretical distribution centered at 1?
    # Or, more likely, we compare the empirical CDF of the *observed counts* (scaled) 
    # to the CDF of the *expected counts* (scaled).
    
    # Let's implement a KS test on the standardized residuals or the ratio R.
    # If we assume the Dickman function provides the mean, we can test if the observed values
    # deviate significantly.
    # However, KS is for comparing two samples or one sample to a distribution.
    # Let's construct two samples for each y:
    # Sample A: Observed densities (count/h)
    # Sample B: Theoretical densities (rho(u)) - repeated to match sample size? 
    # This is tricky because rho(u) is a constant for a fixed u.
    
    # Correct approach for "Observed vs Dickman" with KS:
    # We can bin the data and compare the empirical distribution of the *relative error* 
    # or simply compare the distribution of the *observed counts* to a Poisson distribution 
    # with lambda = Dickman(u) * h. But KS is not ideal for Poisson.
    
    # Let's follow the prompt's specific instruction: "comparing observed vs. Dickman distributions".
    # We will generate a theoretical sample based on the Dickman function.
    # Since Dickman gives a density, we can simulate counts from a Poisson process with lambda = rho(u)*h.
    # Then compare the empirical distribution of actual counts to the simulated Poisson counts.
    
    for y_val in y_values:
        subset = [d for d in data if d.get('y') == y_val]
        if not subset:
            continue
        
        observed_counts = []
        theoretical_counts = []
        
        for d in subset:
            x = d['x']
            h = d['h']
            count = d['count']
            
            u = np.log(x) / np.log(y_val) if y_val > 1 else 1e9
            if u <= 0:
                continue
            
            # Theoretical density
            rho_u = rho(u)
            expected_count = rho_u * h
            
            observed_counts.append(count)
            # Generate theoretical sample (simulating the distribution of counts under the null)
            # We simulate N points from Poisson(expected_count) to compare distributions
            # But KS test compares CDFs. We can just compare the observed counts to the expected count?
            # No, KS needs a distribution.
            # Let's assume the null hypothesis is that the counts follow Poisson(lambda = rho(u)*h).
            # We will generate a large sample of Poisson counts for the theoretical distribution.
            # However, lambda varies with x.
            # To make it comparable, we can normalize: (count - lambda) / sqrt(lambda) -> Standard Normal?
            # Or we can just compare the empirical CDF of the normalized residuals.
            
            # Simplified approach for T027a as per "Plan Principle VII":
            # We compare the empirical distribution of the *ratio* R = count / (rho(u)*h) to a distribution centered at 1.
            # If the model is perfect, R ~ 1.
            # We can test if the distribution of R is consistent with a specific theoretical distribution (e.g., Normal(1, sigma)).
            # But we don't have sigma.
            
            # Let's try: KS test of the observed counts against a Poisson distribution with varying lambda.
            # This is complex.
            
            # Alternative: KS test on the *standardized* values.
            # Z = (count - lambda) / sqrt(lambda)
            # Compare Z to Standard Normal?
            
            # Let's stick to the most direct interpretation:
            # Compare the empirical CDF of the observed counts to the CDF of a Poisson distribution 
            # with lambda = rho(u)*h. Since lambda varies, we can't do a single KS test easily.
            
            # Let's assume the task implies comparing the *distribution of densities* to the *Dickman function*.
            # We will collect all observed densities for a given y.
            # We will collect all theoretical densities (rho(u)) for the same y.
            # Then run KS test on these two samples.
            # Note: rho(u) is a constant for a fixed u, but u varies with x.
            
            pass 
        
        # Re-evaluating the data structure:
        # We have multiple x values for the same y.
        # For each x, we have a theoretical rho(u).
        # We can collect all observed densities and all theoretical densities.
        # Then run KS test between these two lists.
        
        obs_densities = []
        theo_densities = []
        
        for d in subset:
            x = d['x']
            h = d['h']
            count = d['count']
            if h == 0: continue
            
            u = np.log(x) / np.log(y_val) if y_val > 1 else 1e9
            if u <= 0: continue
            
            rho_u = rho(u)
            obs_d = count / h
            obs_densities.append(obs_d)
            theo_densities.append(rho_u)
        
        if len(obs_densities) > 1 and len(theo_densities) > 1:
            ks_stat, p_val = stats.ks_2samp(obs_densities, theo_densities)
            results['ks_tests'][str(y_val)] = {
                'statistic': float(ks_stat),
                'p_value': float(p_val),
                'n_obs': len(obs_densities),
                'n_theo': len(theo_densities)
            }
            logger.info(f"  Y={y_val}: KS Stat={ks_stat:.4f}, P-value={p_val:.4f}")
        else:
            results['ks_tests'][str(y_val)] = {
                'error': 'Insufficient data points for KS test',
                'n_obs': len(obs_densities),
                'n_theo': len(theo_densities)
            }

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Plan-Primary Analysis results saved to {output_path}")
    return results

def run_spec_mandatory_analysis(data: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """
    Spec-Mandatory Analysis (FR-005): Chi-Square Goodness-of-Fit.
    Bins the interval data and compares observed vs expected counts.
    """
    logger.info("Starting Spec-Mandatory (Chi-Square) Analysis...")
    results = {
        'chi_square_tests': {}
    }
    
    y_values = sorted(list(set(d['y'] for d in data if 'y' in d)))
    
    for y_val in y_values:
        subset = [d for d in data if d.get('y') == y_val]
        if not subset:
            continue
        
        # Bin the data by x or h? Spec says "Bin the interval data".
        # Let's bin by x (log scale) to group similar u values.
        # Or simply group all data for a given y and compare total observed vs total expected?
        # Chi-square requires bins.
        # Let's create bins based on the range of x.
        
        x_vals = [d['x'] for d in subset]
        if not x_vals:
            continue
        
        min_x, max_x = min(x_vals), max(x_vals)
        n_bins = min(10, len(subset))
        bin_edges = np.logspace(np.log10(min_x), np.log10(max_x), n_bins + 1)
        
        observed_counts = np.zeros(n_bins)
        expected_counts = np.zeros(n_bins)
        
        for d in subset:
            x = d['x']
            h = d['h']
            count = d['count']
            
            # Determine bin
            bin_idx = np.digitize(x, bin_edges) - 1
            if 0 <= bin_idx < n_bins:
                observed_counts[bin_idx] += count
                
                u = np.log(x) / np.log(y_val) if y_val > 1 else 1e9
                rho_u = rho(u)
                expected_counts[bin_idx] += rho_u * h
        
        # Perform Chi-Square test
        # Handle zero expected counts
        mask = expected_counts > 0
        if np.sum(mask) < 2:
            results['chi_square_tests'][str(y_val)] = {'error': 'Not enough bins with expected counts > 0'}
            continue
        
        chi2, p_val = stats.chisquare(observed_counts[mask], expected_counts[mask])
        
        results['chi_square_tests'][str(y_val)] = {
            'chi2_statistic': float(chi2),
            'p_value': float(p_val),
            'df': int(np.sum(mask) - 1),
            'n_bins': n_bins
        }
        logger.info(f"  Y={y_val}: Chi2={chi2:.4f}, P={p_val:.4f}")

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Spec-Mandatory Analysis results saved to {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Analysis of Smooth Number Distributions")
    parser.add_argument('--plan-grid', type=str, default='data/density_measurements_plan.csv',
                        help='Path to Plan-defined grid data')
    parser.add_argument('--spec-grid', type=str, default='data/density_measurements_spec.csv',
                        help='Path to Spec-defined grid data')
    parser.add_argument('--output', type=str, default='data/model_fits.json',
                        help='Output JSON file for all results')
    args = parser.parse_args()

    # Load Plan data
    try:
        plan_data = load_density_data(args.plan_grid)
        logger.info(f"Loaded {len(plan_data)} rows from Plan grid.")
    except FileNotFoundError as e:
        logger.error(f"Plan grid data not found: {e}")
        sys.exit(1)

    # Load Spec data
    try:
        spec_data = load_density_data(args.spec_grid)
        logger.info(f"Loaded {len(spec_data)} rows from Spec grid.")
    except FileNotFoundError as e:
        logger.error(f"Spec grid data not found: {e}")
        sys.exit(1)

    # Run Plan-Primary Analysis (T026a + T027a)
    plan_results = run_plan_primary_analysis(plan_data, 'data/plan_analysis_results.json')
    
    # Run Spec-Mandatory Analysis (T026b + T027b)
    spec_results = run_spec_mandatory_analysis(spec_data, 'data/spec_analysis_results.json')

    # Combine results
    final_output = {
        'plan_primary': plan_results,
        'spec_mandatory': spec_results
    }

    with open(args.output, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    logger.info(f"All analysis results saved to {args.output}")

if __name__ == '__main__':
    main()