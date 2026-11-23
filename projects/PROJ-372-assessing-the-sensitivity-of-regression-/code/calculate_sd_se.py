"""
Calculate Standard Error of the SD for the comparison and output to artifacts/convergence.log.

This script implements T050:
- Loads coefficient SDs from artifacts/stability/coefficient_sd.json (produced by T048)
- Loads the comparison results from artifacts/stability/stability_comparison.json (produced by T049)
- Calculates the Standard Error (SE) of the SD for the comparison
- Outputs the results to artifacts/convergence.log

The Standard Error of the SD is calculated as: SE = SD / sqrt(2 * (N - 1))
where N is the number of subsets used to compute the SD.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import math

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
STABILITY_DIR = ARTIFACTS_DIR / "stability"

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_se_of_sd(sd_value: float, n_subsets: int) -> float:
    """
    Calculate Standard Error of the Standard Deviation.
    
    Formula: SE = SD / sqrt(2 * (N - 1))
    where N is the number of independent samples (subsets) used to compute the SD.
    
    Args:
        sd_value: The standard deviation value
        n_subsets: Number of subsets used to compute the SD
        
    Returns:
        Standard Error of the SD
    """
    if n_subsets <= 1:
        raise ValueError("Need at least 2 subsets to calculate SE of SD")
    
    if sd_value <= 0:
        # If SD is 0 or negative, SE is 0
        return 0.0
    
    return sd_value / math.sqrt(2 * (n_subsets - 1))

def main():
    """Main function to calculate SE of SD and output to convergence.log."""
    # Define paths
    sd_file = STABILITY_DIR / "coefficient_sd.json"
    comparison_file = STABILITY_DIR / "stability_comparison.json"
    log_file = ARTIFACTS_DIR / "convergence.log"
    
    # Ensure artifacts directory exists
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load coefficient SDs
    print(f"Loading coefficient SDs from {sd_file}...")
    try:
        sd_data = load_json_file(sd_file)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure T048 has been completed and coefficient_sd.json exists.")
        sys.exit(1)
    
    # Load stability comparison results
    print(f"Loading stability comparison from {comparison_file}...")
    try:
        comparison_data = load_json_file(comparison_file)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure T049 has been completed and stability_comparison.json exists.")
        sys.exit(1)
    
    # Prepare log content
    log_lines = []
    log_lines.append("=" * 80)
    log_lines.append("CONVERGENCE ANALYSIS: Standard Error of SD Calculation")
    log_lines.append(f"Generated: {Path(__file__).stem}")
    log_lines.append("=" * 80)
    log_lines.append("")
    
    # Process each dataset and tier
    results = []
    
    for dataset_name, dataset_results in sd_data.items():
        log_lines.append(f"Dataset: {dataset_name}")
        log_lines.append("-" * 40)
        
        for tier_name, tier_data in dataset_results.get("tiers", {}).items():
            sd_value = tier_data.get("sd")
            n_subsets = tier_data.get("n_subsets")
            
            if sd_value is None or n_subsets is None:
                log_lines.append(f"  Tier {tier_name}: Missing SD or n_subsets, skipping")
                continue
            
            try:
                se_value = calculate_se_of_sd(sd_value, n_subsets)
                
                # Check if this tier was compared in T049
                comparison_info = None
                for comp in comparison_data.get("comparisons", []):
                    if (comp.get("dataset") == dataset_name and 
                        comp.get("tier") == tier_name):
                        comparison_info = comp
                        break
                
                # Format results
                se_percent = (se_value / sd_value * 100) if sd_value > 0 else 0
                
                log_lines.append(f"  Tier: {tier_name}")
                log_lines.append(f"    SD: {sd_value:.6f}")
                log_lines.append(f"    N subsets: {n_subsets}")
                log_lines.append(f"    SE of SD: {se_value:.6f} ({se_percent:.2f}% of SD)")
                
                if comparison_info:
                    log_lines.append(f"    Comparison: {comparison_info.get('n1')} vs {comparison_info.get('n2')} subsets")
                    log_lines.append(f"    Diff in SD: {comparison_info.get('diff_sd', 'N/A')}")
                
                results.append({
                    "dataset": dataset_name,
                    "tier": tier_name,
                    "sd": sd_value,
                    "n_subsets": n_subsets,
                    "se_of_sd": se_value,
                    "se_percent": se_percent
                })
                
            except ValueError as e:
                log_lines.append(f"  Tier {tier_name}: Error calculating SE - {e}")
        
        log_lines.append("")
    
    # Summary
    log_lines.append("=" * 80)
    log_lines.append("SUMMARY")
    log_lines.append("=" * 80)
    
    if results:
        avg_se_percent = sum(r["se_percent"] for r in results) / len(results)
        max_se_percent = max(r["se_percent"] for r in results)
        min_se_percent = min(r["se_percent"] for r in results)
        
        log_lines.append(f"Total results: {len(results)}")
        log_lines.append(f"Average SE as % of SD: {avg_se_percent:.2f}%")
        log_lines.append(f"Min SE as % of SD: {min_se_percent:.2f}%")
        log_lines.append(f"Max SE as % of SD: {max_se_percent:.2f}%")
        
        # Check convergence criteria (SC-005: SE < 5% of SD)
        converged_count = sum(1 for r in results if r["se_percent"] < 5.0)
        log_lines.append("")
        log_lines.append(f"Convergence check (SC-005: SE < 5% of SD):")
        log_lines.append(f"  Converged: {converged_count}/{len(results)} ({converged_count/len(results)*100:.1f}%)")
        
        if converged_count == len(results):
            log_lines.append("  RESULT: ALL tiers meet convergence criteria (SC-005)")
        else:
            log_lines.append(f"  RESULT: {len(results) - converged_count} tiers do NOT meet convergence criteria")
            for r in results:
                if r["se_percent"] >= 5.0:
                    log_lines.append(f"    - {r['dataset']} ({r['tier']}): {r['se_percent']:.2f}%")
    else:
        log_lines.append("No valid results to summarize.")
    
    log_lines.append("")
    log_lines.append("=" * 80)
    log_lines.append("END OF CONVERGENCE ANALYSIS")
    log_lines.append("=" * 80)
    
    # Write log file
    log_content = "\n".join(log_lines)
    with open(log_file, 'w') as f:
        f.write(log_content)
    
    print(f"\nConvergence analysis written to: {log_file}")
    print("Log file contains detailed SE calculations and convergence check results.")
    
    # Also print summary to stdout
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results[:5]:  # Show first 5
        print(f"{r['dataset']} ({r['tier']}): SD={r['sd']:.4f}, SE={r['se_of_sd']:.4f} ({r['se_percent']:.1f}%)")
    if len(results) > 5:
        print(f"... and {len(results) - 5} more results")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())