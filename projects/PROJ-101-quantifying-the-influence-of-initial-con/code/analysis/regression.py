import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Project local imports
from ..config import get_full_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Data Classes / Results
# --------------------------------------------------------------------------

class RegressionResult:
    """Container for regression analysis results."""
    def __init__(self, 
                 model_summary: str, 
                 coefficients: Dict[str, float],
                 p_values: Dict[str, float],
                 r_squared: float,
                 aic: float,
                 bic: float,
                 scaling_exponent: Optional[float] = None,
                 scaling_exponent_p_value: Optional[float] = None,
                 scaling_model_stats: Optional[Dict[str, Any]] = None):
        self.model_summary = model_summary
        self.coefficients = coefficients
        self.p_values = p_values
        self.r_squared = r_squared
        self.aic = aic
        self.bic = bic
        self.scaling_exponent = scaling_exponent
        self.scaling_exponent_p_value = scaling_exponent_p_value
        self.scaling_model_stats = scaling_model_stats or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_summary": self.model_summary,
            "coefficients": self.coefficients,
            "p_values": self.p_values,
            "r_squared": self.r_squared,
            "aic": self.aic,
            "bic": self.bic,
            "scaling_exponent": self.scaling_exponent,
            "scaling_exponent_p_value": self.scaling_exponent_p_value,
            "scaling_model_stats": self.scaling_model_stats,
        }

