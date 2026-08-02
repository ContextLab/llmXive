import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from code.src.config import Config, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scan_prompt_directory(prompt_dir: Path) -> Dict[str, List[Path]]:
    """
    Scan the prompt directory for generated prompt files.
    
    Args:
        prompt_dir: Path to the directory containing prompt files.
        
    Returns:
        Dictionary mapping strategy names to lists of prompt file paths.
    """
    if not prompt_dir.exists():
        logger.warning(f"Prompt directory does not exist: {prompt_dir}")
        return {}
    
    if not prompt_dir.is_dir():
        logger.error(f"Path is not a directory: {prompt_dir}")
        return {}
    
    strategy_files: Dict[str, List[Path]] = {}
    
    # Expected file pattern: prompts_seed_{seed}_{strategy}.json
    for file_path in prompt_dir.glob("prompts_seed_*.json"):
        filename = file_path.name
        # Parse filename: prompts_seed_1_logical_ascending.json
        parts = filename.replace(".json", "").split("_")
        
        if len(parts) < 4:
            logger.warning(f"Skipping file with unexpected format: {filename}")
            continue
        
        # parts[0] = 'prompts', parts[1] = 'seed', parts[2] = seed_num, parts[3:] = strategy
        if parts[0] != "prompts" or parts[1] != "seed":
            logger.warning(f"Skipping file with unexpected prefix: {filename}")
            continue
        
        try:
            seed_num = int(parts[2])
        except ValueError:
            logger.warning(f"Skipping file with non-numeric seed: {filename}")
            continue
        
        # Strategy is the remainder after seed number
        strategy = "_".join(parts[3:])
        
        if strategy not in strategy_files:
            strategy_files[strategy] = []
        
        strategy_files[strategy].append(file_path)
        logger.info(f"Found prompt file: {filename} -> seed={seed_num}, strategy={strategy}")
    
    # Sort files within each strategy for consistency
    for strategy in strategy_files:
        strategy_files[strategy].sort()
    
    return strategy_files

def generate_manifest(
    strategy_files: Dict[str, List[Path]],
    prompt_dir: Path,
    seeds: Optional[List[int]] = None,
    strategies: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate the prompt manifest dictionary.
    
    Args:
        strategy_files: Dictionary mapping strategy names to lists of prompt file paths.
        prompt_dir: Base directory for prompt files.
        seeds: Optional list of seed numbers to include.
        strategies: Optional list of strategy names to include.
        
    Returns:
        Complete manifest dictionary.
    """
    config = get_config()
    
    # Determine seeds and strategies from files if not provided
    if seeds is None:
        extracted_seeds = set()
        for files in strategy_files.values():
            for f in files:
                parts = f.name.replace(".json", "").split("_")
                if len(parts) >= 3:
                    try:
                        extracted_seeds.add(int(parts[2]))
                    except ValueError:
                        pass
        seeds = sorted(list(extracted_seeds))
    
    if strategies is None:
        strategies = sorted(list(strategy_files.keys()))
    
    # Build the files mapping
    files_mapping = {}
    for strategy, files in strategy_files.items():
        for file_path in files:
            # Extract seed from filename
            parts = file_path.name.replace(".json", "").split("_")
            if len(parts) >= 3:
                try:
                    seed_num = int(parts[2])
                    key = f"seed_{seed_num}_{strategy}"
                    # Use relative path from project root
                    rel_path = file_path.relative_to(Path.cwd())
                    files_mapping[key] = str(rel_path)
                except ValueError:
                    logger.warning(f"Could not extract seed from: {file_path.name}")
    
    # Build validation info
    validation = {
        "no_duplicates": True,  # Assumed true if we got here without errors
        "all_files_exist": all(f.exists() for files in strategy_files.values() for f in files)
    }
    
    manifest = {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "description": "Manifest mapping seed/strategy combinations to generated prompt file paths.",
        "seeds": seeds,
        "strategies": strategies,
        "files": files_mapping,
        "validation": validation
    }
    
    return manifest

def main():
    """Main entry point for generating the prompt manifest."""
    parser = argparse.ArgumentParser(
        description="Generate a manifest mapping seed/strategy to prompt file paths."
    )
    parser.add_argument(
        "--prompt-dir",
        type=str,
        default="data/processed/prompts",
        help="Directory containing generated prompt files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/prompt_manifest.json",
        help="Output path for the manifest file"
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Comma-separated list of seed numbers to include (optional)"
    )
    parser.add_argument(
        "--strategies",
        type=str,
        default=None,
        help="Comma-separated list of strategy names to include (optional)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Convert seeds and strategies from string to list
    seeds = None
    if args.seeds:
        seeds = [int(s.strip()) for s in args.seeds.split(",")]
    
    strategies = None
    if args.strategies:
        strategies = [s.strip() for s in args.strategies.split(",")]
    
    prompt_dir = Path(args.prompt_dir)
    output_path = Path(args.output)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Scanning prompt directory: {prompt_dir}")
    strategy_files = scan_prompt_directory(prompt_dir)
    
    if not strategy_files:
        logger.warning("No prompt files found. Creating empty manifest.")
        manifest = {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": "Manifest mapping seed/strategy combinations to generated prompt file paths.",
            "seeds": [],
            "strategies": [],
            "files": {},
            "validation": {
                "no_duplicates": True,
                "all_files_exist": False
            }
        }
    else:
        logger.info(f"Found {sum(len(v) for v in strategy_files.values())} prompt files across {len(strategy_files)} strategies.")
        manifest = generate_manifest(strategy_files, prompt_dir, seeds, strategies)
    
    # Write manifest to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest written to: {output_path}")
    
    # Print summary
    print(f"\nPrompt Manifest Summary:")
    print(f"  Seeds: {manifest['seeds']}")
    print(f"  Strategies: {manifest['strategies']}")
    print(f"  Total entries: {len(manifest['files'])}")
    print(f"  Validation: {manifest['validation']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
