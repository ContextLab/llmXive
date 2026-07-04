import os
import sys
import csv
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scipy import stats

# Import logging utilities from the project's utils
try:
    from src.utils.logging import get_logger, info, warning, error, critical
except ImportError:
    # Fallback for direct execution or missing import chain
    logger = logging.getLogger(__name__)
    def get_logger(name): return logging.getLogger(name)
    def info(msg): logging.info(msg)
    def warning(msg): logging.warning(msg)
    def error(msg): logging.error(msg)
    def critical(msg): logging.critical(msg)

def calculate_rmse(predictions: List[float], actuals: List[float]) -> float:
    """Calculate Root Mean Squared Error."""
    if len(predictions) != len(actuals) or len(predictions) == 0:
        raise ValueError("Predictions and actuals must be non-empty and equal length.")
    mse = sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)
    return math.sqrt(mse)

def calculate_mae(predictions: List[float], actuals: List[float]) -> float:
    """Calculate Mean Absolute Error."""
    if len(predictions) != len(actuals) or len(predictions) == 0:
        raise ValueError("Predictions and actuals must be non-empty and equal length.")
    return sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(predictions)

def load_forecasts(file_path: str) -> Dict[str, List[Dict]]:
    """Load forecasts from a CSV file into a dictionary keyed by model name."""
    forecasts = {}
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Forecast file not found: {file_path}")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assume structure: model_name, date, forecast_value, lower_ci, upper_ci
            model = row.get('model_name')
            if not model:
                continue
            if model not in forecasts:
                forecasts[model] = []
            forecasts[model].append({
                'date': row.get('date'),
                'value': float(row.get('forecast_value', 0)),
                'lower_ci': float(row.get('lower_ci', 0)),
                'upper_ci': float(row.get('upper_ci', 0))
            })
    return forecasts

def load_outcomes(file_path: str) -> Dict[str, float]:
    """Load election outcomes from a CSV file keyed by date/state or similar identifier."""
    outcomes = {}
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Outcomes file not found: {file_path}")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming 'date' or 'election_date' is the key
            key = row.get('date') or row.get('election_date')
            if not key:
                continue
            outcomes[key] = float(row.get('actual_result', 0))
    return outcomes

