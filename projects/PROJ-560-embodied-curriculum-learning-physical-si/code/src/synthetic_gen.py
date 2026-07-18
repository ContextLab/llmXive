import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from .models import DatasetRecord
from .logging_config import setup_logging
from .utils import set_seed

logger = logging.getLogger('proj_560')

class SyntheticDataGenerator:
    """
    Generates synthetic datasets with configurable mean differences, sample sizes, 
    and ground truths for statistical validation.
    """
    
    def __init__(self, seed: int = 42, n_samples: int = 1000, 
                 mean_diff: float = 0.5, std_dev: float = 1.0):
        """
        Initialize the generator.
        
        Args:
            seed: Random seed for reproducibility.
            n_samples: Number of records to generate.
            mean_diff: The intended mean difference between groups (effect size proxy).
            std_dev: Standard deviation of the scores.
        """
        self.seed = seed
        self.n_samples = n_samples
        self.mean_diff = mean_diff
        self.std_dev = std_dev
        set_seed(seed)
        logger.info(f"SyntheticDataGenerator initialized with seed={seed}, n={n_samples}, diff={mean_diff}")

    def generate(self) -> List[DatasetRecord]:
        """
        Generates a list of DatasetRecord objects.
        
        Returns:
            List of synthetic records.
        """
        logger.info(f"Generating {self.n_samples} synthetic records...")
        
        # Define instruction types
        instruction_types = ['embodied_physics', 'static_text']
        
        records = []
        
        # Generate scores
        # Group 1: Embodied
        n1 = self.n_samples // 2
        # Group 2: Static
        n2 = self.n_samples - n1
        
        # Pre-test scores: same distribution for both
        pre_scores = np.random.normal(50, self.std_dev, self.n_samples)
        
        # Post-test scores: Embodied has higher mean
        post_scores_embodied = np.random.normal(50 + self.mean_diff, self.std_dev, n1)
        post_scores_static = np.random.normal(50, self.std_dev, n2)
        
        all_post_scores = np.concatenate([post_scores_embodied, post_scores_static])
        
        # Create records
        for i in range(self.n_samples):
            inst_type = instruction_types[0] if i < n1 else instruction_types[1]
            record = DatasetRecord(
                pre_test_score=float(pre_scores[i]),
                post_test_score=float(all_post_scores[i]),
                instruction_type=inst_type,
                covariates={"synthetic": True, "group_index": i}
            )
            records.append(record)
        
        logger.info(f"Generated {len(records)} synthetic records.")
        return records

def generate_mapping_log(output_path: str, generator_params: Dict[str, Any]) -> None:
    """
    Generates a mapping_log file documenting the derivation of synthetic data.
    This satisfies Constitution Principle VI (Simulation-Pedagogy Alignment).
    
    Args:
        output_path: Path to write the mapping log JSON.
        generator_params: Parameters used for generation.
    """
    logger.info(f"Generating mapping log at {output_path}")
    
    mapping_log = {
        "timestamp": None, # Will be handled by logger or we can use datetime
        "concepts": [
            {
                "physics_concept": "Force and Acceleration (Newton's Second Law)",
                "mathematical_concept": "Linear Regression / Slope",
                "mapping_rationale": "The simulation demonstrates that a constant force applied to an object results in a constant acceleration, analogous to a linear relationship between variables.",
                "instruction_type": "embodied_physics"
            },
            {
                "physics_concept": "Conservation of Energy",
                "mathematical_concept": "Summation / Invariance",
                "mapping_rationale": "The sum of kinetic and potential energy remains constant, illustrating the concept of conservation and invariant totals.",
                "instruction_type": "embodied_physics"
            }
        ],
        "generation_parameters": generator_params,
        "constitution_principle": "VI: Simulation-Pedagogy Alignment"
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(mapping_log, f, indent=2)
    
    logger.info("Mapping log generated successfully.")
