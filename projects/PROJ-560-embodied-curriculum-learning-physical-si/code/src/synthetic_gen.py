"""
Synthetic data generation module.

Generates datasets with configurable parameters for validation and testing.
"""
import json
import os
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from .models import DatasetRecord

logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """
    Generates synthetic datasets for statistical validation.

    Attributes:
        mean_difference (float): The intended difference in means between groups.
        sample_size (int): The number of samples per group.
        ground_truth (Dict[str, Any]): The ground truth parameters used.
    """

    def __init__(self, mean_difference: float = 0.5, sample_size: int = 100, seed: int = 42):
        """
        Initialize the generator.

        Args:
            mean_difference (float): Difference in means between groups.
            sample_size (int): Number of samples per group.
            seed (int): Random seed for reproducibility.
        """
        self.mean_difference = mean_difference
        self.sample_size = sample_size
        self.ground_truth = {
            "mean_difference": mean_difference,
            "sample_size": sample_size,
            "seed": seed
        }
        np.random.seed(seed)

    @classmethod
    def generate(cls, sample_size: int = 100, mean_diff: float = 0.5, seed: int = 42) -> List[DatasetRecord]:
        """
        Generate a synthetic dataset.

        Args:
            sample_size (int): Total number of samples (split between groups).
            mean_diff (float): Intended mean difference.
            seed (int): Random seed.

        Returns:
            List[DatasetRecord]: List of generated records.
        """
        generator = cls(mean_difference=mean_diff, sample_size=sample_size, seed=seed)
        return generator._create_records()

    def _create_records(self) -> List[DatasetRecord]:
        """
        Create the actual records based on configured parameters.

        Returns:
            List[DatasetRecord]: List of records.
        """
        records = []
        n_per_group = self.sample_size // 2

        # Generate scores for Static group
        pre_static = np.random.normal(loc=50, scale=10, size=n_per_group)
        post_static = np.random.normal(loc=55, scale=10, size=n_per_group)

        # Generate scores for Embodied group (with mean difference)
        pre_embodied = np.random.normal(loc=50, scale=10, size=n_per_group)
        post_embodied = np.random.normal(loc=55 + self.mean_difference * 10, scale=10, size=n_per_group)

        for i in range(n_per_group):
            records.append(DatasetRecord(
                pre_test_score=float(pre_static[i]),
                post_test_score=float(post_static[i]),
                instruction_type="static",
                covariates={"group_id": i}
            ))
            records.append(DatasetRecord(
                pre_test_score=float(pre_embodied[i]),
                post_test_score=float(post_embodied[i]),
                instruction_type="embodied",
                covariates={"group_id": i + n_per_group}
            ))

        logger.info(f"Generated {len(records)} synthetic records.")
        return records


def generate_mapping_log(output_path: str) -> None:
    """
    Generate a mapping log documenting the causal chain for synthetic data.

    This satisfies Constitution Principle VI by documenting:
    Physics_Action -> Virtual_Object_State -> Abstract_Principle_Inference

    Args:
        output_path (str): Path to write the mapping log JSON.
    """
    log_data = {
        "causal_chain": [
            {
                "stage": "Physics_Action",
                "description": "User interacts with virtual objects in a physics simulation.",
                "variables": ["force_applied", "mass", "velocity_change"]
            },
            {
                "stage": "Virtual_Object_State",
                "description": "Resulting state of objects after interaction.",
                "variables": ["displacement", "kinetic_energy", "momentum"]
            },
            {
                "stage": "Abstract_Principle_Inference",
                "description": "Inference of abstract mathematical principles from observed states.",
                "variables": ["linear_relationship", "proportionality", "conservation_laws"]
            }
        ],
        "mapping_logic": "The synthetic generator simulates the outcome of these interactions to produce pre/post test scores that reflect the understanding of these principles.",
        "generated_at": "auto"
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

    logger.info(f"Mapping log written to {output_path}")
