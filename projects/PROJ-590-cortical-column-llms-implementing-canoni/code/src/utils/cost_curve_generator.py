import json
import os
import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from pathlib import Path

from src.experiments.ablation import run_ablation_study, load_ablation_configs
from src.utils.scaling_analyzer import load_scaling_data

logger = logging.getLogger(__name__)

def generate_cost_curve_data(ablation_results_dir: Optional[str] = None,
                             scaling_results_path: Optional[str] = None,
                             output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Compute the 'cost of biological plausibility' curve.
    
    This function compares the performance (MAE) of ablated variants (recurrence, inhibition)
    against the full model and the baseline. It integrates scaling data to normalize
    the cost by parameter count or training time if available.
    
    Args:
        ablation_results_dir: Directory containing ablation study JSON results.
        scaling_results_path: Path to scaling_law.csv to get baseline parameter counts.
        output_path: Path to write the resulting CSV. Defaults to data/results/cost_curve_data.csv.
    
    Returns:
        pd.DataFrame: The cost curve data.
    """
    project_root = Path(__file__).resolve().parents[3]
    
    if ablation_results_dir is None:
        ablation_results_dir = project_root / "data" / "results" / "ablation"
    else:
        ablation_results_dir = Path(ablation_results_dir)
        
    if scaling_results_path is None:
        scaling_results_path = project_root / "data" / "results" / "scaling_law.csv"
    else:
        scaling_results_path = Path(scaling_results_path)
        
    if output_path is None:
        output_path = project_root / "data" / "results" / "cost_curve_data.csv"
    else:
        output_path = Path(output_path)
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Scaling Data to establish Baseline Parameter Counts
    # We need the baseline (1x columns) parameter count to normalize ablated variants if they differ
    baseline_params = None
    scaling_df = None
    try:
        scaling_df = load_scaling_data(str(scaling_results_path))
        # Assume the first row or the row with 'columns' == 1 is the baseline
        baseline_row = scaling_df[scaling_df['columns'] == 1]
        if baseline_row.empty:
            baseline_row = scaling_df.iloc[0] # Fallback to first if 1x not found
        baseline_params = baseline_row['params']
        logger.info(f"Loaded baseline parameter count: {baseline_params}")
    except Exception as e:
        logger.warning(f"Could not load scaling data for normalization: {e}. Proceeding without param normalization.")
    
    # 2. Load Ablation Results
    # Expected structure: ablation_results_dir contains JSON files for each ablation config
    # We expect the study to have been run by T025b.
    ablation_data = []
    
    if not ablation_results_dir.exists():
        raise FileNotFoundError(f"Ablation results directory not found: {ablation_results_dir}. "
                                "Ensure T025b (run_ablation_study) has been executed.")
    
    json_files = list(ablation_results_dir.glob("*.json"))
    if not json_files:
        # Try subdirectories if standard layout is used
        for subdir in ablation_results_dir.iterdir():
            if subdir.is_dir():
                json_files.extend(subdir.glob("*.json"))
    
    if not json_files:
        raise FileNotFoundError(f"No ablation result JSON files found in {ablation_results_dir}")
    
    baseline_mae = None
    baseline_time = None
    
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                result = json.load(f)
            
            # Extract relevant metrics based on expected ablation schema
            # Schema from T025b: result should contain 'config' and 'metrics' (or similar)
            config = result.get('config', {})
            metrics = result.get('metrics', result) # Fallback if metrics not nested
            
            variant_name = config.get('name', config.get('variant', file_path.stem))
            mae = metrics.get('val_mae', metrics.get('mae'))
            train_time = metrics.get('training_time', metrics.get('time_sec'))
            params = metrics.get('param_count', baseline_params)
            
            if mae is None:
                logger.warning(f"Skipping {file_path}: missing MAE")
                continue
                
            # Identify if this is the full model or baseline
            if 'baseline' in variant_name.lower() or 'baseline' in str(config):
                baseline_mae = mae
                baseline_time = train_time
            
            ablation_data.append({
                'variant': variant_name,
                'mae': mae,
                'time_sec': train_time,
                'params': params,
                'file': file_path.name
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            continue
    
    if not ablation_data:
        raise RuntimeError("No valid ablation results found to compute cost curve.")
    
    # 3. Compute Cost Metrics
    # Cost of Plausibility = (Performance_Full - Performance_Ablated) / Performance_Full
    # We assume 'Full Model' is the most complex ablation variant (e.g., 'full_microcircuit')
    # or the one with the lowest MAE among the microcircuit variants.
    
    # Identify the 'Full' microcircuit model (best performing among non-baseline)
    microcircuit_variants = [d for d in ablation_data if 'baseline' not in d['variant'].lower()]
    
    if not microcircuit_variants:
        raise RuntimeError("No microcircuit variants found in ablation results.")
        
    # Sort by MAE (lower is better) to find the 'Full' implementation (should be best)
    microcircuit_variants.sort(key=lambda x: x['mae'])
    full_model = microcircuit_variants[0]
    
    if baseline_mae is None:
        # If baseline wasn't explicitly in the ablation JSONs, try to load from baseline_runner output
        baseline_log = project_root / "data" / "logs" / "training_log.json"
        if baseline_log.exists():
            with open(baseline_log, 'r') as f:
                log_data = json.load(f)
                # Assume last entry or 'final' key
                if isinstance(log_data, list):
                    baseline_mae = log_data[-1].get('val_mae')
                elif isinstance(log_data, dict):
                    baseline_mae = log_data.get('final_val_mae')
        
    if baseline_mae is None:
        # Fallback: use the worst ablation as a proxy if baseline missing (not ideal but prevents crash)
        logger.warning("Baseline MAE not found. Using worst performing variant as proxy.")
        baseline_mae = max(d['mae'] for d in ablation_data)

    cost_rows = []
    
    # Calculate cost for each ablated variant relative to the Full Model and Baseline
    for variant in ablation_data:
        variant_name = variant['variant']
        mae = variant['mae']
        
        # Cost of removing specific feature = (Full_MAE - Variant_MAE) / Full_MAE
        # Positive cost means performance dropped (bad), Negative means it improved (feature was noise)
        # We want to show the "Cost of Plausibility": How much worse is the Full model compared to the Ablated?
        # Actually, the "Cost" is usually: (Performance_Full - Performance_Baseline) / Performance_Baseline
        # But here we want the curve comparing ablated vs full.
        
        # Let's define "Plausibility Cost" for a variant as the MAE difference from the Full Model
        # If Full Model is better (lower MAE), the cost of using the ablated version is the error increase.
        # If the task is "Cost of Biological Plausibility", we want to know: 
        # "How much worse is the Full Model compared to a simple baseline?"
        # AND "How much does removing a feature (ablation) recover performance (reduce cost)?"
        
        # Metric: Relative Error Increase vs Full Model
        if full_model['mae'] > 0:
            relative_error_vs_full = (mae - full_model['mae']) / full_model['mae']
        else:
            relative_error_vs_full = 0.0
            
        # Metric: Relative Error vs Baseline (if available)
        if baseline_mae and baseline_mae > 0:
            relative_error_vs_baseline = (mae - baseline_mae) / baseline_mae
        else:
            relative_error_vs_baseline = 0.0
            
        # Cost of Plausibility for this specific configuration:
        # If this IS the full model, the cost is (Full - Baseline) / Baseline
        # If this is an ablation, the cost is (Ablation - Baseline) / Baseline
        
        if baseline_mae:
            cost_of_plausibility = (mae - baseline_mae) / baseline_mae
        else:
            cost_of_plausibility = 0.0
        
        cost_rows.append({
            'variant': variant_name,
            'mae': mae,
            'baseline_mae': baseline_mae,
            'full_model_mae': full_model['mae'],
            'relative_error_vs_full': relative_error_vs_full,
            'relative_error_vs_baseline': relative_error_vs_baseline,
            'cost_of_plausibility': cost_of_plausibility,
            'params': variant['params'],
            'time_sec': variant['time_sec']
        })
    
    df = pd.DataFrame(cost_rows)
    
    # Sort by cost of plausibility (descending) to show the curve from simplest to most complex
    df = df.sort_values(by='cost_of_plausibility', ascending=False)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Cost curve data written to {output_path}")
    
    return df

def main():
    """Entry point for script execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = Path(__file__).resolve().parents[3]
    output_path = project_root / "data" / "results" / "cost_curve_data.csv"
    
    try:
        df = generate_cost_curve_data(output_path=str(output_path))
        print(f"Successfully generated cost curve data at {output_path}")
        print(df.to_string())
    except Exception as e:
        logger.error(f"Failed to generate cost curve data: {e}")
        raise

if __name__ == "__main__":
    main()