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
    def __init__(self, seed: Optional[int] = None):
        """
        Initializes the SyntheticDataGenerator.
        
        Args:
            seed: Random seed for reproducibility.
        """
        self.seed = seed if seed is not None else 42
        set_seed(self.seed)
        logger.info(f"SyntheticDataGenerator initialized with seed {self.seed}")

    def generate(self, n_samples: int = 1000) -> List[DatasetRecord]:
        """
        Generates synthetic dataset records.
        
        Args:
            n_samples: Number of samples to generate.
            
        Returns:
            List of DatasetRecord objects.
        """
        logger.info(f"Generating {n_samples} synthetic records.")
        
        records = []
        
        # Generate instruction types
        instruction_types = ["embodied", "static", "control"]
        # Generate scores with some mean difference
        # Embodied group has higher gain
        embodied_count = n_samples // 3
        static_count = n_samples // 3
        control_count = n_samples - embodied_count - static_count
        
        # Pre-test scores (normally distributed)
        pre_emb = np.random.normal(50, 10, embodied_count)
        pre_stat = np.random.normal(50, 10, static_count)
        pre_ctrl = np.random.normal(50, 10, control_count)
        
        # Post-test scores
        # Embodied: higher gain
        post_emb = pre_emb + np.random.normal(15, 5, embodied_count) # Mean gain 15
        # Static: lower gain
        post_stat = pre_stat + np.random.normal(5, 5, static_count) # Mean gain 5
        # Control: no gain
        post_ctrl = pre_ctrl + np.random.normal(0, 5, control_count) # Mean gain 0
        
        all_pre = np.concatenate([pre_emb, pre_stat, pre_ctrl])
        all_post = np.concatenate([post_emb, post_stat, post_ctrl])
        all_types = ["embodied"] * embodied_count + ["static"] * static_count + ["control"] * control_count
        
        for i in range(n_samples):
            record = DatasetRecord(
                pre_test_score=float(all_pre[i]),
                post_test_score=float(all_post[i]),
                instruction_type=all_types[i],
                covariates={"sample_id": i}
            )
            records.append(record)
        
        logger.info(f"Generated {len(records)} synthetic records.")
        return records

def generate_mapping_log(output_path: str):
    """
    Generates a mapping_log.json file documenting the physics-to-math mapping.
    This satisfies Constitution Principle VI.
    Skipped if --mode=secondary_analysis (handled by caller).
    
    Args:
        output_path: Path to the output JSON file.
    """
    logger.info(f"Generating mapping log at {output_path}")
    
    mapping_data = {
        "physics_param": "velocity",
        "math_concept": "rate_of_change",
        "mapping_rule": "velocity_in_simulation = rate_of_change_in_math_problem",
        "description": "Mapping virtual object velocity to mathematical rate of change concept."
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(mapping_data, f, indent=2)
    
    logger.info("Mapping log generated successfully.")
