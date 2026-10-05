"""
Distribution Fitting Script (T020)

Fits log-normal, Weibull, and gamma distributions to speedrun times using MLE.
Performs Kolmogorov-Smirnov (KS) tests and calculates AIC.
Handles low-sample games by running Anderson-Darling tests and flagging them.
Saves results to data/processed/distribution_fits.csv.
"""

import csv
import json
import logging
import os
import sys
import math
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.special import gammaln

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path
from scripts.preprocess import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/logs/fit_distributions.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data():
    """Load the preprocessed run records CSV."""
    input_path = Path('data/processed/run_records.csv')
    if not input_path.exists():
        logger.error(f"Processed data not found: {input_path}. Run preprocessing first.")
        raise FileNotFoundError(f"Processed data not found: {input_path}. Run preprocessing first.")
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert run_time_seconds to float
            try:
                row['run_time_seconds'] = float(row['run_time_seconds'])
                data.append(row)
            except ValueError:
                logger.warning(f"Skipping row with invalid run_time_seconds: {row.get('run_time_seconds')}")
    return data

def group_by_game(data):
    """Group data by game_id."""
    games = {}
    for row in data:
        game_id = row['game_id']
        if game_id not in games:
            games[game_id] = []
        games[game_id].append(row['run_time_seconds'])
    return games

def fit_distribution(times, dist_name):
    """
    Fit a distribution to the times using MLE.
    Returns parameters, KS statistic, KS p-value, and AIC.
    """
    if len(times) < 2:
        return None, None, None, None

    times = np.array(times)
    # Filter out non-positive values for log-normal, gamma, weibull
    if dist_name in ['lognorm', 'gamma', 'weibull_min']:
        valid_mask = times > 0
        if np.sum(valid_mask) < 2:
            logger.warning(f"Not enough positive values for {dist_name} fit in sample of size {len(times)}")
            return None, None, None, None
        times = times[valid_mask]

    try:
        if dist_name == 'lognorm':
            # scipy.stats.lognorm: s is shape (sigma), scale is exp(mu)
            # Fit using log-transformed data to get mu, sigma directly
            log_times = np.log(times)
            mu, sigma = stats.norm.fit(log_times)
            # Convert back to lognorm parameters: s=sigma, scale=exp(mu)
            params = {'s': sigma, 'scale': np.exp(mu)}
            # For AIC and KS, we use the fitted lognorm object
            dist = stats.lognorm(**params)
            
        elif dist_name == 'weibull_min':
            # Weibull minimum (standard Weibull)
            # scipy.stats.weibull_min: c is shape (k), scale is scale
            params = stats.weibull_min.fit(times, floc=0) # Fix location to 0
            dist = stats.weibull_min(*params)

        elif dist_name == 'gamma':
            # Gamma distribution
            params = stats.gamma.fit(times, floc=0) # Fix location to 0
            dist = stats.gamma(*params)
        
        else:
            raise ValueError(f"Unknown distribution: {dist_name}")

        # Kolmogorov-Smirnov test
        # KS test compares empirical CDF to theoretical CDF
        ks_stat, ks_pvalue = stats.kstest(times, dist.cdf)

        # AIC calculation: 2k - 2ln(L)
        # k = number of parameters
        # ln(L) = log-likelihood
        k = len(params)
        log_likelihood = np.sum(dist.logpdf(times))
        aic = 2 * k - 2 * log_likelihood

        return params, ks_stat, ks_pvalue, aic

    except Exception as e:
        logger.warning(f"Failed to fit {dist_name} to game: {e}")
        return None, None, None, None

def perform_anderson_darling(times, dist_name):
    """
    Perform Anderson-Darling test for a distribution.
    Returns the AD statistic.
    """
    if len(times) < 2:
        return None

    times = np.array(times)
    if dist_name in ['lognorm', 'gamma', 'weibull_min']:
        valid_mask = times > 0
        if np.sum(valid_mask) < 2:
            return None
        times = times[valid_mask]

    try:
        if dist_name == 'lognorm':
            log_times = np.log(times)
            ad_stat, crit_vals, sig_level = stats.anderson(log_times, dist='norm')
            return ad_stat # AD stat for log-transformed data
        elif dist_name == 'weibull_min':
            # AD test for Weibull is not directly in scipy, use gamma as proxy or custom
            # For simplicity, we'll use the generic AD test against the fitted distribution
            params = stats.weibull_min.fit(times, floc=0)
            dist = stats.weibull_min(*params)
            # scipy.stats.anderson does not support arbitrary CDFs directly in older versions
            # We will compute it manually or use a placeholder if not supported
            # Let's try to use the built-in if available, else fallback to None or custom
            # Since scipy < 1.10 doesn't support custom CDF in anderson, we'll skip for now
            # or implement a simple version.
            # For this task, we'll return None for Weibull AD if not directly supported
            # But let's try to compute it manually:
            n = len(times)
            sorted_times = np.sort(times)
            y = dist.cdf(sorted_times)
            # AD statistic formula: -n - (1/n) * sum((2i-1)*(ln(y_i) + ln(1-y_{n+1-i})))
            # Avoid log(0)
            y = np.clip(y, 1e-10, 1-1e-10)
            i = np.arange(1, n+1)
            ad_stat = -n - (1/n) * np.sum((2*i - 1) * (np.log(y) + np.log(1 - y[::-1])))
            return ad_stat
        elif dist_name == 'gamma':
            params = stats.gamma.fit(times, floc=0)
            dist = stats.gamma(*params)
            n = len(times)
            sorted_times = np.sort(times)
            y = dist.cdf(sorted_times)
            y = np.clip(y, 1e-10, 1-1e-10)
            i = np.arange(1, n+1)
            ad_stat = -n - (1/n) * np.sum((2*i - 1) * (np.log(y) + np.log(1 - y[::-1])))
            return ad_stat
        else:
            return None
    except Exception as e:
        logger.warning(f"Failed AD test for {dist_name}: {e}")
        return None

