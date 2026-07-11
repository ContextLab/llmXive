"""
Script to generate prompt ordering strategies from DAG manifest.
Implements T022: Logical Ascending sorter and strategy runner.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.prompt_gen import PromptGenerator
from code.src.parser_utils import load_json_file, save_json_file
from code.src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_examples_from_manifest(manifest_path: Path) -> List[Dict]:
    """
    Loads examples from the DAG manifest file.
    
    Args:
        manifest_path: Path to the dag_manifest.json file.
        
    Returns:
        List of example dictionaries.
    """
    logger.info(f"Loading examples from {manifest_path}")
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"DAG manifest not found: {manifest_path}")
    
    manifest = load_json_file(manifest_path)
    
    # Extract examples from manifest
    # Assuming manifest structure: {"entries": [...], "metadata": {...}}
    # or flat list of entries with 'id', 'input', 'output', etc.
    entries = manifest.get('entries', manifest)
    
    if not isinstance(entries, list):
        raise ValueError("Manifest must contain a list of entries")
    
    logger.info(f"Loaded {len(entries)} examples from manifest")
    return entries

def save_strategy_outputs(output_dir: Path, strategy_results: Dict[str, List[Dict]], seed: int):
    """
    Saves strategy outputs to JSON files.
    
    Args:
        output_dir: Directory to save output files.
        strategy_results: Dictionary mapping strategy names to ordered example lists.
        seed: Seed value used for generation.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for strategy_name, examples in strategy_results.items():
        output_path = output_dir / f"prompts_{strategy_name}_seed{seed}.json"
        save_json_file(examples, output_path)
        logger.info(f"Saved {strategy_name} strategy to {output_path} ({len(examples)} examples)")

def main():
    """Main entry point for prompt strategy generation."""
    parser = argparse.ArgumentParser(description="Generate prompt ordering strategies")
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
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic operations"
    )
    parser.add_argument(
        "--strategies",
        type=str,
        nargs="+",
        default=["logical_ascending", "logical_random"],
        help="Strategies to generate (logical_ascending, logical_random, original_cds)"
    )
    
    args = parser.parse_args()
    
    config = Config()
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    
    # Initialize generator
    generator = PromptGenerator(seed=args.seed)
    
    try:
        # Load examples
        examples = load_examples_from_manifest(manifest_path)
        
        if not examples:
            logger.warning("No examples found in manifest. Exiting.")
            return 1
        
        # Extract dag_manifest for depth lookups (the whole manifest is the lookup dict)
        dag_manifest = load_json_file(manifest_path)
        
        # Generate strategies
        logger.info(f"Generating strategies: {args.strategies}")
        strategy_results = generator.generate_strategies(
            examples=examples,
            dag_manifest=dag_manifest,
            strategies=args.strategies
        )
        
        # Save outputs
        save_strategy_outputs(output_dir, strategy_results, args.seed)
        
        # Generate summary manifest
        summary = {
            "seed": args.seed,
            "strategies": args.strategies,
            "input_manifest": str(manifest_path),
            "output_dir": str(output_dir),
            "total_examples": len(examples),
            "strategy_counts": {k: len(v) for k, v in strategy_results.items()}
        }
        
        summary_path = output_dir / f"strategy_summary_seed{args.seed}.json"
        save_json_file(summary, summary_path)
        logger.info(f"Saved strategy summary to {summary_path}")
        
        logger.info("Strategy generation completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during strategy generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
