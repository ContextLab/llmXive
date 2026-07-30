"""
Pilot Runner for Synthetic Human Judgment Data Collection.

Orchestrates the synthetic pilot study by:
1. Loading the stimuli manifest generated in T014.
2. Invoking the synthetic data generator (T025) to simulate participant responses.
3. Writing raw response data to data/raw/synthetic_pilot_responses.csv.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories, set_all_seeds, get_seed
from analysis.synthetic_data_generator import generate_synthetic_responses

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'logs' / 'pilot_runner.log')
    ]
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load and validate the stimuli manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Stimuli manifest not found at {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    logger.info(f"Loaded manifest with {len(manifest)} stimuli")
    return manifest

def run_pilot(
    manifest_path: Path,
    output_path: Path,
    num_participants: int = 10,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Orchestrate the synthetic pilot study.
    
    Args:
        manifest_path: Path to stimuli_manifest.json
        output_path: Path for the output CSV
        num_participants: Number of simulated participants
        seed: Random seed for reproducibility
        
    Returns:
        Summary statistics of the generated data
    """
    if seed is None:
        seed = get_seed()
    
    set_all_seeds(seed)
    logger.info(f"Starting pilot study with seed {seed} and {num_participants} participants")
    
    # Load stimuli
    stimuli = load_manifest(manifest_path)
    if not stimuli:
        raise ValueError("Manifest is empty; cannot generate pilot data.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic responses
    logger.info(f"Generating synthetic responses for {len(stimuli)} stimuli...")
    responses = generate_synthetic_responses(
        stimuli=stimuli,
        num_participants=num_participants,
        seed=seed
    )
    
    if not responses:
        raise RuntimeError("Failed to generate any synthetic responses.")
    
    # Write to CSV
    import pandas as pd
    df = pd.DataFrame(responses)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully wrote {len(df)} responses to {output_path}")
    
    # Compute summary
    summary = {
        "total_responses": len(df),
        "unique_participants": df['participant_id'].nunique(),
        "unique_stimuli": df['stimulus_id'].nunique(),
        "overall_accuracy": float(df['accuracy'].mean()),
        "seed": seed,
        "num_participants_configured": num_participants
    }
    
    logger.info(f"Summary: {summary}")
    return summary

def main():
    parser = argparse.ArgumentParser(description="Run synthetic pilot study")
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/interim/stimuli_manifest.json",
        help="Path to stimuli manifest JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/synthetic_pilot_responses.csv",
        help="Path for output CSV"
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
    
    # Ensure directories
    ensure_directories()
    
    manifest_path = project_root / args.manifest
    output_path = project_root / args.output
    
    try:
        summary = run_pilot(
            manifest_path=manifest_path,
            output_path=output_path,
            num_participants=args.participants,
            seed=args.seed
        )
        print(json.dumps(summary, indent=2))
    except Exception as e:
        logger.error(f"Pilot study failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()