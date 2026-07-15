"""
Subspace Rank Analysis Module

This module implements logic to load per-effect LoRA subspace ranks
from data/subspace_ranks.json and prepare data for correlation analysis
with concept bleeding metrics (US2/US3).

It validates the input data structure and provides a utility function
to retrieve ranks for specific effects, enabling downstream statistical
analysis (T025).
"""
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import from existing API surface
from data_loader import compute_subspace_ranks
from state_manager import register_artifact, compute_sha256

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_subspace_ranks(ranks_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load per-effect LoRA subspace ranks from JSON file.

    Args:
        ranks_path: Path to subspace_ranks.json. Defaults to data/subspace_ranks.json.

    Returns:
        Dictionary containing subspace rank data keyed by effect name.

    Raises:
        FileNotFoundError: If the ranks file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
        ValueError: If the data structure is invalid.
    """
    if ranks_path is None:
        ranks_path = Path("data/subspace_ranks.json")

    if not ranks_path.exists():
        logger.error(f"Subspace ranks file not found: {ranks_path}")
        raise FileNotFoundError(f"Subspace ranks file not found: {ranks_path}")

    try:
        with open(ranks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in subspace ranks file: {e}")
        raise

    # Validate structure: expect a dict with 'ranks' key or direct effect keys
    if not isinstance(data, dict):
        raise ValueError("Subspace ranks data must be a JSON object (dictionary).")

    # If it has a 'ranks' key, use that; otherwise assume root is the ranks dict
    ranks_data = data.get('ranks', data)

    if not isinstance(ranks_data, dict):
        raise ValueError("Subspace ranks data must contain a dictionary of effect -> rank.")

    logger.info(f"Loaded subspace ranks for {len(ranks_data)} effects from {ranks_path}")
    return ranks_data

def prepare_correlation_data(ranks_data: Dict[str, Any], results_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Prepare data for correlation analysis by merging subspace ranks with
    concept bleeding metrics from results.csv.

    Args:
        ranks_data: Loaded subspace ranks dictionary.
        results_path: Path to results.csv. Defaults to data/results.csv.

    Returns:
        List of dictionaries containing merged data points for analysis.
        Each dict contains: {'effect', 'subspace_rank', 'cesr_score', 'lpips_distance', ...}
    """
    if results_path is None:
        results_path = Path("data/results.csv")

    if not results_path.exists():
        logger.warning(f"Results file not found at {results_path}. Cannot merge data.")
        # Return only subspace rank data if results are missing
        return [
            {'effect': effect, 'subspace_rank': rank, 'cesr_score': None, 'lpips_distance': None}
            for effect, rank in ranks_data.items()
        ]

    import csv
    merged_data = []

    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                effect = row.get('effect')
                if effect and effect in ranks_data:
                    merged_point = {
                        'effect': effect,
                        'subspace_rank': ranks_data[effect],
                        'quantization_level': row.get('quantization_level'),
                        'cesr_score': float(row.get('cesr_score', 0)) if row.get('cesr_score') else None,
                        'lpips_distance': float(row.get('lpips_distance', 0)) if row.get('lpips_distance') else None,
                        'cosine_similarity': float(row.get('cosine_similarity', 0)) if row.get('cosine_similarity') else None
                    }
                    merged_data.append(merged_point)
    except Exception as e:
        logger.error(f"Error reading results file: {e}")
        # Return partial data
        merged_data = [
            {'effect': effect, 'subspace_rank': rank, 'cesr_score': None, 'lpips_distance': None}
            for effect, rank in ranks_data.items()
        ]

    logger.info(f"Prepared {len(merged_data)} data points for correlation analysis.")
    return merged_data

def main():
    """
    Main entry point for subspace rank analysis.
    Loads ranks, validates structure, and prepares data for correlation.
    """
    logger.info("Starting subspace rank analysis (T021)...")

    try:
        # 1. Load Subspace Ranks
        ranks = load_subspace_ranks()
        logger.info(f"Successfully loaded ranks: {list(ranks.keys())}")

        # 2. Prepare for Correlation
        data_points = prepare_correlation_data(ranks)
        
        # 3. Output summary to console and save a prepared JSON for downstream tasks
        output_file = Path("data/subspace_rank_analysis_input.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_points, f, indent=2)
        
        logger.info(f"Prepared analysis data saved to {output_file}")
        
        # Register the output artifact
        artifact_hash = compute_sha256(output_file)
        register_artifact(output_file, artifact_hash)
        logger.info(f"Registered artifact: {output_file} (hash: {artifact_hash})")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        sys.exit(1)

    logger.info("Subspace rank analysis completed successfully.")

if __name__ == "__main__":
    main()
