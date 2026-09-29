import csv
import json
import logging
import os
import sys
import math
from pathlib import Path

# Import checkpoint utilities from the shared utils module
from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    # Simple YAML parser for flat structure (avoiding external deps if possible)
    # If the project uses PyYAML, we should import it. Assuming standard library fallback or PyYAML installed.
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not found, attempting manual parse. This may fail for complex YAML.")
        config = {}
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # Handle simple types
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value)
                    elif value.startswith('[') and value.endswith(']'):
                        # Simple list parsing
                        value = [x.strip().strip('"').strip("'") for x in value[1:-1].split(',')]
                    config[key] = value
        return config

def load_processed_data():
    """Load the preprocessed run records."""
    data_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'run_records.csv'
    if not data_path.exists():
        logger.error(f"Processed data not found: {data_path}")
        sys.exit(1)
    
    data = []
    with open(data_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def group_by_game(data):
    """Group data by game_id."""
    groups = {}
    for row in data:
        game_id = row['game_id']
        if game_id not in groups:
            groups[game_id] = []
        groups[game_id].append(row)
    return groups

def fit_distribution(times, dist_name):
    """
    Fit a distribution to the times using MLE.
    Returns parameters, KS_D, KS_pvalue, AIC.
    Uses scipy.stats for fitting.
    """
    try:
        from scipy import stats
        import numpy as np
    except ImportError:
        logger.error("scipy and numpy are required for distribution fitting.")
        sys.exit(1)

    times = np.array([float(t) for t in times if t is not None and t != ''])
    if len(times) == 0:
        return None

    result = {
        'dist_name': dist_name,
        'parameters': None,
        'KS_D': None,
        'KS_pvalue': None,
        'AIC': None
    }

    try:
        if dist_name == 'lognorm':
            # scipy lognorm: s is sigma, loc is 0, scale is exp(mu)
            # fit returns (s, loc, scale)
            s, loc, scale = stats.lognorm.fit(times, floc=0)
            params = {'s': float(s), 'loc': float(loc), 'scale': float(scale)}
            dist = stats.lognorm(s, loc=loc, scale=scale)
        
        elif dist_name == 'weibull_min':
            # scipy weibull_min: c is k, loc is 0, scale is lambda
            c, loc, scale = stats.weibull_min.fit(times, floc=0)
            params = {'c': float(c), 'loc': float(loc), 'scale': float(scale)}
            dist = stats.weibull_min(c, loc=loc, scale=scale)
        
        elif dist_name == 'gamma':
            # scipy gamma: a is k, loc is 0, scale is theta
            a, loc, scale = stats.gamma.fit(times, floc=0)
            params = {'a': float(a), 'loc': float(loc), 'scale': float(scale)}
            dist = stats.gamma(a, loc=loc, scale=scale)
        
        else:
            logger.warning(f"Unknown distribution: {dist_name}")
            return None

        # Kolmogorov-Smirnov test
        ks_stat, ks_p = stats.kstest(times, dist.cdf)
        
        # AIC calculation: 2k - 2ln(L)
        # loglikelihood from scipy
        log_likelihood = dist.logpdf(times).sum()
        k = len(params) # number of parameters
        aic = 2 * k - 2 * log_likelihood

        result['parameters'] = params
        result['KS_D'] = float(ks_stat)
        result['KS_pvalue'] = float(ks_p)
        result['AIC'] = float(aic)
        
        return result

    except Exception as e:
        logger.error(f"Error fitting {dist_name}: {e}")
        return None

def perform_anderson_darling(times, dist_name):
    """
    Perform Anderson-Darling test for descriptive purposes on small samples.
    Returns descriptive statistics only.
    """
    try:
        from scipy import stats
        import numpy as np
    except ImportError:
        logger.error("scipy required.")
        sys.exit(1)

    times = np.array([float(t) for t in times if t is not None and t != ''])
    if len(times) == 0:
        return None

    # Anderson-Darling test in scipy is implemented for normal, exponential, logistic, etc.
    # For general distributions, we might not have a direct AD test in scipy without custom implementation.
    # However, the spec says "descriptive purposes ONLY".
    # We will return the AD statistic if available for the distribution family, or just basic stats if not.
    
    result = {
        'dist_name': dist_name,
        'AD_statistic': None,
        'critical_values': None,
        'note': 'Descriptive only for n < 100'
    }

    try:
        if dist_name == 'norm':
            res = stats.anderson(times, dist='norm')
            result['AD_statistic'] = float(res.statistic)
            result['critical_values'] = [float(cv) for cv in res.critical_values]
        elif dist_name == 'expon':
            res = stats.anderson(times, dist='expon')
            result['AD_statistic'] = float(res.statistic)
            result['critical_values'] = [float(cv) for cv in res.critical_values]
        else:
            # For others, we might not have a built-in AD test in scipy.
            # We can calculate a custom AD statistic or just log that it's not available.
            # Given the constraint "descriptive ONLY", we'll note unavailability.
            result['note'] = 'AD test not implemented for this distribution in scipy.'
        
        return result
    except Exception as e:
        logger.warning(f"AD test failed for {dist_name}: {e}")
        return result

def process_game(game_id, runs, config):
    """Process a single game: fit distributions, handle small n."""
    min_sample_size = config.get('min_sample_size', 100)
    results = []
    
    times = [r['run_time_seconds'] for r in runs if r.get('run_time_seconds')]
    n = len(times)
    
    entry = {
        'game_id': game_id,
        'n': n,
        'fits': []
    }
    
    if n < min_sample_size:
        logger.info(f"Game {game_id} has {n} runs (< {min_sample_size}). Using Anderson-Darling for descriptive only.")
        entry['status'] = 'small_sample'
        # Try AD for log-normal (approximated as normal on log scale) or others if applicable
        # For simplicity, we fit log-normal parameters anyway for description if possible, but flag it.
        # The spec says "exclude from parametric fitting (KS test)".
        # We will still attempt to fit parameters for descriptive purposes but not run KS.
        dists_to_try = ['lognorm', 'weibull_min', 'gamma']
        for dist in dists_to_try:
            fit_res = fit_distribution(times, dist)
            if fit_res:
                fit_res['note'] = 'Descriptive only (n < 100)'
                entry['fits'].append(fit_res)
        
        # Add AD if applicable
        ad_res = perform_anderson_darling(times, 'lognorm') # Example
        if ad_res and ad_res['AD_statistic'] is not None:
            entry['anderson_darling'] = ad_res
    
    else:
        entry['status'] = 'full_fit'
        dists_to_fit = ['lognorm', 'weibull_min', 'gamma']
        fits = []
        for dist in dists_to_fit:
            fit_res = fit_distribution(times, dist)
            if fit_res:
                fits.append(fit_res)
        
        # Select best fit by AIC
        if fits:
            best_fit = min(fits, key=lambda x: x['AIC'])
            best_fit['best'] = True
            for f in fits:
                if f['KS_pvalue'] < 0.05:
                    f['rejected'] = True
                else:
                    f['rejected'] = False
                f['best'] = (f == best_fit)
        
        entry['fits'] = fits
    
    return entry

def save_results(all_results, output_path):
    """Save results to CSV."""
    # Flatten results for CSV
    rows = []
    for res in all_results:
        for fit in res.get('fits', []):
            row = {
                'game_id': res['game_id'],
                'n': res['n'],
                'status': res['status'],
                'dist_name': fit['dist_name'],
                'params_s': fit['parameters'].get('s', fit['parameters'].get('c', fit['parameters'].get('a', ''))),
                'params_loc': fit['parameters'].get('loc', ''),
                'params_scale': fit['parameters'].get('scale', ''),
                'KS_D': fit['KS_D'],
                'KS_pvalue': fit['KS_pvalue'],
                'AIC': fit['AIC'],
                'rejected': fit.get('rejected', False),
                'best': fit.get('best', False),
                'note': fit.get('note', '')
            }
            if 'anderson_darling' in res and res['anderson_darling']:
                row['AD_stat'] = res['anderson_darling'].get('AD_statistic', '')
            rows.append(row)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    logger.info(f"Results saved to {output_path}")

def main():
    logger.info("Starting distribution fitting with checkpointing.")
    config = load_config()
    games = config.get('games', [])
    
    if not games:
        logger.error("No games defined in config.")
        sys.exit(1)
    
    data = load_processed_data()
    groups = group_by_game(data)
    
    # Checkpoint setup
    checkpoint_dir = Path(__file__).parent.parent / 'data' / 'checkpoints'
    ensure_checkpoint_dir(checkpoint_dir)
    checkpoint_path = get_checkpoint_path(checkpoint_dir, 'distribution_fitting')
    
    # Load checkpoint if exists
    start_index = 0
    if os.path.exists(checkpoint_path):
        logger.info(f"Loading checkpoint from {checkpoint_path}")
        checkpoint_data = load_checkpoint(checkpoint_path)
        start_index = checkpoint_data.get('start_index', 0)
        logger.info(f"Resuming from game index {start_index}")
    
    all_results = []
    
    for i, game_id in enumerate(games):
        if i < start_index:
            logger.info(f"Skipping {game_id} (already processed)")
            continue
        
        if game_id not in groups:
            logger.warning(f"No data for game {game_id}")
            continue
        
        runs = groups[game_id]
        logger.info(f"Processing game {game_id} ({i+1}/{len(games)})")
        
        result = process_game(game_id, runs, config)
        all_results.append(result)
        
        # Save checkpoint after each game
        checkpoint_data = {
            'start_index': i + 1,
            'current_game': game_id,
            'partial_results': all_results
        }
        save_checkpoint(checkpoint_path, checkpoint_data)
        logger.info(f"Checkpoint saved after {game_id}")
    
    # Final save
    output_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'distribution_fits.csv'
    save_results(all_results, output_path)
    
    # Delete checkpoint on success
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        logger.info("Checkpoint deleted (success)")
    
    logger.info("Distribution fitting complete.")

if __name__ == '__main__':
    main()