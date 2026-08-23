"""
Test Instance Generator for Co-Evolving Policy Distillation.

This module implements the generation of held-out test instances for both
propositional logic proofs and grid-world navigation tasks. These instances
are strictly separate from the training data to ensure valid evaluation of
catastrophic forgetting and generalization (FR-005).

The generator uses distinct seeds from the training data configuration to
guarantee statistical independence between training and test sets.
"""

import random
import json
import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Import existing generators to ensure consistency in data format
from .logic_generator import LogicProofGenerator, LogicGenerationError
from .grid_generator import GridWorldGenerator, GridGenerationError
from src.utils.config import load_config, Config
from src.utils.checksums import update_checksum_for_file, load_checksums, save_checksums


class TestGenerationError(Exception):
    """Custom exception for test instance generation failures."""
    pass


class TestInstanceGenerator:
    """
    Generates held-out test instances for evaluation.

    This class ensures that test instances are:
    1. Generated with seeds distinct from training data.
    2. Valid according to the same rules as training data.
    3. Saved to the specified output path with integrity checksums.
    """

    def __init__(self, config: Config):
        """
        Initialize the TestInstanceGenerator.

        Args:
            config: Configuration object containing seeds, counts, and paths.
        """
        self.config = config
        self.logic_generator = LogicProofGenerator(config)
        self.grid_generator = GridWorldGenerator(config)
        
        # Calculate a distinct seed offset for test data to ensure separation
        # from training data seeds defined in config
        self.test_seed_offset = 10000 
        
    def _get_test_seed(self, base_seed: int, index: int) -> int:
        """
        Generate a unique seed for a test instance based on base seed and index.
        
        Args:
            base_seed: The base seed from config.
            index: The index of the test instance.
        
        Returns:
            A unique integer seed.
        """
        return (base_seed + self.test_seed_offset + index) % (2**32 - 1)

    def generate_logic_proofs(self, count: int, base_seed: int) -> List[Dict[str, Any]]:
        """
        Generate a list of valid propositional logic proofs for testing.
        
        Args:
            count: Number of proofs to generate.
            base_seed: Base seed for reproducibility.
        
        Returns:
            List of dictionaries containing proof data.
        
        Raises:
            TestGenerationError: If generation fails after retries.
        """
        proofs = []
        
        for i in range(count):
            seed = self._get_test_seed(base_seed, i)
            random.seed(seed)
            
            try:
                # Use the existing logic generator with the specific test seed
                # We generate 1 proof at a time to ensure we get exactly 'count' valid ones
                proof_data = self.logic_generator.generate_proof(seed=seed)
                proofs.append(proof_data)
            except LogicGenerationError as e:
                raise TestGenerationError(f"Failed to generate logic proof {i}: {e}")
        
        return proofs

    def generate_grids(self, count: int, base_seed: int) -> List[Dict[str, Any]]:
        """
        Generate a list of solvable grid-world navigation tasks for testing.
        
        Args:
            count: Number of grids to generate.
            base_seed: Base seed for reproducibility.
        
        Returns:
            List of dictionaries containing grid data.
        
        Raises:
            TestGenerationError: If generation fails after retries.
        """
        grids = []
        
        for i in range(count):
            seed = self._get_test_seed(base_seed, i)
            random.seed(seed)
            
            try:
                # Use the existing grid generator with the specific test seed
                grid_data = self.grid_generator.generate_grid(seed=seed)
                grids.append(grid_data)
            except GridGenerationError as e:
                raise TestGenerationError(f"Failed to generate grid {i}: {e}")
        
        return grids

    def generate_test_instances(self) -> Dict[str, Any]:
        """
        Generate the complete set of held-out test instances.
        
        This method orchestrates the generation of both logic and grid test data
        according to the configuration, ensuring they are strictly separate
        from training data.
        
        Returns:
            Dictionary containing 'logic_proofs' and 'grid_worlds' lists.
        
        Raises:
            TestGenerationError: If any generation step fails.
        """
        base_seed = self.config.test_seed
        
        # Generate logic proofs
        logic_count = self.config.test_logic_count
        if logic_count > 0:
            logic_proofs = self.generate_logic_proofs(logic_count, base_seed)
        else:
            logic_proofs = []
        
        # Generate grid worlds
        grid_count = self.config.test_grid_count
        if grid_count > 0:
            grid_worlds = self.generate_grids(grid_count, base_seed)
        else:
            grid_worlds = []
        
        test_data = {
            "metadata": {
                "base_seed": base_seed,
                "test_seed_offset": self.test_seed_offset,
                "logic_count": len(logic_proofs),
                "grid_count": len(grid_worlds),
                "generated_from": "test_generator.py"
            },
            "logic_proofs": logic_proofs,
            "grid_worlds": grid_worlds
        }
        
        return test_data

    def save_test_instances(self, output_path: Optional[str] = None) -> str:
        """
        Generate and save test instances to a JSON file.
        
        Args:
            output_path: Optional path to save the file. If None, uses config path.
        
        Returns:
            Path to the saved file.
        
        Raises:
            TestGenerationError: If generation or saving fails.
        """
        if output_path is None:
            output_path = self.config.test_output_path
        
        output_file = Path(output_path)
        
        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate data
        test_data = self.generate_test_instances()
        
        # Write to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2)
        except IOError as e:
            raise TestGenerationError(f"Failed to write test instances to {output_file}: {e}")
        
        # Register checksum
        try:
            update_checksum_for_file(output_file)
        except Exception as e:
            # Log warning but don't fail the generation if checksum fails
            print(f"Warning: Failed to update checksum for {output_file}: {e}", file=sys.stderr)
        
        return str(output_file)


def main():
    """
    CLI entry point for generating test instances.
    
    Usage:
        python -m src.generators.test_generator [--config path/to/config.json]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate held-out test instances")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        generator = TestInstanceGenerator(config)
        
        output_path = args.output if args.output else config.test_output_path
        saved_path = generator.save_test_instances(output_path)
        
        print(f"Successfully generated test instances to: {saved_path}")
        
        # Verify file exists
        if not os.path.exists(saved_path):
            raise TestGenerationError(f"Output file not found after generation: {saved_path}")
            
        return 0
        
    except TestGenerationError as e:
        print(f"Error generating test instances: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
