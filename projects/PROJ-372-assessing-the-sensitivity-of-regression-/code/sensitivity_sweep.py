"""
Sensitivity Sweep Logic for Breusch-Pagan p-value cutoffs.

This module implements the logic to sweep through conventional significance
thresholds for the Breusch-Pagan test, re-classify datasets based on
violation severity, and compute the variance in classification rates.

Output: artifacts/meta_analysis/sensitivity_sweep.json
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import math

# Constants for output paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
PROFILES_DIR = ARTIFACTS_DIR / "profiles"
META_ANALYSIS_DIR = ARTIFACTS_DIR / "meta_analysis"
OUTPUT_FILE = META_ANALYSIS_DIR / "sensitivity_sweep.json"

# Conventional significance thresholds for Breusch-Pagan test
# These represent standard cutoffs used in statistical practice
BP_PVALUE_CUTOFFS = [0.01, 0.05, 0.10, 0.20]

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_profiles() -> List[Dict[str, Any]]:
    """
    Load all dataset profile JSON files from artifacts/profiles.
    
    Returns:
        List of profile dictionaries containing dataset metadata and violation stats.
    """
    if not PROFILES_DIR.exists():
        raise FileNotFoundError(f"Profiles directory not found: {PROFILES_DIR}")
    
    profiles = []
    for json_file in PROFILES_DIR.glob("*.json"):
        try:
            profile = load_json_file(json_file)
            # Validate required fields exist
            if 'breusch_pagan_pvalue' in profile and 'breusch_pagan_stat' in profile:
                profiles.append(profile)
            else:
                print(f"Warning: Skipping {json_file} - missing required fields")
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    return profiles

def classify_violation_severity(bp_pvalue: float, bp_stat: float, condition_number: float, cutoff: float) -> str:
    """
    Classify violation severity based on BP p-value and other metrics.
    
    Severity classification logic:
    - High: BP p-value < cutoff (significant heteroscedasticity) OR condition_number > 30
    - Medium: BP p-value >= cutoff but BP stat is moderately elevated
    - Low: No significant violations detected
    
    Args:
        bp_pvalue: Breusch-Pagan test p-value
        bp_stat: Breusch-Pagan test statistic
        condition_number: Condition number of the design matrix
        cutoff: P-value cutoff for significance testing
    
    Returns:
        Severity classification string: 'High', 'Medium', or 'Low'
    """
    # Check for multicollinearity first
    if condition_number > 30:
        return "High"
    
    # Check for significant heteroscedasticity
    if bp_pvalue < cutoff:
        return "High"
    
    # Check for moderate violations (using heuristic thresholds)
    # If p-value is close to cutoff or BP stat is elevated but not significant
    if bp_pvalue < cutoff * 2 and bp_stat > 1.0:
        return "Medium"
    
    return "Low"

def run_sensitivity_sweep(profiles: List[Dict[str, Any]], cutoffs: List[float]) -> Dict[str, Any]:
    """
    Perform sensitivity sweep across different BP p-value cutoffs.
    
    For each cutoff, re-classify all datasets and compute:
    - Count of datasets in each severity category
    - Classification rate (proportion) for each category
    - Variance in classification rates across cutoffs
    
    Args:
        profiles: List of dataset profiles
        cutoffs: List of p-value cutoffs to sweep through
    
    Returns:
        Dictionary containing sweep results and variance metrics
    """
    results = {
        "sweep_parameters": {
            "cutoffs": cutoffs,
            "total_datasets": len(profiles)
        },
        "classification_counts": {},
        "classification_rates": {},
        "per_cutoff_details": []
    }
    
    # Initialize counters for each severity level
    severity_levels = ["High", "Medium", "Low"]
    
    for cutoff in cutoffs:
        counts = {level: 0 for level in severity_levels}
        details = []
        
        for profile in profiles:
            bp_pvalue = profile.get('breusch_pagan_pvalue', 1.0)
            bp_stat = profile.get('breusch_pagan_stat', 0.0)
            condition_number = profile.get('condition_number', 1.0)
            
            severity = classify_violation_severity(bp_pvalue, bp_stat, condition_number, cutoff)
            counts[severity] += 1
            
            details.append({
                "dataset_id": profile.get('dataset_id', 'unknown'),
                "bp_pvalue": bp_pvalue,
                "bp_stat": bp_stat,
                "condition_number": condition_number,
                "severity_at_cutoff": severity
            })
        
        # Calculate rates
        total = len(profiles) if profiles else 1  # Avoid division by zero
        rates = {level: count / total for level, count in counts.items()}
        
        results["classification_counts"][f"cutoff_{cutoff}"] = counts
        results["classification_rates"][f"cutoff_{cutoff}"] = rates
        results["per_cutoff_details"].append({
            "cutoff": cutoff,
            "counts": counts,
            "rates": rates,
            "details": details
        })
    
    # Calculate variance in classification rates across cutoffs
    variance_analysis = {}
    for level in severity_levels:
        rates_across_cutoffs = [
            results["classification_rates"][f"cutoff_{c}"][level] 
            for c in cutoffs
        ]
        
        if len(rates_across_cutoffs) > 1:
            mean_rate = sum(rates_across_cutoffs) / len(rates_across_cutoffs)
            variance = sum((r - mean_rate) ** 2 for r in rates_across_cutoffs) / len(rates_across_cutoffs)
            std_dev = math.sqrt(variance)
        else:
            variance = 0.0
            std_dev = 0.0
            mean_rate = rates_across_cutoffs[0] if rates_across_cutoffs else 0.0
        
        variance_analysis[level] = {
            "mean_rate": mean_rate,
            "variance": variance,
            "std_dev": std_dev,
            "rates_across_cutoffs": dict(zip([f"cutoff_{c}" for c in cutoffs], rates_across_cutoffs))
        }
    
    results["variance_analysis"] = variance_analysis
    
    return results

def main():
    """Main entry point for sensitivity sweep analysis."""
    parser = argparse.ArgumentParser(
        description="Perform sensitivity sweep on Breusch-Pagan p-value cutoffs"
    )
    parser.add_argument(
        "--cutoffs",
        type=str,
        default=",".join(map(str, BP_PVALUE_CUTOFFS)),
        help="Comma-separated list of p-value cutoffs to sweep (default: 0.01,0.05,0.10,0.20)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help="Output file path for sweep results"
    )
    
    args = parser.parse_args()
    
    # Parse cutoffs
    cutoffs = [float(c.strip()) for c in args.cutoffs.split(",")]
    cutoffs = sorted(cutoffs)  # Ensure sorted order
    
    print(f"Loading dataset profiles from {PROFILES_DIR}...")
    profiles = load_profiles()
    
    if not profiles:
        print("Error: No valid dataset profiles found. Cannot perform sensitivity sweep.")
        sys.exit(1)
    
    print(f"Loaded {len(profiles)} dataset profiles.")
    print(f"Performing sensitivity sweep across {len(cutoffs)} cutoffs: {cutoffs}")
    
    # Run the sensitivity sweep
    results = run_sensitivity_sweep(profiles, cutoffs)
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Sensitivity sweep results written to {output_path}")
    
    # Print summary
    print("\n=== Sensitivity Sweep Summary ===")
    print(f"Total datasets analyzed: {results['sweep_parameters']['total_datasets']}")
    print(f"Cutoffs tested: {cutoffs}")
    print("\nVariance in classification rates across cutoffs:")
    for level, stats in results['variance_analysis'].items():
        print(f"  {level}: mean={stats['mean_rate']:.3f}, std_dev={stats['std_dev']:.3f}")

if __name__ == "__main__":
    main()