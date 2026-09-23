import csv
import json
import logging
import os
import sys
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import checkpoint utilities from the shared utils module
from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/distribution_fitting.log')
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = 'code/config.yaml') -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed, attempting manual parsing or returning defaults")
        # Fallback if yaml is missing, though requirements should handle it
        return {
            'games': [],
            'min_sample_size': 100,
            'salt': 'default_salt',
            'effect_size_assumptions': 0.5
        }

def load_processed_data(data_path: str = 'data/processed/run_records.csv') -> List[Dict[str, Any]]:
    """Load preprocessed run records from CSV."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run T013a first.")
    
    records = []
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['run_time_seconds'] = float(row['run_time_seconds'])
                row['attempt_number'] = int(row['attempt_number'])
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping row due to conversion error: {e}")
                continue
            records.append(row)
    return records

def group_by_game(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group records by game_id."""
    grouped = {}
    for record in records:
        game_id = record.get('game_id')
        if game_id:
            if game_id not in grouped:
                grouped[game_id] = []
            grouped[game_id].append(record)
    return grouped

def fit_distribution(times: List[float], distribution_name: str) -> Optional[Dict[str, Any]]:
    """
    Fit a distribution to the given times using MLE.
    Returns parameters, KS statistic, p-value, and AIC.
    """
    try:
        from scipy import stats
        import numpy as np
    except ImportError:
        logger.error("scipy or numpy not installed. Cannot fit distributions.")
        raise

    data = np.array(times)
    if len(data) < 2:
        return None

    params = None
    ks_stat = None
    p_value = None
    aic = None
    fitted_dist = None

    try:
        if distribution_name == 'log-normal':
            # Log-normal: scipy uses (s, loc, scale). We estimate s, loc, scale.
            # Often we fix loc=0 for positive data, but let scipy estimate.
            shape, loc, scale = stats.lognorm.fit(data, floc=0)
            fitted_dist = stats.lognorm(shape, loc=scale) # fix loc for CDF calculation if needed
            params = {'shape': float(shape), 'scale': float(scale)}
            
            # KS Test
            ks_stat, p_value = stats.kstest(data, 'lognorm', args=(shape, loc, scale))
            
            # AIC
            log_likelihood = np.sum(fitted_dist.logpdf(data))
            k = 2 # number of parameters estimated (shape, scale) - loc fixed
            aic = 2 * k - 2 * log_likelihood

        elif distribution_name == 'Weibull':
            # Weibull: scipy uses (c, loc, scale)
            c, loc, scale = stats.weibull_min.fit(data, floc=0)
            fitted_dist = stats.weibull_min(c, loc=scale)
            params = {'c': float(c), 'scale': float(scale)}

            ks_stat, p_value = stats.kstest(data, 'weibull_min', args=(c, loc, scale))

            log_likelihood = np.sum(fitted_dist.logpdf(data))
            k = 2
            aic = 2 * k - 2 * log_likelihood

        elif distribution_name == 'Gamma':
            # Gamma: scipy uses (a, loc, scale)
            a, loc, scale = stats.gamma.fit(data, floc=0)
            fitted_dist = stats.gamma(a, loc=scale)
            params = {'a': float(a), 'scale': float(scale)}

            ks_stat, p_value = stats.kstest(data, 'gamma', args=(a, loc, scale))

            log_likelihood = np.sum(fitted_dist.logpdf(data))
            k = 2
            aic = 2 * k - 2 * log_likelihood
        else:
            logger.warning(f"Unknown distribution: {distribution_name}")
            return None

    except Exception as e:
        logger.error(f"Error fitting {distribution_name}: {e}")
        return None

    return {
        'distribution': distribution_name,
        'parameters': params,
        'KS_D': float(ks_stat) if ks_stat else None,
        'KS_pvalue': float(p_value) if p_value else None,
        'AIC': float(aic) if aic else None
    }

def perform_anderson_darling(times: List[float], distribution_name: str) -> Dict[str, Any]:
    """
    Perform Anderson-Darling test for descriptive purposes only.
    Note: scipy.stats.anderson does not take distribution parameters directly for all cases
    in the same way as kstest, but we can test against specific distributions.
    """
    try:
        from scipy import stats
        import numpy as np
    except ImportError:
        return {'error': 'scipy not available'}

    data = np.array(times)
    result = {'test': 'Anderson-Darling', 'distribution': distribution_name, 'statistic': None, 'critical_values': None}

    try:
        if distribution_name == 'log-normal':
            # AD test for lognormal
            res = stats.anderson(data, dist='lognorm')
            result['statistic'] = float(res.statistic)
            result['critical_values'] = [float(v) for v in res.critical_values]
        elif distribution_name == 'normal':
            res = stats.anderson(data, dist='norm')
            result['statistic'] = float(res.statistic)
            result['critical_values'] = [float(v) for v in res.critical_values]
        else:
            # Fallback to normal if specific AD not supported for this dist in scipy
            res = stats.anderson(data, dist='norm')
            result['statistic'] = float(res.statistic)
            result['critical_values'] = [float(v) for v in res.critical_values]
            result['note'] = f"AD for {distribution_name} not directly supported, using Normal as proxy for shape check"
    except Exception as e:
        result['error'] = str(e)

    return result

