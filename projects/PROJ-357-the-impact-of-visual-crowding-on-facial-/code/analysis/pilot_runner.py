import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.synthetic_data_generator import generate_synthetic_responses, load_manifest as gen_load_manifest, save_responses
from config import get_seed, set_all_seeds, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str) -> dict:
    """Load the stimuli manifest JSON."""
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    with open(path, 'r') as f:
        return json.load(f)

def run_pilot(manifest_path: str, output_dir: str, num_participants: int = 10, seed: int = 42) -> str:
    """
    Execute the synthetic pilot study.
    
    Args:
        manifest_path: Path to stimuli_manifest.json
        output_dir: Directory to write raw response data
        num_participants: Number of simulated participants
        seed: Random seed for reproducibility
    
    Returns:
        Path to the generated raw responses file
    """
    logger.info(f"Starting Synthetic Pilot with {num_participants} participants")
    
    # Set seeds
    set_all_seeds(seed)
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    ensure_directories([output_path])
    
    # Load manifest
    logger.info(f"Loading manifest from {manifest_path}")
    manifest = load_manifest(manifest_path)
    
    stimuli_list = list(manifest.values())
    if not stimuli_list:
        raise ValueError("Manifest contains no stimuli entries.")
    
    logger.info(f"Found {len(stimuli_list)} stimuli to process.")
    
    # Generate responses
    raw_responses = generate_synthetic_responses(
        stimuli_list=stimuli_list,
        num_participants=num_participants,
        seed=seed
    )
    
    # Define output file path
    output_file = output_path / "raw_pilot_responses.json"
    
    # Save responses
    save_responses(raw_responses, str(output_file))
    
    logger.info(f"Successfully generated raw pilot data at {output_file}")
    return str(output_file)

def main():
    parser = argparse.ArgumentParser(description="Execute the synthetic pilot study.")
    parser.add_argument(
        "--manifest", 
        type=str, 
        default="data/interim/stimuli_manifest.json",
        help="Path to the stimuli manifest JSON file."
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/interim",
        help="Directory to store raw pilot response data."
    )
    parser.add_argument(
        "--participants", 
        type=int, 
        default=10,
        help="Number of simulated participants."
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for reproducibility."
    )
    
    args = parser.parse_args()
    
    try:
        result_path = run_pilot(
            manifest_path=args.manifest,
            output_dir=args.output_dir,
            num_participants=args.participants,
            seed=args.seed
        )
        print(f"Pilot execution complete. Output: {result_path}")
    except Exception as e:
        logger.error(f"Pilot execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()