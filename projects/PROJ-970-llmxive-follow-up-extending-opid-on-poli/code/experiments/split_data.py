"""
Data splitting logic for the OPID experiment.

Splits episodes into training and validation sets for each (Tier, Threshold) combination.
Saves the validation set configuration to data/processed/validation_set_config.json.
"""
import json
import os
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import random

from config import get_seed, set_seed, ensure_directories

logger = logging.getLogger(__name__)


@dataclass
class SplitConfig:
    """Configuration for data splitting."""
    validation_ratio: float = 0.2
    seed: int = 42


@dataclass
class ValidationSetConfig:
    """Configuration for a single validation set split."""
    tier: int
    threshold: float
    total_episodes: int
    train_indices: List[int]
    val_indices: List[int]
    val_size: int
    train_size: int


def split_episodes_for_setting(
    tier: int,
    threshold: float,
    total_episodes: int,
    config: SplitConfig
) -> ValidationSetConfig:
    """
    Split episodes for a specific (Tier, Threshold) setting.
    
    Args:
        tier: The complexity tier (1, 2, or 3)
        threshold: The routing threshold (0.0 to 1.0)
        total_episodes: Total number of episodes for this setting
        config: SplitConfig with validation ratio and seed
    
    Returns:
        ValidationSetConfig with train and validation indices
    """
    # Set seed for this specific split to ensure determinism
    set_seed(config.seed)
    
    # Generate all episode indices
    all_indices = list(range(total_episodes))
    
    # Shuffle indices deterministically
    random.shuffle(all_indices)
    
    # Calculate split point
    val_size = int(total_episodes * config.validation_ratio)
    train_size = total_episodes - val_size
    
    # Split indices
    val_indices = sorted(all_indices[:val_size])
    train_indices = sorted(all_indices[train_size:])
    
    return ValidationSetConfig(
        tier=tier,
        threshold=threshold,
        total_episodes=total_episodes,
        train_indices=train_indices,
        val_indices=val_indices,
        val_size=val_size,
        train_size=train_size
    )


def run_data_splitting(
    tiers: List[int],
    thresholds: List[float],
    episodes_per_setting: int,
    validation_ratio: float = 0.2,
    seed: int = 42
) -> Dict[str, ValidationSetConfig]:
    """
    Run data splitting for all (Tier, Threshold) combinations.
    
    Args:
        tiers: List of tier IDs to process
        thresholds: List of threshold values to process
        episodes_per_setting: Number of episodes per (Tier, Threshold) setting
        validation_ratio: Ratio of episodes for validation (default 0.2)
        seed: Base seed for reproducibility
    
    Returns:
        Dictionary mapping (tier, threshold) string key to ValidationSetConfig
    """
    config = SplitConfig(validation_ratio=validation_ratio, seed=seed)
    splits = {}
    
    for tier in tiers:
        for threshold in thresholds:
            key = f"tier_{tier}_threshold_{threshold:.1f}"
            split_config = split_episodes_for_setting(
                tier=tier,
                threshold=threshold,
                total_episodes=episodes_per_setting,
                config=config
            )
            splits[key] = split_config
            logger.info(
                f"Split {key}: {split_config.train_size} train, "
                f"{split_config.val_size} validation"
            )
    
    return splits


def save_validation_config(
    splits: Dict[str, ValidationSetConfig],
    output_path: str
) -> None:
    """
    Save validation set configuration to JSON file.
    
    Args:
        splits: Dictionary of ValidationSetConfig objects
        output_path: Path to save the JSON file
    """
    # Ensure output directory exists
    ensure_directories([os.path.dirname(output_path)])
    
    # Convert to serializable format
    serializable_splits = {}
    for key, config in splits.items():
        serializable_splits[key] = asdict(config)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_splits, f, indent=2)
    
    logger.info(f"Saved validation config to {output_path}")


def main():
    """Main entry point for data splitting script."""
    # Import config values
    from config import EPISODES_PER_SETTING, get_tier_config
    
    # Get tiers and thresholds
    tiers = [1, 2, 3]
    
    # Generate thresholds from 0.0 to 1.0 in 0.1 increments
    import numpy as np
    thresholds = np.arange(0.0, 1.01, 0.1).tolist()
    
    logger.info(f"Running data splitting for {len(tiers)} tiers and "
               f"{len(thresholds)} thresholds")
    logger.info(f"Episodes per setting: {EPISODES_PER_SETTING}")
    
    # Run splitting
    splits = run_data_splitting(
        tiers=tiers,
        thresholds=thresholds,
        episodes_per_setting=EPISODES_PER_SETTING,
        validation_ratio=0.2,
        seed=42
    )
    
    # Save configuration
    output_path = "data/processed/validation_set_config.json"
    save_validation_config(splits, output_path)
    
    logger.info("Data splitting completed successfully")
    return splits


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
