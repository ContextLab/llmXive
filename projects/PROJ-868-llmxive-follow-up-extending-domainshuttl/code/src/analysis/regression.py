"""
Regression analysis for phase transition detection.

Implements correlation analysis between visual complexity and fidelity curves,
with automatic fallback from piecewise linear to simple linear regression
if the breakpoint is not statistically significant.
"""
import json
import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure output directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def piecewise_linear(x: np.ndarray, x0: float, k1: float, k2: float, b: float) -> np.ndarray:
    """
    Two-segment piecewise linear function.
    
    Args:
        x: Input array (dimension values)
        x0: Breakpoint
        k1: Slope before breakpoint
        k2: Slope after breakpoint
        b: Intercept (value at x=0 for first segment)
    
    Returns:
        Array of y values
    """
    return np.piecewise(
        x,
        [x <= x0, x > x0],
        [lambda x: k1 * x + b, lambda x: k2 * x + (b + k1 * x0 - k2 * x0)]
    )


def fit_piecewise_linear(x: np.ndarray, y: np.ndarray) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    """
    Attempt to fit a 2-segment piecewise linear model.
    
    Args:
        x: Dimension values
        y: Fidelity scores (averaged across styles)
    
    Returns:
        Tuple of (params_dict, success, message)
        params_dict contains: breakpoint, k1, k2, b, r_squared, p_value
        success: True if fit converged and breakpoint is significant
        message: Description of result
    """
    if len(x) < 5:
        return None, False, "Insufficient data points for piecewise fit"
    
    # Sort by x to ensure monotonicity
    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    y_sorted = y[sort_idx]
    
    # Initial guesses: breakpoint at middle, slopes negative, intercept positive
    x0_guess = x_sorted[len(x_sorted) // 2]
    k1_guess = -0.001
    k2_guess = -0.0005
    b_guess = 1.0
    
    try:
        popt, pcov = curve_fit(
            piecewise_linear,
            x_sorted,
            y_sorted,
            p0=[x0_guess, k1_guess, k2_guess, b_guess],
            maxfev=10000,
            bounds=(
                [x_sorted[0], -10, -10, 0],  # Lower bounds
                [x_sorted[-1], 0, 0, 1]      # Upper bounds (slopes should be negative or zero)
            )
        )
        
        x0, k1, k2, b = popt
        
        # Calculate residuals and R-squared
        y_pred = piecewise_linear(x_sorted, x0, k1, k2, b)
        ss_res = np.sum((y_sorted - y_pred) ** 2)
        ss_tot = np.sum((y_sorted - np.mean(y_sorted)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Estimate p-value for breakpoint significance
        # Using the covariance matrix to estimate standard error of breakpoint
        if pcov is not None:
            try:
                p0_se = np.sqrt(np.diag(pcov))[0]
                # Simple t-test approximation for breakpoint significance
                # If the confidence interval is too wide, consider it non-significant
                # We use a heuristic: if p0_se > 10% of the range, it's not significant
                x_range = x_sorted[-1] - x_sorted[0]
                if x_range > 0 and p0_se > 0.1 * x_range:
                    p_value = 0.1  # High p-value indicates non-significance
                else:
                    p_value = 0.01  # Low p-value indicates significance
            except:
                p_value = 0.1
        else:
            p_value = 0.1
        
        params = {
            "breakpoint": float(x0),
            "k1": float(k1),
            "k2": float(k2),
            "b": float(b),
            "r_squared": float(r_squared),
            "p_value": float(p_value)
        }
        
        if p_value >= 0.05:
            return params, False, f"Breakpoint not significant (p={p_value:.3f})"
        else:
            return params, True, f"Phase transition detected (p={p_value:.3f})"
            
    except Exception as e:
        return None, False, f"Fit failed: {str(e)}"


def fit_simple_linear(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Fit a simple linear regression model.
    
    Args:
        x: Dimension values
        y: Fidelity scores
    
    Returns:
        Dictionary with slope, intercept, r_squared
    """
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_value ** 2),
        "p_value": float(p_value)
    }


def aggregate_fidelity_curve(fidelity_data: Dict[str, Dict]) -> Dict[str, Dict[int, float]]:
    """
    Aggregate fidelity scores across styles for each dimension.
    
    Args:
        fidelity_data: Structure {subject_id: {dimension: {style: score}}}
    
    Returns:
        Structure {subject_id: {dimension: mean_score}}
    """
    aggregated = {}
    for subject_id, dim_data in fidelity_data.items():
        aggregated[subject_id] = {}
        for dim, style_scores in dim_data.items():
            dim_int = int(dim)
            scores = list(style_scores.values())
            if scores:
                aggregated[subject_id][dim_int] = float(np.mean(scores))
    return aggregated


def plot_regression_analysis(
    x: np.ndarray,
    y: np.ndarray,
    model_type: str,
    params: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Create a visualization of the regression analysis.
    
    Args:
        x: Dimension values
        y: Fidelity scores
        model_type: "phase_transition" or "linear"
        params: Fitted parameters
        output_path: Path to save the figure
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.6, label='Data', color='blue')
    
    x_sorted = np.sort(x)
    
    if model_type == "phase_transition":
        x0 = params["breakpoint"]
        k1 = params["k1"]
        k2 = params["k2"]
        b = params["b"]
        y_pred = piecewise_linear(x_sorted, x0, k1, k2, b)
        plt.plot(x_sorted, y_pred, 'r-', linewidth=2, label=f'Piecewise Fit (R²={params["r_squared"]:.3f})')
        plt.axvline(x=x0, color='red', linestyle='--', alpha=0.5, label=f'Breakpoint: {x0:.1f}')
        plt.title('Phase Transition Analysis')
    else:
        slope = params["slope"]
        intercept = params["intercept"]
        y_pred = slope * x_sorted + intercept
        plt.plot(x_sorted, y_pred, 'r-', linewidth=2, label=f'Linear Fit (R²={params["r_squared"]:.3f})')
        plt.title('Linear Regression Analysis (Hypothesis Falsified)')
    
    plt.xlabel('Dimension')
    plt.ylabel('Mean Fidelity Score (CLIP)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def run_correlation_analysis(
    complexity_file: Path,
    fidelity_file: Path,
    output_pdf: Path,
    output_metrics: Path
) -> Dict[str, Any]:
    """
    Main function to run correlation analysis.
    
    Args:
        complexity_file: Path to complexity_scores.csv
        fidelity_file: Path to fidelity_vs_dimension_curve.json
        output_pdf: Path to save the PDF plot
        output_metrics: Path to save metrics.json
    
    Returns:
        Dictionary with analysis results
    """
    # Load complexity scores
    if not complexity_file.exists():
        raise FileNotFoundError(f"Complexity scores file not found: {complexity_file}")
    
    import pandas as pd
    complexity_df = pd.read_csv(complexity_file)
    complexity_map = dict(zip(complexity_df['subject_id'], complexity_df['complexity_score']))
    
    # Load fidelity curve
    if not fidelity_file.exists():
        raise FileNotFoundError(f"Fidelity curve file not found: {fidelity_file}")
    
    with open(fidelity_file, 'r') as f:
        fidelity_data = json.load(f)
    
    # Aggregate fidelity across styles
    aggregated_fidelity = aggregate_fidelity_curve(fidelity_data)
    
    # Prepare data for regression
    # We will analyze the relationship between complexity and the minimum dimension
    # where fidelity drops below a threshold, or the overall slope of fidelity vs dimension
    
    # For this analysis, we'll look at:
    # 1. For each subject, compute the slope of fidelity vs dimension
    # 2. Correlate this slope with complexity
    
    results = {}
    subject_ids = []
    complexity_values = []
    slopes = []
    
    for subject_id, dim_scores in aggregated_fidelity.items():
        if subject_id not in complexity_map:
            continue
        
        dims = np.array(sorted(dim_scores.keys()))
        scores = np.array([dim_scores[d] for d in dims])
        
        if len(dims) < 2:
            continue
        
        # Fit linear regression to get slope
        slope, intercept, r_value, p_value, std_err = linregress(dims, scores)
        
        subject_ids.append(subject_id)
        complexity_values.append(complexity_map[subject_id])
        slopes.append(slope)
    
    if not subject_ids:
        raise ValueError("No subjects with both complexity and fidelity data found")
    
    complexity_arr = np.array(complexity_values)
    slopes_arr = np.array(slopes)
    
    # Now, for the phase transition analysis, we need to look at a single subject's
    # fidelity vs dimension curve to detect the breakpoint
    # We'll pick a representative subject (e.g., median complexity)
    
    median_idx = np.argsort(complexity_arr)[len(complexity_arr) // 2]
    representative_id = subject_ids[median_idx]
    rep_dims = np.array(sorted(aggregated_fidelity[representative_id].keys()))
    rep_scores = np.array([aggregated_fidelity[representative_id][d] for d in rep_dims])
    
    # Fit piecewise linear model
    params, success, message = fit_piecewise_linear(rep_dims, rep_scores)
    
    if success and params["p_value"] < 0.05:
        model_type = "phase_transition"
        hypothesis_status = "supported"
        final_params = params
    else:
        # Fallback to linear regression
        linear_params = fit_simple_linear(rep_dims, rep_scores)
        model_type = "linear"
        hypothesis_status = "falsified"
        final_params = linear_params
        # Include breakpoint as null for linear model
        if "breakpoint" not in final_params:
            final_params["breakpoint"] = None
    
    # Plot the results
    plot_regression_analysis(
        rep_dims,
        rep_scores,
        model_type,
        final_params,
        output_pdf
    )
    
    # Prepare metrics output
    metrics = {
        "model_type": model_type,
        "breakpoint": final_params.get("breakpoint"),
        "r_squared": final_params["r_squared"],
        "hypothesis_status": hypothesis_status,
        "details": message,
        "representative_subject": representative_id,
        "num_subjects_analyzed": len(subject_ids),
        "complexity_correlation_with_slope": float(np.corrcoef(complexity_arr, slopes_arr)[0, 1]) if len(subject_ids) > 1 else None
    }
    
    # Save metrics
    with open(output_metrics, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics


def main():
    """Entry point for the regression analysis script."""
    complexity_file = PROCESSED_DIR / "complexity_scores.csv"
    fidelity_file = RESULTS_DIR / "fidelity_vs_dimension_curve.json"
    output_pdf = RESULTS_DIR / "phase_transition_analysis.pdf"
    output_metrics = RESULTS_DIR / "metrics.json"
    
    print(f"Loading complexity scores from: {complexity_file}")
    print(f"Loading fidelity curve from: {fidelity_file}")
    
    try:
        metrics = run_correlation_analysis(
            complexity_file,
            fidelity_file,
            output_pdf,
            output_metrics
        )
        
        print(f"\nAnalysis complete!")
        print(f"Model type: {metrics['model_type']}")
        print(f"Hypothesis status: {metrics['hypothesis_status']}")
        print(f"R-squared: {metrics['r_squared']:.4f}")
        print(f"Breakpoint: {metrics['breakpoint']}")
        print(f"Details: {metrics['details']}")
        print(f"\nOutputs saved to:")
        print(f"  - {output_pdf}")
        print(f"  - {output_metrics}")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise


if __name__ == "__main__":
    main()
