"""
Generate prompt manifest mapping seed/strategy to file paths.

This script scans the output directory of run_batch_strategies.py and
creates a manifest file (data/processed/prompt_manifest.json) that maps
each seed and strategy combination to its generated prompt file path.

This satisfies task T028.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.src.parser_utils import load_json_file, save_json_file

logger = logging.getLogger(__name__)

def scan_prompt_directory(prompt_dir: Path) -> List[Dict[str, Any]]:
    """Scan directory for prompt files and extract metadata."""
    if not prompt_dir.exists():
        logger.warning(f"Prompt directory does not exist: {prompt_dir}")
        return []
    
    entries = []
    for file_path in prompt_dir.glob("prompts_seed_*.json"):
        try:
            # Extract seed and strategy from filename
            # Format: prompts_seed_{seed}_{strategy}.json
            stem = file_path.stem
            parts = stem.split("_")
            
            if len(parts) >= 4 and parts[0] == "prompts" and parts[1] == "seed":
                seed = int(parts[2])
                strategy = parts[3]
                
                # Load file to get count
                data = load_json_file(file_path)
                prompt_count = len(data.get("prompts", [])) if isinstance(data, dict) else 0
                
                entries.append({
                    "seed": seed,
                    "strategy": strategy,
                    "file_path": str(file_path),
                    "prompt_count": prompt_count,
                    "file_size_bytes": file_path.stat().st_size
                })
            else:
                logger.warning(f"Unexpected filename format: {file_path.name}")
                
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            continue
    
    return entries

def generate_manifest(prompt_dir: Path, output_path: Path) -> Dict[str, Any]:
    """Generate prompt manifest from scanned directory."""
    entries = scan_prompt_directory(prompt_dir)
    
    # Sort by seed then strategy
    entries.sort(key=lambda x: (x["seed"], x["strategy"]))
    
    manifest = {
        "generated_at": str(Path(__file__).resolve()),
        "prompt_directory": str(prompt_dir),
        "total_files": len(entries),
        "total_prompts": sum(e["prompt_count"] for e in entries),
        "entries": entries
    }
    
    # Save manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json_file(manifest, output_path)
    
    logger.info(f"Generated manifest with {len(entries)} entries at {output_path}")
    return manifest

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate prompt manifest from batch outputs"
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
        help="Output path for manifest file"
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
    
    prompt_dir = Path(args.prompt_dir)
    output_path = Path(args.output)
    
    manifest = generate_manifest(prompt_dir, output_path)
    
    # Print summary
    print(f"\nPrompt Manifest Summary:")
    print(f"  Total files: {manifest['total_files']}")
    print(f"  Total prompts: {manifest['total_prompts']}")
    print(f"  Manifest saved to: {output_path}")
    
    if manifest['total_files'] == 0:
        logger.warning("No prompt files found. Ensure run_batch_strategies.py has been executed.")

if __name__ == "__main__":
    main()
