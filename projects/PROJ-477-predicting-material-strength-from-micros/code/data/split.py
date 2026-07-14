"""
Data Splitter for Material Strength Prediction Project.

Implements stratified splitting of the dataset into train/validation/test sets
based on yield strength bins to ensure balanced distribution across splits.
Generates manifest files mapping image IDs to splits and labels.
"""
import os
import csv
import logging
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Import from project utils
from utils.config import get_project_root, get_data_dir, get_processed_dir, get_results_dir, set_seed, get_seed
from utils.logging_config import get_logger

# Constants
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15
RANDOM_STATE = 42
NUM_BINS = 10  # Number of bins for stratification

def setup_logging() -> logging.Logger:
    """Setup logging for the splitter module."""
    return get_logger("splitter", "split")

def load_processed_manifest(manifest_path: Path) -> List[Dict]:
    """
    Load the processed manifest containing image IDs and labels.

    Args:
        manifest_path: Path to the manifest CSV/JSON file.

    Returns:
        List of dictionaries containing image metadata.
    """
    logger = logging.getLogger("splitter")
    samples = []

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    # Try loading as CSV first, then JSON
    if manifest_path.suffix.lower() == '.csv':
        with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append(row)
    elif manifest_path.suffix.lower() == '.json':
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                samples = data
            elif isinstance(data, dict) and 'samples' in data:
                samples = data['samples']
    else:
        raise ValueError(f"Unsupported manifest format: {manifest_path.suffix}")

    logger.info(f"Loaded {len(samples)} samples from {manifest_path}")
    return samples

def binarize_labels_for_stratification(
    samples: List[Dict],
    label_field: str = "yield_strength_mpa",
    num_bins: int = NUM_BINS
) -> List[Tuple[Dict, int]]:
    """
    Bin continuous labels for stratified splitting.

    Args:
        samples: List of sample dictionaries.
        label_field: Field name containing the label.
        num_bins: Number of bins to create.

    Returns:
        List of tuples (sample, bin_index).
    """
    logger = logging.getLogger("splitter")

    # Extract labels
    labels = []
    valid_samples = []
    for sample in samples:
        if label_field in sample:
            try:
                val = float(sample[label_field])
                if not (val == val):  # NaN check
                    logger.warning(f"NaN label found for {sample.get('image_id', 'unknown')}, skipping")
                    continue
                labels.append(val)
                valid_samples.append(sample)
            except (ValueError, TypeError):
                logger.warning(f"Invalid label '{sample[label_field]}' for {sample.get('image_id', 'unknown')}, skipping")

    if not labels:
        raise ValueError("No valid labels found for stratification")

    # Create bins
    min_val, max_val = min(labels), max(labels)
    if min_val == max_val:
        # All same value, assign all to bin 0
        bins = [0] * len(valid_samples)
    else:
        bin_width = (max_val - min_val) / num_bins
        bins = []
        for sample in valid_samples:
            val = float(sample[label_field])
            bin_idx = min(int((val - min_val) / bin_width), num_bins - 1)
            bins.append(bin_idx)

    logger.info(f"Created {num_bins} bins from label range [{min_val:.2f}, {max_val:.2f}]")

    return list(zip(valid_samples, bins))

