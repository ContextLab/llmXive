"""
Task T034: Generate metadata JSON files for each sparsity subset.

For each sparsity level subset (e.g., sparsity_1pct.csv, sparsity_25pct.csv),
this script generates a corresponding JSON metadata file containing:
- seed: The random seed used for sampling
- percentage: The sparsity percentage (e.g., 1, 5, 25)
- criteria: Description of the stratification criteria used
- checksum: SHA256 checksum of the subset file content

Output files are saved to: data/metadata/sparsity_<level>_<seed>.json
"""
import os
import sys
import json
import hashlib
import argparse
import glob
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.checksum_utils import compute_sha256

logger = get_logger(__name__)


def load_rss_manifest(manifest_path: str) -> dict:
    """
    Load the RSS manifest to retrieve the seed and criteria used.
    
    Args:
        manifest_path: Path to the RSS manifest JSON file.
        
    Returns:
        Dictionary containing 'seed' and 'criteria'.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"RSS manifest not found at {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)


def generate_metadata(
    subset_path: str,
    manifest: dict,
    output_dir: str,
    level_name: str,
    seed: int
) -> dict:
    """
    Generate metadata for a single sparsity subset.
    
    Args:
        subset_path: Path to the CSV subset file.
        manifest: Dictionary with RSS configuration (seed, criteria).
        output_dir: Directory to save the metadata JSON.
        level_name: String identifier for the level (e.g., '1pct', '25pct').
        seed: The random seed used.
        
    Returns:
        Dictionary containing the generated metadata.
    """
    if not os.path.exists(subset_path):
        raise FileNotFoundError(f"Subset file not found at {subset_path}")
    
    # Compute checksum of the file
    checksum = compute_sha256(subset_path)
    
    metadata = {
        "seed": seed,
        "percentage": int(level_name.replace('pct', '')),
        "criteria": manifest.get('criteria', 'Stratified sampling based on formation_energy'),
        "checksum": checksum
    }
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save metadata file
    output_filename = f"sparsity_{level_name}_{seed}.json"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Generated metadata for {level_name}: {output_path}")
    return metadata


def main():
    """Main entry point for generating sparsity metadata."""
    parser = argparse.ArgumentParser(description="Generate metadata for sparsity subsets.")
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/metadata/rss_config.json",
        help="Path to the RSS manifest/config file."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/processed",
        help="Directory containing sparsity subset CSV files."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/metadata",
        help="Directory to save generated metadata JSON files."
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="sparsity_*pct.csv",
        help="Glob pattern to match subset files."
    )
    
    args = parser.parse_args()
    
    logger.info(f"Loading RSS manifest from {args.manifest}")
    manifest = load_rss_manifest(args.manifest)
    
    seed = manifest.get('seed', 42)
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Find all matching subset files
    pattern = str(input_dir / args.pattern)
    subset_files = glob.glob(pattern)
    
    if not subset_files:
        logger.warning(f"No files found matching pattern: {pattern}")
        sys.exit(0)
    
    logger.info(f"Found {len(subset_files)} subset files.")
    
    generated_count = 0
    for subset_file in sorted(subset_files):
        # Extract level name from filename (e.g., 'sparsity_10pct.csv' -> '10pct')
        filename = os.path.basename(subset_file)
        level_name = filename.replace('.csv', '')
        
        try:
            generate_metadata(
                subset_path=subset_file,
                manifest=manifest,
                output_dir=str(output_dir),
                level_name=level_name,
                seed=seed
            )
            generated_count += 1
        except Exception as e:
            logger.error(f"Failed to generate metadata for {subset_file}: {e}")
            continue
    
    logger.info(f"Successfully generated metadata for {generated_count}/{len(subset_files)} subsets.")


if __name__ == "__main__":
    main()