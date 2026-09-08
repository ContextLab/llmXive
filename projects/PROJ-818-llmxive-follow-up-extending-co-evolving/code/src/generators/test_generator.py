"""
Test Instance Generator Module.

Generates held-out test instances for both propositional logic proofs
and grid-world navigation tasks. These instances use distinct seeds
from training data to ensure strict separation (FR-005 compliance).
"""

import random
import json
import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Import existing generators
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator
from src.utils.config import load_config, Config
from src.utils.checksums import compute_file_sha256, save_checksums

class TestGenerationError(Exception):
    """Custom exception for test generation failures."""
    pass


class TestInstanceGenerator:
    """
    Generates held-out test instances strictly separate from training data.
    
    This generator ensures that the test set is disjoint from the training
    set by using a distinct seed range and strictly separate generation logic.
    """

    def __init__(self, config: Config):
        """
        Initialize the test generator.
        
        Args:
            config: Configuration object containing seeds and generation parameters.
        """
        self.config = config
        self.logic_generator = LogicProofGenerator(config)
        self.grid_generator = GridWorldGenerator(config)
        
        # Determine test seed range to ensure separation from training
        # Training uses seeds [0, config.num_training_instances)
        # Test uses seeds [config.num_training_instances, config.num_training_instances + config.num_test_instances)
        self.test_seed_start = config.num_training_instances
        self.test_seed_end = self.test_seed_start + config.num_test_instances

    def generate_logic_test_instances(self) -> List[Dict[str, Any]]:
        """
        Generate held-out propositional logic proof instances.
        
        Returns:
            List of dictionaries representing valid logic proofs.
        """
        instances = []
        
        # Iterate through the dedicated test seed range
        for i in range(self.config.num_test_logic_instances):
            # Calculate a unique seed for this instance that is distinct from training
            instance_seed = self.test_seed_start + i
            
            # Set seed for reproducibility of this specific instance
            random.seed(instance_seed)
            
            try:
                # Generate a single proof instance
                proof = self.logic_generator.generate_single_proof(seed=instance_seed)
                proof['_metadata'] = {
                    'instance_id': f'logic_test_{i:05d}',
                    'seed': instance_seed,
                    'set': 'held-out-test'
                }
                instances.append(proof)
            except Exception as e:
                raise TestGenerationError(f"Failed to generate logic test instance {i}: {e}")
        
        return instances

    def generate_grid_test_instances(self) -> List[Dict[str, Any]]:
        """
        Generate held-out grid-world navigation instances.
        
        Returns:
            List of dictionaries representing solvable grid worlds.
        """
        instances = []
        
        # Iterate through the dedicated test seed range for grids
        for i in range(self.config.num_test_grid_instances):
            # Calculate a unique seed for this instance
            instance_seed = self.test_seed_start + self.config.num_test_logic_instances + i
            
            # Set seed for reproducibility
            random.seed(instance_seed)
            
            try:
                # Generate a single grid instance
                grid = self.grid_generator.generate_single_grid(seed=instance_seed)
                grid['_metadata'] = {
                    'instance_id': f'grid_test_{i:05d}',
                    'seed': instance_seed,
                    'set': 'held-out-test'
                }
                instances.append(grid)
            except Exception as e:
                raise TestGenerationError(f"Failed to generate grid test instance {i}: {e}")
        
        return instances

    def generate_all_test_instances(self) -> Dict[str, Any]:
        """
        Generate all held-out test instances (logic and grid).
        
        Returns:
            Dictionary containing 'logic_proofs' and 'grid_worlds' lists.
        """
        return {
            'metadata': {
                'generated_by': 'TestInstanceGenerator',
                'total_logic_instances': self.config.num_test_logic_instances,
                'total_grid_instances': self.config.num_test_grid_instances,
                'seed_range_start': self.test_seed_start,
                'seed_range_end': self.test_seed_end,
                'separation_from_training': True
            },
            'logic_proofs': self.generate_logic_test_instances(),
            'grid_worlds': self.generate_grid_test_instances()
        }

    def save_test_instances(self, output_path: Optional[str] = None) -> str:
        """
        Generate and save test instances to a JSON file.
        
        Args:
            output_path: Optional path to save the file. Defaults to config path.
        
        Returns:
            Path to the saved file.
        """
        if output_path is None:
            output_path = str(self.config.test_instances_path)
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate instances
        test_data = self.generate_all_test_instances()
        
        # Write to file
        with open(output_path_obj, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Register checksum
        checksum = compute_file_sha256(output_path_obj)
        checksums_data = {
            'file': str(output_path_obj),
            'sha256': checksum,
            'type': 'test_instances',
            'timestamp': str(self.config.seed) # Using seed as a simple timestamp proxy for determinism
        }
        
        # Append to checksums file
        checksums_file = self.config.checksums_path
        if checksums_file.exists():
            with open(checksums_file, 'r') as f:
                existing = json.load(f)
            existing['test_instances'] = checksums_data
        else:
            existing = {'test_instances': checksums_data}
        
        save_checksums(existing, checksums_file)
        
        return str(output_path_obj)


def main():
    """Main entry point for generating test instances."""
    try:
        config = load_config()
        generator = TestInstanceGenerator(config)
        output_path = generator.save_test_instances()
        print(f"Successfully generated and saved test instances to: {output_path}")
        return 0
    except Exception as e:
        print(f"Error generating test instances: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
