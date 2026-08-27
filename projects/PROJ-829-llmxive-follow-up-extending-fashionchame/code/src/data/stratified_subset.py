import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

def load_filtered_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Loads the filtered subset manifest."""
    if not Path(manifest_path).exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)

def stratify_samples(samples: List[Dict[str, Any]], class_key: str = 'garment_class') -> Dict[str, List[Dict[str, Any]]]:
    """Stratifies samples by class."""
    stratified = defaultdict(list)
    for sample in samples:
        cls = sample.get(class_key, 'Unknown')
        stratified[cls].append(sample)
    return stratified

def validate_subset_balance(stratified: Dict[str, List[Dict[str, Any]]], min_count: int = 10) -> bool:
    """Validates that each class has enough samples."""
    for cls, samples in stratified.items():
        if len(samples) < min_count:
            print(f"Warning: Class {cls} has only {len(samples)} samples.")
            return False
    return True

def save_stratified_subset(stratified: Dict[str, List[Dict[str, Any]]], output_path: str) -> None:
    """Saves the stratified subset to a manifest."""
    manifest = {
        "stratified_by": "garment_class",
        "classes": {}
    }
    for cls, samples in stratified.items():
        manifest["classes"][cls] = [s.get('id') for s in samples]
        # Optionally save full sample data
        # manifest["classes"][cls] = samples

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Stratified subset saved to {output_path}")

def run_pipeline(input_manifest_path: str, output_manifest_path: str) -> None:
    """Runs the stratified subset pipeline."""
    samples = load_filtered_manifest(input_manifest_path)
    stratified = stratify_samples(samples)
    validate_subset_balance(stratified)
    save_stratified_subset(stratified, output_manifest_path)

def main():
    parser = argparse.ArgumentParser(description="Stratify Subset")
    parser.add_argument('--input', type=str, default='data/processed/filtered_subset_manifest.json')
    parser.add_argument('--output', type=str, default='data/processed/stratified_subset_manifest.json')
    args = parser.parse_args()

    run_pipeline(args.input, args.output)

if __name__ == '__main__':
    main()
