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
    Generates synthetic datasets for validation.
    
    This class creates datasets with configurable mean differences, sample sizes,
    and ground truths for statistical validation.
    """
    
    def __init__(self) -> None:
        """Initialize the generator."""
        self.mapping_log: List[Dict[str, Any]] = []
    
    def generate(
        self,
        n: int,
        seed: int,
        mean_diff_embodied: float,
        mean_diff_static: float
    ) -> List[DatasetRecord]:
        """
        Generate a synthetic dataset.
        
        Args:
            n: Total number of records to generate.
            seed: Random seed for reproducibility.
            mean_diff_embodied: Mean difference for embodied group.
            mean_diff_static: Mean difference for static group.
            
        Returns:
            List of DatasetRecord objects.
        """
        set_seed(seed)
        
        # Split data into two groups
        n_embodied = n // 2
        n_static = n - n_embodied
        
        records: List[DatasetRecord] = []
        
        # Generate embodied group
        pre_scores_emb = np.random.normal(50, 10, n_embodied)
        post_scores_emb = pre_scores_emb + np.random.normal(mean_diff_embodied, 5, n_embodied)
        
        for i in range(n_embodied):
            records.append(DatasetRecord(
                pre_test_score=float(pre_scores_emb[i]),
                post_test_score=float(post_scores_emb[i]),
                instruction_type="embodied",
                covariates={"group_size": n_embodied}
            ))
            self.mapping_log.append({
                "physics_param": f"embodied_group_{i}",
                "math_concept": "gain_score",
                "mapping_rule": f"post - pre = {mean_diff_embodied} (target)",
                "causal_mechanism": "Virtual manipulation is assumed to map to abstract principle understanding via linear gain mapping rule."
            })
        
        # Generate static group
        pre_scores_stat = np.random.normal(50, 10, n_static)
        post_scores_stat = pre_scores_stat + np.random.normal(mean_diff_static, 5, n_static)
        
        for i in range(n_static):
            records.append(DatasetRecord(
                pre_test_score=float(pre_scores_stat[i]),
                post_test_score=float(post_scores_stat[i]),
                instruction_type="static",
                covariates={"group_size": n_static}
            ))
            self.mapping_log.append({
                "physics_param": f"static_group_{i}",
                "math_concept": "gain_score",
                "mapping_rule": f"post - pre = {mean_diff_static} (target)",
                "causal_mechanism": "Virtual manipulation is assumed to map to abstract principle understanding via linear gain mapping rule."
            })
        
        return records

    def write_mapping_log(self, output_path: str) -> None:
        """
        Write the mapping log to a JSON file.
        
        Args:
            output_path: Path to the output JSON file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.mapping_log, f, indent=2)
        
        logger.info(f"Mapping log written to {output_path}")

def generate_mapping_log(generator: SyntheticDataGenerator, output_path: str) -> None:
    """
    Generate and write the mapping log.
    
    Args:
        generator: The SyntheticDataGenerator instance.
        output_path: Path to the output JSON file.
    """
    generator.write_mapping_log(output_path)