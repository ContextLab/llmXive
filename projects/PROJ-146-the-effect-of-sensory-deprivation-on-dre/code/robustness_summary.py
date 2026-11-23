"""
Robustness Summary Generation Module

Generates a 'Robustness' summary section for the final report by aggregating
model stability metrics, bootstrap confidence interval widths, and threshold
sensitivity findings.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from serialize_results import serialize_sensitivity_results
from sensitivity import load_protocol

logger = logging.getLogger(__name__)


def load_bootstrap_results(base_path: str = "results/models") -> Optional[pd.DataFrame]:
    """
    Load bootstrap results from the serialized JSON file.
    
    Args:
        base_path: Root directory for model results.
        
    Returns:
        DataFrame with bootstrap metrics or None if not found.
    """
    file_path = os.path.join(base_path, "bootstrap_results.json")
    if not os.path.exists(file_path):
        logger.warning(f"Bootstrap results file not found at {file_path}. Skipping robustness summary generation.")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        # Flatten if necessary, assuming structure: {'results': [...]}
        if 'results' in data:
            return pd.DataFrame(data['results'])
        return pd.DataFrame([data])
    except Exception as e:
        logger.error(f"Failed to load bootstrap results: {e}")
        return None


def load_threshold_sweep_results(base_path: str = "results/models") -> Optional[pd.DataFrame]:
    """
    Load threshold sweep results from the serialized JSON file.
    
    Args:
        base_path: Root directory for model results.
        
    Returns:
        DataFrame with threshold sweep metrics or None if not found.
    """
    file_path = os.path.join(base_path, "sensitivity_sweep_results.json")
    if not os.path.exists(file_path):
        logger.warning(f"Threshold sweep results file not found at {file_path}. Skipping robustness summary generation.")
        return None
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        if 'results' in data:
            return pd.DataFrame(data['results'])
        return pd.DataFrame([data])
    except Exception as e:
        logger.error(f"Failed to load threshold sweep results: {e}")
        return None


def calculate_stability_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate stability metrics from bootstrap results.
    
    Args:
        df: DataFrame containing bootstrap results with columns like 'ci_width', 'estimate', 'flag'.
        
    Returns:
        Dictionary with stability metrics.
    """
    if df is None or df.empty:
        return {"stability_score": None, "unstable_count": 0, "total_count": 0}
    
    total_count = len(df)
    # Assuming 'flag' column indicates 'unstable' if it crosses zero or CI is too wide
    unstable_count = df[df.get('flag', '') == 'unstable'].shape[0]
    
    # Calculate average CI width
    if 'ci_width' in df.columns:
        avg_ci_width = df['ci_width'].mean()
        std_ci_width = df['ci_width'].std()
    else:
        avg_ci_width = None
        std_ci_width = None
        
    stability_score = 1.0 - (unstable_count / total_count) if total_count > 0 else 0.0
    
    return {
        "stability_score": round(stability_score, 4),
        "unstable_count": int(unstable_count),
        "total_count": int(total_count),
        "average_ci_width": round(avg_ci_width, 4) if avg_ci_width is not None else None,
        "ci_width_std": round(std_ci_width, 4) if std_ci_width is not None else None
    }


def calculate_threshold_sensitivity_metrics(df: pd.DataFrame, protocol: Dict) -> Dict[str, Any]:
    """
    Calculate sensitivity metrics across different thresholds.
    
    Args:
        df: DataFrame containing threshold sweep results.
        protocol: Protocol dictionary containing threshold labels.
        
    Returns:
        Dictionary with sensitivity metrics.
    """
    if df is None or df.empty:
        return {"sensitivity_variance": None, "thresholds_tested": []}
        
    thresholds = df['threshold_label'].unique().tolist() if 'threshold_label' in df.columns else []
    
    # Calculate variance of effect sizes across thresholds
    if 'effect_size' in df.columns and len(df) > 1:
        effect_var = df['effect_size'].var()
    else:
        effect_var = None
        
    return {
        "sensitivity_variance": round(effect_var, 4) if effect_var is not None else None,
        "thresholds_tested": thresholds,
        "effect_size_range": {
            "min": float(df['effect_size'].min()) if 'effect_size' in df.columns else None,
            "max": float(df['effect_size'].max()) if 'effect_size' in df.columns else None
        }
    }


def generate_robustness_summary(
    base_path: str = "results/models",
    output_path: str = "results/reports/robustness_summary.json"
) -> Dict[str, Any]:
    """
    Generate a comprehensive Robustness summary section for the final report.
    
    This function aggregates stability metrics from bootstrap analysis and 
    sensitivity metrics from threshold sweeps to produce a summary of the 
    model's robustness.
    
    Args:
        base_path: Root directory for model results.
        output_path: Path to save the robustness summary JSON.
        
    Returns:
        Dictionary containing the robustness summary.
    """
    logger.info("Generating Robustness Summary section...")
    
    # Load protocol for labels
    protocol = load_protocol()
    
    # Load results
    bootstrap_df = load_bootstrap_results(base_path)
    sweep_df = load_threshold_sweep_results(base_path)
    
    # Calculate metrics
    stability_metrics = calculate_stability_metrics(bootstrap_df)
    sensitivity_metrics = calculate_threshold_sensitivity_metrics(sweep_df, protocol)
    
    # Construct summary
    summary = {
        "generated_at": datetime.now().isoformat(),
        "section_title": "Robustness Analysis Summary",
        "stability_analysis": {
            "method": "Bootstrap Resampling",
            "metrics": stability_metrics,
            "interpretation": "A stability score closer to 1.0 indicates high robustness of the effect estimates."
        },
        "sensitivity_analysis": {
            "method": "Threshold Sweep",
            "metrics": sensitivity_metrics,
            "interpretation": "Lower variance across thresholds indicates the findings are robust to the definition of sensory deprivation."
        },
        "overall_robustness": {
            "score": (stability_metrics.get("stability_score") or 0) * 0.5 + (1.0 - (sensitivity_metrics.get("sensitivity_variance") or 0)) * 0.5,
            "status": "Robust" if (stability_metrics.get("stability_score") or 0) > 0.8 else "Needs Review",
            "notes": "Summary combines stability (bootstrap) and sensitivity (threshold) metrics."
        },
        "data_source": "Simulation-based (Synthetic)",
        "associational_warning": "All findings are framed as associational and derived from simulation data."
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save summary
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Robustness summary saved to {output_path}")
    return summary


def main():
    """Main entry point for generating the robustness summary."""
    setup_logging = None
    try:
        from logging_config import setup_logging
        setup_logging()
    except ImportError:
        logging.basicConfig(level=logging.INFO)
        
    generate_robustness_summary()
    logger.info("Robustness summary generation complete.")


if __name__ == "__main__":
    main()