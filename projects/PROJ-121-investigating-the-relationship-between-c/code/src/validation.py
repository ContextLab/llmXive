import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import logging
import json

from .stats import compute_correlation_coefficient, monte_carlo_shuffle_test
from .config import DEFAULT_BIN_SIZE_DAYS
from .utils import get_logger

logger = get_logger(__name__)

def generate_synthetic_dataset(
    n_points: int = 100,
    start_date: Optional[datetime] = None,
    true_amplitude: float = 0.05,
    true_phase_days: float = 182.5,
    noise_level: float = 0.02,
    seed: Optional[int] = 42
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a synthetic dataset with a known ground-truth correlation.
    
    The anisotropy signal is modeled as a sinusoid with a specific amplitude and phase,
    correlated with a solar proxy series. Noise is added to simulate real measurements.
    
    Args:
        n_points: Number of data points to generate.
        start_date: Start date for the time series. Defaults to 10 years ago.
        true_amplitude: The known amplitude of the injected signal.
        true_phase_days: The known phase offset in days.
        noise_level: Standard deviation of the Gaussian noise.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (DataFrame, ground_truth_dict)
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=365 * 10)
        
    rng = np.random.default_rng(seed)
    
    # Generate time series
    time_delta_days = np.arange(n_points) * DEFAULT_BIN_SIZE_DAYS
    timestamps = [start_date + timedelta(days=int(d)) for d in time_delta_days]
    
    # Generate solar proxy (e.g., sunspot number) - periodic with some noise
    # Period ~ 11 years (4015 days), but for short synthetic data we use a shorter period for testing
    # or just a trend. Let's use a simple sinusoid for the proxy too to ensure correlation.
    # Proxy period = 11 years for realism, but we'll inject a signal at a specific frequency.
    # For the sake of this test, let's assume the solar proxy drives the anisotropy.
    # We create a proxy that has a strong periodic component.
    proxy_period_days = 365.25 * 11  # 11 year solar cycle
    proxy_signal = np.sin(2 * np.pi * time_delta_days / proxy_period_days)
    proxy_noise = rng.normal(0, 0.1, n_points)
    solar_proxy = proxy_signal + proxy_noise
    
    # Generate anisotropy signal
    # Anisotropy is driven by the solar proxy with a phase shift and amplitude
    # Dipole amplitude A(t) = A0 + A_signal * sin(2*pi*t/Period + phi) + noise
    # We inject a known correlation: Anisotropy = f(SolarProxy) + noise
    # Let's make it a direct linear correlation with a known coefficient for simplicity
    # or a phase-shifted sinusoid. The task asks for "known ground truth correlation".
    # Let's use: Anisotropy = true_amplitude * sin(2*pi*(time - true_phase)/Period) + noise
    # And ensure SolarProxy is correlated with that same sinusoid.
    
    # To ensure a known correlation, we define the anisotropy as a function of the proxy
    # plus noise.
    # Anisotropy = beta * (SolarProxy - mean) + noise
    # But we need a "known amplitude and phase".
    # Let's generate the "true" signal first, then derive proxy from it (or vice versa).
    
    true_signal = true_amplitude * np.sin(2 * np.pi * (time_delta_days - true_phase_days) / 365.25)
    anisotropy = true_signal + rng.normal(0, noise_level, n_points)
    
    # Make solar proxy correlated with the true signal
    # Proxy = alpha * true_signal + noise
    alpha = 1.0
    solar_proxy = alpha * true_signal + rng.normal(0, noise_level * 0.5, n_points)
    
    df = pd.DataFrame({
        'interval_start': timestamps,
        'dipole_amp': anisotropy,
        'solar_proxy': solar_proxy,
        'partial_interval': False
    })
    
    ground_truth = {
        'true_amplitude': true_amplitude,
        'true_phase_days': true_phase_days,
        'noise_level': noise_level,
        'correlation_strength': alpha,
        'n_points': n_points
    }
    
    return df, ground_truth

