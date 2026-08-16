import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.src.config import get_config
from code.src.prompt_gen import PromptGenerator
from code.src.parser_utils import load_json_file, save_json_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

STRATEGIES = ["original_cds", "logical_ascending", "logical_random"]

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the DAG manifest containing parsed traces and metadata."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"DAG manifest not found at {manifest_path}")
    return load_json_file(manifest_path)

def generate_prompts_for_seed(
    generator: PromptGenerator,
    manifest_data: Dict[str, Any],
    seed: int,
    strategy: str,
    output_dir: Path,
    max_examples: Optional[int] = None
) -> List[str]:
    """
    Generate prompts for a single seed and strategy.

    Args:
        generator: The PromptGenerator instance.
        manifest_data: The full DAG manifest data.
        seed: The random seed for this batch.
        strategy: One of 'original_cds', 'logical_ascending', 'logical_random'.
        output_dir: Directory to save the generated prompt files.
        max_examples: Optional limit on number of examples to include per prompt.

    Returns:
        List of file paths generated.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}. Must be one of {STRATEGIES}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract examples from manifest
    # Assuming manifest structure: {"entries": [...], "metadata": {...}}
    entries = manifest_data.get("entries", [])
    if not entries:
        logger.warning(f"No entries found in manifest for seed {seed}")
        return []

    # Generate the prompt configuration for this seed/strategy
    # The generator handles sorting/shuffling internally based on strategy
    prompt_files = []

    # We create one prompt file per seed/strategy combination containing
    # the ordered set of examples for that configuration.
    # In a many-shot setting, this might be a single file per seed/strategy
    # or split by prompt length. Here we assume one file per seed/strategy.
    output_filename = f"seed_{seed}_{strategy}.json"
    output_path = output_dir / output_filename

    try:
        # Use the generator to create the ordered list of examples
        ordered_examples = generator.generate_ordered_examples(
            examples=entries,
            strategy=strategy,
            seed=seed,
            max_examples=max_examples
        )

        # Save the ordered examples to a JSON file
        # Structure: { "seed": int, "strategy": str, "examples": [...] }
        output_data = {
            "seed": seed,
            "strategy": strategy,
            "num_examples": len(ordered_examples),
            "examples": ordered_examples
        }

        save_json_file(output_data, output_path)
        prompt_files.append(str(output_path))
        logger.info(f"Generated {output_path} with {len(ordered_examples)} examples")

    except Exception as e:
        logger.error(f"Failed to generate prompts for seed {seed}, strategy {strategy}: {e}")
        raise

    return prompt_files

def run_batch(
    manifest_path: Path,
    seeds: List[int],
    output_base_dir: Path,
    max_examples_per_prompt: Optional[int] = None,
    strategies: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run prompt generation for multiple seeds and strategies.

    Args:
        manifest_path: Path to the DAG manifest JSON.
        seeds: List of random seeds to process.
        output_base_dir: Base directory for output prompts.
        max_examples_per_prompt: Limit on examples per prompt file.
        strategies: List of strategies to run (defaults to all).

    Returns:
        Summary dictionary of generated files.
    """
    strategies = strategies or STRATEGIES
    logger.info(f"Starting batch generation for {len(seeds)} seeds and {len(strategies)} strategies")

    # Load manifest
    manifest_data = load_manifest(manifest_path)

    # Initialize generator
    config = get_config()
    generator = PromptGenerator(config=config)

    results = {
        "seeds": seeds,
        "strategies": strategies,
        "output_dir": str(output_base_dir),
        "files": [],
        "errors": []
    }

    for seed in seeds:
        logger.info(f"Processing seed {seed}")
        for strategy in strategies:
            try:
                seed_output_dir = output_base_dir
                generated_files = generate_prompts_for_seed(
                    generator=generator,
                    manifest_data=manifest_data,
                    seed=seed,
                    strategy=strategy,
                    output_dir=seed_output_dir,
                    max_examples=max_examples_per_prompt
                )
                results["files"].extend(generated_files)
            except Exception as e:
                error_msg = f"Seed {seed}, Strategy {strategy}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

    logger.info(f"Batch generation complete. Generated {len(results['files'])} files.")
    if results["errors"]:
        logger.warning(f"Encountered {len(results['errors'])} errors during generation.")

    return results

def main():
    parser = argparse.ArgumentParser(
        description="Batch runner to generate prompts for multiple seeds across strategies."
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to the DAG manifest JSON file."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42, 123, 456, 789, 101112],
        help="List of random seeds to process."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/prompts",
        help="Directory to save generated prompt files."
    )
    parser.add_argument(
        "--strategies",
        type=str,
        nargs="+",
        choices=STRATEGIES,
        help="Specific strategies to run (default: all)."
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=None,
        help="Maximum number of examples per prompt file."
    )

    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)

    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        sys.exit(1)

    try:
        results = run_batch(
            manifest_path=manifest_path,
            seeds=args.seeds,
            output_base_dir=output_dir,
            max_examples_per_prompt=args.max_examples,
            strategies=args.strategies
        )

        # Save a summary manifest
        summary_path = output_dir / "batch_run_summary.json"
        save_json_file(results, summary_path)
        logger.info(f"Summary saved to {summary_path}")

    except Exception as e:
        logger.error(f"Batch run failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