def calculate_coverage(
    forecasts: Dict[str, List[Dict]], 
    outcomes: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate the empirical coverage rate of prediction intervals against actual outcomes.
    Returns a dict mapping model name to coverage proportion (0.0 to 1.0).
    """
    coverage_counts = {model: 0 for model in forecasts}
    total_checks = {model: 0 for model in forecasts}
    
    for model, preds in forecasts.items():
        for pred in preds:
            date = pred['date']
            if date in outcomes:
                actual = outcomes[date]
                lower = pred['lower_ci']
                upper = pred['upper_ci']
                
                total_checks[model] += 1
                if lower <= actual <= upper:
                    coverage_counts[model] += 1
    
    coverage_rates = {}
    for model in forecasts:
        if total_checks[model] > 0:
            coverage_rates[model] = coverage_counts[model] / total_checks[model]
        else:
            coverage_rates[model] = 0.0
            warning(f"No matching outcomes found for model {model} to calculate coverage.")
    
    return coverage_rates

def perform_binomial_coverage_test(
    coverage_rates: Dict[str, float],
    p0: float = 0.95,
    alpha: float = 0.05
) -> Dict[str, Dict]:
    """
    Perform a binomial test for each model's coverage rate against the null hypothesis.
    Null Hypothesis (H0): The true coverage probability is p0 (e.g., 0.95).
    Alternative Hypothesis (H1): The true coverage probability is not p0.
    
    Args:
        coverage_rates: Dict of model -> observed coverage proportion.
        p0: Expected coverage probability under H0 (default 0.95 for 95% CI).
        alpha: Significance level for the test (default 0.05).
        
    Returns:
        Dict mapping model name to test results: {
            'observed_coverage': float,
            'n_trials': int,
            'p_value': float,
            'reject_null': bool,
            'significance_level': float
        }
    """
    results = {}
    
    # We need the number of trials (n) to perform the binomial test.
    # Since this function receives rates, we must re-calculate or assume we have access to counts.
    # However, to strictly follow the task of implementing the test in metrics.py,
    # we assume the caller provides rates and we might need to re-iterate or store counts.
    # To make this robust, we will re-calculate the counts based on the logic in calculate_coverage
    # if we had access to the raw data, but here we only have rates.
    # 
    # Correction: The task asks to implement the test. A binomial test requires (k, n).
    # Since `calculate_coverage` returns a rate, we lost 'n'. 
    # We must modify the approach: The function `perform_binomial_coverage_test` should ideally
    # take the raw counts or be called with the data used in `calculate_coverage`.
    # 
    # Given the API surface constraint, I will implement a version that assumes we can
    # re-calculate the "n" if we had the data, OR we accept that we need to pass 'n' as well.
    # But the signature is fixed by the task description context.
    # Let's assume the caller passes the coverage_rates and we need to infer or we must
    # change the return of calculate_coverage to include 'n'.
    # 
    # Better approach for this specific task: Re-implement the counting logic or assume
    # we have the counts. Since I cannot change the signature of `calculate_coverage` 
    # without breaking other tasks, I will implement a helper that re-calculates the 
    # necessary counts if we had the raw forecasts and outcomes, OR I will assume 
    # the `coverage_rates` dict is accompanied by a `counts` dict.
    # 
    # Wait, the task says "Implement binomial test...". It doesn't strictly say the signature.
    # I will implement a function that takes the raw data needed to perform the test
    # to ensure correctness, as passing only the rate makes the test impossible (missing n).
    # 
    # Actually, looking at the previous function `calculate_coverage`, it returns rates.
    # To perform the binomial test, we need the number of trials.
    # I will extend the logic to accept the raw forecasts and outcomes directly, 
    # or return a dictionary with counts from `calculate_coverage`? No, that changes API.
    # 
    # Let's assume the standard pattern: The test function should take the necessary inputs.
    # I will implement `perform_binomial_coverage_test` to accept `forecasts` and `outcomes`
    # directly, calculating the counts internally. This is the most robust implementation.
    # If the caller only has rates, they cannot perform the test.
    # 
    # Revised Plan:
    # 1. Calculate the coverage counts (k) and total trials (n) internally.
    # 2. Perform the binomial test using scipy.stats.binom_test (or binomtest in newer scipy).
    # 3. Return the result.
    
    # Re-calculating counts internally to ensure we have 'n'
    # We need to match the logic in calculate_coverage
    
    for model, preds in forecasts.items():
        k = 0 # successes
        n = 0 # trials
        
        for pred in preds:
            date = pred['date']
            if date in outcomes:
                actual = outcomes[date]
                lower = pred['lower_ci']
                upper = pred['upper_ci']
                n += 1
                if lower <= actual <= upper:
                    k += 1
        
        if n == 0:
            results[model] = {
                'observed_coverage': 0.0,
                'n_trials': 0,
                'p_value': 1.0, # Undefined, but safe
                'reject_null': False,
                'significance_level': alpha,
                'message': 'No trials available'
            }
            continue
        
        observed_rate = k / n
        
        # Perform Binomial Test
        # scipy.stats.binomtest is preferred in newer versions, binom_test is deprecated
        # We handle both to be safe
        try:
            test_result = stats.binomtest(k, n, p0, alternative='two-sided')
            p_value = test_result.pvalue
        except AttributeError:
            # Fallback for older scipy
            p_value = stats.binom_test(k, n, p0, alternative='two-sided')
        
        reject_null = p_value < alpha
        
        results[model] = {
            'observed_coverage': observed_rate,
            'n_trials': n,
            'p_value': p_value,
            'reject_null': reject_null,
            'significance_level': alpha
        }
        
        status = "REJECTED" if reject_null else "NOT REJECTED"
        info(f"Model {model}: Coverage {observed_rate:.4f} (n={n}), "
             f"p-value={p_value:.4f}, H0 (p={p0}) {status} at alpha={alpha}")
    
    return results

def evaluate_frequentist_methods(
    forecasts_file: str, 
    outcomes_file: str
) -> Dict[str, Dict]:
    """
    Evaluate frequentist methods (Simple Avg, Weighted Avg) against outcomes.
    Calculates RMSE, MAE, and performs coverage tests if intervals are available.
    """
    try:
        forecasts = load_forecasts(forecasts_file)
        outcomes = load_outcomes(outcomes_file)
    except FileNotFoundError as e:
        error(str(e))
        return {}
    
    metrics_results = {}
    
    # Calculate RMSE and MAE
    for model, preds in forecasts.items():
        values = [p['value'] for p in preds]
        dates = [p['date'] for p in preds]
        
        actuals = []
        for d in dates:
            if d in outcomes:
                actuals.append(outcomes[d])
            else:
                actuals.append(None)
        
        # Filter out None
        clean_values = []
        clean_actuals = []
        for v, a in zip(values, actuals):
            if a is not None:
                clean_values.append(v)
                clean_actuals.append(a)
        
        if len(clean_values) > 0:
            rmse = calculate_rmse(clean_values, clean_actuals)
            mae = calculate_mae(clean_values, clean_actuals)
            metrics_results[model] = {
                'rmse': rmse,
                'mae': mae,
                'n_evaluated': len(clean_values)
            }
        else:
            metrics_results[model] = {
                'rmse': None,
                'mae': None,
                'n_evaluated': 0,
                'error': 'No matching outcomes'
            }
    
    # Calculate Coverage and Binomial Test
    coverage_rates = calculate_coverage(forecasts, outcomes)
    # Pass the original forecasts and outcomes to the binomial test function
    # to ensure we have the counts (n)
    binomial_results = perform_binomial_coverage_test(forecasts, outcomes, p0=0.95, alpha=0.05)
    
    # Merge coverage results
    for model, rate in coverage_rates.items():
        if model not in metrics_results:
            metrics_results[model] = {}
        metrics_results[model]['coverage_rate'] = rate
        metrics_results[model]['coverage_test'] = binomial_results.get(model)
    
    return metrics_results

def main():
    """Main entry point for running metrics evaluation."""
    # Default paths relative to project root
    forecasts_path = "data/processed/frequentist_forecasts.csv"
    outcomes_path = "data/processed/outcomes.csv" # Assumed path based on T009a
    
    # Check if files exist
    if not os.path.exists(forecasts_path):
        error(f"Forecast file not found at {forecasts_path}")
        sys.exit(1)
    
    if not os.path.exists(outcomes_path):
        error(f"Outcomes file not found at {outcomes_path}")
        sys.exit(1)
    
    info("Starting evaluation of frequentist methods...")
    results = evaluate_frequentist_methods(forecasts_path, outcomes_path)
    
    info("Evaluation Results:")
    for model, metrics in results.items():
        info(f"  Model: {model}")
        if 'rmse' in metrics and metrics['rmse'] is not None:
            info(f"    RMSE: {metrics['rmse']:.4f}")
            info(f"    MAE: {metrics['mae']:.4f}")
        if 'coverage_test' in metrics:
            test = metrics['coverage_test']
            info(f"    Coverage Test (p0=0.95):")
            info(f"      Observed: {test['observed_coverage']:.4f} (n={test['n_trials']})")
            info(f"      P-value: {test['p_value']:.4f}")
            info(f"      Reject H0? {test['reject_null']}")
    
    info("Evaluation complete.")

if __name__ == "__main__":
    main()