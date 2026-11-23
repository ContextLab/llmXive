"""
Test Instance Generator for Co-Evolving Policy Distillation.

Generates held-out test instances for both logic proofs and grid-world tasks.
Uses a disjoint seed range from the training set to ensure strict separation
(FR-004).
"""

import random
import json
import os
import sys
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Import existing generators
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator
from src.utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestGenerationError(Exception):
    """Exception raised when test instance generation fails."""
    pass

class TestInstanceGenerator:
    """
    Generates held-out test instances using a disjoint seed range.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the generator.

        Args:
            config: Configuration object. If None, loads default config.
        """
        self.config = config or Config()
        self.logic_generator = LogicProofGenerator(self.config)
        self.grid_generator = GridWorldGenerator(self.config)
        
        # Define disjoint seed range for test instances
        # Training starts at TRAIN_SEED_START, Test starts at TEST_SEED_START
        self.test_seed_start = self.config.TEST_SEED_START
        self.num_test_instances = self.config.NUM_TEST_INSTANCES
        
        logger.info(f"Initialized TestInstanceGenerator with seed range: {self.test_seed_start} to {self.test_seed_start + self.num_test_instances}")

    def _generate_logic_test_instances(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate a specified number of logic proof test instances.

        Args:
            count: Number of instances to generate.

        Returns:
            List of test instance dictionaries.
        """
        instances = []
        seeds_used = []

        for i in range(count):
            seed = self.test_seed_start + i
            seeds_used.append(seed)
            instance_id = f"logic_test_{seed}"

            try:
                # Generate a single instance with the specific seed
                # The generator handles the retry logic internally
                instance = self.logic_generator.generate_single_instance(
                    seed=seed,
                    rule_set_id=f"rule_set_logic_{seed % 5}"  # Distribute across rule sets
                )
                
                if instance:
                    test_instance = {
                        "id": instance_id,
                        "domain": "logic",
                        "rule_set_id": instance.get("rule_set_id", f"rule_set_logic_{seed % 5}"),
                        "instance_data": {
                            "problem": instance.get("problem", ""),
                            "solution": instance.get("solution", "")
                        }
                    }
                    instances.append(test_instance)
                    logger.debug(f"Generated logic test instance: {instance_id}")
                else:
                    logger.warning(f"Failed to generate logic test instance for seed {seed} after retries. Skipping.")

            except Exception as e:
                logger.error(f"Error generating logic test instance {instance_id}: {e}")
                # Continue with next instance rather than failing the whole batch

        logger.info(f"Generated {len(instances)} logic test instances from seeds {seeds_used}")
        return instances

    def _generate_grid_test_instances(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate a specified number of grid-world test instances.

        Args:
            count: Number of instances to generate.

        Returns:
            List of test instance dictionaries.
        """
        instances = []
        seeds_used = []

        for i in range(count):
            seed = self.test_seed_start + count + i  # Offset to ensure disjoint seeds even within test set
            seeds_used.append(seed)
            instance_id = f"grid_test_{seed}"

            try:
                # Generate a single instance with the specific seed
                instance = self.grid_generator.generate_single_instance(
                    seed=seed,
                    rule_set_id=f"rule_set_grid_{seed % 4}"  # Distribute across rule sets
                )
                
                if instance:
                    test_instance = {
                        "id": instance_id,
                        "domain": "grid",
                        "rule_set_id": instance.get("rule_set_id", f"rule_set_grid_{seed % 4}"),
                        "instance_data": {
                            "problem": instance.get("problem", ""),
                            "solution": instance.get("solution", "")
                        }
                    }
                    instances.append(test_instance)
                    logger.debug(f"Generated grid test instance: {instance_id}")
                else:
                    logger.warning(f"Failed to generate grid test instance for seed {seed} after retries. Skipping.")

            except Exception as e:
                logger.error(f"Error generating grid test instance {instance_id}: {e}")
                # Continue with next instance rather than failing the whole batch

        logger.info(f"Generated {len(instances)} grid test instances from seeds {seeds_used}")
        return instances

    def generate_all_test_instances(self) -> List[Dict[str, Any]]:
        """
        Generate all held-out test instances (both logic and grid).

        Returns:
            List of all test instance dictionaries.
        """
        logger.info("Starting test instance generation...")
        
        # Calculate split: half logic, half grid (or use config if specified)
        logic_count = self.num_test_instances // 2
        grid_count = self.num_test_instances - logic_count

        logger.info(f"Generating {logic_count} logic and {grid_count} grid test instances")

        logic_instances = self._generate_logic_test_instances(logic_count)
        grid_instances = self._generate_grid_test_instances(grid_count)

        all_instances = logic_instances + grid_instances
        
        logger.info(f"Successfully generated {len(all_instances)} total test instances")
        return all_instances

    def save_test_instances(self, output_path: str, instances: List[Dict[str, Any]]) -> None:
        """
        Save test instances to a JSON file.

        Args:
            output_path: Path to the output JSON file.
            instances: List of test instance dictionaries.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(instances, f, indent=2)

        logger.info(f"Saved {len(instances)} test instances to {output_path}")

    def run(self, output_path: str = "data/test_instances.json") -> List[Dict[str, Any]]:
        """
        Main entry point to generate and save test instances.

        Args:
            output_path: Path to save the output JSON file.

        Returns:
            List of generated test instances.
        """
        logger.info(f"Running test generation pipeline, output: {output_path}")
        
        instances = self.generate_all_test_instances()
        
        if not instances:
            logger.error("No test instances were generated. This may indicate a failure in the generators.")
            # We do not raise here to allow the pipeline to continue if partial data is acceptable,
            # but the validation step (T015a) should catch this.
        
        self.save_test_instances(output_path, instances)
        
        return instances

def main():
    """CLI entry point for test instance generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate held-out test instances")
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/test_instances.json",
        help="Output path for test instances JSON"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Override the number of test instances to generate (uses config default if not set)"
    )
    parser.add_argument(
        "--seed-start",
        type=int,
        default=None,
        help="Override the starting seed for test instances"
    )

    args = parser.parse_args()

    try:
        config = Config()
        
        # Apply CLI overrides
        if args.count is not None:
            config.NUM_TEST_INSTANCES = args.count
        if args.seed_start is not None:
            config.TEST_SEED_START = args.seed_start

        generator = TestInstanceGenerator(config)
        generator.run(output_path=args.output)
        
        logger.info("Test instance generation completed successfully.")
        return 0

    except TestGenerationError as e:
        logger.error(f"Test generation failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during test generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
