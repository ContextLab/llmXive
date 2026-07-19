import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from config import get_config
from models import generate_interaction_terms

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_regression_results(config: Dict[str, Any]) -> pd.DataFrame:
    """Load regression results from JSON/Parquet."""
    derived_path = Path(config['derived_path'])
    path = derived_path / 'regression_results.json'
    
    if not path.exists():
        logger.error(f"Regression results file not found at {path}. Run regression training first.")
        return pd.DataFrame()
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Ensure we return a DataFrame with the expected structure for analysis
    if isinstance(data, dict):
        return pd.DataFrame([data])
    elif isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame()

def load_sensitivity_analysis(config: Dict[str, Any]) -> pd.DataFrame:
    """Load sensitivity analysis data from CSV."""
    derived_path = Path(config['derived_path'])
    path = derived_path / 'sensitivity_analysis.csv'
    
    if path.exists():
        return pd.read_csv(path)
    else:
        logger.warning(f"Sensitivity analysis file not found at {path}")
        return pd.DataFrame()

def check_threshold_stability(config: Dict[str, Any], thresholds: List[float] = [0.40, 0.45, 0.50, 0.55, 0.60]) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping thresholds.
    FR-006: Verify critical interaction vector does not change sign or magnitude by >10%.
    
    This function re-runs the collapse detection logic with different thresholds
    to see how the critical interaction vector (SNR x RT60 coefficient) varies.
    """
    logger.info(f"Starting sensitivity analysis for thresholds: {thresholds}")
    
    # Load the stress curves and collapse points to re-evaluate
    derived_path = Path(config['derived_path'])
    collapse_path = derived_path / 'collapse_points.parquet'
    stress_path = derived_path / 'stress_curves.parquet'
    
    if not collapse_path.exists() or not stress_path.exists():
        raise FileNotFoundError(
            f"Required data files missing. Need {collapse_path} and {stress_path}. "
            "Run main.py and US2 tasks first."
        )
    
    collapse_df = pd.read_parquet(collapse_path)
    stress_df = pd.read_parquet(stress_path)
    
    if collapse_df.empty or stress_df.empty:
        raise ValueError("Input dataframes are empty. Cannot perform sensitivity analysis.")
    
    results = []
    
    # We need to map the collapse points back to the specific threshold used
    # Since collapse points were generated with a specific threshold (likely 0.5),
    # we need to re-calculate collapse points for each threshold in the sweep.
    # This requires re-processing the stress curves.
    
    # For efficiency, we'll process the stress curves once and apply different thresholds
    # The stress curve contains: clip_id, snr, rt60, sss, wer, ...
    
    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")
        
        # Normalize SSS if needed (assume it's already normalized to baseline)
        # Identify collapse points where SSS < threshold AND WER > 2x baseline
        # We need baseline WER per scenario/model
        baseline_wer_path = derived_path / 'baseline_wer.json'
        if baseline_wer_path.exists():
            with open(baseline_wer_path, 'r') as f:
                baseline_wers = json.load(f)
            baseline_wer_map = {(item['model_id'], item['scenario_id']): item['baseline_value'] 
                                for item in baseline_wers}
        else:
            logger.warning("baseline_wer.json not found. Using 0.1 as default baseline.")
            baseline_wer_map = {}
        
        # Re-calculate collapse points for this threshold
        threshold_results = []
        
        # Group by clip_id to find the first collapse point
        # We assume stress_df is sorted by distortion intensity
        for (model_id, scenario_id, clip_id), group in stress_df.groupby(['model_id', 'scenario_id', 'clip_id']):
            # Sort by intensity (e.g., SNR descending or RT60 ascending depending on distortion)
            # Assuming group is already sorted by distortion intensity
            group = group.sort_values(by=['snr', 'rt60']) # Adjust sorting as needed
            
            collapse_found = False
            collapse_vector = None
            
            for _, row in group.iterrows():
                sss = row['sss']
                wer = row['wer']
                
                # Get baseline WER for this scenario
                baseline_key = (model_id, scenario_id)
                baseline_wer = baseline_wer_map.get(baseline_key, 0.1)
                
                # Check collapse criteria
                if sss < threshold and wer > 2.0 * baseline_wer:
                    collapse_found = True
                    collapse_vector = {
                        'snr': row['snr'],
                        'rt60': row['rt60'],
                        'interaction': row['snr'] * row['rt60']
                    }
                    break
            
            if collapse_found:
                threshold_results.append({
                    'model_id': model_id,
                    'scenario_id': scenario_id,
                    'clip_id': clip_id,
                    'threshold': threshold,
                    'collapse_snr': collapse_vector['snr'],
                    'collapse_rt60': collapse_vector['rt60'],
                    'collapse_interaction': collapse_vector['interaction']
                })
        
        if threshold_results:
            threshold_df = pd.DataFrame(threshold_results)
            # Calculate the mean critical interaction vector for this threshold
            # We use the interaction term coefficient as the proxy for the "critical vector"
            mean_interaction = threshold_df['collapse_interaction'].mean()
            mean_snr = threshold_df['collapse_snr'].mean()
            mean_rt60 = threshold_df['collapse_rt60'].mean()
            
            results.append({
                'threshold': threshold,
                'mean_interaction': mean_interaction,
                'mean_snr': mean_snr,
                'mean_rt60': mean_rt60,
                'count': len(threshold_results)
            })
    
    # Check stability
    stability_report = {
        "thresholds_tested": thresholds,
        "results": results,
        "stable": True,
        "variance": 0.0
    }
    
    if len(results) > 1:
        interaction_coeffs = [r["mean_interaction"] for r in results]
        variance = np.var(interaction_coeffs)
        stability_report["variance"] = float(variance)
        
        # Check if magnitude changes by >10%
        mean_val = np.mean(interaction_coeffs)
        if mean_val != 0:
            max_deviation = np.max(np.abs(np.array(interaction_coeffs) - mean_val)) / np.abs(mean_val)
            if max_deviation > 0.10:
                stability_report["stable"] = False
                logger.warning(f"Critical interaction vector varies by {max_deviation:.2%} (>10%). Unstable.")
        else:
            # If mean is 0, check absolute variance
            if variance > 0.001: # Small threshold for zero-mean
                stability_report["stable"] = False
    
    return stability_report

def generate_stability_report(config: Dict[str, Any], stability_data: Dict[str, Any]) -> Path:
    """Generate and save stability report as CSV and update regression results."""
    derived_path = Path(config['derived_path'])
    output_path = derived_path / 'sensitivity_analysis.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert results to DataFrame
    rows = []
    for res in stability_data["results"]:
        rows.append({
            "threshold": res["threshold"],
            "mean_snr": res["mean_snr"],
            "mean_rt60": res["mean_rt60"],
            "mean_interaction": res["mean_interaction"],
            "count": res["count"]
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved sensitivity analysis to {output_path}")
    
    # Update regression results with stability info
    reg_results_path = derived_path / 'regression_results.json'
    if reg_results_path.exists():
        with open(reg_results_path, 'r') as f:
            reg_data = json.load(f)
        reg_data['stability_analysis'] = {
            'stable': stability_data['stable'],
            'variance': stability_data['variance'],
            'thresholds_tested': stability_data['thresholds_tested']
        }
        with open(reg_results_path, 'w') as f:
            json.dump(reg_data, f, indent=2)
        logger.info(f"Updated {reg_results_path} with stability analysis.")
    
    return output_path

def main():
    """Main entry point for analysis.py."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analysis and Sensitivity Testing")
    parser.add_argument("--validate-sss", action="store_true", help="Validate SSS and run sensitivity analysis")
    
    args = parser.parse_args()
    config = get_config()
    
    # Ensure derived_path is set
    if 'derived_path' not in config:
        config['derived_path'] = str(Path(config['project_root']) / 'data' / 'derived')
    
    if args.validate_sss:
        logger.info("Running sensitivity analysis...")
        try:
            stability_data = check_threshold_stability(config)
            generate_stability_report(config, stability_data)
            logger.info("Sensitivity analysis completed successfully.")
        except FileNotFoundError as e:
            logger.error(f"Data files missing: {e}")
            sys.exit(1)
        except ValueError as e:
            logger.error(f"Data processing error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during sensitivity analysis: {e}")
            sys.exit(1)
    else:
        logger.info("No action specified. Use --validate-sss to run sensitivity analysis.")

if __name__ == "__main__":
    main()
