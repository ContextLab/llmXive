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
        # Handle both 'GarmentFeatureClass' (from spec) and 'garment_class' (from data)
        cls = sample.get('GarmentFeatureClass') or sample.get(class_key, 'Unknown')
        stratified[cls].append(sample)
    return stratified

def validate_subset_balance(stratified: Dict[str, List[Dict[str, Any]]], min_count: int = 10) -> bool:
    """Validates that each class has enough samples."""
    valid = True
    for cls, samples in stratified.items():
        if len(samples) < min_count:
            print(f"Warning: Class {cls} has only {len(samples)} samples.")
            valid = False
    return valid

def save_stratified_subset(stratified: Dict[str, List[Dict[str, Any]]], output_path: str) -> None:
    """Saves the stratified subset to a manifest.
    
    This artifact MUST list samples grouped by GarmentFeatureClass to satisfy 
    Constitution Principle VI.
    """
    manifest = {
        "stratified_by": "GarmentFeatureClass",
        "total_samples": sum(len(v) for v in stratified.values()),
        "classes": {}
    }
    
    for cls, samples in stratified.items():
        # Extract sample IDs and key metadata for the manifest
        # We store the full sample data to ensure downstream tasks have access
        # to optical_flow_magnitude and other attributes without re-loading
        manifest["classes"][cls] = {
            "count": len(samples),
            "sample_ids": [s.get('id', s.get('sample_id')) for s in samples],
            "samples": samples  # Store full sample objects for downstream use
        }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Stratified subset saved to {output_path}")
    print(f"Classes: {list(manifest['classes'].keys())}")
    for cls, data in manifest["classes"].items():
        print(f"  {cls}: {data['count']} samples")

def run_pipeline(input_manifest_path: str, output_manifest_path: str) -> None:
    """Runs the stratified subset pipeline.
    
    1. Loads the filtered subset manifest (from T021-redo).
    2. Stratifies samples by GarmentFeatureClass.
    3. Validates balance (warns if < 10 per class).
    4. Saves the stratified manifest to disk.
    """
    print(f"Loading filtered manifest from {input_manifest_path}...")
    samples = load_filtered_manifest(input_manifest_path)
    print(f"Loaded {len(samples)} samples.")
    
    print("Stratifying by GarmentFeatureClass...")
    stratified = stratify_samples(samples)
    
    print("Validating subset balance...")
    is_balanced = validate_subset_balance(stratified)
    
    if not is_balanced:
        print("Warning: Subset is imbalanced. Proceeding anyway.")
    
    print(f"Saving stratified manifest to {output_manifest_path}...")
    save_stratified_subset(stratified, output_manifest_path)
    print("Pipeline complete.")

def main():
    parser = argparse.ArgumentParser(description="Stratify Subset for Benchmark")
    parser.add_argument('--input', type=str, 
                        default='data/processed/filtered_subset_manifest.json',
                        help='Path to filtered subset manifest')
    parser.add_argument('--output', type=str, 
                        default='data/processed/stratified_subset_manifest.json',
                        help='Path to output stratified manifest')
    args = parser.parse_args()

    run_pipeline(args.input, args.output)

if __name__ == '__main__':
    main()