class TrialValidationReport:
    def __init__(self, valid: bool, message: str, counts: Dict[str, int]):
        self.valid = valid
        self.message = message
        self.counts = counts

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def load_ftle_sweep_results() -> List[Dict[str, Any]]:
    """Loads the FTLE sweep results from the processed data directory."""
    config = get_full_config()
    path = Path(config.analysis.output_dir) / "ftle_sweep.json"
    if not path.exists():
        raise FileNotFoundError(f"FTLE sweep results not found at {path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Normalise to a list of dicts
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data

def load_baseline_results() -> Dict[int, float]:
    """
    Loads asymptotic baseline ``lambda_max`` for each N configuration.
    Returns a dict mapping N (int) -> lambda_max (float).
    """
    config = get_full_config()
    baseline_dir = Path(config.analysis.output_dir)
    baselines = {}

    for f in baseline_dir.glob("baseline_*.json"):
        try:
            with open(f, 'r') as file:
                content = json.load(file)
                n_str = f.stem.replace("baseline_", "")
                if n_str.isdigit() and "lambda_max" in content:
                    baselines[int(n_str)] = float(content["lambda_max"])
                    logger.info(f"Loaded baseline for N={n_str}: {content['lambda_max']}")
        except Exception as e:
            logger.warning(f"Could not load baseline file {f}: {e}")

    return baselines

def validate_trial_counts(required_counts: Dict[float, int]) -> TrialValidationReport:
    """Validates that the required number of trials exist for each noise level."""
    sweep_data = load_ftle_sweep_results()
    counts = {}
    for row in sweep_data:
        sigma = row.get("sigma")
        if sigma is not None:
            counts[sigma] = counts.get(sigma, 0) + 1

    valid = True
    messages = []
    for sigma, req in required_counts.items():
        actual = counts.get(sigma, 0)
        if actual < req:
            valid = False
            messages.append(f"Missing trials for sigma={sigma}: need {req}, have {actual}")

    if valid:
        return TrialValidationReport(True, "All trial counts met.", counts)
    return TrialValidationReport(False, "; ".join(messages), counts)

def compute_deviations(ftle_data: List[Dict[str, Any]], 
                       baselines: Dict[int, float]) -> List[Dict[str, Any]]:
    """
    Computes the deviation Δλ = λ_FTLE – λ_baseline for each entry.
    """
    results = []
    for row in ftle_data:
        n = row.get("N")
        sigma = row.get("sigma")
        t_window = row.get("T")
        lambda_ftle = row.get("lambda_ftle")
        trial_id = row.get("trial_id")

        if n not in baselines:
            logger.warning(f"Skipping row N={n}: no baseline found.")
            continue

        lambda_base = baselines[n]
        deviation = lambda_ftle - lambda_base

        results.append({
            "trial_id": trial_id,
            "N": n,
            "sigma": sigma,
            "T": t_window,
            "lambda_ftle": lambda_ftle,
            "lambda_baseline": lambda_base,
            "deviation": deviation,
        })
    return results

def run_ttest_bias(deviations: List[float], baseline_val: float = 0.0) -> Dict[str, float]:
    """One‑sample t‑test that the mean deviation differs from ``baseline_val``."""
    if not deviations:
        return {"p_value": 1.0, "statistic": 0.0, "effect_size": 0.0}

    arr = np.array(deviations)
    stat, p_val = stats.ttest_1samp(arr, baseline_val)

    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    d = mean / std if std > 0 else 0.0

    return {
        "p_value": float(p_val),
        "statistic": float(stat),
        "effect_size": float(d),
    }

def select_best_model(deviations_df: "pd.DataFrame") -> Dict[str, Any]:
    """
    Selects the best functional form for deviation scaling using AIC/BIC.
    Models considered: linear, log‑linear, power‑law.
    """
    # Import pandas lazily – this avoids import‑time failures if pandas is not installed.
    import pandas as pd

    candidates = []

    # Linear model: deviation ~ sigma
    try:
        model_lin = ols('deviation ~ sigma', data=deviations_df).fit()
        candidates.append(("linear", model_lin, model_lin.aic, model_lin.bic))
    except Exception as e:
        logger.warning(f"Linear model failed: {e}")

    # Log‑linear model: deviation ~ log(sigma)
    try:
        df_log = deviations_df.copy()
        df_log['log_sigma'] = np.log(df_log['sigma'].replace(0, np.nan))
        df_log = df_log.dropna(subset=['log_sigma'])
        if not df_log.empty:
            model_log = ols('deviation ~ log_sigma', data=df_log).fit()
            candidates.append(("log_linear", model_log, model_log.aic, model_log.bic))
    except Exception as e:
        logger.warning(f"Log‑Linear model failed: {e}")

    # Power‑law model: log(deviation) ~ log(sigma)
    try:
        df_pow = deviations_df.copy()
        df_pow = df_pow[df_pow['deviation'] > 0]
        if not df_pow.empty:
            df_pow['log_dev'] = np.log(df_pow['deviation'])
            df_pow['log_sig'] = np.log(df_pow['sigma'])
            model_pow = ols('log_dev ~ log_sig', data=df_pow).fit()
            candidates.append(("power_law", model_pow, model_pow.aic, model_pow.bic))
    except Exception as e:
        logger.warning(f"Power Law model failed: {e}")

    if not candidates:
        raise RuntimeError("No valid regression models could be fitted.")

    # Choose model with lowest AIC
    candidates.sort(key=lambda x: x[2])
    best_name, best_model, best_aic, best_bic = candidates[0]

    return {
        "best_model_name": best_name,
        "model": best_model,
        "aic": best_aic,
        "bic": best_bic,
        "summary": best_model.summary().as_csv(),
    }

def calculate_scaling_exponent(deviations_df: "pd.DataFrame") -> Tuple[Optional[float], Optional[float], Dict[str, Any]]:
    """
    Calculates the scaling exponent relating system dimension (N) to bias magnitude.
    """
    import pandas as pd  # lazy import

    if deviations_df.empty:
        logger.warning("Cannot calculate scaling exponent: empty dataframe.")
        return None, None, {}

    if 'N' not in deviations_df.columns or 'deviation' not in deviations_df.columns:
        logger.error("Missing required columns 'N' or 'deviation' for scaling analysis.")
        return None, None, {}

    grouped = deviations_df.groupby('N')['deviation'].mean().reset_index()
    grouped['bias_magnitude'] = grouped['deviation'].abs()
    valid_rows = grouped[grouped['bias_magnitude'] > 0]

    if len(valid_rows) < 2:
        logger.warning("Insufficient N values to fit a scaling law.")
        return None, None, {}

    X = np.log(valid_rows['N'].values)
    y = np.log(valid_rows['bias_magnitude'].values)

    slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)

    exponent = slope
    stats_dict = {
        "r_squared": float(r_value ** 2),
        "p_value": float(p_value),
        "std_error": float(std_err),
        "n_points": len(valid_rows),
        "method": "linear_regression_on_log_transformed_data",
    }

    logger.info(f"Calculated scaling exponent (alpha): {exponent:.4f} (p={p_value:.4f})")
    return exponent, p_value, stats_dict

