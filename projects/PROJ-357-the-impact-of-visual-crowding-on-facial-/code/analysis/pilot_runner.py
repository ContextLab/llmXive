import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path to ensure imports work regardless of cwd
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.synthetic_data_generator import load_manifest, generate_synthetic_responses, save_responses
from config import get_seed, set_all_seeds, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: Path) -> list:
    """Load the stimuli manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    # Handle both list format and dict format with 'stimuli' key
    if isinstance(manifest_data, list):
        return manifest_data
    elif isinstance(manifest_data, dict) and 'stimuli' in manifest_data:
        return manifest_data['stimuli']
    else:
        raise ValueError("Manifest must be a list or a dict with 'stimuli' key")

def run_pilot(
    manifest_path: Path,
    output_dir: Path,
    num_participants: int = 10,
    seed: int = 42
) -> dict:
    """
    Execute the synthetic pilot study.
    
    Args:
        manifest_path: Path to stimuli_manifest.json
        output_dir: Directory to save raw response data
        num_participants: Number of simulated participants
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary with pilot run statistics
    """
    logger.info(f"Starting synthetic pilot with {num_participants} participants")
    
    # Ensure output directory exists
    ensure_directories([output_dir])
    
    # Set seed
    set_all_seeds(seed)
    
    # Load manifest
    logger.info(f"Loading manifest from {manifest_path}")
    stimuli = load_manifest(manifest_path)
    logger.info(f"Loaded {len(stimuli)} stimuli")
    
    if not stimuli:
        raise ValueError("Manifest contains no stimuli to process")
    
    # Generate responses
    logger.info("Generating synthetic responses...")
    responses = generate_synthetic_responses(
        stimuli=stimuli,
        num_participants=num_participants,
        seed=seed
    )
    
    logger.info(f"Generated {len(responses)} raw responses")
    
    # Save responses
    output_file = output_dir / "raw_synthetic_responses.csv"
    save_responses(responses, output_file)
    
    logger.info(f"Saved raw responses to {output_file}")
    
    # Compute summary statistics
    stats = {
        "num_stimuli": len(stimuli),
        "num_participants": num_participants,
        "total_responses": len(responses),
        "output_file": str(output_file),
        "seed": seed
    }
    
    return stats

def main():
    parser = argparse.ArgumentParser(
        description="Execute the synthetic pilot study for visual crowding research"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/interim/stimuli_manifest.json",
        help="Path to stimuli manifest JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/interim",
        help="Directory to save raw response data"
    )
    parser.add_argument(
        "--participants",
        type=int,
        default=10,
        help="Number of simulated participants"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed (default: from config)"
    )
    
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        sys.exit(1)
    
    try:
        stats = run_pilot(
            manifest_path=manifest_path,
            output_dir=output_dir,
            num_participants=args.participants,
            seed=args.seed
        )
        
        logger.info("Pilot run completed successfully")
        logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
        
        # Write stats to a log file for verification
        stats_file = output_dir / "pilot_run_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
    except Exception as e:
        logger.error(f"Pilot run failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
