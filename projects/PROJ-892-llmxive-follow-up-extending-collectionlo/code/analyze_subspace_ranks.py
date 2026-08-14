"""
Module to load per-effect LoRA subspace ranks and prepare data for correlation analysis.

This module implements T021: Load subspace ranks from data/subspace_ranks.json
and prepare the data structure for correlation analysis with concept bleeding metrics.
"""
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_subspace_ranks(ranks_path: Optional[Path] = None) -> Dict[str, int]:
    """
    Load per-effect LoRA subspace ranks from a JSON file.
    
    Args:
        ranks_path: Path to the subspace_ranks.json file. Defaults to 
                   data/subspace_ranks.json relative to project root.
    
    Returns:
        Dictionary mapping effect names (str) to their subspace ranks (int).
    
    Raises:
        FileNotFoundError: If the ranks file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if ranks_path is None:
        # Default path relative to project root
        ranks_path = Path("data/subspace_ranks.json")
    
    if not ranks_path.exists():
        raise FileNotFoundError(
            f"Subspace ranks file not found: {ranks_path}. "
            "Ensure T009b has completed successfully."
        )
    
    logger.info(f"Loading subspace ranks from: {ranks_path}")
    
    with open(ranks_path, 'r', encoding='utf-8') as f:
        ranks_data = json.load(f)
    
    # Validate structure
    if not isinstance(ranks_data, dict):
        raise ValueError(
            f"Expected JSON object (dict) in {ranks_path}, "
            f"but got {type(ranks_data).__name__}"
        )
    
    # Validate values are integers
    for effect, rank in ranks_data.items():
        if not isinstance(rank, int):
            raise ValueError(
                f"Rank for effect '{effect}' must be an integer, "
                f"got {type(rank).__name__}: {rank}"
            )
        if rank <= 0:
            logger.warning(
                f"Non-positive rank detected for effect '{effect}': {rank}. "
                "This may indicate an issue with the SVD computation."
            )
    
    logger.info(f"Successfully loaded {len(ranks_data)} effect ranks: {list(ranks_data.keys())}")
    return ranks_data


def prepare_correlation_data(
    ranks: Dict[str, int],
    results_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Prepare data for correlation analysis by merging subspace ranks with 
    concept bleeding metrics from results.csv.
    
    This function joins the subspace rank data with the quantitative metrics
    computed in previous tasks (T018, T019) to create a unified dataset
    suitable for statistical analysis (T025).
    
    Args:
        ranks: Dictionary of effect -> rank from load_subspace_ranks().
        results_path: Path to results.csv. Defaults to data/results.csv.
    
    Returns:
        List of dictionaries, each containing:
            - 'effect': str (effect name)
            - 'rank': int (subspace rank)
            - 'cesr_score': float (concept bleeding metric, may be None)
            - 'lpips_distance': float (fidelity metric, may be None)
            - 'cosine_similarity_delta': float (adherence drop, may be None)
            - 'quantization_level': str (e.g., 'FP16', 'INT8', 'INT4')
    
    Note:
        If results_path is provided but the file doesn't exist or is empty,
        this function returns a list containing only the rank information
        with None values for metrics, allowing the correlation analysis
        to proceed with partial data (though with reduced statistical power).
    """
    if results_path is None:
        results_path = Path("data/results.csv")
    
    logger.info(f"Preparing correlation data from ranks and: {results_path}")
    
    # Initialize result list with rank data
    correlation_data = []
    
    for effect, rank in ranks.items():
        entry = {
            'effect': effect,
            'rank': rank,
            'cesr_score': None,
            'lpips_distance': None,
            'cosine_similarity_delta': None,
            'quantization_level': None
        }
        correlation_data.append(entry)
    
    # Try to merge with results.csv if it exists
    if results_path.exists():
        logger.info(f"Merging with results data from: {results_path}")
        import pandas as pd
        
        try:
            df = pd.read_csv(results_path)
            
            # Expected columns based on T018, T019, T020
            required_cols = ['effect', 'quantization_level']
            optional_cols = ['cesr_score', 'lpips_distance', 'cosine_similarity_delta']
            
            # Check for required columns
            missing_required = [c for c in required_cols if c not in df.columns]
            if missing_required:
                logger.warning(
                    f"Results CSV missing required columns: {missing_required}. "
                    "Proceeding with rank-only data."
                )
                return correlation_data
            
            # Aggregate metrics by effect (handle multiple quantization levels)
            for idx, entry in enumerate(correlation_data):
                effect = entry['effect']
                
                # Filter rows for this effect
                effect_rows = df[df['effect'] == effect]
                
                if len(effect_rows) == 0:
                    logger.debug(f"No results found for effect: {effect}")
                    continue
                
                # For CESR, we typically want the mean across quantization levels
                # or we could analyze per-level. Here we prepare for per-level analysis.
                for _, row in effect_rows.iterrows():
                    q_level = row['quantization_level']
                    
                    # Create a new entry for each quantization level
                    # to preserve granularity for statistical analysis
                    new_entry = entry.copy()
                    new_entry['quantization_level'] = q_level
                    
                    if 'cesr_score' in df.columns and not pd.isna(row['cesr_score']):
                        new_entry['cesr_score'] = float(row['cesr_score'])
                    
                    if 'lpips_distance' in df.columns and not pd.isna(row['lpips_distance']):
                        new_entry['lpips_distance'] = float(row['lpips_distance'])
                    
                    if 'cosine_similarity_delta' in df.columns and not pd.isna(row['cosine_similarity_delta']):
                        new_entry['cosine_similarity_delta'] = float(row['cosine_similarity_delta'])
                    
                    correlation_data.append(new_entry)
            
            logger.info(f"Successfully merged {len(effect_rows) if 'effect_rows' in locals() else 0} "
                        f"result rows for effect '{effect}'")
            
        except Exception as e:
            logger.warning(
                f"Failed to merge results from {results_path}: {e}. "
                "Proceeding with rank-only data."
            )
    else:
        logger.warning(
            f"Results file not found: {results_path}. "
            "Proceeding with rank-only data. Correlation analysis will require results.csv."
        )
    
    logger.info(f"Prepared {len(correlation_data)} data entries for correlation analysis")
    return correlation_data