def stratified_split(
    samples_with_bins: List[Tuple[Dict, int]],
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
    test_ratio: float = TEST_RATIO,
    random_state: int = RANDOM_STATE
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Perform stratified split on samples based on binned labels.

    Args:
        samples_with_bins: List of (sample, bin_index) tuples.
        train_ratio: Proportion for training set.
        val_ratio: Proportion for validation set.
        test_ratio: Proportion for test set.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (train_samples, val_samples, test_samples).
    """
    logger = logging.getLogger("splitter")
    set_seed(random_state)

    # Group by bin
    bin_groups = defaultdict(list)
    for sample, bin_idx in samples_with_bins:
        bin_groups[bin_idx].append(sample)

    train_samples = []
    val_samples = []
    test_samples = []

    # Split within each bin
    for bin_idx, group_samples in bin_groups.items():
        random.shuffle(group_samples)
        n = len(group_samples)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        n_test = n - n_train - n_val  # Remainder to test

        train_samples.extend(group_samples[:n_train])
        val_samples.extend(group_samples[n_train:n_train + n_val])
        test_samples.extend(group_samples[n_train + n_val:])

    # Shuffle final sets
    random.shuffle(train_samples)
    random.shuffle(val_samples)
    random.shuffle(test_samples)

    logger.info(f"Split complete: Train={len(train_samples)}, Val={len(val_samples)}, Test={len(test_samples)}")

    # Verify ratios
    total = len(train_samples) + len(val_samples) + len(test_samples)
    logger.info(f"Ratios: Train={len(train_samples)/total:.2%}, Val={len(val_samples)/total:.2%}, Test={len(test_samples)/total:.2%}")

    return train_samples, val_samples, test_samples

def write_manifest(
    samples: List[Dict],
    split_name: str,
    output_path: Path,
    label_field: str = "yield_strength_mpa"
) -> None:
    """
    Write a split manifest to CSV.

    Args:
        samples: List of sample dictionaries.
        split_name: Name of the split (train/val/test).
        output_path: Path to write the manifest.
        label_field: Field name for the label.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['image_id', 'split', label_field, 'filename']
    if label_field not in samples[0] and len(samples) > 0:
        # Fallback if label field missing in some samples
        fieldnames = ['image_id', 'split', 'filename']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for sample in samples:
            row = {
                'image_id': sample.get('image_id', sample.get('filename')),
                'split': split_name,
                'filename': sample.get('filename', sample.get('image_id'))
            }
            if label_field in sample:
                row[label_field] = sample[label_field]
            writer.writerow(row)

def generate_split_manifests(
    train_samples: List[Dict],
    val_samples: List[Dict],
    test_samples: List[Dict],
    processed_dir: Path,
    label_field: str = "yield_strength_mpa"
) -> Dict[str, Path]:
    """
    Generate manifest files for all splits.

    Args:
        train_samples: Training samples.
        val_samples: Validation samples.
        test_samples: Test samples.
        processed_dir: Directory to write manifests.
        label_field: Field name for the label.

    Returns:
        Dictionary mapping split names to manifest paths.
    """
    logger = logging.getLogger("splitter")
    manifest_paths = {}

    for split_name, samples in [("train", train_samples), ("val", val_samples), ("test", test_samples)]:
        manifest_path = processed_dir / f"{split_name}_manifest.csv"
        write_manifest(samples, split_name, manifest_path, label_field)
        manifest_paths[split_name] = manifest_path
        logger.info(f"Wrote {split_name} manifest: {manifest_path}")

    return manifest_paths

def write_split_stats(
    train_samples: List[Dict],
    val_samples: List[Dict],
    test_samples: List[Dict],
    results_dir: Path,
    label_field: str = "yield_strength_mpa"
) -> Path:
    """
    Write split statistics to JSON.

    Args:
        train_samples: Training samples.
        val_samples: Validation samples.
        test_samples: Test samples.
        results_dir: Directory to write stats.
        label_field: Field name for the label.

    Returns:
        Path to the stats file.
    """
    logger = logging.getLogger("splitter")
    stats_path = results_dir / "split_statistics.json"
    stats_path.parent.mkdir(parents=True, exist_ok=True)

    def get_label_stats(samples: List[Dict]) -> Dict:
        if not samples or label_field not in samples[0]:
            return {"count": 0, "min": None, "max": None, "mean": None}
        labels = [float(s[label_field]) for s in samples if label_field in s]
        return {
            "count": len(labels),
            "min": min(labels) if labels else None,
            "max": max(labels) if labels else None,
            "mean": sum(labels) / len(labels) if labels else None
        }

    stats = {
        "train": get_label_stats(train_samples),
        "val": get_label_stats(val_samples),
        "test": get_label_stats(test_samples),
        "total": len(train_samples) + len(val_samples) + len(test_samples)
    }

    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    logger.info(f"Wrote split statistics: {stats_path}")
    return stats_path

def main() -> int:
    """
    Main entry point for data splitting.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger = setup_logging()
    logger.info("Starting data split process")

    try:
        # Get paths
        project_root = get_project_root()
        processed_dir = get_processed_dir()
        results_dir = get_results_dir()

        # Load manifest from preprocess step
        # Assuming preprocess outputs to data/processed/manifest.csv or similar
        # We look for the manifest generated by T012 (preprocess)
        manifest_candidates = [
            processed_dir / "manifest.csv",
            processed_dir / "preprocessed_manifest.csv",
            processed_dir / "dataset_manifest.csv"
        ]

        manifest_path = None
        for candidate in manifest_candidates:
            if candidate.exists():
                manifest_path = candidate
                break

        if not manifest_path:
            # Try to find any CSV in processed dir
            csv_files = list(processed_dir.glob("*.csv"))
            if csv_files:
                manifest_path = csv_files[0]
                logger.warning(f"Using first CSV found: {manifest_path}")
            else:
                raise FileNotFoundError(
                    "No manifest file found in processed directory. "
                    "Run preprocess.py (T012) first."
                )

        logger.info(f"Using manifest: {manifest_path}")

        # Load samples
        samples = load_processed_manifest(manifest_path)

        # Binarize for stratification
        samples_with_bins = binarize_labels_for_stratification(samples)

        # Split
        train_samples, val_samples, test_samples = stratified_split(samples_with_bins)

        # Write manifests
        generate_split_manifests(train_samples, val_samples, test_samples, processed_dir)

        # Write stats
        write_split_stats(train_samples, val_samples, test_samples, results_dir)

        logger.info("Data split completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Data split failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())