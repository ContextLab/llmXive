"""
Test Instance Generator for Co-Evolving Policy Distillation.

This module implements the generation of held-out test instances for
both propositional logic proofs and grid-world navigation tasks.
It ensures strict separation from the training set by using distinct seeds,
satisfying FR-005 compliance.
"""

import random
import json
import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Import existing generators to ensure consistency with training data
from .logic_generator import LogicProofGenerator
from .grid_generator import GridWorldGenerator
from ..utils.config import load_config, Config
from ..utils.checksums import compute_file_sha256, save_checksums


class TestGenerationError(Exception):
    """Custom exception for test generation failures."""
    pass


class TestInstanceGenerator:
    """
    Generates held-out test instances for validation and baseline measurement.

    This generator uses distinct seeds from the training data to ensure
    that the test set is strictly separate, preventing data leakage.
    """

    def __init__(self, config: Config):
        """
        Initialize the generator with configuration.

        Args:
            config: Configuration object containing seeds and generation parameters.
        """
        self.config = config
        self.logic_generator = LogicProofGenerator(config)
        self.grid_generator = GridWorldGenerator(config)
        
        # Extract test-specific seeds or derive them to be distinct from training
        # We assume config has a base seed, and we offset it for test generation
        self.test_seed_base = config.seed + 10000
        random.seed(self.test_seed_base)

    def generate_logic_proofs(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate a specified number of logic proof test instances.

        Args:
            count: Number of proofs to generate.

        Returns:
            List of dictionaries containing proof data.

        Raises:
            TestGenerationError: If generation fails repeatedly.
        """
        proofs = []
        for i in range(count):
            seed = self.test_seed_base + i
            try:
                proof = self.logic_generator.generate_single_proof(seed=seed)
                proofs.append(proof)
            except Exception as e:
                raise TestGenerationError(f"Failed to generate logic proof #{i}: {str(e)}")
        
        return proofs

    def generate_grid_worlds(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate a specified number of grid world test instances.

        Args:
            count: Number of grids to generate.

        Returns:
            List of dictionaries containing grid data.

        Raises:
            TestGenerationError: If generation fails repeatedly.
        """
        grids = []
        for i in range(count):
            seed = self.test_seed_base + 5000 + i  # Offset to ensure distinctness
            try:
                grid = self.grid_generator.generate_single_grid(seed=seed)
                grids.append(grid)
            except Exception as e:
                raise TestGenerationError(f"Failed to generate grid world #{i}: {str(e)}")
        
        return grids

    def generate_all_test_instances(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate all test instances and save them to a JSON file.

        Args:
            output_path: Path to save the JSON file. Defaults to config specified path.

        Returns:
            Dictionary containing the generated test data and metadata.
        """
        if output_path is None:
            output_path = self.config.test_output_path or "data/test_instances.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine counts from config, with defaults
        logic_count = self.config.test_logic_count or 50
        grid_count = self.config.test_grid_count or 50

        # Generate instances
        logic_proofs = self.generate_logic_proofs(logic_count)
        grid_worlds = self.generate_grid_worlds(grid_count)

        # Structure the output
        test_data = {
            "metadata": {
                "seed_base": self.test_seed_base,
                "logic_count": logic_count,
                "grid_count": grid_count,
                "total_instances": logic_count + grid_count,
                "generated_at": str(Path(output_path).stat().st_mtime) if output_path.exists() else "new"
            },
            "logic_proofs": logic_proofs,
            "grid_worlds": grid_worlds
        }

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)

        # Register checksum
        checksum = compute_file_sha256(output_path)
        save_checksums(str(output_path), checksum)

        return test_data


def main():
    """Main entry point for the test generator."""
    try:
        config = load_config()
        generator = TestInstanceGenerator(config)
        result = generator.generate_all_test_instances()
        
        print(f"Successfully generated {result['metadata']['total_instances']} test instances.")
        print(f"Logic proofs: {result['metadata']['logic_count']}")
        print(f"Grid worlds: {result['metadata']['grid_count']}")
        print(f"Saved to: {config.test_output_path}")
        
        return 0
    except TestGenerationError as e:
        print(f"Test generation failed: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
