"""
Generate trend_results.json by aggregating trend, CI, and correlation data.
Calculate SHA-256 hashes and update state file per FR-012.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from utils.state_manager import calculate_sha256, load_state, save_state, update_artifact_checksums

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if not found or invalid."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required artifact not found: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

def aggregate_trend_data(
    trend_results_path: Path,
    ci_results_path: Path,
    correlation_results_path: Path
) -> Dict[str, Any]:
    """
    Aggregate trend, confidence interval, and correlation data into a single result.
    Merges data by tag name.
    """
    # Load source files
    trends = load_json_safe(trend_results_path)
    cis = load_json_safe(ci_results_path)
    correlations = load_json_safe(correlation_results_path)

    # Ensure structure is a list of records
    if not isinstance(trends, list):
        raise ValueError(f"Expected list in {trend_results_path}, got {type(trends)}")
    
    # Index CI and Correlation data by tag for easy merging
    ci_map = {item['tag']: item for item in cis.get('results', []) if 'tag' in item}
    corr_map = {item['tag']: item for item in correlations.get('results', []) if 'tag' in item}

    aggregated_results = []

    for trend_record in trends:
        tag = trend_record.get('tag')
        if not tag:
            continue

        # Start with trend data
        merged_record = dict(trend_record)

        # Add CI data if available
        if tag in ci_map:
            merged_record['confidence_interval'] = ci_map[tag]
        else:
            merged_record['confidence_interval'] = None

        # Add Correlation data if available
        if tag in corr_map:
            merged_record['correlation'] = corr_map[tag]
        else:
            merged_record['correlation'] = None

        aggregated_results.append(merged_record)

    return {
        "metadata": {
            "generated_at": trends[0].get('metadata', {}).get('generated_at', 'unknown') if trends else 'unknown',
            "source_files": {
                "trends": str(trend_results_path),
                "confidence_intervals": str(ci_results_path),
                "correlations": str(correlation_results_path)
            }
        },
        "results": aggregated_results
    }

def update_state_file(
    state_path: Path,
    trend_results_path: Path,
    ci_results_path: Path,
    new_results_path: Path
) -> None:
    """
    Calculate SHA-256 hashes for trend_results.json and confidence_interval.json,
    and update the project state file per FR-012.
    """
    # Calculate hashes for the newly generated file and the CI file
    hashes = {
        "trend_results.json": calculate_sha256(new_results_path),
        "confidence_interval.json": calculate_sha256(ci_results_path)
    }

    # Load existing state
    state = load_state(state_path)

    # Update checksums
    update_artifact_checksums(state, hashes)

    # Save updated state
    save_state(state_path, state)
    print(f"State file updated at {state_path}")

def main():
    """Main entry point for generating trend results."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data" / "processed"
    state_path = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

    # Input files (produced by T014, T016, T040)
    trend_results_path = data_dir / "trend_analysis_output.json" # Assuming T014 output name based on context
    ci_results_path = data_dir / "confidence_interval.json"     # Explicitly mentioned in task
    correlation_results_path = data_dir / "correlation_results.json" # Assuming T040 output name

    # Output file
    output_path = data_dir / "trend_results.json"

    print(f"Starting aggregation of trend data...")
    print(f"  Trends: {trend_results_path}")
    print(f"  CI: {ci_results_path}")
    print(f"  Correlations: {correlation_results_path}")

    # Validate inputs exist (fail loudly)
    if not trend_results_path.exists():
        raise FileNotFoundError(f"Missing required input: {trend_results_path}. Ensure T014 has run.")
    if not ci_results_path.exists():
        raise FileNotFoundError(f"Missing required input: {ci_results_path}. Ensure T016 has run.")
    if not correlation_results_path.exists():
        raise FileNotFoundError(f"Missing required input: {correlation_results_path}. Ensure T040 has run.")

    # Aggregate
    final_data = aggregate_trend_data(trend_results_path, ci_results_path, correlation_results_path)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2)
    
    print(f"Aggregated results saved to {output_path}")

    # Update state
    if state_path.exists():
        update_state_file(state_path, trend_results_path, ci_results_path, output_path)
    else:
        print(f"Warning: State file not found at {state_path}. Skipping state update.")

if __name__ == "__main__":
    main()
