import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

# Random Seed Configuration
RANDOM_SEED: int = 42

# Bootstrap Configuration
BOOTSTRAP_ITERATIONS: int = 1000

# Validation Thresholds
VALIDITY_THRESHOLD: float = 0.1  # Default threshold for bootstrap variance check

# Significance Thresholds for Sensitivity Analysis
THRESHOLDS: List[float] = [0.01, 0.05, 0.10]

# Violation Sweep Configuration
VIOLATION_SWEEP_CONFIG: Dict[str, List[float]] = {
    "ar_coefficients": [0.0, 0.3, 0.5],
    "contamination_rates": [0.0, 0.1, 0.3],
    "separation_values": [0.0, 1.0, 1.5]
}

# Dataset Configuration: Specific list of 10 diverse public datasets
# Continuous (3): iris, wine, wine_quality_red
# Count (3): concrete, airfoil, yacht
# Binary (4): breast_cancer, heart_disease, pima, ionosphere
DATASET_LIST: List[Dict[str, Any]] = [
    {"id": "iris", "source": "openml", "outcome_type": "continuous", "url": "https://data.openml.org/datasets/1"},
    {"id": "wine", "source": "openml", "outcome_type": "continuous", "url": "https://data.openml.org/datasets/13"},
    {"id": "wine_quality_red", "source": "openml", "outcome_type": "continuous", "url": "https://data.openml.org/datasets/28"},
    {"id": "concrete", "source": "openml", "outcome_type": "count", "url": "https://data.openml.org/datasets/125"},
    {"id": "airfoil", "source": "openml", "outcome_type": "count", "url": "https://data.openml.org/datasets/154"},
    {"id": "yacht", "source": "openml", "outcome_type": "count", "url": "https://data.openml.org/datasets/184"},
    {"id": "breast_cancer", "source": "openml", "outcome_type": "binary", "url": "https://data.openml.org/datasets/53"},
    {"id": "heart_disease", "source": "openml", "outcome_type": "binary", "url": "https://data.openml.org/datasets/141"},
    {"id": "pima", "source": "openml", "outcome_type": "binary", "url": "https://data.openml.org/datasets/150"},
    {"id": "ionosphere", "source": "openml", "outcome_type": "binary", "url": "https://data.openml.org/datasets/146"}
]

def ensure_directories() -> None:
    """Create necessary project directories if they do not exist."""
    dirs = [
        "code", "tests", "tests/unit", "tests/integration", "tests/contract",
        "data/raw", "data/processed", "data/results", "docs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def get_dataset_config() -> List[Dict[str, Any]]:
    """Return the list of dataset configurations."""
    return DATASET_LIST

# Verification logic to ensure the list contains exactly 3 continuous, 3 count, and 4 binary datasets
def verify_dataset_distribution() -> bool:
    """Verify the distribution of dataset types in DATASET_LIST."""
    counts = {"continuous": 0, "count": 0, "binary": 0}
    for ds in DATASET_LIST:
        outcome = ds.get("outcome_type")
        if outcome in counts:
            counts[outcome] += 1
    return counts["continuous"] == 3 and counts["count"] == 3 and counts["binary"] == 4

if __name__ == "__main__":
    ensure_directories()
    if not verify_dataset_distribution():
        raise ValueError("Dataset distribution verification failed!")
    print("Dataset configuration verified successfully.")
    print(f"Continuous: {counts['continuous']}, Count: {counts['count']}, Binary: {counts['binary']}")
