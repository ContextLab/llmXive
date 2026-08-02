import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the DAG manifest file.
    
    Args:
        manifest_path: Path to the DAG manifest JSON file
        
    Returns:
        Dictionary containing the manifest data
    """
    logger.info(f"Loading DAG manifest from {manifest_path}")
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"DAG manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    logger.info(f"Loaded manifest with {len(manifest.get('entries', []))} entries")
    return manifest

def generate_prompts_for_seed(
    entries: List[Dict[str, Any]],
    seed: int,
    strategy: str,
    output_dir: Path
) -> List[str]:
    """
    Generate prompts for a specific seed and strategy.
    
    Args:
        entries: List of DAG manifest entries
        seed: Random seed for the generation
        strategy: Strategy name ('logical_ascending', 'logical_random', 'original_cds')
        output_dir: Directory to save generated prompt files
        
    Returns:
        List of paths to generated prompt files
    """
    logger.info(f"Generating prompts for seed={seed}, strategy={strategy}")
    
    random.seed(seed)
    
    # Filter and sort entries based on strategy
    filtered_entries = []
    
    if strategy == 'logical_ascending':
        # Sort by logical difficulty score (depth) in ascending order
        filtered_entries = sorted(
            entries,
            key=lambda x: x.get('logical_difficulty_score', 0)
        )
    elif strategy == 'logical_random':
        # Random shuffle with fixed seed
        filtered_entries = entries.copy()
        random.shuffle(filtered_entries)
    elif strategy == 'original_cds':
        # Sort by semantic curvature score (if available)
        filtered_entries = sorted(
            entries,
            key=lambda x: x.get('semantic_curvature_score', 0)
        )
    else:
        logger.warning(f"Unknown strategy: {strategy}, using original order")
        filtered_entries = entries
    
    # Create output subdirectory for this seed
    seed_output_dir = output_dir / strategy / str(seed)
    seed_output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Create a prompt file with the ordered examples
    prompt_file = seed_output_dir / 'prompt.json'
    
    prompt_data = {
        'seed': seed,
        'strategy': strategy,
        'examples': [
            {
                'id': entry.get('id'),
                'trace': entry.get('trace', ''),
                'depth': entry.get('logical_difficulty_score', 0),
                'curvature': entry.get('semantic_curvature_score', 0)
            }
            for entry in filtered_entries
        ]
    }
    
    with open(prompt_file, 'w', encoding='utf-8') as f:
        json.dump(prompt_data, f, indent=2)
    
    generated_files.append(str(prompt_file))
    logger.info(f"Generated prompt file: {prompt_file}")
    
    return generated_files

def run_batch(
    manifest: Dict[str, Any],
    seeds: List[int],
    strategies: List[str],
    output_dir: Path
) -> Dict[str, List[str]]:
    """
    Run batch generation for all seeds and strategies.
    
    Args:
        manifest: Loaded DAG manifest
        seeds: List of seeds to process
        strategies: List of strategies to generate
        output_dir: Base directory for output files
        
    Returns:
        Dictionary mapping strategy/seed to list of generated files
    """
    entries = manifest.get('entries', [])
    results = {}
    
    logger.info(f"Starting batch generation: {len(seeds)} seeds, {len(strategies)} strategies")
    
    for strategy in strategies:
        results[strategy] = []
        
        for seed in seeds:
            files = generate_prompts_for_seed(entries, seed, strategy, output_dir)
            results[strategy].extend(files)
    
    logger.info(f"Batch generation complete. Generated {sum(len(v) for v in results.values())} files")
    return results

def main():
    """
    Main entry point for the batch strategy runner.
    """
    parser = argparse.ArgumentParser(
        description='Generate prompts for multiple seeds and strategies'
    )
    parser.add_argument(
        '--manifest',
        type=str,
        default='data/processed/dag_manifest.json',
        help='Path to the DAG manifest file'
    )
    parser.add_argument(
        '--seeds',
        type=str,
        default='42,123,456,789,101112,131415,161718,192021,222324,252627',
        help='Comma-separated list of seeds'
    )
    parser.add_argument(
        '--strategies',
        type=str,
        default='logical_ascending,logical_random,original_cds',
        help='Comma-separated list of strategies'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed/prompts',
        help='Output directory for generated prompts'
    )
    
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    seeds = [int(s.strip()) for s in args.seeds.split(',')]
    strategies = [s.strip() for s in args.strategies.split(',')]
    
    if not manifest_path.exists():
        logger.error(f"DAG manifest not found: {manifest_path}")
        sys.exit(1)
    
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = run_batch(manifest, seeds, strategies, output_dir)
    
    # Summary
    total_files = sum(len(files) for files in results.values())
    logger.info(f"Generation complete. Total files: {total_files}")
    for strategy, files in results.items():
        logger.info(f"  {strategy}: {len(files)} files")
    
    sys.exit(0)

if __name__ == '__main__':
    main()