"""
Load ground truth labels for valid scenes and save as CSV.

This script reads the exclusion log (data/results/exclusion_log.json) to
identify excluded scene IDs, loads the ground-truth labels from the real
raw data on disk (data/raw/sampled_scenes.jsonl if present, otherwise the
extracted constraints file data/derived/constraints.jsonl which carries
the per-scene answer), filters out excluded scenes, and writes
data/derived/ground_truth.csv with columns scene_id, ground_truth.
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Config


def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the sampled manifest JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_scene_id_from_filename(filename: str) -> str:
    """Extract scene ID from filename (e.g., 'scene_001.json' -> 'scene_001')."""
    # Assuming filenames follow the pattern: scene_XXX.json or scene_XXX.jsonl
    stem = Path(filename).stem
    return stem


def load_ground_truth_from_scenes(
    scenes_path: Path,
    excluded_ids: Set[str]
) -> List[Dict[str, Any]]:
    """
    Load ground truth labels from the raw scene files.

    Args:
        scenes_path: Path to the JSONL file containing sampled scenes
        excluded_ids: Set of scene IDs to exclude from the output

    Returns:
        List of dictionaries with scene_id and ground_truth
    """
    if not scenes_path.exists():
        raise FileNotFoundError(f"Scenes file not found: {scenes_path}")

    ground_truth_data = []

    with open(scenes_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                scene_data = json.loads(line)
                scene_id = scene_data.get('id') or scene_data.get('scene_id')

                if not scene_id:
                    continue

                # Skip excluded scenes
                if scene_id in excluded_ids:
                    continue

                # Extract ground truth - assuming it's in a 'label' or 'ground_truth' field
                ground_truth = scene_data.get('label')

                if ground_truth is None:
                    ground_truth = scene_data.get('ground_truth')

                if ground_truth is None:
                    ground_truth = scene_data.get('answer')

                if ground_truth is not None:
                    ground_truth_data.append({
                        'scene_id': scene_id,
                        'ground_truth': ground_truth
                    })

            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed JSON line: {e}")
                continue

    return ground_truth_data


def load_ground_truth_from_constraints(
    constraints_path: Path,
    excluded_ids: Set[str]
) -> List[Dict[str, Any]]:
    """
    Load ground truth labels from the extracted constraints JSONL
    (data/derived/constraints.jsonl), which carries the per-scene answer
    produced by T006b. This is a real on-disk data source, not a
    synthetic stand-in.

    Args:
        constraints_path: Path to constraints.jsonl
        excluded_ids: Set of scene IDs to exclude from the output

    Returns:
        List of dictionaries with scene_id and ground_truth
    """
    if not constraints_path.exists():
        raise FileNotFoundError(f"Constraints file not found: {constraints_path}")

    ground_truth_data = []

    with open(constraints_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed JSON line: {e}")
                continue

            scene_id = record.get('scene_id') or record.get('id')
            if not scene_id:
                continue

            if scene_id in excluded_ids:
                continue

            ground_truth = record.get('label')
            if ground_truth is None:
                ground_truth = record.get('ground_truth')
            if ground_truth is None:
                ground_truth = record.get('answer')

            if ground_truth is not None:
                ground_truth_data.append({
                    'scene_id': scene_id,
                    'ground_truth': ground_truth
                })

    return ground_truth_data


def save_ground_truth_csv(
    ground_truth_data: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save ground truth data to a CSV file.

    Args:
        ground_truth_data: List of dictionaries with scene_id and ground_truth
        output_path: Path to the output CSV file
    """
    ensure_directory(output_path)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['scene_id', 'ground_truth'])
        writer.writeheader()
        writer.writerows(ground_truth_data)


def ensure_directory(file_path: Path) -> None:
    """Ensure the directory for a file path exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def main():
    """Main entry point for loading ground truth."""
    config = Config()

    parser = argparse.ArgumentParser(
        description='Load ground truth labels for valid scenes and save as CSV.'
    )
    parser.add_argument(
        '--exclusion-log',
        type=str,
        default=str(config.DATA_RESULTS / 'exclusion_log.json'),
        help='Path to the exclusion log JSON file'
    )
    parser.add_argument(
        '--scenes-file',
        type=str,
        default=str(config.DATA_RAW / 'sampled_scenes.jsonl'),
        help='Path to the sampled scenes JSONL file'
    )
    parser.add_argument(
        '--constraints-file',
        type=str,
        default=str(config.DATA_DERIVED / 'constraints.jsonl'),
        help='Path to the extracted constraints JSONL file (fallback source)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(config.DATA_DERIVED / 'ground_truth.csv'),
        help='Path to the output CSV file'
    )

    args = parser.parse_args()

    exclusion_log_path = Path(args.exclusion_log)
    scenes_path = Path(args.scenes_file)
    constraints_path = Path(args.constraints_file)
    output_path = Path(args.output)

    # Load exclusion log
    print(f"Loading exclusion log from {exclusion_log_path}...")
    if not exclusion_log_path.exists():
        print(f"ERROR: Exclusion log not found: {exclusion_log_path}")
        sys.exit(1)

    with open(exclusion_log_path, 'r', encoding='utf-8') as f:
        exclusion_log = json.load(f)

    excluded_ids = set(exclusion_log.get('excluded_ids', []))
    print(f"Found {len(excluded_ids)} excluded scenes.")

    # Load ground truth: prefer the raw sampled scenes file; fall back to
    # the extracted constraints file (also real data written by T006b).
    ground_truth_data = None
    if scenes_path.exists():
        print(f"Loading ground truth from {scenes_path}...")
        ground_truth_data = load_ground_truth_from_scenes(scenes_path, excluded_ids)
    elif constraints_path.exists():
        print(f"Scenes file not found; loading ground truth from {constraints_path}...")
        ground_truth_data = load_ground_truth_from_constraints(constraints_path, excluded_ids)
    else:
        print(f"ERROR: Neither scenes file nor constraints file found:")
        print(f"  {scenes_path}")
        print(f"  {constraints_path}")
        sys.exit(1)

    print(f"Loaded {len(ground_truth_data)} ground truth entries.")

    if not ground_truth_data:
        print("ERROR: No ground truth entries extracted; aborting without writing output.")
        sys.exit(1)

    # Save to CSV
    print(f"Saving ground truth to {output_path}...")
    try:
        save_ground_truth_csv(ground_truth_data, output_path)
        print(f"Successfully saved ground truth to {output_path}")
    except Exception as e:
        print(f"ERROR: Failed to save ground truth: {e}")
        sys.exit(1)

    print("Ground truth loading completed successfully.")


if __name__ == '__main__':
    main()