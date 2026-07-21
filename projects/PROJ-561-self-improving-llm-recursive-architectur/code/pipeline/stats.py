import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy.optimize import curve_fit
from scipy.stats import t
import json
import os

from config import PathConfig

def exponential_decay(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
  """
  Exponential decay model: y = a * exp(-b * x) + c
  
  Parameters:
      x: Independent variable (e.g., cycle number)
      a: Initial amplitude (difference between start and asymptote)
      b: Decay rate
      c: Asymptotic value (plateau)
      
  Returns:
      y: Modeled values
  """
  return a * np.exp(-b * x) + c


def fit_exponential_decay(
    cycle_numbers: List[int], 
    metric_values: List[float]
) -> Dict[str, Any]:
  """
  Fit an exponential decay model to performance metrics across cycles.
  
  Parameters:
      cycle_numbers: List of cycle indices (x-axis)
      metric_values: List of metric values (y-axis)
      
  Returns:
      Dictionary containing:
          - fitted_params: dict with keys 'a', 'b', 'c'
          - r_squared: coefficient of determination
          - plateau_cycle: cycle index where plateau is detected (or None)
          - success: boolean indicating if fit succeeded
          - message: description of result
  """
  if len(cycle_numbers) < 3:
      return {
          "fitted_params": None,
          "r_squared": None,
          "plateau_cycle": None,
          "success": False,
          "message": "Insufficient data points (need at least 3) for exponential decay fit."
      }

  x_data = np.array(cycle_numbers, dtype=float)
  y_data = np.array(metric_values, dtype=float)

  # Initial guesses: a = y0 - y_last, b = 0.1, c = y_last
  try:
      p0 = [y_data[0] - y_data[-1], 0.1, y_data[-1]]
      
      # Ensure bounds prevent physical impossibilities (b > 0)
      p_bounds = (
          [-np.inf, 0.0, -np.inf],  # Lower bounds
          [np.inf, np.inf, np.inf]   # Upper bounds
      )

      popt, pcov = curve_fit(
          exponential_decay, 
          x_data, 
          y_data, 
          p0=p0, 
          bounds=p_bounds,
          maxfev=5000
      )
      
      a, b, c = popt
      
      # Calculate R-squared
      y_pred = exponential_decay(x_data, *popt)
      ss_res = np.sum((y_data - y_pred) ** 2)
      ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
      r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
      
      # Detect plateau: where derivative is effectively zero
      # derivative = -a * b * exp(-b * x)
      # We look for the first cycle where the absolute change < 0.1% of initial range
      plateau_cycle = None
      if a != 0 and b != 0:
          initial_range = abs(a)
          threshold = 0.001 * initial_range
          for i, x_val in enumerate(x_data):
              deriv = abs(-a * b * np.exp(-b * x_val))
              if deriv < threshold:
                  plateau_cycle = int(x_val)
                  break
      
      return {
          "fitted_params": {"a": float(a), "b": float(b), "c": float(c)},
          "r_squared": float(r_squared),
          "plateau_cycle": plateau_cycle,
          "success": True,
          "message": f"Fit successful. R²={r_squared:.4f}, Plateau detected at cycle {plateau_cycle}."
      }
      
  except Exception as e:
      return {
          "fitted_params": None,
          "r_squared": None,
          "plateau_cycle": None,
          "success": False,
          "message": f"Fit failed: {str(e)}"
      }


def detect_plateau_or_degradation(
    metrics_history: List[Dict[str, Any]], 
    metric_key: str = "gsm8k_accuracy"
) -> Dict[str, Any]:
  """
  Analyze metric history to detect plateau or degradation cycles.
  
  Parameters:
      metrics_history: List of trajectory entries (dicts) containing cycle data
      metric_key: Key in the entry to analyze (e.g., "gsm8k_accuracy", "arc_accuracy")
      
  Returns:
      Dictionary containing:
          - plateau_cycle: First cycle identified as plateau (or None)
          - degradation_cycle: First cycle identified as degradation (or None)
          - trend: "improving", "plateau", "degrading", or "mixed"
          - analysis_summary: Human-readable summary
  """
  if len(metrics_history) < 2:
      return {
          "plateau_cycle": None,
          "degradation_cycle": None,
          "trend": "insufficient_data",
          "analysis_summary": "Not enough cycles to determine trend."
      }

  cycles = []
  values = []
  for entry in metrics_history:
      cycles.append(entry.get("cycle_number"))
      val = entry.get(metric_key)
      if val is None:
          val = 0.0 # Handle missing gracefully
      values.append(val)

  # Detect degradation: any drop > 1% from previous
  degradation_cycle = None
  for i in range(1, len(values)):
      if values[i] < values[i-1] * 0.99: # 1% drop threshold
          degradation_cycle = cycles[i]
          break

  # Detect plateau using derivative analysis on raw data
  # Simple heuristic: if last 3 changes are < 0.5% of mean
  plateau_cycle = None
  if len(values) >= 3:
      recent_changes = []
      for i in range(len(values)-3, len(values)):
          if i > 0:
              change = abs(values[i] - values[i-1])
              recent_changes.append(change)
      
      if recent_changes:
          mean_val = np.mean(values)
          threshold = 0.005 * mean_val # 0.5%
          if all(c < threshold for c in recent_changes):
              plateau_cycle = cycles[-1]

  # Determine trend
  if degradation_cycle is not None:
      trend = "degrading"
  elif plateau_cycle is not None:
      trend = "plateau"
  elif values[-1] > values[0]:
      trend = "improving"
  else:
      trend = "mixed"

  summary = f"Trend: {trend}. "
  if degradation_cycle:
      summary += f"Degradation detected at cycle {degradation_cycle}. "
  if plateau_cycle:
      summary += f"Plateau detected at cycle {plateau_cycle}. "

  return {
      "plateau_cycle": plateau_cycle,
      "degradation_cycle": degradation_cycle,
      "trend": trend,
      "analysis_summary": summary
  }


def save_decay_fit_results(
    fit_result: Dict[str, Any], 
    cycle_numbers: List[int], 
    metric_values: List[float],
    metric_name: str = "gsm8k_accuracy"
) -> str:
  """
  Save exponential decay fit results to a JSON file in the results directory.
  
  Parameters:
      fit_result: Dictionary from fit_exponential_decay()
      cycle_numbers: List of cycle numbers used
      metric_values: List of metric values used
      metric_name: Name of the metric for the filename
      
  Returns:
      Path to the saved JSON file
  """
  config = PathConfig()
  output_path = os.path.join(config.results_dir, f"decay_fit_{metric_name}.json")
  
  data_to_save = {
      "metric_name": metric_name,
      "cycle_numbers": cycle_numbers,
      "metric_values": metric_values,
      "fit_results": fit_result,
      "timestamp": "auto-generated" # In real usage, use datetime.now().isoformat()
  }
  
  with open(output_path, 'w') as f:
      json.dump(data_to_save, f, indent=2)
      
  return output_path


def save_bootstrap_results(
    p_values: Dict[str, float], 
    baseline_mean: float, 
    modified_mean: float,
    comparison_name: str = "baseline_vs_modified"
) -> str:
  """
  Save bootstrap comparison results to a JSON file.
  
  Parameters:
      p_values: Dictionary mapping metric names to p-values
      baseline_mean: Mean of baseline metric
      modified_mean: Mean of modified metric
      comparison_name: Identifier for this comparison
      
  Returns:
      Path to the saved JSON file
  """
  config = PathConfig()
  output_path = os.path.join(config.results_dir, f"bootstrap_{comparison_name}.json")
  
  data_to_save = {
      "comparison_name": comparison_name,
      "baseline_mean": baseline_mean,
      "modified_mean": modified_mean,
      "p_values": p_values,
      "significance_threshold": 0.05
  }
  
  with open(output_path, 'w') as f:
      json.dump(data_to_save, f, indent=2)
      
  return output_path


def paired_bootstrap_test(
    baseline_values: List[float], 
    modified_values: List[float], 
    n_iterations: int = 1000,
    alpha: float = 0.05
) -> Dict[str, Any]:
  """
  Perform a paired bootstrap test to compare two sets of metric values.
  
  Parameters:
      baseline_values: List of metric values from baseline
      modified_values: List of metric values from modified model
      n_iterations: Number of bootstrap iterations
      alpha: Significance level
      
  Returns:
      Dictionary containing:
          - p_value: Two-tailed p-value
          - significant: Boolean indicating if difference is significant
          - mean_diff: Mean of (modified - baseline)
          - ci_lower: Lower bound of 95% CI
          - ci_upper: Upper bound of 95% CI
  """
  if len(baseline_values) != len(modified_values):
      raise ValueError("Baseline and modified value lists must have equal length.")
  if len(baseline_values) == 0:
      raise ValueError("Value lists cannot be empty.")

  baseline_arr = np.array(baseline_values)
  modified_arr = np.array(modified_values)
  
  # Calculate observed mean difference
  observed_diff = np.mean(modified_arr - baseline_arr)
  
  # Bootstrap resampling
  boot_diffs = []
  n = len(baseline_arr)
  for _ in range(n_iterations):
      # Resample with replacement
      idx = np.random.choice(n, size=n, replace=True)
      boot_baseline = baseline_arr[idx]
      boot_modified = modified_arr[idx]
      boot_diffs.append(np.mean(boot_modified - boot_baseline))
      
  boot_diffs = np.array(boot_diffs)
  
  # Calculate p-value (two-tailed)
  # Proportion of bootstrapped diffs that are as or more extreme than observed
  # under the null hypothesis that the true difference is 0.
  # We shift the bootstrap distribution to be centered at 0 for the null test
  boot_diffs_centered = boot_diffs - np.mean(boot_diffs)
  
  # Two-tailed p-value
  extreme_count = np.sum(np.abs(boot_diffs_centered) >= np.abs(observed_diff))
  p_value = extreme_count / n_iterations
  
  # Confidence interval
  ci_lower = np.percentile(boot_diffs, 2.5)
  ci_upper = np.percentile(boot_diffs, 97.5)
  
  return {
      "p_value": float(p_value),
      "significant": p_value < alpha,
      "mean_diff": float(observed_diff),
      "ci_lower": float(ci_lower),
      "ci_upper": float(ci_upper)
  }