"""
Configuration module for the sensitivity analysis pipeline.

This module defines constants, sample size tiers, and verified dataset
sources. It serves as the single source of truth for dataset IDs and
their corresponding access methods.
"""

from typing import Dict, Any

# Sample size tiers as percentages of the full dataset.
# Defined in T017 as the representative tiered values.
SAMPLE_SIZE_TIERS: list[int] = [10, 25, 50, 75, 90]

# Random seed for reproducibility across all experiments.
RANDOM_SEED: int = 42

# Maximum number of rows to load into memory for profiling if the dataset is large.
# Datasets exceeding this will be subsampled to ensure memory compliance.
MAX_ROWS_FOR_PROFILING: int = 100_000

# Threshold for condition number to flag multicollinearity.
CONDITION_NUMBER_THRESHOLD: float = 30.0

# Convergence criteria for resampling experiments (Standard Error of SD).
CONVERGENCE_THRESHOLD: float = 0.05

# Maximum number of subsets to generate per tier during convergence checks.
MAX_SUBSETS_PER_TIER: int = 500

# Initial number of subsets to generate per tier before convergence check.
INITIAL_SUBSETS_PER_TIER: int = 200

# Verified Dataset Registry
# Keys are dataset IDs, values are dictionaries containing source type and
# the specific identifier or URL needed to load the data.
# This dictionary is the single source of truth for T012 (downloader).
VERIFIED_DATASETS: Dict[str, Dict[str, Any]] = {
    "UCI:Auto": {
        "source": "UCI",
        "name": "Auto",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data",
        "description": "Auto MPG dataset for regression analysis.",
        "target_column": "mpg",
        "delimiter": " "
    },
    "HuggingFace:california_housing": {
        "source": "HuggingFace",
        "name": "california_housing",
        "dataset_id": "skops/california_housing",
        "description": "California Housing dataset for regression.",
        "target_column": "MedHouseVal"
    },
    "UCI:Concrete": {
        "source": "UCI",
        "name": "Concrete Compressive Strength",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/concrete_slump_and_compressive_strength.csv",
        "description": "Concrete compressive strength dataset.",
        "target_column": "Concrete compressive strength (MPa)"
    },
    "HuggingFace:concrete_strength": {
        "source": "HuggingFace",
        "name": "concrete_strength",
        "dataset_id": "burtenshaw/concrete_strength",
        "description": "Alternative source for concrete strength data.",
        "target_column": "compressive_strength"
    }
}