def generate_deviation_plot(results: List[Dict[str, Any]], output_path: Path):
    """Creates Δλ vs. σ plot with error bars."""
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.DataFrame(results)

    plt.figure(figsize=(10, 6))
    for n_val in df['N'].unique():
        subset = df[df['N'] == n_val]
        grouped = subset.groupby('sigma')['deviation'].agg(['mean', 'std', 'count']).reset_index()
        grouped['se'] = grouped['std'] / np.sqrt(grouped['count'])
        plt.errorbar(grouped['sigma'], grouped['mean'], yerr=grouped['se'],
                     label=f'N={n_val}', capsize=5, marker='o')

    plt.xlabel('Noise Level (sigma)')
    plt.ylabel('Deviation (Δλ)')
    plt.title('Deviation of FTLE from Baseline vs Noise Level')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved deviation plot to {output_path}")

def generate_convergence_plot(results: List[Dict[str, Any]], output_path: Path):
    """Creates FTLE vs. window‑size plot for three representative noise levels."""
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.DataFrame(results)

    sigmas = df['sigma'].unique()
    if len(sigmas) < 3:
        logger.warning(f"Only {len(sigmas)} noise levels found; need ≥3 for convergence plot.")
        return

    selected = sigmas[:3]

    plt.figure(figsize=(10, 6))
    for sigma in selected:
        subset = df[df['sigma'] == sigma]
        grouped = subset.groupby('T')['lambda_ftle'].mean().reset_index()
        plt.plot(grouped['T'], grouped['lambda_ftle'], label=f'sigma={sigma}', marker='o')

    plt.xlabel('Window Size (T)')
    plt.ylabel('FTLE (λ)')
    plt.title('FTLE Convergence over Window Size')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved convergence plot to {output_path}")

def run_full_regression_analysis() -> RegressionResult:
    """
    Orchestrates the full regression pipeline and writes artefacts.
    """
    logger.info("Starting full regression analysis...")

    ftle_data = load_ftle_sweep_results()
    baselines = load_baseline_results()

    if not ftle_data:
        raise ValueError("No FTLE data found to analyse.")
    if not baselines:
        raise ValueError("No baseline data found to compute deviations.")

    deviations_data = compute_deviations(ftle_data, baselines)
    if not deviations_data:
        raise ValueError("Could not compute deviations – mismatch in N values?")

    df_dev = pd.DataFrame(deviations_data)

    # 1‑sample t‑test on all deviations
    all_devs = df_dev['deviation'].tolist()
    ttest_res = run_ttest_bias(all_devs)

    # Model selection
    model_info = select_best_model(df_dev)

    # Scaling exponent (N vs bias)
    scaling_exponent, scaling_p, scaling_stats = calculate_scaling_exponent(df_dev)

    result = RegressionResult(
        model_summary=model_info["summary"],
        coefficients=model_info["model"].params.to_dict(),
        p_values={k: float(v) for k, v in model_info["model"].pvalues.to_dict().items()},
        r_squared=float(model_info["model"].rsquared),
        aic=float(model_info["aic"]),
        bic=float(model_info["bic"]),
        scaling_exponent=scaling_exponent,
        scaling_exponent_p_value=scaling_p,
        scaling_model_stats=scaling_stats,
    )

    # Save visualisations and final JSON
    cfg = get_full_config()
    out_dir = Path(cfg.analysis.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generate_deviation_plot(deviations_data, out_dir / "plot_deviation_vs_noise.png")
    generate_convergence_plot(ftle_data, out_dir / "plot_convergence.png")

    results_path = out_dir / "results.json"
    with open(results_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    logger.info(f"Regression analysis complete. Results saved to {results_path}")
    return result

def main():
    """CLI entry‑point for the regression step."""
    try:
        res = run_full_regression_analysis()
        print(json.dumps(res.to_dict(), indent=2))
    except Exception as e:
        logger.error(f"Regression failed: {e}", exc_info=True)
        sys.exit(1)
