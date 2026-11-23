"""
Baseline Orchestrator for llmXive.

This module implements the orchestration logic to generate baseline manifests
for all required seeds. It iterates through the seed sequence, calls the
baseline generator for each seed, handles retry logic for unstable seeds,
and ensures all 5 valid manifests are generated before proceeding.

This task (T019b) provides the orchestration loop but does NOT execute the
actual training runs; T019c/T019d execute the runs.
"""
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.llmxive.baseline_generator import generate_baseline_manifest
from src.llmxive.config import get_deterministic_config
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR, ERR_SEED_UNSTABLE
from src.llmxive.seed_manager import SeedManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaselineOrchestrator:
    """
    Orchestrates the generation of baseline manifests for all required seeds.

    This class manages the loop that calls baseline_generator.py for each seed,
    handles retry logic for unstable seeds, and ensures all 5 valid manifests
    are generated before proceeding.
    """

    def __init__(self, model_id: str, num_valid_seeds: int = 5, max_attempts_per_seed: Optional[int] = None):
        """
        Initialize the BaselineOrchestrator.

        Args:
            model_id: The model identifier (e.g., 'phi2', 'qwen15')
            num_valid_seeds: Number of valid seeds to generate (default: 5 per FR-004)
            max_attempts_per_seed: Maximum attempts per seed slot. If None, infinite retry.
        """
        self.model_id = model_id
        self.num_valid_seeds = num_valid_seeds
        self.max_attempts_per_seed = max_attempts_per_seed
        self.manifest_dir = Path("data/processed/baseline_manifests")
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize seed manager
        self.seed_manager = SeedManager()

    def _get_manifest_path(self, seed_id: int) -> Path:
        """Get the path for a seed's manifest file."""
        return self.manifest_dir / f"{self.model_id}_{seed_id}.json"

    def _load_existing_manifest(self, seed_id: int) -> Optional[Dict[str, Any]]:
        """Load an existing manifest if it exists."""
        path = self._get_manifest_path(seed_id)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load existing manifest for seed {seed_id}: {e}")
        return None

    def _generate_single_baseline(self, seed_id: int) -> Dict[str, Any]:
        """
        Generate a single baseline manifest for a specific seed.

        Args:
            seed_id: The seed identifier

        Returns:
            Dictionary containing the baseline manifest data

        Raises:
            ERR_SEED_UNSTABLE: If the seed fails stability verification
            DATA_INTEGRITY_ERROR: If manifest generation fails
        """
        logger.info(f"Generating baseline manifest for seed {seed_id}...")
        
        try:
            # Generate the baseline manifest
            manifest = generate_baseline_manifest(
                model_id=self.model_id,
                seed=seed_id,
                steps=50
            )
            
            # Verify the manifest was generated successfully
            if not manifest or 'status' not in manifest:
                raise DATA_INTEGRITY_ERROR(f"Failed to generate manifest for seed {seed_id}")
            
            # Check stability status
            if manifest.get('status') == 'UNSTABLE':
                raise ERR_SEED_UNSTABLE(f"Seed {seed_id} failed stability verification")
            
            # Save the manifest
            manifest_path = self._get_manifest_path(seed_id)
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Successfully generated and saved manifest for seed {seed_id}")
            return manifest

        except ERR_SEED_UNSTABLE:
            raise
        except Exception as e:
            logger.error(f"Failed to generate baseline for seed {seed_id}: {e}")
            raise DATA_INTEGRITY_ERROR(f"Failed to generate baseline for seed {seed_id}: {e}")

    def orchestrate(self, seed_sequence: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Orchestrate the generation of baseline manifests for all required seeds.

        This method implements the loop that calls baseline_generator.py for each
        seed in the sequence, handles retry logic for unstable seeds, and ensures
        all 5 valid manifests are generated before proceeding.

        Args:
            seed_sequence: Optional list of seeds to use. If None, uses the
                          deterministic sequence from config.

        Returns:
            List of successfully generated manifest dictionaries

        Raises:
            DATA_INTEGRITY_ERROR: If unable to generate required number of valid seeds
        """
        if seed_sequence is None:
            # Get deterministic seed sequence from config
            seed_sequence = get_deterministic_config()['seed_sequence']
        
        logger.info(f"Starting baseline orchestration for model {self.model_id}")
        logger.info(f"Seed sequence: {seed_sequence}")
        
        valid_manifests = []
        seed_index = 0
        attempts_per_seed = {}
        
        while len(valid_manifests) < self.num_valid_seeds and seed_index < len(seed_sequence):
            current_seed = seed_sequence[seed_index]
            
            # Track attempts for this seed
            if current_seed not in attempts_per_seed:
                attempts_per_seed[current_seed] = 0
            
            # Check max attempts constraint
            if self.max_attempts_per_seed is not None:
                if attempts_per_seed[current_seed] >= self.max_attempts_per_seed:
                    logger.warning(f"Max attempts reached for seed {current_seed}, skipping")
                    seed_index += 1
                    continue
            
            try:
                # Generate baseline for current seed
                manifest = self._generate_single_baseline(current_seed)
                valid_manifests.append(manifest)
                
                # Reset attempt counter for successful seed
                attempts_per_seed[current_seed] = 0
                seed_index += 1
                
            except ERR_SEED_UNSTABLE as e:
                logger.warning(f"Seed {current_seed} unstable: {e}")
                attempts_per_seed[current_seed] = attempts_per_seed.get(current_seed, 0) + 1
                
                # If we have max attempts, move to next seed
                if self.max_attempts_per_seed is not None and attempts_per_seed[current_seed] >= self.max_attempts_per_seed:
                    logger.info(f"Moving to next seed after {attempts_per_seed[current_seed]} attempts")
                    seed_index += 1
                
                # If infinite retry, stay on same seed (don't increment seed_index)
                # The next iteration will retry the same seed
                
            except DATA_INTEGRITY_ERROR as e:
                logger.error(f"Data integrity error for seed {current_seed}: {e}")
                seed_index += 1
                # Move to next seed on data integrity errors
        
        if len(valid_manifests) < self.num_valid_seeds:
            raise DATA_INTEGRITY_ERROR(
                f"Failed to generate {self.num_valid_seeds} valid manifests. "
                f"Only generated {len(valid_manifests)} valid manifests."
            )
        
        logger.info(f"Successfully orchestrated generation of {len(valid_manifests)} valid manifests")
        return valid_manifests

    def get_generated_manifests(self) -> List[Path]:
        """
        Get paths to all generated manifest files.

        Returns:
            List of Path objects pointing to generated manifest files
        """
        return list(self.manifest_dir.glob(f"{self.model_id}_*.json"))

def main():
    """
    Main entry point for baseline orchestration.

    This function demonstrates the usage of BaselineOrchestrator by
    generating baseline manifests for a specified model.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Orchestrate baseline manifest generation')
    parser.add_argument('--model', type=str, required=True, 
                      choices=['phi2', 'qwen15'],
                      help='Model to generate baselines for')
    parser.add_argument('--seeds', type=int, default=5,
                      help='Number of valid seeds to generate')
    parser.add_argument('--max-attempts', type=int, default=None,
                      help='Maximum attempts per seed (None for infinite retry)')
    
    args = parser.parse_args()
    
    orchestrator = BaselineOrchestrator(
        model_id=args.model,
        num_valid_seeds=args.seeds,
        max_attempts_per_seed=args.max_attempts
    )
    
    try:
        manifests = orchestrator.orchestrate()
        logger.info(f"Orchestration complete. Generated {len(manifests)} manifests:")
        for manifest in manifests:
            logger.info(f"  Seed {manifest['seed_id']}: {manifest['status']}")
    except DATA_INTEGRITY_ERROR as e:
        logger.error(f"Orchestration failed: {e}")
        raise

if __name__ == '__main__':
    main()