def process_game(game_id: str, runs: List[Dict[str, Any]], min_sample_size: int, checkpoint_dir: str) -> Optional[Dict[str, Any]]:
    """
    Process a single game: fit distributions, run tests, handle checkpointing.
    """
    times = [r['run_time_seconds'] for r in runs if 'run_time_seconds' in r]
    
    if len(times) < min_sample_size:
        logger.info(f"Game {game_id} has {len(times)} runs (< {min_sample_size}). Skipping MLE fitting.")
        # Still return descriptive stats if needed, but main output is skipped
        return {
            'game_id': game_id,
            'n_runs': len(times),
            'status': 'excluded_low_sample',
            'reason': f'n < {min_sample_size}'
        }

    # Check for existing checkpoint for this game
    checkpoint_path = get_checkpoint_path(checkpoint_dir, f"dist_fit_{game_id}")
    if os.path.exists(checkpoint_path):
        logger.info(f"Loading checkpoint for {game_id}")
        return load_checkpoint(checkpoint_path)

    results = {
        'game_id': game_id,
        'n_runs': len(times),
        'status': 'success',
        'fits': []
    }

    distributions = ['log-normal', 'Weibull', 'Gamma']
    
    for dist_name in distributions:
        fit_result = fit_distribution(times, dist_name)
        if fit_result:
            results['fits'].append(fit_result)
            
            # Flag rejected distributions
            if fit_result['KS_pvalue'] is not None and fit_result['KS_pvalue'] < 0.05:
                logger.warning(f"Game {game_id}: {dist_name} rejected (p < 0.05)")
                results['fits'][-1]['rejected'] = True
            else:
                results['fits'][-1]['rejected'] = False

    # Select best fit by AIC
    if results['fits']:
        best_fit = min(results['fits'], key=lambda x: x['AIC'] if x['AIC'] is not None else float('inf'))
        results['best_fit'] = best_fit['distribution']
        results['best_fit_aic'] = best_fit['AIC']

    # Save checkpoint
    save_checkpoint(checkpoint_path, results)
    logger.info(f"Checkpoint saved for {game_id}")

    return results

def save_results(all_results: List[Dict[str, Any]], output_path: str = 'data/processed/distribution_fits.csv'):
    """Save results to CSV."""
    if not all_results:
        logger.warning("No results to save.")
        return

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Flatten results for CSV
    rows = []
    for res in all_results:
        base = {
            'game_id': res['game_id'],
            'n_runs': res['n_runs'],
            'status': res['status']
        }
        
        if res['status'] == 'excluded_low_sample':
            base['reason'] = res.get('reason', 'Unknown')
            rows.append(base)
            continue

        if 'fits' in res:
            for fit in res['fits']:
                row = base.copy()
                row['distribution'] = fit['distribution']
                row['params'] = json.dumps(fit['parameters'])
                row['KS_D'] = fit['KS_D']
                row['KS_pvalue'] = fit['KS_pvalue']
                row['AIC'] = fit['AIC']
                row['rejected'] = fit.get('rejected', False)
                rows.append(row)
        
        if 'best_fit' in res:
            # Append best fit info to the last row or create a summary row?
            # Let's add a summary row for the best fit
            summary_row = base.copy()
            summary_row['is_best_fit'] = True
            summary_row['best_distribution'] = res['best_fit']
            summary_row['best_aic'] = res['best_fit_aic']
            rows.append(summary_row)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for distribution fitting."""
    logger.info("Starting distribution fitting process.")
    
    # Load config
    config = load_config()
    games = config.get('games', [])
    min_sample_size = config.get('min_sample_size', 100)
    
    if not games:
        logger.error("No games specified in config.yaml. Exiting.")
        sys.exit(1)

    # Load data
    try:
        records = load_processed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Group by game
    grouped_data = group_by_game(records)
    
    # Ensure checkpoint directory
    checkpoint_dir = 'data/checkpoints/distribution_fits'
    ensure_checkpoint_dir(checkpoint_dir)

    all_results = []
    
    for game_id in games:
        if game_id not in grouped_data:
            logger.warning(f"Game {game_id} not found in processed data.")
            continue
        
        logger.info(f"Processing game: {game_id}")
        try:
            result = process_game(game_id, grouped_data[game_id], min_sample_size, checkpoint_dir)
            if result:
                all_results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {game_id}: {e}")
            # Decide whether to stop or continue. Continue with error logged.
            all_results.append({
                'game_id': game_id,
                'n_runs': 0,
                'status': 'error',
                'error': str(e)
            })

    # Save final results
    save_results(all_results)
    logger.info("Distribution fitting complete.")

if __name__ == '__main__':
    main()