def process_game(game_id, times, min_sample_size):
    """Process a single game: fit distributions, run tests, handle low sample."""
    results = []
    n = len(times)
    
    # Low sample check
    is_low_sample = n < min_sample_size
    
    # Define distributions to fit
    dists = ['lognorm', 'weibull_min', 'gamma']
    
    best_fit = None
    best_aic = float('inf')
    
    for dist_name in dists:
        params, ks_stat, ks_pvalue, aic = fit_distribution(times, dist_name)
        
        if params is None:
            continue
        
        # Map scipy names to human readable
        dist_label = {
            'lognorm': 'log-normal',
            'weibull_min': 'Weibull',
            'gamma': 'Gamma'
        }[dist_name]
        
        # Run AD test
        ad_stat = perform_anderson_adarling(times, dist_name)
        
        row = {
            'game_id': game_id,
            'distribution_family': dist_label,
            'n': n,
            'KS_D': ks_stat,
            'KS_pvalue': ks_pvalue,
            'AIC': aic,
            'ad_statistic': ad_stat,
            'is_low_sample': is_low_sample
        }
        
        # Store parameters as JSON string
        row['parameters'] = json.dumps(params)
        
        results.append(row)
        
        if aic < best_aic:
            best_aic = aic
            best_fit = dist_label
            
    # If low sample, we still add the parametric rows if fit was successful,
    # but we also need to add a 'descriptive' row if NO parametric fit was possible
    # or if we want to explicitly mark it. The task says:
    # "Filter out games with <100 runs" -> T021a handles filtering in the CSV or logic.
    # "Run Anderson-Darling test on low-sample games" -> Done above.
    # "Add 'descriptive' rows for excluded games" -> T021c handles adding the row.
    # So here we just return the fitted rows. T021a/c will filter/add based on n.
    
    return results, best_fit

def save_results(all_results, output_path):
    """Save results to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'game_id', 'distribution_family', 'n', 'parameters', 
        'KS_D', 'KS_pvalue', 'AIC', 'ad_statistic', 'is_low_sample'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)
    
    logger.info(f"Results saved to {output_path}")

def main():
    logger.info("Starting distribution fitting with checkpointing.")
    
    config = load_config()
    min_sample_size = config.get('min_sample_size', 100)
    
    # Load data
    try:
        data = load_processed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    games = group_by_game(data)
    logger.info(f"Loaded processed data for {len(games)} games.")
    
    # Checkpoint setup
    checkpoint_dir = ensure_checkpoint_dir()
    checkpoint_path = get_checkpoint_path('fit_distributions')
    checkpoint = load_checkpoint(checkpoint_path)
    
    processed_games = set(checkpoint.get('processed_games', []))
    all_results = []
    
    game_ids = list(games.keys())
    
    for i, game_id in enumerate(game_ids):
        # Checkpoint resume
        if game_id in processed_games:
            logger.info(f"Skipping already processed game: {game_id}")
            continue
        
        logger.info(f"Processing game {i+1}/{len(game_ids)}: {game_id}")
        
        times = games[game_id]
        game_results, best_fit = process_game(game_id, times, min_sample_size)
        
        all_results.extend(game_results)
        
        # Save checkpoint after each game
        processed_games.add(game_id)
        save_checkpoint(checkpoint_path, {
            'processed_games': list(processed_games),
            'partial_results_count': len(all_results)
        })
        
        logger.info(f"Completed game: {game_id}, best fit: {best_fit}")
    
    # Save final results
    output_path = 'data/processed/distribution_fits.csv'
    save_results(all_results, output_path)
    
    # Clean up checkpoint on success
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        logger.info("Checkpoint cleaned up.")
        
    logger.info("Distribution fitting completed successfully.")

if __name__ == '__main__':
    main()
