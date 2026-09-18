"""
Test Instance Generator for Co-Evolving Policy Distillation.

Generates held-out test instances for both logic proofs and grid-world navigation.
Uses a separate seed range to ensure strict separation from the training set,
satisfying FR-004 and providing baseline measurement data.
"""
import random
import json
import os
import sys
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator
from src.utils.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestGenerationError(Exception):
    """Custom exception for test generation failures."""
    pass

class TestInstanceGenerator:
    """
    Generates held-out test instances using a distinct seed range
    to guarantee separation from training data.
    """

    def __init__(self, config: Config):
        self.config = config
        # Define a distinct seed range for test instances to ensure separation
        # Training uses seeds [0, TRAIN_SIZE), Test uses [TEST_OFFSET, TEST_OFFSET + TEST_SIZE)
        self.test_seed_offset = config.get('test_seed_offset', 10000)
        self.test_instance_count = config.get('test_instance_count', 50)
        
        self.logic_generator = LogicProofGenerator(config)
        self.grid_generator = GridWorldGenerator(config)

    def generate_logic_test_instances(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate logic proof test instances using a separate seed range.
        
        Args:
            count: Number of instances to generate. Defaults to config value.
            
        Returns:
            List of test instance dictionaries.
        """
        if count is None:
            count = self.test_instance_count
        
        instances = []
        base_seed = self.test_seed_offset + 1000  # Offset specifically for logic test data
        
        logger.info(f"Generating {count} logic test instances with base seed {base_seed}")
        
        for i in range(count):
            instance_seed = base_seed + i
            random.seed(instance_seed)
            
            try:
                # Generate a valid proof instance
                # We use the logic generator's internal method to create a single instance
                # The generator handles axiom selection and proof construction
                instance_data = self.logic_generator._generate_single_proof_instance()
                
                instance = {
                    "id": f"test_logic_{instance_seed}",
                    "domain": "logic",
                    "rule_set_id": f"rule_set_{random.randint(1, 5)}", # Assign a rule set ID
                    "instance_data": instance_data
                }
                
                # Validate the instance has required fields
                if not all(k in instance_data for k in ['axioms', 'target', 'proof_steps']):
                    raise TestGenerationError(f"Invalid logic instance generated: missing required fields")
                    
                instances.append(instance)
                
            except Exception as e:
                logger.warning(f"Failed to generate logic test instance {i}: {e}")
                # Skip invalid instances rather than failing the whole run
                # This matches the behavior in the training generators
                continue

        logger.info(f"Successfully generated {len(instances)} logic test instances")
        return instances

    def generate_grid_test_instances(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate grid-world test instances using a separate seed range.
        
        Args:
            count: Number of instances to generate. Defaults to config value.
            
        Returns:
            List of test instance dictionaries.
        """
        if count is None:
            count = self.test_instance_count
        
        instances = []
        base_seed = self.test_seed_offset + 5000  # Different offset for grid test data
        
        logger.info(f"Generating {count} grid test instances with base seed {base_seed}")
        
        for i in range(count):
            instance_seed = base_seed + i
            random.seed(instance_seed)
            
            try:
                # Generate a solvable grid instance
                instance_data = self.grid_generator._generate_single_grid_instance()
                
                instance = {
                    "id": f"test_grid_{instance_seed}",
                    "domain": "grid",
                    "rule_set_id": f"rule_set_{random.randint(1, 3)}", # Assign a rule set ID
                    "instance_data": instance_data
                }
                
                # Validate the instance has required fields
                if not all(k in instance_data for k in ['grid', 'start', 'goal', 'obstacles', 'rules']):
                    raise TestGenerationError(f"Invalid grid instance generated: missing required fields")
                    
                instances.append(instance)
                
            except Exception as e:
                logger.warning(f"Failed to generate grid test instance {i}: {e}")
                continue

        logger.info(f"Successfully generated {len(instances)} grid test instances")
        return instances

    def generate_all_test_instances(self) -> List[Dict[str, Any]]:
        """
        Generate all test instances (logic and grid) and combine them.
        
        Returns:
            Combined list of all test instances.
        """
        logger.info("Starting generation of all test instances")
        
        logic_instances = self.generate_logic_test_instances()
        grid_instances = self.generate_grid_test_instances()
        
        all_instances = logic_instances + grid_instances
        
        logger.info(f"Total test instances generated: {len(all_instances)}")
        return all_instances

    def save_test_instances(self, instances: List[Dict[str, Any]], output_path: str) -> None:
        """
        Save test instances to a JSON file.
        
        Args:
            instances: List of test instances to save.
            output_path: Path to the output JSON file.
        """
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(instances, f, indent=2)
        
        logger.info(f"Saved {len(instances)} test instances to {output_path}")

def main():
    """Main entry point for generating test instances."""
    logger.info("Starting Test Instance Generator")
    
    try:
        # Load configuration
        config = Config.load()
        
        # Create generator
        generator = TestInstanceGenerator(config)
        
        # Generate instances
        test_instances = generator.generate_all_test_instances()
        
        if not test_instances:
            raise TestGenerationError("No test instances were generated.")
        
        # Determine output path from config or default
        output_path = config.get('test_output_path', 'data/test_instances.json')
        
        # Save instances
        generator.save_test_instances(test_instances, output_path)
        
        logger.info("Test instance generation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Test instance generation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