def main():
    """
    Main entry point for T021: Load subspace ranks and prepare correlation data.
    
    This function:
    1. Loads subspace ranks from data/subspace_ranks.json
    2. Prepares correlation data by merging with results.csv (if available)
    3. Outputs a summary to the console
    4. Optionally saves the prepared data to a JSON file for downstream analysis
    
    Exit codes:
        0: Success
        1: Error (file not found, invalid data, etc.)
    """
    project_root = Path(__file__).parent.parent
    ranks_path = project_root / "data" / "subspace_ranks.json"
    results_path = project_root / "data" / "results.csv"
    output_path = project_root / "data" / "correlation_data.json"
    
    try:
        # Step 1: Load subspace ranks
        ranks = load_subspace_ranks(ranks_path)
        
        # Step 2: Prepare correlation data
        correlation_data = prepare_correlation_data(ranks, results_path)
        
        # Step 3: Print summary
        print("\n" + "="*60)
        print("T021: Subspace Rank Correlation Data Preparation")
        print("="*60)
        print(f"\nLoaded {len(ranks)} effect ranks:")
        for effect, rank in sorted(ranks.items()):
            print(f"  - {effect:12s}: rank = {rank}")
        
        print(f"\nPrepared {len(correlation_data)} data entries for correlation analysis.")
        
        # Count entries with metrics
        entries_with_cesr = sum(1 for e in correlation_data if e['cesr_score'] is not None)
        entries_with_lpips = sum(1 for e in correlation_data if e['lpips_distance'] is not None)
        entries_with_delta = sum(1 for e in correlation_data if e['cosine_similarity_delta'] is not None)
        
        print(f"\nMetric coverage:")
        print(f"  - CESR scores: {entries_with_cesr} / {len(correlation_data)}")
        print(f"  - LPIPS distances: {entries_with_lpips} / {len(correlation_data)}")
        print(f"  - Cosine similarity deltas: {entries_with_delta} / {len(correlation_data)}")
        
        # Step 4: Save prepared data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(correlation_data, f, indent=2)
        
        print(f"\nSaved prepared correlation data to: {output_path}")
        print("="*60 + "\n")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in subspace ranks file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())