import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.src.config import PROJECT_ROOT
from code.src.parser_utils import load_json_file, save_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scan_prompt_directory(prompt_dir: Path) -> List[Dict[str, Any]]:
    """
    Scan the prompt directory for generated prompt files.
    
    Expects files in the format:
    <seed>_<strategy>.json
    
    Returns a list of metadata dictionaries for each found prompt.
    """
    if not prompt_dir.exists():
        logger.warning(f"Prompt directory does not exist: {prompt_dir}")
        return []

    entries = []
    for file_path in prompt_dir.iterdir():
        if file_path.is_file() and file_path.suffix == '.json':
            # Parse filename: seed_strategy.json
            stem = file_path.stem
            parts = stem.split('_')
            
            if len(parts) >= 2:
                # Assume format: seed_strategy (e.g., seed_42_logical_ascending)
                # Strategy might be multi-word, so join everything after the first part
                seed = parts[0]
                strategy = '_'.join(parts[1:])
                
                try:
                    # Load the prompt file to verify it's valid JSON and extract metadata
                    with open(file_path, 'r', encoding='utf-8') as f:
                        prompt_data = json.load(f)
                    
                    # Extract metadata from the prompt data if available
                    entry = {
                        "seed": seed,
                        "strategy": strategy,
                        "file_path": str(file_path.relative_to(PROJECT_ROOT)),
                        "absolute_path": str(file_path),
                        "num_examples": len(prompt_data.get('examples', [])),
                        "target_task": prompt_data.get('target_task', 'unknown'),
                        "model": prompt_data.get('model', 'unknown')
                    }
                    entries.append(entry)
                    logger.debug(f"Found prompt: {file_path.name} -> seed={seed}, strategy={strategy}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON file {file_path}: {e}")
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            else:
                logger.warning(f"Skipping file with unexpected naming format: {file_path.name}")
    
    return entries


def generate_manifest(prompt_dir: Path, output_path: Path) -> Dict[str, Any]:
    """
    Generate a manifest JSON file mapping seed/strategy to file paths.
    
    Args:
        prompt_dir: Directory containing generated prompt files
        output_path: Path where the manifest JSON should be written
    
    Returns:
        The manifest dictionary
    """
    # Scan for prompts
    prompt_entries = scan_prompt_directory(prompt_dir)
    
    if not prompt_entries:
        logger.warning(f"No valid prompt files found in {prompt_dir}")
        manifest = {
            "metadata": {
                "generated_from": str(prompt_dir.relative_to(PROJECT_ROOT)),
                "total_prompts": 0,
                "strategies_found": [],
                "seeds_found": []
            },
            "prompts": []
        }
    else:
        # Organize by seed and strategy
        manifest = {
            "metadata": {
                "generated_from": str(prompt_dir.relative_to(PROJECT_ROOT)),
                "total_prompts": len(prompt_entries),
                "strategies_found": sorted(list(set(e["strategy"] for e in prompt_entries))),
                "seeds_found": sorted(list(set(e["seed"] for e in prompt_entries)))
            },
            "prompts": prompt_entries
        }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save manifest
    save_json_file(manifest, output_path)
    logger.info(f"Manifest generated with {len(prompt_entries)} entries: {output_path}")
    
    return manifest


def main():
    """
    Main entry point for generating the prompt manifest.
    
    Usage:
        python -m scripts.generate_prompt_manifest --prompt_dir data/processed/prompts --output data/processed/prompt_manifest.json
    """
    parser = argparse.ArgumentParser(
        description="Generate a manifest JSON mapping seed/strategy to prompt file paths."
    )
    parser.add_argument(
        "--prompt_dir",
        type=str,
        default="data/processed/prompts",
        help="Directory containing generated prompt JSON files (default: data/processed/prompts)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/prompt_manifest.json",
        help="Output path for the manifest JSON (default: data/processed/prompt_manifest.json)"
    )
    
    args = parser.parse_args()
    
    prompt_dir = Path(args.prompt_dir)
    output_path = Path(args.output)
    
    # Make paths absolute relative to project root
    if not prompt_dir.is_absolute():
        prompt_dir = PROJECT_ROOT / prompt_dir
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    
    logger.info(f"Scanning prompt directory: {prompt_dir}")
    logger.info(f"Output manifest path: {output_path}")
    
    try:
        manifest = generate_manifest(prompt_dir, output_path)
        logger.info("Manifest generation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