def save_synthetic_dataset(
    df: pd.DataFrame,
    output_path: str,
    ground_truth: Dict[str, Any],
    gt_path: Optional[str] = None
) -> None:
    """
    Save the synthetic dataset and ground truth metadata to disk.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(path, index=False)
    logger.info(f"Saved synthetic dataset to {path}")
    
    if gt_path:
        gt_file = Path(gt_path)
        gt_file.parent.mkdir(parents=True, exist_ok=True)
        with open(gt_file, 'w') as f:
            json.dump(ground_truth, f, indent=2, default=str)
        logger.info(f"Saved ground truth to {gt_file}")

def run_blind_validation(
    input_path: str,
    ground_truth_path: str,
    output_metrics_path: str,
    n_permutations: int = 1000,
    significance_level: float = 0.05
) -> Dict[str, float]:
    """
    Perform blind validation using the synthetic dataset.
    
    This function loads the synthetic data (generated with known ground truth),
    runs the correlation analysis as if it were real data (blind), and compares
    the results against the ground truth to calculate False Positive Rate (fp_rate)
    and Power.
    
    Since we have ONE synthetic dataset with a KNOWN signal injected:
    1. We run the correlation test.
    2. If the test detects significance (p < alpha), it's a "True Positive" (Power).
    3. If the test does NOT detect significance, it's a "False Negative" (1 - Power).
    
    To calculate fp_rate, we would ideally need a dataset with NO signal.
    However, the task implies validating the system's ability to detect the injected signal.
    In a strict "blind validation" context for a single run:
    - Power = 1 if detected, 0 if not.
    - fp_rate is technically not calculable from a single positive dataset.
    
    However, to satisfy the requirement of writing 'fp_rate', we interpret this as:
    - We run the Monte Carlo shuffle. If the null hypothesis (no correlation) is rejected,
      we count it as a detection.
    - If the ground truth says there IS a correlation, and we detect it -> Power = 1.
    - If the ground truth says there IS a correlation, and we DON'T detect it -> Power = 0.
    
    To estimate fp_rate, we might need to run the test on the *same* data but assume
    the null is true? No, that's not right.
    
    Let's re-read FR-011: "verify FR-011 requirements".
    Usually, validation involves:
    1. Positive Control (Signal injected): Measure Power (Sensitivity).
    2. Negative Control (No signal injected): Measure False Positive Rate (Specificity).
    
    T027 generated a dataset with "known ground truth correlation".
    If we only have ONE dataset with signal, we can only measure Power.
    If the task implies we should generate a dataset with NO signal as well, that would be T027's scope.
    Given T027 says "known ground truth correlation", it implies a positive case.
    
    How to report fp_rate?
    Perhaps the "blind validation" implies running the test many times on the synthetic data
    with different seeds? Or maybe the "synthetic dataset" contains multiple realizations?
    Or, we assume the standard definition:
    - Power: Probability of rejecting H0 when H1 is true.
    - fp_rate: Probability of rejecting H0 when H0 is true.
    
    If we only have H1 data, we can only estimate Power.
    However, to provide a value for fp_rate as requested, we can:
    1. Assume the system is calibrated (fp_rate ~ significance_level) if not tested.
    2. OR, generate a negative control dataset on the fly if the input is only positive?
    
    Let's look at the task again: "Implement blind validation... using the synthetic dataset generated in T027".
    T027 generates "a simulated dataset with a known ground truth correlation".
    This is a single positive case (or a set of them).
    
    If the dataset has a signal, and we detect it -> Power = 1.
    If we don't -> Power = 0.
    
    What about fp_rate?
    If the task strictly requires `fp_rate` in the output, and we only have positive data,
    we might need to generate a "null" dataset internally to measure the false positive rate,
    or report the theoretical alpha as the expected fp_rate if we assume the test is valid.
    
    However, a more robust interpretation for a "blind validation" script is:
    The script should run the analysis.
    If the input data has a signal:
       - If detected: Power contribution = 1
       - If not: Power contribution = 0
       - fp_rate contribution = 0 (because H1 is true, we can't measure FP here)
    
    If the input data has NO signal (which T027 didn't explicitly say it generates, but maybe we should):
       - If detected: FP contribution = 1
       - If not: FP contribution = 0
    
    Since T027 explicitly says "known ground truth correlation", we assume H1 is true.
    To get an fp_rate, we might need to run the test on a shuffled version of the data (which T027's data doesn't have a signal for? No, it does).
    
    Let's assume the "blind validation" involves running the Monte Carlo test.
    The Monte Carlo test itself estimates the p-value.
    
    Strategy:
    1. Load the synthetic data (which has a signal).
    2. Run the correlation test (Monte Carlo shuffle).
    3. Determine if significant.
    4. Calculate Power: 1.0 if significant, 0.0 otherwise.
    5. Calculate fp_rate: Since we don't have a negative control dataset, we cannot empirically measure fp_rate from this single file.
       However, to satisfy the output format, we can run a quick "negative control" simulation internally:
       Generate a small synthetic dataset with NO signal (amplitude=0) and run the test on it.
       If it detects significance, that's a false positive.
       We can do this with a few permutations or a small sample to estimate the fp_rate.
       
       Alternatively, if the "synthetic dataset" from T027 is a *collection* of datasets (some with signal, some without), we would iterate.
       But T027 says "a simulated dataset".
       
       Let's implement a hybrid approach:
       - Use the provided positive dataset to calculate Power.
       - Generate a small "null" dataset internally (amplitude=0) to estimate fp_rate.
       - Run the test on the null dataset. If significant -> FP.
       - Repeat null test N times to estimate fp_rate.
       
       This ensures we output real metrics based on running the code, not just hardcoded values.

    """
    logger.info(f"Loading synthetic dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Convert interval_start to datetime if string
    if df['interval_start'].dtype == 'object':
        df['interval_start'] = pd.to_datetime(df['interval_start'])
    
    # Load ground truth
    with open(ground_truth_path, 'r') as f:
        ground_truth = json.load(f)
    
    has_signal = ground_truth.get('true_amplitude', 0) > 0
    
    # --- Calculate Power (using the provided positive dataset) ---
    # Run Monte Carlo shuffle test
    # We need two series: anisotropy and solar_proxy
    y_aniso = df['dipole_amp'].values
    x_proxy = df['solar_proxy'].values
    
    # Run the test
    # monte_carlo_shuffle_test returns a dict with p_value and is_significant
    try:
        mc_result = monte_carlo_shuffle_test(
            x_proxy, y_aniso,
            n_permutations=n_permutations,
            alpha=significance_level
        )
        
        detected = mc_result['is_significant']
        
        power = 1.0 if detected else 0.0
    except Exception as e:
        logger.error(f"Error running Monte Carlo test on positive data: {e}")
        power = 0.0
        detected = False
    
    # --- Calculate False Positive Rate (using internal negative control) ---
    # We generate a small dataset with NO signal to estimate fp_rate
    # We run the test multiple times on random noise to see how often we reject H0
    n_fp_trials = 50  # Number of trials to estimate fp_rate
    fp_count = 0
    
    rng = np.random.default_rng(12345) # Fixed seed for reproducibility of the validation metric
    for i in range(n_fp_trials):
        # Generate noise-only data
        n_points = len(df)
        x_null = rng.normal(0, 1, n_points)
        y_null = rng.normal(0, 1, n_points)
        
        # Run test
        try:
            mc_null = monte_carlo_shuffle_test(
                x_null, y_null,
                n_permutations=100, # Fewer perms for speed in validation
                alpha=significance_level
            )
            if mc_null['is_significant']:
                fp_count += 1
        except Exception:
            pass
    
    fp_rate = fp_count / n_fp_trials
    
    metrics = {
        'fp_rate': float(fp_rate),
        'power': float(power),
        'n_permutations': n_permutations,
        'detected_in_positive': detected,
        'ground_truth_amplitude': ground_truth.get('true_amplitude'),
        'n_fp_trials': n_fp_trials
    }
    
    # Write metrics
    out_path = Path(output_metrics_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Validation metrics written to {out_path}")
    logger.info(f"FP Rate: {fp_rate:.4f}, Power: {power:.4f}")
    
    return metrics

def main():
    """
    Entry point for the blind validation script.
    Expects:
      --input data/synthetic/validation_input.csv
      --ground-truth data/synthetic/gt_metadata.json
      --output data/results/validation_metrics.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run blind validation on synthetic data")
    parser.add_argument("--input", type=str, required=True, help="Path to synthetic input CSV")
    parser.add_argument("--ground-truth", type=str, required=True, help="Path to ground truth JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output metrics JSON")
    parser.add_argument("--n-permutations", type=int, default=1000, help="Number of Monte Carlo permutations")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    run_blind_validation(
        input_path=args.input,
        ground_truth_path=args.ground_truth,
        output_metrics_path=args.output,
        n_permutations=args.n_permutations,
        significance_level=args.alpha
    )

if __name__ == "__main__":
    main()
