import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import find_peaks
from scipy.stats import linregress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/visualization/plots.log')
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
RESULTS_PLOTS_DIR = Path("data/processed")
RESULTS_DIR = Path("results/plots")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PLOTS_DIR.mkdir(parents=True, exist_ok=True)

def load_processed_data() -> pd.DataFrame:
    """Load the final processed dataset with imputed features."""
    encoded_path = RESULTS_PLOTS_DIR / "encoded_features.csv"
    if not encoded_path.exists():
        raise FileNotFoundError(f"Required file not found: {encoded_path}. Run preprocessing first.")
    return pd.read_csv(encoded_path)

def load_predictions() -> pd.DataFrame:
    """Load model predictions to compare with actuals."""
    # Attempt to load predictions from a standard location or derive from data
    pred_path = RESULTS_PLOTS_DIR / "predictions.csv"
    if pred_path.exists():
        return pd.read_csv(pred_path)
    # Fallback: If no explicit prediction file, we assume the dataset has 'yield_strength_mpa'
    # and we will use the model to predict on the fly if needed, but for this task
    # we focus on the raw relationship in the data first.
    logger.warning("predictions.csv not found. Analyzing raw data relationships.")
    return None

def detect_non_monotonic_segments(
    strain_rates: np.ndarray,
    yield_strengths: np.ndarray,
    threshold_slope_change: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Detect non-monotonic regimes in the strain rate vs. yield strength relationship.
    
    A regime is considered non-monotonic if the local trend changes direction
    (increasing to decreasing or vice versa) significantly.
    
    Args:
        strain_rates: Array of strain rates (log-scaled usually).
        yield_strengths: Array of yield strengths.
        threshold_slope_change: Minimum change in slope to count as a regime shift.
    
    Returns:
        List of dictionaries describing detected non-monotonic regimes.
    """
    if len(strain_rates) < 3:
        return []

    # Sort by strain rate to ensure temporal/physical ordering
    sorted_indices = np.argsort(strain_rates)
    sr_sorted = strain_rates[sorted_indices]
    ys_sorted = yield_strengths[sorted_indices]

    # Calculate local slopes (finite differences)
    slopes = np.diff(ys_sorted) / np.diff(np.log10(sr_sorted + 1e-9)) # Log scale for strain rate

    # Detect sign changes in slopes (peaks/valleys)
    # A sign change from + to - is a peak, - to + is a valley.
    # We look for indices where the slope sign flips.
    sign_changes = np.where(np.diff(np.sign(slopes)) != 0)[0]

    non_monotonic_regimes = []

    for idx in sign_changes:
        # Define the segment around the change
        start_idx = idx
        end_idx = idx + 1
        
        # Check if the magnitude of change is significant
        slope_before = slopes[idx]
        slope_after = slopes[idx + 1] if idx + 1 < len(slopes) else slope_before
        
        # Determine the type of non-monotonicity
        if slope_before > 0 and slope_after < 0:
            regime_type = "peak"
            description = "Yield strength increases then decreases with strain rate"
        elif slope_before < 0 and slope_after > 0:
            regime_type = "valley"
            description = "Yield strength decreases then increases with strain rate"
        else:
            continue # Ignore negligible changes

        non_monotonic_regimes.append({
            "strain_rate_start": float(sr_sorted[start_idx]),
            "strain_rate_end": float(sr_sorted[end_idx]),
            "yield_strength_at_change": float(ys_sorted[idx + 1]),
            "regime_type": regime_type,
            "description": description,
            "slope_before": float(slope_before),
            "slope_after": float(slope_after)
        })

    return non_monotonic_regimes

def analyze_non_monotonicity_by_family(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze non-monotonic behavior grouped by alloy family.
    
    Returns a summary of detected regimes per family.
    """
    results = {
        "families_analyzed": [],
        "non_monotonic_families": [],
        "global_regimes": []
    }

    if 'alloy_family' not in df.columns or 'strain_rate_s_inv' not in df.columns:
        logger.error("Missing required columns in dataframe for non-monotonic analysis.")
        return results

    families = df['alloy_family'].unique()
    
    for family in families:
        family_data = df[df['alloy_family'] == family].copy()
        if len(family_data) < 5:
            continue
        
        family_data = family_data.sort_values('strain_rate_s_inv')
        
        regimes = detect_non_monotonic_segments(
            family_data['strain_rate_s_inv'].values,
            family_data['yield_strength_mpa'].values
        )
        
        results["families_analyzed"].append(family)
        
        if regimes:
            results["non_monotonic_families"].append(family)
            for regime in regimes:
                regime["alloy_family"] = family
                results["global_regimes"].append(regime)

    return results

def plot_non_monotonic_detection(
    df: pd.DataFrame,
    output_path: Path,
    family_filter: str = None
):
    """
    Generate a plot highlighting non-monotonic regimes.
    
    If family_filter is None, plots the first 3 largest families to avoid clutter.
    """
    plt.figure(figsize=(12, 8))
    
    families = df['alloy_family'].unique()
    
    # If filtering, use it; otherwise pick representative families
    families_to_plot = [family_filter] if family_filter else []
    if not families_to_plot:
        # Sort by count descending
        counts = df['alloy_family'].value_counts()
        families_to_plot = counts.head(3).index.tolist()
    
    for family in families_to_plot:
        if family not in families:
            continue
        
        family_data = df[df['alloy_family'] == family].copy()
        family_data = family_data.sort_values('strain_rate_s_inv')
        
        plt.scatter(
            family_data['strain_rate_s_inv'],
            family_data['yield_strength_mpa'],
            label=family,
            alpha=0.6,
            s=50
        )
        
        # Fit a simple smoothing curve to visualize the trend
        # Using a lowess-like approach or simple polynomial fit for visualization
        if len(family_data) > 5:
            x = family_data['strain_rate_s_inv'].values
            y = family_data['yield_strength_mpa'].values
            # Sort for plotting
            sorted_idx = np.argsort(x)
            x_sorted = x[sorted_idx]
            y_sorted = y[sorted_idx]
            
            # Simple moving average or polynomial fit for trend line
            # Using a 2nd degree polynomial for smoothness
            coeffs = np.polyfit(np.log10(x_sorted + 1e-9), y_sorted, 2)
            p = np.poly1d(coeffs)
            x_fit = np.linspace(x_sorted.min(), x_sorted.max(), 100)
            y_fit = p(np.log10(x_fit + 1e-9))
            
            plt.plot(x_fit, y_fit, linestyle='--', alpha=0.7)

    plt.xscale('log')
    plt.xlabel('Strain Rate (s⁻¹)')
    plt.ylabel('Yield Strength (MPa)')
    plt.title('Strain Rate vs Yield Strength: Non-Monotonic Regime Detection')
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved non-monotonic detection plot to {output_path}")

def main():
    """
    Main entry point for T032: Non-Monotonic Detection.
    
    1. Loads processed data.
    2. Detects non-monotonic regimes per alloy family.
    3. Saves a detailed report to data/processed/non_monotonic_report.json.
    4. Generates a visualization to results/plots/non_monotonic_detection.png.
    """
    logger.info("Starting T032: Non-Monotonic Detection")
    
    try:
        # 1. Load Data
        df = load_processed_data()
        logger.info(f"Loaded {len(df)} records for analysis.")
        
        # 2. Analyze Non-Monotonicity
        analysis_results = analyze_non_monotonicity_by_family(df)
        
        # 3. Save Report
        report_path = RESULTS_PLOTS_DIR / "non_monotonic_report.json"
        with open(report_path, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        logger.info(f"Saved non-monotonic report to {report_path}")
        
        # 4. Generate Plot
        plot_path = RESULTS_DIR / "non_monotonic_detection.png"
        plot_non_monotonic_detection(df, plot_path)
        
        # Summary Log
        if analysis_results["non_monotonic_families"]:
            logger.warning(
                f"Detected non-monotonic regimes in {len(analysis_results['non_monotonic_families'])} "
                f"families: {', '.join(analysis_results['non_monotonic_families'])}. "
                f"These may indicate failure regimes or complex physics."
            )
        else:
            logger.info("No significant non-monotonic regimes detected in the dataset.")
            
        return analysis_results

    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during non-monotonic detection: {e}")
        raise

if __name__ == "__main__":
    main()