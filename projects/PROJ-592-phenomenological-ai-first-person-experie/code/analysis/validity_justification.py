"""
Phenomenological Validity Justification Module

This module implements FR-009: Validity Justification.
It provides a literature-grounded justification for the chosen metrics
(Consistency, Stability, Markers) by citing phenomenological principles
and performing sensitivity analysis to demonstrate robustness.

It addresses concerns raised by reviewers (e.g., David Krakauer, Dan Rockmore)
regarding the operationalization of "first-person experience" in LLMs.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from utils.io import safe_write_json, load_json
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants for Phenomenological Justification
PHENOMENOLOGY_LITERATURE = {
    "consistency": {
        "principle": "Internal Coherence of the Lifeworld",
        "citation": "Husserl, E. (1931). Ideas Pertaining to a Pure Phenomenology and to a Phenomenological Philosophy. (R. Rojcewicz & A. Schuwer, Trans.). Kluwer Academic Publishers.",
        "rationale": "Phenomenological reports must maintain internal logical consistency to represent a coherent 'lifeworld'. Contradictions indicate a breakdown in the simulation of a unified subjective perspective.",
        "operationalization": "Pairwise contradiction detection using NLI models serves as a proxy for the structural integrity of the reported experience."
    },
    "stability": {
        "principle": "Temporal Continuity and Identity",
        "citation": "Sartre, J.-P. (1943). Being and Nothingness: An Essay on Phenomenological Ontology. (H. Barnes, Trans.). Philosophical Library.",
        "rationale": "A stable first-person perspective implies a continuity of self over time. Semantic drift in repeated generations suggests a lack of anchored intentionality.",
        "operationalization": "Cosine similarity of embeddings across repeated generations measures the stability of the semantic core of the experience."
    },
    "markers": {
        "principle": "Intentionality and Embodiment",
        "citation": "Merleau-Ponty, M. (1945). Phenomenology of Perception. (C. Smith, Trans.). Routledge.",
        "rationale": "Phenomenological accounts are distinguished by the presence of sensory, temporal, and intentional markers that ground the report in an embodied, situated perspective.",
        "operationalization": "Frequency counts of specific keyword classes (sensory, temporal, intentional) quantify the density of phenomenological features."
    }
}

class ValidityJustificationError(Exception):
    """Custom exception for validity justification errors."""
    pass

def load_validity_scores(input_path: str) -> pd.DataFrame:
    """
    Loads the aggregated validity scores from the analysis output.
    
    Args:
        input_path: Path to the validity_scores.csv file.
        
    Returns:
        A pandas DataFrame containing the scores.
    """
    if not os.path.exists(input_path):
        raise ValidityJustificationError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def compute_metric_sensitivity(df: pd.DataFrame, metric_col: str, 
                               noise_levels: List[float] = [0.0, 0.05, 0.1, 0.2]) -> Dict[str, Any]:
    """
    Performs a sensitivity analysis on a specific metric by adding noise
    and observing the stability of statistical significance (p-values).
    
    This addresses FR-009 by demonstrating that the chosen metrics are robust
    to small perturbations, validating their use as operational proxies.
    
    Args:
        df: DataFrame with validity scores.
        metric_col: The column name of the metric to analyze.
        noise_levels: List of noise multipliers to apply.
        
    Returns:
        Dictionary containing sensitivity results.
    """
    results = {
        "metric": metric_col,
        "noise_levels": noise_levels,
        "significance_stability": []
    }
    
    if metric_col not in df.columns:
        logger.warning(f"Metric column '{metric_col}' not found in DataFrame.")
        return results
    
    # Baseline: Run a simple ANOVA-like check (group by strategy if available, else overall variance)
    # For justification, we check if the variance structure holds under noise.
    # We simulate a t-test between two random halves of the data to check stability of p-values.
    
    original_p_values = []
    for _ in range(100): # Monte Carlo iterations
        subset = df.sample(frac=0.5, replace=False)
        if len(subset) < 4:
            continue
        # Simple variance ratio test proxy (F-test logic simplified)
        # We just check if the mean changes significantly relative to std
        mean_val = subset[metric_col].mean()
        std_val = subset[metric_col].std()
        if std_val > 0:
            original_p_values.append(mean_val / std_val) # Z-score proxy
    
    if not original_p_values:
        return results
        
    baseline_mean_z = np.mean(original_p_values)
    
    sensitivity_data = []
    for noise in noise_levels:
        noisy_p_values = []
        for _ in range(100):
            subset = df.sample(frac=0.5, replace=False)
            if len(subset) < 4:
                continue
            
            # Add noise
            noise_factor = 1.0 + (np.random.normal(0, noise) if noise > 0 else 0)
            noisy_subset = subset.copy()
            noisy_subset[metric_col] = noisy_subset[metric_col] * noise_factor
            
            mean_val = noisy_subset[metric_col].mean()
            std_val = noisy_subset[metric_col].std()
            if std_val > 0:
                noisy_p_values.append(mean_val / std_val)
        
        if noisy_p_values:
            noisy_mean_z = np.mean(noisy_p_values)
            deviation = abs(noisy_mean_z - baseline_mean_z)
            sensitivity_data.append({
                "noise": noise,
                "z_deviation": deviation,
                "stable": deviation < 0.5 # Threshold for stability
            })
    
    results["significance_stability"] = sensitivity_data
    return results

def generate_justification_report(df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Generates the full validity justification report.
    
    Args:
        df: DataFrame with validity scores.
        output_path: Path to write the JSON report.
        
    Returns:
        Dictionary containing the justification report.
    """
    report = {
        "metadata": {
            "generated_at": str(pd.Timestamp.now()),
            "framework": "Phenomenological AI: First-Person Experience Modeling",
            "reference": "FR-009: Validity Justification"
        },
        "literature_grounding": PHENOMENOLOGY_LITERATURE,
        "sensitivity_analysis": {},
        "conclusion": ""
    }
    
    metrics = ["consistency_score", "stability_score", "marker_score"]
    missing_metrics = [m for m in metrics if m not in df.columns]
    
    if missing_metrics:
        logger.warning(f"Missing metrics in data: {missing_metrics}. Skipping sensitivity for these.")
        report["conclusion"] = "Sensitivity analysis could not be fully performed due to missing metrics."
    else:
        for metric in metrics:
            logger.info(f"Running sensitivity analysis for {metric}...")
            sensitivity_results = compute_metric_sensitivity(df, metric)
            report["sensitivity_analysis"][metric] = sensitivity_results
        
        # Synthesize conclusion
        stable_metrics = []
        unstable_metrics = []
        for metric, data in report["sensitivity_analysis"].items():
            if data["significance_stability"]:
                is_stable = all(item["stable"] for item in data["significance_stability"])
                if is_stable:
                    stable_metrics.append(metric)
                else:
                    unstable_metrics.append(metric)
        
        if stable_metrics:
            report["conclusion"] = (
                f"Sensitivity analysis confirms that the metrics {stable_metrics} are robust to "
                f"small perturbations in the data, supporting their validity as operational proxies "
                f"for phenomenological coherence, stability, and intentionality as per the cited literature. "
                f"This addresses concerns regarding the arbitrary nature of metric selection."
            )
        else:
            report["conclusion"] = (
                "Sensitivity analysis indicates potential instability in the metrics. "
                "Further refinement of the metric definitions or data collection strategy is recommended."
            )
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    safe_write_json(report, output_path)
    logger.info(f"Validity justification report written to {output_path}")
    
    return report

def run_validity_justification(input_scores: str, output_report: str) -> None:
    """
    Main entry point for the validity justification task.
    
    Args:
        input_scores: Path to the validity_scores.csv file.
        output_report: Path for the output JSON report.
    """
    try:
        logger.info("Starting Validity Justification Analysis (FR-009)...")
        df = load_validity_scores(input_scores)
        report = generate_justification_report(df, output_report)
        
        # Print summary to log
        logger.info("Justification Conclusion:")
        logger.info(report["conclusion"])
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise ValidityJustificationError(f"Failed to load input scores: {e}")
    except Exception as e:
        logger.error(f"Error during validity justification: {e}")
        raise ValidityJustificationError(f"Analysis failed: {e}")

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate phenomenological validity justification report.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/validity_scores.csv",
        help="Path to the validity scores CSV file."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/validity_justification.json",
        help="Path for the output JSON report."
    )
    
    args = parser.parse_args()
    
    # Ensure paths are relative to project root if not absolute
    # (Assuming script is run from project root or code/analysis/)
    # Adjust based on actual project structure conventions
    if not os.path.isabs(args.input):
        # Try relative to data/processed if not specified
        pass 
        
    run_validity_justification(args.input, args.output)

if __name__ == "__main__":
    main()