import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.hygiene import calculate_sha256, load_state, save_state, update_artifact_checksums

def load_json_safe(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file safely, raising an error if it doesn't exist or is invalid."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required artifact not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

def aggregate_trend_data() -> Dict[str, Any]:
    """
    Aggregate and finalize trend results by merging data from:
    - data/processed/trend_intermediate.json (T014)
    - data/processed/confidence_interval.json (T016)
    - data/processed/correlation_results.json (T040)
    
    Returns the merged dictionary.
    """
    processed_dir = project_root / "data" / "processed"
    
    # Define paths to upstream artifacts
    intermediate_path = processed_dir / "trend_intermediate.json"
    ci_path = processed_dir / "confidence_interval.json"
    correlation_path = processed_dir / "correlation_results.json"
    
    # Load upstream artifacts
    print(f"Loading {intermediate_path}...")
    intermediate_data = load_json_safe(intermediate_path)
    
    print(f"Loading {ci_path}...")
    ci_data = load_json_safe(ci_path)
    
    print(f"Loading {correlation_path}...")
    correlation_data = load_json_safe(correlation_path)
    
    # Initialize the final results structure
    final_results = {
        "metadata": {
            "source": "T018_Aggregation",
            "description": "Aggregated trend analysis results including Mann-Kendall tests, Theil-Sen slopes, confidence intervals, and external correlations."
        },
        "tags": []
    }
    
    # We assume the data is keyed by tag name or has a list of tags
    # Let's inspect the structure and merge accordingly
    # Expected structure for intermediate: { "tags": [ { "tag": "python", "slope": ..., "p_value": ..., ... }, ... ] }
    # Expected structure for ci: { "tags": [ { "tag": "python", "ci_lower": ..., "ci_upper": ... }, ... ] }
    # Expected structure for correlation: { "tags": [ { "tag": "python", "correlation": ..., "magnitude": ... }, ... ] }
    
    # Helper to find an entry by tag name
    def find_entry(tag_list, tag_name):
        for entry in tag_list:
            if entry.get("tag") == tag_name:
                return entry
        return None

    # Get the list of tags from the intermediate data (source of truth for trends)
    if "tags" not in intermediate_data:
        raise ValueError("trend_intermediate.json must contain a 'tags' list")
    
    trend_tags = intermediate_data["tags"]
    
    # Retrieve CI and Correlation data for lookup
    ci_tags_list = ci_data.get("tags", [])
    corr_tags_list = correlation_data.get("tags", [])
    
    # Merge data
    for trend_entry in trend_tags:
        tag_name = trend_entry.get("tag")
        if not tag_name:
            continue
        
        # Find corresponding CI and Correlation entries
        ci_entry = find_entry(ci_tags_list, tag_name)
        corr_entry = find_entry(corr_tags_list, tag_name)
        
        merged_entry = {
            "tag": tag_name,
            "trend_analysis": {
                "slope": trend_entry.get("slope"),
                "mann_kendall_statistic": trend_entry.get("mann_kendall_statistic"),
                "raw_p_value": trend_entry.get("raw_p_value"),
                "adjusted_p_value": trend_entry.get("adjusted_p_value"),
                "classification": trend_entry.get("classification"),
                "power": trend_entry.get("power"),
                "mdes": trend_entry.get("mdes")
            },
            "confidence_interval": {
                "lower_bound": ci_entry.get("ci_lower") if ci_entry else None,
                "upper_bound": ci_entry.get("ci_upper") if ci_entry else None,
                "confidence_level": 0.95,
                "method": "block_bootstrap"
            } if ci_entry else {
                "lower_bound": None,
                "upper_bound": None,
                "confidence_level": 0.95,
                "method": "block_bootstrap",
                "note": "No CI data available for this tag"
            },
            "external_correlation": {
                "correlation_coefficient": corr_entry.get("correlation") if corr_entry else None,
                "magnitude": corr_entry.get("magnitude") if corr_entry else None,
                "p_value": corr_entry.get("p_value") if corr_entry else None,
                "external_metrics_source": "GitHub/NPM"
            } if corr_entry else {
                "correlation_coefficient": None,
                "magnitude": None,
                "p_value": None,
                "external_metrics_source": "None",
                "note": "No correlation data available for this tag"
            }
        }
        
        final_results["tags"].append(merged_entry)
    
    # Add summary statistics if available in intermediate
    if "summary" in intermediate_data:
        final_results["summary"] = intermediate_data["summary"]
    
    return final_results

def update_state_file(final_results_path: Path, ci_path: Path):
    """
    Calculate SHA-256 hashes for the final results and CI files,
    and update the state file.
    """
    state_path = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
    
    if not state_path.exists():
        print(f"Warning: State file not found at {state_path}. Creating new state file.")
        # Initialize a basic state if it doesn't exist (though T009 should have done this)
        state_data = {"artifacts": {}}
    else:
        state_data = load_state(state_path)
    
    # Calculate hashes
    final_hash = calculate_sha256(final_results_path)
    ci_hash = calculate_sha256(ci_path)
    
    # Update checksums
    updated_state = update_artifact_checksums(
        state_data, 
        {
            str(final_results_path.relative_to(project_root)): final_hash,
            str(ci_path.relative_to(project_root)): ci_hash
        }
    )
    
    # Save updated state
    save_state(updated_state, state_path)
    print(f"State file updated at {state_path}")

def main():
    """Main entry point for T018: Aggregate and finalize trend results."""
    print("Starting T018: Aggregate and finalize trend results...")
    
    processed_dir = project_root / "data" / "processed"
    output_path = processed_dir / "trend_results.json"
    ci_path = processed_dir / "confidence_interval.json"
    
    # Verify upstream artifacts exist (redundant with load_json_safe but explicit)
    required_files = [
        processed_dir / "trend_intermediate.json",
        ci_path,
        processed_dir / "correlation_results.json"
    ]
    
    for f in required_files:
        if not f.exists():
            print(f"ERROR: Required upstream artifact missing: {f}")
            print("T018 cannot proceed. Please ensure T014, T016, and T040 have completed successfully.")
            sys.exit(1)
    
    try:
        # Aggregate data
        final_results = aggregate_trend_data()
        
        # Write final results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"Successfully wrote aggregated results to {output_path}")
        
        # Update state file with checksums
        update_state_file(output_path, ci_path)
        
        print("T018 completed successfully.")
        return 0
        
    except Exception as e:
        print(f"ERROR during T018 execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
