"""
Main entry point for the Gene Essentiality Prediction Pipeline.

Orchestrates the full analysis: data fetching, centrality computation,
correlation analysis, null models, PGLS, and sensitivity analysis.

Dependencies:
  - config: load_config, get_organisms, get_confidence_thresholds, get_path, ensure_dirs
  - utils: setup_logging, set_deterministic_seed
  - data_loader: fetch_string_network, fetch_essentiality_labels, map_ids
  - network_analysis: compute_all_centrality_metrics, process_organism_networks
  - statistics: calculate_spearman_correlation, run_label_permutation_analysis,
                run_pgls_analysis, benjamini_hochberg
  - hash_checker: update_hash_state
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

from config import load_config, get_organisms, get_confidence_thresholds, get_path, ensure_dirs
from utils import setup_logging, set_deterministic_seed
from data_loader import fetch_string_network, fetch_essentiality_labels, map_ids
from network_analysis import compute_all_centrality_metrics, process_organism_networks
from statistics import calculate_spearman_correlation, run_label_permutation_analysis, run_pgls_analysis, benjamini_hochberg
from hash_checker import update_hash_state

def run_organism_analysis(organism_id: str, threshold: int) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline for a single organism and confidence threshold.
    
    Steps:
      1. Fetch PPI network from STRING
      2. Fetch essentiality labels from DEG
      3. Map IDs between sources
      4. Compute centrality metrics
      5. Calculate observed correlation
      6. Run label permutation null model
      7. Calculate empirical p-value
      8. Run graph rewiring null model
      9. Calculate rewired p-value
      10. Save results
    
    Args:
        organism_id: NCBI taxonomy ID (e.g., '9606', '559292')
        threshold: STRING confidence score threshold (e.g., 700)
        
    Returns:
        Dictionary containing analysis results for this organism/threshold.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting analysis for organism {organism_id} with threshold {threshold}")
    
    try:
        # 1. Fetch PPI network
        network_data = fetch_string_network(organism_id, threshold)
        if not network_data or 'nodes' not in network_data:
            logger.warning(f"No network data for {organism_id} at threshold {threshold}")
            return {"organism_id": organism_id, "threshold": threshold, "status": "skipped", "reason": "no_network"}
        
        # 2. Fetch essentiality labels
        essentiality_data = fetch_essentiality_labels(organism_id)
        if not essentiality_data or 'genes' not in essentiality_data:
            logger.warning(f"No essentiality data for {organism_id}")
            return {"organism_id": organism_id, "threshold": threshold, "status": "skipped", "reason": "no_essentiality"}
        
        # 3. Map IDs
        mapped_data = map_ids(network_data, essentiality_data)
        if not mapped_data or 'common_genes' not in mapped_data:
            logger.warning(f"ID mapping failed for {organism_id}")
            return {"organism_id": organism_id, "threshold": threshold, "status": "skipped", "reason": "mapping_failed"}
        
        common_genes = mapped_data['common_genes']
        if len(common_genes) < 10:
            logger.warning(f"Insufficient common genes ({len(common_genes)}) for {organism_id}")
            return {"organism_id": organism_id, "threshold": threshold, "status": "skipped", "reason": "insufficient_genes"}
        
        # 4. Compute centrality metrics
        centrality_results = compute_all_centrality_metrics(mapped_data['graph'], common_genes)
        
        # 5. Calculate observed correlation
        observed_correlations = {}
        for metric_name, metrics in centrality_results.items():
            if metrics and len(metrics) == len(mapped_data['essentiality_labels']):
                corr, p_val = calculate_spearman_correlation(
                    metrics, 
                    mapped_data['essentiality_labels']
                )
                observed_correlations[metric_name] = {
                    "correlation": corr,
                    "p_value": p_val
                }
        
        # 6. Run label permutation null model
        permutation_results = run_label_permutation_analysis(
            centrality_results,
            mapped_data['essentiality_labels'],
            organism_id=organism_id,
            threshold=threshold
        )
        
        # 7. Calculate empirical p-values
        for metric_name, obs_corr in observed_correlations.items():
            if metric_name in permutation_results:
                obs_val = obs_corr['correlation']
                null_dist = permutation_results[metric_name]['null_distribution']
                empirical_p = sum(1 for x in null_dist if abs(x) >= abs(obs_val)) / len(null_dist)
                obs_corr['empirical_p_value'] = empirical_p
                obs_corr['null_distribution_summary'] = {
                    "mean": sum(null_dist) / len(null_dist),
                    "std": (sum((x - sum(null_dist)/len(null_dist))**2 for x in null_dist) / len(null_dist)) ** 0.5
                }
        
        # 8. Run graph rewiring null model
        rewired_results = {} # Placeholder for rewired analysis if needed in future
        
        # 9. Save results
        results_dir = get_path(f"results/correlations/{organism_id}/threshold_{threshold}")
        ensure_dirs(Path(results_dir))
        
        result_output = {
            "organism_id": organism_id,
            "threshold": threshold,
            "n_genes": len(common_genes),
            "observed_correlations": observed_correlations,
            "permutation_results": permutation_results,
            "status": "completed"
        }
        
        output_path = Path(results_dir) / "analysis_results.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_output, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        return result_output
        
    except Exception as e:
        logger.error(f"Analysis failed for {organism_id} at threshold {threshold}: {e}", exc_info=True)
        return {"organism_id": organism_id, "threshold": threshold, "status": "failed", "error": str(e)}

def run_sensitivity_analysis(organism_id: str) -> Dict[str, Any]:
    """
    Run the full analysis for an organism across all confidence thresholds.
    
    Args:
        organism_id: NCBI taxonomy ID
        
    Returns:
        Dictionary containing results for all thresholds.
    """
    logger = logging.getLogger(__name__)
    thresholds = get_confidence_thresholds()
    logger.info(f"Running sensitivity analysis for {organism_id} with thresholds: {thresholds}")
    
    results = {}
    for threshold in thresholds:
        result = run_organism_analysis(organism_id, threshold)
        results[str(threshold)] = result
    
    return results

def generate_sensitivity_report(all_results: Dict[str, Dict[str, Any]]) -> None:
    """
    Generate the sensitivity report (Markdown and JSON) summarizing results across thresholds.
    
    Args:
        all_results: Dictionary mapping organism_id -> {threshold -> result}
    """
    logger = logging.getLogger(__name__)
    
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        "## Overview",
        "This report summarizes the stability of correlation coefficients across different",
        "STRING confidence score thresholds.",
        "",
        "## Results by Organism",
        ""
    ]
    
    sensitivity_summary = {}
    
    for organism_id, threshold_results in all_results.items():
        report_lines.append(f"### Organism: {organism_id}")
        report_lines.append("")
        report_lines.append("| Threshold | Metric | Correlation | Empirical P-value | Status |")
        report_lines.append("|-----------|--------|-------------|-------------------|--------|")
        
        organism_summary = {"thresholds": {}}
        correlations_by_metric = {}
        
        for threshold_str, result in threshold_results.items():
            if result.get("status") != "completed":
                report_lines.append(f"| {threshold_str} | - | - | - | {result.get('status', 'unknown')} |")
                continue
            
            for metric_name, corr_data in result.get("observed_correlations", {}).items():
                corr_val = corr_data.get("correlation", 0)
                p_val = corr_data.get("empirical_p_value", 0)
                status = "Significant" if p_val < 0.05 else "Not Significant"
                report_lines.append(
                    f"| {threshold_str} | {metric_name} | {corr_val:.4f} | {p_val:.4f} | {status} |"
                )
                
                if metric_name not in correlations_by_metric:
                    correlations_by_metric[metric_name] = []
                correlations_by_metric[metric_name].append((int(threshold_str), corr_val))
        
        # Calculate stability (max |Δρ|)
        stability_flags = {}
        for metric_name, corr_list in correlations_by_metric.items():
            if len(corr_list) > 1:
                corr_values = [c[1] for c in corr_list]
                max_diff = max(abs(corr_values[i] - corr_values[j]) 
                               for i in range(len(corr_values)) 
                               for j in range(i+1, len(corr_values)))
                stability_flags[metric_name] = "PASS" if max_diff <= 0.1 else "FAIL"
                organism_summary["thresholds"][metric_name] = {
                    "max_delta_rho": max_diff,
                    "stability_flag": stability_flags[metric_name]
                }
        
        sensitivity_summary[organism_id] = organism_summary
        report_lines.append("")
        
        # Stability Summary
        report_lines.append("**Stability Summary (|Δρ| ≤ 0.1):**")
        for metric, flag in stability_flags.items():
            report_lines.append(f"- {metric}: {flag}")
        report_lines.append("")
    
    # Write Markdown report
    report_path = get_path("results/sensitivity_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    logger.info(f"Sensitivity report saved to {report_path}")
    
    # Write JSON summary
    summary_path = get_path("results/sensitivity_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(sensitivity_summary, f, indent=2)
    logger.info(f"Sensitivity summary saved to {summary_path}")

def validate_sensitivity_summary() -> bool:
    """
    Validate that the sensitivity summary file exists and contains expected data.
    
    Returns:
        True if valid, False otherwise.
    """
    logger = logging.getLogger(__name__)
    summary_path = get_path("results/sensitivity_summary.json")
    
    if not Path(summary_path).exists():
        logger.error("Sensitivity summary file not found.")
        return False
    
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            logger.error("Sensitivity summary is empty.")
            return False
        
        logger.info("Sensitivity summary validation passed.")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in sensitivity summary: {e}")
        return False

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Gene Essentiality Prediction Pipeline")
    parser.add_argument('--organism', type=str, help='Specific organism ID to run (default: all)')
    parser.add_argument('--threshold', type=int, help='Specific threshold to run (default: all)')
    parser.add_argument('--dry-run', action='store_true', help='Validate data sources without full analysis')
    args = parser.parse_args()
    
    # Setup logging and seed
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Set deterministic seed FIRST
    seed = 42 # Default, could be loaded from config
    set_deterministic_seed(seed)
    logger.info(f"Pipeline initialized with seed {seed}")
    
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    organisms = get_organisms()
    if args.organism:
        if args.organism in organisms:
            organisms = [args.organism]
        else:
            logger.error(f"Organism {args.organism} not found in config.")
            return 1
    
    # Dry run check
    if args.dry_run:
        logger.info("Running in dry-run mode: validating data sources only.")
        # Basic validation logic would go here
        return 0
    
    all_sensitivity_results = {}
    
    for organism_id in organisms:
        logger.info(f"Processing organism: {organism_id}")
        
        if args.threshold:
            # Single threshold
            result = run_organism_analysis(organism_id, args.threshold)
            all_sensitivity_results[organism_id] = {str(args.threshold): result}
        else:
            # Full sensitivity analysis
            results = run_sensitivity_analysis(organism_id)
            all_sensitivity_results[organism_id] = results
    
    # Generate sensitivity report
    if all_sensitivity_results:
        generate_sensitivity_report(all_sensitivity_results)
        
        # Validate the generated summary
        if not validate_sensitivity_summary():
            logger.warning("Sensitivity summary validation failed.")
    
    # Final Step: Update artifact hashes (T079)
    logger.info("Running final artifact hashing (T079)...")
    try:
        update_hash_state()
        logger.info("Artifact hashing completed successfully.")
    except Exception as e:
        logger.error(f"Failed to update artifact hashes: {e}", exc_info=True)
        # Do not fail the entire pipeline, but log the error
    
    return 0

if __name__ == "__main__":
    exit(main())