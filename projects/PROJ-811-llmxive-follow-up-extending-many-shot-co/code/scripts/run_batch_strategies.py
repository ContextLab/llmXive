"""
Batch runner to generate prompts for multiple seeds across three strategies.

This script orchestrates the prompt generation process for User Story 2 (US2).
It iterates over a list of configured seeds and three prompt strategies:
1. Logical Ascending (sorted by DAG depth)
2. Logical Random (shuffled with fixed seed)
3. Original CDS (sorted by Semantic Curvature)

Outputs are saved to data/processed/prompts/ in JSON format.
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.src.config import get_config
from code.src.prompt_gen import PromptGenerator
from code.src.parser_utils import load_json_file, save_json_file

logger = logging.getLogger(__name__)

STRATEGIES = [
    "logical_ascending",
    "logical_random",
    "original_cds"
]

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the DAG manifest containing parsed traces and metadata."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"DAG manifest not found at {manifest_path}")
    
    logger.info(f"Loading DAG manifest from {manifest_path}")
    data = load_json_file(manifest_path)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected manifest to be a list, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} entries from manifest")
    return data

def generate_prompts_for_seed(
    generator: PromptGenerator,
    examples: List[Dict[str, Any]],
    seed: int,
    strategy: str,
    output_dir: Path
) -> Optional[Path]:
    """Generate prompts for a single seed and strategy."""
    try:
        logger.info(f"Generating prompts for seed={seed}, strategy={strategy}")
        
        # Generate the ordered examples based on strategy
        ordered_examples = generator.generate_ordering(
            examples=examples,
            strategy=strategy,
            seed=seed
        )
        
        if not ordered_examples:
            logger.warning(f"No examples generated for seed={seed}, strategy={strategy}")
            return None
        
        # Assemble prompts
        prompt_data = generator.assemble_prompts(
            examples=ordered_examples,
            seed=seed,
            strategy=strategy
        )
        
        # Save to file
        output_file = output_dir / f"prompts_seed_{seed}_{strategy}.json"
        save_json_file(prompt_data, output_file)
        
        logger.info(f"Saved {len(prompt_data['prompts'])} prompts to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to generate prompts for seed={seed}, strategy={strategy}: {e}", exc_info=True)
        return None

def run_batch(
    config: Any,
    manifest_path: Path,
    output_dir: Path,
    seeds: List[int],
    strategies: List[str]
) -> Dict[str, Any]:
    """Run batch prompt generation for all seeds and strategies."""
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load manifest
    try:
        examples = load_manifest(manifest_path)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return {"status": "failed", "error": str(e)}
    
    # Initialize generator
    generator = PromptGenerator(config)
    
    # Track results
    results = {
        "seeds_processed": [],
        "strategies_processed": [],
        "outputs": [],
        "errors": [],
        "total_prompts_generated": 0
    }
    
    for seed in seeds:
        for strategy in strategies:
            if strategy not in STRATEGIES:
                logger.warning(f"Unknown strategy {strategy} for seed {seed}, skipping")
                continue
            
            output_file = generate_prompts_for_seed(
                generator=generator,
                examples=examples,
                seed=seed,
                strategy=strategy,
                output_dir=output_dir
            )
            
            if output_file:
                results["seeds_processed"].append(seed)
                results["strategies_processed"].append(strategy)
                results["outputs"].append({
                    "seed": seed,
                    "strategy": strategy,
                    "output_file": str(output_file)
                })
            else:
                results["errors"].append({
                    "seed": seed,
                    "strategy": strategy,
                    "error": "Generation failed"
                })
    
    results["status"] = "completed"
    logger.info(f"Batch run completed. Generated {results['total_prompts_generated']} prompts across {len(results['outputs'])} configurations.")
    return results

def main():
    """Main entry point for the batch runner."""
    parser = argparse.ArgumentParser(
        description="Batch runner for generating prompts across seeds and strategies"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/processed/dag_manifest.json",
        help="Path to DAG manifest file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/prompts",
        help="Output directory for generated prompts"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=None,
        help="List of seeds to process (overrides config)"
    )
    parser.add_argument(
        "--strategies",
        type=str,
        nargs="+",
        default=None,
        help="List of strategies to process (overrides config)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Load config
    try:
        config = get_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Determine seeds and strategies
    seeds = args.seeds if args.seeds else config.get("experiment", {}).get("seeds", [42, 123, 456])
    strategies = args.strategies if args.strategies else config.get("experiment", {}).get("strategies", STRATEGIES)
    
    logger.info(f"Processing {len(seeds)} seeds: {seeds}")
    logger.info(f"Processing {len(strategies)} strategies: {strategies}")
    
    # Resolve paths
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    
    # Run batch
    results = run_batch(
        config=config,
        manifest_path=manifest_path,
        output_dir=output_dir,
        seeds=seeds,
        strategies=strategies
    )
    
    # Save run report
    report_path = output_dir / "batch_run_report.json"
    save_json_file(results, report_path)
    logger.info(f"Saved batch run report to {report_path}")
    
    # Exit with appropriate code
    if results.get("status") == "failed":
        logger.error("Batch run failed")
        sys.exit(1)
    else:
        logger.info("Batch run completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
