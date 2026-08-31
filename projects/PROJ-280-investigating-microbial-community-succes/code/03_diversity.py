import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.stats.power import FTestAnovaPower
import skbio
from skbio.stats.distance import permanova
from skbio.diversity import alpha_diversity

from utils import log_underpowered_flag, benjamini_hochberg_fdr

# Custom logging formatter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_msg = f"[{record.levelname}] [{record.name}] {record.getMessage()}"
        record.msg = log_msg
        return super().format(record)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/processed/diversity_analysis.log')
        ]
    )
    # Add custom formatter to handlers if needed
    for handler in logging.getLogger().handlers:
        handler.setFormatter(CustomFormatter())

def load_processed_data(processed_dir: str = "data/processed") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load filtered feature table and sample metadata."""
    feature_table_path = Path(processed_dir) / "filtered_feature_table.csv"
    metadata_path = Path(processed_dir) / "sample_metadata.csv"

    if not feature_table_path.exists():
        logging.error("CRITICAL DATA GAP: Feature table not found at {feature_table_path}")
        sys.exit(1)
    if not metadata_path.exists():
        logging.error("CRITICAL DATA GAP: Sample metadata not found at {metadata_path}")
        sys.exit(1)

    feature_table = pd.read_csv(feature_table_path, index_col=0)
    metadata = pd.read_csv(metadata_path)

    return feature_table, metadata

def calculate_alpha_metrics(feature_table: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    """Calculate Shannon and Simpson alpha diversity indices."""
    alpha_results = {}
    for sample_id in feature_table.index:
        counts = feature_table.loc[sample_id].values
        shannon = alpha_diversity('shannon', counts)
        simpson = alpha_diversity('simpson', counts)
        alpha_results[sample_id] = {'shannon': shannon, 'simpson': simpson}

    alpha_df = pd.DataFrame(alpha_results).T
    alpha_df = alpha_df.reset_index().rename(columns={'index': 'sample_id'})
    alpha_df = alpha_df.merge(metadata, on='sample_id', how='left')
    return alpha_df

def calculate_beta_metrics(feature_table: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    """Calculate Bray-Curtis beta diversity distance matrix."""
    try:
        # skbio expects a pd.DataFrame with samples as rows
        dist_matrix = skbio.diversity.beta_diversity(
            metric='braycurtis',
            counts=feature_table,
            ids=feature_table.index,
            validate=True
        )
        # Convert to DataFrame for easier manipulation
        dist_df = pd.DataFrame(dist_matrix.to_data_frame())
        return dist_df
    except Exception as e:
        logging.error(f"Error calculating beta diversity: {e}")
        return pd.DataFrame()

def estimate_permanova_power(n_groups: int, effect_size: float = 0.15, alpha: float = 0.05) -> float:
    """Estimate power for PERMANOVA using F-test approximation."""
    # Using FTestAnovaPower from statsmodels
    # Note: PERMANOVA is an F-test on distances.
    # We approximate with one-way ANOVA power calculation.
    # effect_size (f) is derived from R^2: f = sqrt(R^2 / (1 - R^2))
    f = np.sqrt(effect_size**2 / (1 - effect_size**2))
    
    # Total N is needed. We'll use the actual sample count from metadata later.
    # This function is a helper for the report generation.
    return 0.0 # Placeholder, actual calculation done in validate_power_requirements

def validate_power_requirements(metadata: pd.DataFrame, target_effect_size: float = 0.15) -> Dict[str, Any]:
    """
    Perform power analysis for PERMANOVA.
    Reads sample_pool_validation.json to get counts if available, otherwise uses metadata.
    """
    # Load sample pool validation if it exists
    validation_path = Path("data/processed/sample_pool_validation.json")
    n_total = len(metadata)
    n_per_group = n_total // 3 # Assuming 3 stages: early, intermediate, mature
    
    # If validation file exists, use those counts
    if validation_path.exists():
        with open(validation_path, 'r') as f:
            val_data = json.load(f)
            n_total = val_data.get('total_samples', n_total)
            per_stage = val_data.get('per_stage', {})
            # Estimate min per group if available
            if per_stage:
                n_per_group = min(per_stage.values())
            else:
                n_per_group = n_total // 3

    # Calculate effect size f from R^2
    # R^2 = 0.15 -> f = sqrt(0.15 / 0.85)
    r_squared = target_effect_size
    f = np.sqrt(r_squared / (1 - r_squared))

    # Power analysis
    power_analysis = FTestAnovaPower()
    # groups = 3 (early, intermediate, mature)
    k = 3 
    n = n_total
    
    try:
        power = power_analysis.solve_power(effect_size=f, nobs1=n/k, alpha=0.05, ratio=1, alternative='larger')
        # Note: solve_power might return NaN or complex if inputs are weird, handle gracefully
        if np.isnan(power) or np.isinf(power):
            power = 0.0
    except Exception:
        power = 0.0

    flag = "PASS" if power >= 0.8 and n_per_group >= 10 else "UNDERPOWERED"
    
    return {
        "power": float(power),
        "n_per_group": int(n_per_group),
        "total_samples": int(n_total),
        "effect_size": float(r_squared),
        "flag": flag
    }

def save_power_analysis_report(report: Dict[str, Any], output_path: str = "data/processed/power_analysis_report.json"):
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Power analysis report saved to {output_path}")

def save_sample_size_validation(report: Dict[str, Any], output_path: str = "data/processed/sample_size_validation.json"):
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Sample size validation saved to {output_path}")

def save_power_analysis_sensitivity(report: Dict[str, Any], output_path: str = "data/processed/power_analysis_sensitivity.json"):
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Power analysis sensitivity report saved to {output_path}")

def run_permanova_test(dist_matrix: pd.DataFrame, metadata: pd.DataFrame, group_col: str = 'stage') -> Dict[str, Any]:
    """Run PERMANOVA test on the distance matrix."""
    # Ensure metadata index matches dist_matrix index
    metadata = metadata.set_index('sample_id')
    common_idx = dist_matrix.index.intersection(metadata.index)
    dist_subset = dist_matrix.loc[common_idx, common_idx]
    meta_subset = metadata.loc[common_idx]

    result = permanova(dist_subset, meta_subset, column=group_col)
    return {
        "f_value": result['f_value'],
        "p_value": result['p_value'],
        "r_squared": result['r2']
    }

def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    return benjamini_hochberg_fdr(p_values)

def perform_pairwise_permanova(dist_matrix: pd.DataFrame, metadata: pd.DataFrame, group_col: str = 'stage') -> List[Dict[str, Any]]:
    """Perform pairwise PERMANOVA tests between all stages."""
    metadata = metadata.set_index('sample_id')
    common_idx = dist_matrix.index.intersection(metadata.index)
    dist_subset = dist_matrix.loc[common_idx, common_idx]
    meta_subset = metadata.loc[common_idx]
    
    stages = meta_subset[group_col].unique()
    comparisons = []
    p_values = []
    
    for i, stage_a in enumerate(stages):
        for stage_b in stages[i+1:]:
            mask_a = meta_subset[group_col] == stage_a
            mask_b = meta_subset[group_col] == stage_b
            mask = mask_a | mask_b
            
            sub_dist = dist_subset.loc[common_idx[mask], common_idx[mask]]
            sub_meta = meta_subset.loc[common_idx[mask]]
            
            try:
                res = permanova(sub_dist, sub_meta, column=group_col)
                comparisons.append({
                    "stage_a": stage_a,
                    "stage_b": stage_b,
                    "p_value": float(res['p_value']),
                    "r_squared": float(res['r2'])
                })
                p_values.append(res['p_value'])
            except Exception as e:
                logging.warning(f"Pairwise test failed for {stage_a} vs {stage_b}: {e}")

    # Apply FDR correction
    if p_values:
        fdr_p_values = apply_fdr_correction(p_values)
        for i, comp in enumerate(comparisons):
            comp['fdr_p_value'] = float(fdr_p_values[i])
    else:
        for comp in comparisons:
            comp['fdr_p_value'] = None

    return comparisons

def save_pairwise_matrix(comparisons: List[Dict[str, Any]], output_path: str = "data/processed/permanova_pairwise_matrix.json"):
    with open(output_path, 'w') as f:
        json.dump({"comparisons": comparisons}, f, indent=2)
    logging.info(f"Pairwise matrix saved to {output_path}")

def save_results(alpha_df: pd.DataFrame, beta_df: pd.DataFrame, permanova_results: Dict, pairwise_results: List[Dict], output_path: str = "data/processed/diversity_metrics.json"):
    output = {
        "alpha_metrics": alpha_df.to_dict(orient='records'),
        "beta_metrics_summary": {
            "method": "braycurtis",
            "shape": list(beta_df.shape) if not beta_df.empty else [0, 0]
        },
        "permanova_results": permanova_results,
        "pairwise_comparisons": pairwise_results
    }
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    logging.info(f"Diversity metrics saved to {output_path}")

def main():
    setup_logging()
    logging.info("Starting Diversity Analysis Pipeline...")

    # Load data
    feature_table, metadata = load_processed_data()
    
    # Calculate Alpha Diversity
    logging.info("Calculating alpha diversity...")
    alpha_df = calculate_alpha_metrics(feature_table, metadata)

    # Calculate Beta Diversity
    logging.info("Calculating beta diversity...")
    beta_df = calculate_beta_metrics(feature_table, metadata)

    # Power Analysis (T020)
    logging.info("Performing power analysis...")
    power_report = validate_power_requirements(metadata)
    save_power_analysis_report(power_report)
    
    # T050: Power Analysis Sensitivity Check
    # If underpowered, calculate minimum required sample size
    if power_report['flag'] == 'UNDERPOWERED':
        logging.warning("Study is underpowered. Generating sensitivity report...")
        target_power = 0.8
        effect_size = power_report['effect_size'] # R^2 = 0.15
        f = np.sqrt(effect_size**2 / (1 - effect_size**2))
        
        # We need to find N such that power >= 0.8
        # We iterate to find the required N
        k = 3 # groups
        n_min = 6 # minimum to run
        n_required = n_min
        
        power_calc = FTestAnovaPower()
        while True:
            try:
                p = power_calc.solve_power(effect_size=f, nobs1=n_required/k, alpha=0.05, ratio=1, alternative='larger')
                if p >= target_power:
                    n_required = int(n_required)
                    break
            except:
                pass
            
            n_required += 1
            if n_required > 1000: # Safety break
                n_required = -1
                break
        
        sensitivity_report = {
            "current_power": power_report['power'],
            "target_power": target_power,
            "observed_effect_size_r2": effect_size,
            "current_n_total": power_report['total_samples'],
            "current_n_per_group": power_report['n_per_group'],
            "minimum_n_required_total": n_required if n_required != -1 else "Not calculable within bounds",
            "minimum_n_per_group": n_required // k if n_required != -1 else "Not calculable within bounds",
            "status": "UNDERPOWERED"
        }
        save_power_analysis_sensitivity(sensitivity_report)
    else:
        logging.info("Power analysis passed. Skipping sensitivity report.")
        # Still create an empty or pass report if needed, but spec says "if underpowered"
        # We'll create a report indicating it passed to be consistent
        sensitivity_report = {
            "current_power": power_report['power'],
            "target_power": 0.8,
            "status": "PASS",
            "message": "Power requirement met. No additional samples needed."
        }
        save_power_analysis_sensitivity(sensitivity_report)

    # T020b: Gate Check (Sample Size Validation)
    # This task creates the gate file and prevents T021 if failed
    gate_report = {
        "power_pass": power_report['power'] >= 0.8,
        "n_per_group_pass": power_report['n_per_group'] >= 10,
        "total_samples": power_report['total_samples'],
        "n_per_group": power_report['n_per_group'],
        "gate_status": "PASS" if (power_report['power'] >= 0.8 and power_report['n_per_group'] >= 10) else "FAIL"
    }
    save_sample_size_validation(gate_report)

    if gate_report['gate_status'] == "FAIL":
        logging.error("UNDERPOWERED: Gate failed. Stopping pipeline before PERMANOVA.")
        # Save results so far but do not run PERMANOVA
        save_results(alpha_df, beta_df, {}, [], "data/processed/diversity_metrics.json")
        sys.exit(0) # Exit cleanly but stop further analysis

    # T021: Run PERMANOVA only if gate passes
    logging.info("Running PERMANOVA...")
    permanova_result = run_permanova_test(beta_df, metadata)
    
    # T045: Pairwise PERMANOVA
    logging.info("Running pairwise PERMANOVA...")
    pairwise_results = perform_pairwise_permanova(beta_df, metadata)
    save_pairwise_matrix(pairwise_results)

    # T023: Ecological Flagging
    # Check for small effect sizes
    for comp in pairwise_results:
        if comp['fdr_p_value'] is not None and comp['fdr_p_value'] <= 0.05 and comp['r_squared'] < 0.1:
            comp['ecological_flag'] = "statistically_significant_but_weak"
        else:
            comp['ecological_flag'] = None

    # Save final metrics
    save_results(alpha_df, beta_df, permanova_result, pairwise_results)

    logging.info("Diversity Analysis Pipeline completed.")

if __name__ == "__main__":
    main()