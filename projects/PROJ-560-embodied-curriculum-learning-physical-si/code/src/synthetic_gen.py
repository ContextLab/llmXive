import json
import os
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from .models import DatasetRecord
from .logging_config import setup_logging
from .utils import set_seed

logger = setup_logging(log_file="data/derivation_logs/synthetic.log")

class SyntheticDataGenerator:
    """
    Generates synthetic datasets with configurable parameters for statistical validation.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        set_seed(seed)
        self.logger = logging.getLogger("embodied_curriculum.synthetic")
    
    def generate(
        self,
        n_samples: int = 100,
        mean_embodied: float = 15.0,
        mean_static: float = 5.0,
        std_dev: float = 5.0,
        pre_test_mean: float = 50.0,
        pre_test_std: float = 10.0
    ) -> List[DatasetRecord]:
        """
        Generate synthetic dataset.
        
        Args:
            n_samples: Total number of samples.
            mean_embodied: Mean gain for embodied group.
            mean_static: Mean gain for static group.
            std_dev: Standard deviation for gains.
            pre_test_mean: Mean pre-test score.
            pre_test_std: Standard deviation for pre-test scores.
        
        Returns:
            List of DatasetRecord objects.
        """
        self.logger.info(f"Generating {n_samples} synthetic records.")
        
        # Ensure half are embodied, half static
        n_embodied = n_samples // 2
        n_static = n_samples - n_embodied
        
        records = []
        
        # Generate Pre-test scores (common distribution)
        pre_scores = np.random.normal(pre_test_mean, pre_test_std, n_samples)
        
        # Generate Post-test scores based on group
        # Gain = Post - Pre => Post = Pre + Gain
        
        # Embodied group
        embodied_gains = np.random.normal(mean_embodied, std_dev, n_embodied)
        embodied_pre = pre_scores[:n_embodied]
        embodied_post = embodied_pre + embodied_gains
        
        for i in range(n_embodied):
            record = DatasetRecord(
                pre_test_score=float(embodied_pre[i]),
                post_test_score=float(embodied_post[i]),
                instruction_type="embodied_physics",
                covariates={"group": "embodied", "gain": float(embodied_gains[i])}
            )
            records.append(record)
        
        # Static group
        static_gains = np.random.normal(mean_static, std_dev, n_static)
        static_pre = pre_scores[n_embodied:]
        static_post = static_pre + static_gains
        
        for i in range(n_static):
            record = DatasetRecord(
                pre_test_score=float(static_pre[i]),
                post_test_score=float(static_post[i]),
                instruction_type="static_text",
                covariates={"group": "static", "gain": float(static_gains[i])}
            )
            records.append(record)
        
        self.logger.info(f"Synthetic generation complete. Total records: {len(records)}")
        return records
    
    def generate_mapping_log(self, output_path: str = "data/synthetic/mapping_log.json"):
        """
        Create a mapping log documenting the causal chain for Constitution Principle VI.
        """
        log_path = Path(output_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        mapping_data = {
            "causal_chain": [
                {
                    "stage": "Physics_Action",
                    "description": "Student manipulates virtual objects (e.g., levers, pulleys).",
                    "variables": ["force", "distance", "work"]
                },
                {
                    "stage": "Virtual_Object_State",
                    "description": "System updates state based on physical simulation engine.",
                    "variables": ["position", "velocity", "energy"]
                },
                {
                    "stage": "Abstract_Principle_Inference",
                    "description": "Student infers mathematical relationship (e.g., Work = Force x Distance).",
                    "variables": ["gain_score", "concept_mastery"]
                }
            ],
            "generated_parameters": {
                "seed": self.seed,
                "embodied_mean_gain": 15.0,
                "static_mean_gain": 5.0,
                "std_dev": 5.0
            },
            "timestamp": str(np.datetime64('now'))
        }
        
        with open(log_path, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        self.logger.info(f"Mapping log written to {log_path}")
        return str(log_path)
