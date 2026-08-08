import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import hygiene utilities for SHA-256 and state management
from utils.hygiene import calculate_sha256, load_state, save_state, update_artifact_checksums

# Project root relative to this script (assuming code/analysis/generate_trend_results.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        print(f"Error: Required file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def aggregate_trend_data() -> Dict[str, Any]:
    """
    Aggregate data from intermediate trend files into the final trend_results.json.
    
    Sources:
    - data/processed/trend_intermediate.json (from T014)
    - data/processed/confidence_interval.json (from T016)
    - data/processed/correlation_results.json (from T040)
    
    Returns:
        Dictionary containing the merged results.
    """
    # Define paths
    intermediate_path = DATA_PROCESSED_DIR / "trend_intermediate.json"
    ci_path = DATA_PROCESSED_DIR / "confidence_interval.json"
    corr_path = DATA_PROCESSED_DIR / "correlation_results.json"
    
    # Load upstream artifacts
    intermediate_data = load_json_safe(intermediate_path)
    ci_data = load_json_safe(ci_path)
    corr_data = load_json_safe(corr_path)
    
    # Verify all upstream artifacts exist
    if intermediate_data is None:
        raise FileNotFoundError(f"Upstream artifact missing: {intermediate_path}")
    if ci_data is None:
        raise FileNotFoundError(f"Upstream artifact missing: {ci_path}")
    if corr_data is None:
        raise FileNotFoundError(f"Upstream artifact missing: {corr_path}")
    
    # Merge data structures
    # Assuming all sources use a common key (e.g., 'tags' or 'results') or are list-based dicts
    # We will merge by tag name if possible, or simply combine top-level keys if structure allows.
    # Based on typical analysis outputs, we expect a list of tag results or a dict keyed by tag.
    
    final_results = {
        "metadata": {
            "generated_by": "T018_Aggregation",
            "source_files": [
                str(intermediate_path.relative_to(PROJECT_ROOT)),
                str(ci_path.relative_to(PROJECT_ROOT)),
                str(corr_path.relative_to(PROJECT_ROOT))
            ],
            "description": "Aggregated trend analysis results including Mann-Kendall statistics, Theil-Sen slopes, confidence intervals, and external correlation metrics."
        },
        "results": []
    }
    
    # Helper to find tag index by name in a list of dicts
    def find_tag_index(tag_list, tag_name):
        for i, item in enumerate(tag_list):
            if isinstance(item, dict) and item.get("tag_name") == tag_name:
                return i
        return -1

    # Process intermediate data (likely the primary structure)
    if isinstance(intermediate_data, list):
        final_results["results"] = list(intermediate_data)
    elif isinstance(intermediate_data, dict) and "results" in intermediate_data:
        final_results["results"] = intermediate_data["results"]
    else:
        # Fallback: treat as single result or error
        final_results["results"] = [intermediate_data] if isinstance(intermediate_data, dict) else []

    # Merge Confidence Intervals
    ci_entries = ci_data.get("results", []) if isinstance(ci_data, dict) else (ci_data if isinstance(ci_data, list) else [])
    for ci_entry in ci_entries:
        tag_name = ci_entry.get("tag_name")
        if not tag_name:
            continue
        idx = find_tag_index(final_results["results"], tag_name)
        if idx != -1:
            final_results["results"][idx]["confidence_interval"] = {
                "lower_bound": ci_entry.get("lower_bound"),
                "upper_bound": ci_entry.get("upper_bound"),
                "confidence_level": ci_entry.get("confidence_level", 0.95)
            }
        else:
            # If tag exists in CI but not in main results, add it
            final_results["results"].append({
                "tag_name": tag_name,
                "confidence_interval": {
                    "lower_bound": ci_entry.get("lower_bound"),
                    "upper_bound": ci_entry.get("upper_bound"),
                    "confidence_level": ci_entry.get("confidence_level", 0.95)
                }
            })

    # Merge Correlation Results
    corr_entries = corr_data.get("results", []) if isinstance(corr_data, dict) else (corr_data if isinstance(corr_data, list) else [])
    for corr_entry in corr_entries:
        tag_name = corr_entry.get("tag_name")
        if not tag_name:
            continue
        idx = find_tag_index(final_results["results"], tag_name)
        if idx != -1:
            final_results["results"][idx]["correlation"] = {
                "external_metric_source": corr_entry.get("source"),
                "correlation_coefficient": corr_entry.get("coefficient"),
                "magnitude_interpretation": corr_entry.get("magnitude"),
                "p_value": corr_entry.get("p_value")
            }
        else:
            final_results["results"].append({
                "tag_name": tag_name,
                "correlation": {
                    "external_metric_source": corr_entry.get("source"),
                    "correlation_coefficient": corr_entry.get("coefficient"),
                    "magnitude_interpretation": corr_entry.get("magnitude"),
                    "p_value": corr_entry.get("p_value")
                }
            })

    return final_results

def update_state_file(artifact_path: Path, state_path: Path):
    """
    Calculate SHA-256 hash for the artifact and update the project state file.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found for hashing: {artifact_path}")
    
    file_hash = calculate_sha256(artifact_path)
    
    # Load state
    state = load_state(state_path)
    
    # Update checksums
    update_artifact_checksums(state, str(artifact_path.relative_to(PROJECT_ROOT)), file_hash)
    
    # Save state
    save_state(state, state_path)
    print(f"State file updated: {state_path}")
    print(f"  Artifact: {artifact_path.name} -> SHA-256: {file_hash}")

def main():
    """Main entry point for T018: Aggregate and finalize trend results."""
    print("Starting T018: Aggregating Trend Results...")
    
    try:
        # 1. Aggregate data
        aggregated_data = aggregate_trend_data()
        
        # 2. Define output path
        output_path = DATA_PROCESSED_DIR / "trend_results.json"
        
        # 3. Write final JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(aggregated_data, f, indent=2, default=str)
        
        print(f"Successfully wrote aggregated results to: {output_path}")
        
        # 4. Update state file (FR-012)
        update_state_file(output_path, STATE_FILE)
        
        # 5. Also update CI file hash if it exists (FR-012 requirement mentions both)
        ci_path = DATA_PROCESSED_DIR / "confidence_interval.json"
        if ci_path.exists():
            update_state_file(ci_path, STATE_FILE)
        
        print("T018 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        print(f"Critical Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error during aggregation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
