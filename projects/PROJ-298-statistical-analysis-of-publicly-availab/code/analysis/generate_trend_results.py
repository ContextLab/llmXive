import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

from utils.state_manager import calculate_sha256, load_state, save_state, update_artifact_checksums

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return None

def aggregate_trend_data() -> Dict[str, Any]:
    """
    Aggregates trend analysis, confidence intervals, and correlation data
    into a single trend_results.json structure.
    """
    trend_data_path = DATA_PROCESSED_DIR / "trend_analysis.json"
    ci_data_path = DATA_PROCESSED_DIR / "confidence_interval.json"
    correlation_data_path = DATA_PROCESSED_DIR / "correlation_results.json"

    # Load individual components
    trend_data = load_json_safe(trend_data_path) or {}
    ci_data = load_json_safe(ci_data_path) or {}
    correlation_data = load_json_safe(correlation_data_path) or {}

    # Structure the aggregated result
    aggregated = {
        "metadata": {
            "source_files": {
                "trend_analysis": str(trend_data_path),
                "confidence_intervals": str(ci_data_path),
                "correlation_results": str(correlation_data_path)
            },
            "generated_at": None, # Will be set by the runner if needed, or left to pipeline
            "version": "1.0.0"
        },
        "results": []
    }

    # Merge data by tag
    # Assume trend_data has a list of tags or a dict keyed by tag
    # Based on typical pipeline outputs: trend_data might be a dict {tag: {stats}}
    # We need to align keys from all three sources.

    all_tags = set(trend_data.keys()) | set(ci_data.keys()) | set(correlation_data.keys())

    for tag in sorted(all_tags):
        tag_result = {
            "tag": tag,
            "trend": trend_data.get(tag, {}),
            "confidence_interval": ci_data.get(tag, {}),
            "correlation": correlation_data.get(tag, {})
        }
        aggregated["results"].append(tag_result)

    return aggregated

def update_state_file(artifacts: Dict[str, str]) -> None:
    """
    Calculates SHA-256 hashes for the generated files and updates the state file.
    """
    state = load_state(STATE_FILE_PATH)
    if not state:
        state = {
            "project": "PROJ-298-statistical-analysis-of-publicly-availab",
            "artifacts": {},
            "last_updated": None
        }

    updated_checksums = {}
    for artifact_name, file_path_str in artifacts.items():
        file_path = Path(file_path_str)
        if file_path.exists():
            checksum = calculate_sha256(file_path)
            updated_checksums[artifact_name] = {
                "path": str(file_path),
                "sha256": checksum
            }
            print(f"Calculated SHA-256 for {artifact_name}: {checksum}")
        else:
            print(f"Warning: Artifact file not found for state update: {file_path}")

    # Update the state dictionary
    state["artifacts"].update(updated_checksums)
    state["last_updated"] = "generated_by_T018" # Placeholder for actual timestamp logic if needed

    save_state(state, STATE_FILE_PATH)
    print(f"State file updated at {STATE_FILE_PATH}")

def main():
    """
    Main entry point for T018:
    1. Aggregate trend, CI, and correlation data.
    2. Save to data/processed/trend_results.json.
    3. Calculate SHA-256 for trend_results.json and confidence_interval.json.
    4. Update state file.
    """
    print("Starting T018: Generate trend_results.json and update state.")

    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Aggregate Data
    print("Aggregating data from trend_analysis.json, confidence_interval.json, and correlation_results.json...")
    aggregated_data = aggregate_trend_data()

    output_path = DATA_PROCESSED_DIR / "trend_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated_data, f, indent=2)
    print(f"Saved aggregated results to {output_path}")

    # 2. Calculate Hashes and Update State
    artifacts_to_hash = {
        "trend_results.json": str(output_path),
        "confidence_interval.json": str(DATA_PROCESSED_DIR / "confidence_interval.json")
    }

    update_state_file(artifacts_to_hash)

    print("T018 completed successfully.")

if __name__ == "__main__":
    main()