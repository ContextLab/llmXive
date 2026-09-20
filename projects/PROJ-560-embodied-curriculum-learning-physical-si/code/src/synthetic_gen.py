import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from .models import DatasetRecord
from .utils import set_seed


logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """
    Generates synthetic datasets with configurable parameters for validation.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator with an optional seed.
        
        Args:
            seed: Random seed for reproducibility.
        """
        self.seed = seed if seed is not None else 42
        set_seed(self.seed)
        
    def generate(
        self, 
        n_samples: int = 100, 
        mean_diff: float = 0.5, 
        std_dev: float = 1.0,
        instruction_types: Optional[List[str]] = None
    ) -> List[DatasetRecord]:
        """
        Generate synthetic records.
        
        Args:
            n_samples: Total number of samples.
            mean_diff: Expected mean difference between groups.
            std_dev: Standard deviation of scores.
            instruction_types: List of instruction types to simulate.
            
        Returns:
            List of DatasetRecord objects.
        """
        if instruction_types is None:
            instruction_types = ["embodied", "static"]
            
        records = []
        n_per_group = n_samples // len(instruction_types)
        
        # Generate base scores for control group (static)
        base_scores = np.random.normal(loc=50, scale=std_dev, size=n_per_group)
        
        # Generate scores for treatment group (embodied) with mean shift
        treatment_scores = np.random.normal(
            loc=50 + mean_diff, 
            scale=std_dev, 
            size=n_per_group
        )
        
        all_scores = list(base_scores) + list(treatment_scores)
        all_types = instruction_types[0] * n_per_group + instruction_types[1] * n_per_group
        
        # Shuffle
        indices = np.random.permutation(len(all_scores))
        all_scores = [all_scores[i] for i in indices]
        all_types = [all_types[i] for i in indices]
        
        for score, itype in zip(all_scores, all_types):
            # Simulate pre/post based on a simple model
            # pre = base, post = base + gain (random noise + group effect)
            pre = np.random.normal(50, std_dev)
            gain = (mean_diff if itype == instruction_types[1] else 0) + np.random.normal(0, std_dev * 0.5)
            post = pre + gain
            
            record = DatasetRecord(
                pre_test_score=float(pre),
                post_test_score=float(post),
                instruction_type=itype,
                covariates={"source": "synthetic"}
            )
            records.append(record)
            
        logger.info(f"Generated {len(records)} synthetic records.")
        return records


def generate_mapping_log(
    records: List[DatasetRecord], 
    output_path: str,
    physics_params: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate a mapping log documenting the derivation of synthetic data.
    
    Args:
        records: The generated records.
        output_path: Path to write the log.
        physics_params: Physics parameters mapped to math concepts.
    """
    log_entry = {
        "timestamp": None, # Set by system or datetime
        "mapping_type": "physics_to_math",
        "physics_parameters": physics_params or {},
        "math_concepts": {
            "instruction_type_embodied": "Simulated physical interaction",
            "instruction_type_static": "Static abstract representation"
        },
        "record_count": len(records),
        "generation_seed": 42, # Or from generator
        "principle": "Constitution Principle VI: Simulation-Pedagogy Alignment"
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(log_entry, f, indent=2)
        
    logger.info(f"Mapping log written to {output_path}")
