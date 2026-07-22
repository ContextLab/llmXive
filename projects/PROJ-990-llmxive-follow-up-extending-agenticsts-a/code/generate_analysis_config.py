"""
Generate a snapshot of the analysis configuration for reproducibility.
This script records the exact random seeds, hyperparameters, and dataset split ratios
used for the specific run, ensuring full reproducibility of the statistical results.
"""
import os
import json
import logging
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_split_metadata(split_dir: Path) -> Dict[str, Any]:
    """
    Load metadata about the dataset splits to capture the split ratios.
    Reads the validation_set_ids.json and infers ratios from the CSV files.
    """
    metadata = {
        "train_count": 0,
        "ablation_train_count": 0,
        "validation_count": 0,
        "test_count": 0,
        "total_count": 0,
        "ratios": {}
    }

    counts = {}
    split_files = [
        ("train_set.csv", "train_count"),
        ("ablation_train_set.csv", "ablation_train_count"),
        ("validation_set.csv", "validation_count"),
        ("test_set.csv", "test_count")
    ]

    for filename, key in split_files:
        filepath = split_dir / filename
        if filepath.exists():
            # Count lines (excluding header)
            with open(filepath, 'r') as f:
                # Skip header
                next(f, None)
                count = sum(1 for _ in f)
                counts[key] = count
                metadata[key] = count
                metadata["total_count"] += count
        else:
            logger.warning(f"Split file not found: {filepath}")
            counts[key] = 0
            metadata[key] = 0

    if metadata["total_count"] > 0:
        for key, count in counts.items():
            if key.endswith("_count"):
                ratio_key = key.replace("_count", "_ratio")
                metadata["ratios"][ratio_key] = count / metadata["total_count"]

    # Load validation set IDs if available
    validation_ids_file = split_dir / "validation_set_ids.json"
    if validation_ids_file.exists():
        with open(validation_ids_file, 'r') as f:
            metadata["validation_ids"] = json.load(f)
        metadata["validation_count"] = len(metadata["validation_ids"])

    return metadata

def load_ablation_config(ablation_dir: Path) -> Dict[str, Any]:
    """
    Load ablation configuration if available.
    """
    config = {
        "ablation_labels_train_exists": False,
        "ablation_labels_validation_exists": False,
        "sample_count": None,
        "fallback_flag": None
    }

    train_labels = ablation_dir / "ablation_labels_train.json"
    if train_labels.exists():
        config["ablation_labels_train_exists"] = True

    val_labels = ablation_dir / "ablation_labels_validation.json"
    if val_labels.exists():
        config["ablation_labels_validation_exists"] = True

    # Check sample count from fallback flag
    fallback_file = ablation_dir / "fallback_flag.json"
    if fallback_file.exists():
        with open(fallback_file, 'r') as f:
            fallback_data = json.load(f)
            config["fallback_flag"] = fallback_data.get("fallback", False)
            config["reason"] = fallback_data.get("reason", None)

    return config

def generate_analysis_config(
    output_path: Path,
    split_dir: Optional[Path] = None,
    ablation_dir: Optional[Path] = None,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive analysis configuration snapshot.

    Args:
        output_path: Path where the config JSON will be written.
        split_dir: Directory containing split CSV files.
        ablation_dir: Directory containing ablation labels and fallback flags.
        random_seed: Specific seed to record (if not set, uses current state).

    Returns:
        The generated configuration dictionary.
    """
    # Default directories
    if split_dir is None:
        split_dir = Path("data/processed")
    else:
        split_dir = Path(split_dir)

    if ablation_dir is None:
        ablation_dir = Path("data/processed")
    else:
        ablation_dir = Path(ablation_dir)

    # Capture random state
    if random_seed is None:
        random_seed = random.getstate()
        np_seed = np.random.get_state()
        random_seed_val = None
    else:
        random_seed_val = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        random_seed = random.getstate()
        np_seed = np.random.get_state()

    config = {
        "experiment_id": "llmXive-follow-up-extending-agenticsts-a",
        "task_id": "T037",
        "description": "Analysis configuration snapshot for reproducibility",
        "generated_at": None,  # Will be set by caller or omitted
        "random_seeds": {
            "python_random": str(random_seed),
            "numpy_random": str(np_seed),
            "explicit_seed": random_seed_val
        },
        "hyperparameters": {
            "token_budget": 4096,
            "min_context": 256,
            "k_dynamic": "model_predicted_or_fallback_2",
            "k_static": "all_layers",
            "k_random": "uniform_random",
            "correlation_threshold": 0.7,
            "sample_size_threshold": 300,
            "token_reduction_threshold": 0.30
        },
        "dataset_splits": load_split_metadata(split_dir),
        "ablation_config": load_ablation_config(ablation_dir),
        "statistical_tests": {
            "paired_test": "McNemar's test",
            "unpaired_test": "Permutation test",
            "token_test": "Paired t-test (or Wilcoxon if non-normal)",
            "correction": "Bonferroni"
        },
        "reproducibility_notes": [
            "This snapshot captures the exact configuration used for the analysis.",
            "Random seeds are recorded to ensure reproducibility of stochastic processes.",
            "Dataset split ratios are derived from the actual split files.",
            "Hyperparameters are hardcoded constants from the project specification.",
            "Statistical test selection depends on trajectory divergence (T024a)."
        ]
    }

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2, default=str)

    logger.info(f"Analysis configuration saved to: {output_path}")
    return config

def main():
    """Main entry point for generating the analysis config."""
    output_path = Path("data/processed/analysis_config.json")
    split_dir = Path("data/processed")
    ablation_dir = Path("data/processed")

    logger.info(f"Generating analysis configuration snapshot...")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Split directory: {split_dir}")
    logger.info(f"Ablation directory: {ablation_dir}")

    config = generate_analysis_config(
        output_path=output_path,
        split_dir=split_dir,
        ablation_dir=ablation_dir
    )

    logger.info("Analysis configuration generation complete.")
    return 0

if __name__ == "__main__":
    exit(main())
