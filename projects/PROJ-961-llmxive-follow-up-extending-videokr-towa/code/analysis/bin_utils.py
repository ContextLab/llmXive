import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.config import get_project_root, get_path, ensure_dir

logger = logging.getLogger(__name__)

def load_bin_counts_from_t19() -> Dict[str, int]:
    """
    Load bin counts from the stratify_accuracy output (T019).
    Assumes T019 wrote to data/processed/bin_counts.json.
    """
    path = get_path("data/processed/bin_counts.json")
    if not path.exists():
        logger.warning(f"Bin counts file not found at {path}. Returning empty dict.")
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)

def load_chain_lengths_from_t13() -> List[int]:
    """
    Load chain_length values from the annotated dataset (T013).
    Reads data/processed/annotated_videokr.csv.
    """
    path = get_path("data/processed/annotated_videokr.csv")
    if not path.exists():
        raise FileNotFoundError(f"Annotated dataset not found at {path}")
    
    chain_lengths = []
    with open(path, 'r') as f:
        # Simple CSV parsing assuming first row is header
        header = f.readline().strip().split(',')
        try:
            idx = header.index('chain_length')
        except ValueError:
            raise ValueError("chain_length column not found in annotated dataset")
        
        for line in f:
            parts = line.strip().split(',')
            if len(parts) > idx:
                try:
                    val = int(parts[idx])
                    chain_lengths.append(val)
                except ValueError:
                    continue
    
    return chain_lengths

def determine_bin_strategy(bin_counts: Dict[str, int], min_samples: int = 50) -> Dict[str, Any]:
    """
    Determine if bins need merging or if analysis should be deferred.
    Returns strategy details.
    """
    strategy = {
        'bins': [],
        'strategy': 'original',
        'merged_bins': [],
        'deferred': False,
        'reason': None
    }

    # Sort bins by hop count (assuming keys are like '1', '2', '3+')
    sorted_bins = sorted(bin_counts.keys(), key=lambda x: int(x.replace('+', '')) if '+' in x else int(x))
    
    strategy['bins'] = sorted_bins
    
    # Check for low power bins
    low_power_bins = [b for b in sorted_bins if bin_counts.get(b, 0) < min_samples]
    
    if not low_power_bins:
        logger.info("All bins have sufficient power.")
        return strategy
    
    # Attempt merging logic (simplified: merge lowest with adjacent)
    if low_power_bins:
        # Simple heuristic: merge the last bin (usually '3+') with previous if low
        last_bin = sorted_bins[-1]
        if bin_counts.get(last_bin, 0) < min_samples and len(sorted_bins) > 1:
            prev_bin = sorted_bins[-2]
            merged_count = bin_counts.get(last_bin, 0) + bin_counts.get(prev_bin, 0)
            
            if merged_count >= min_samples:
                logger.info(f"Merging {last_bin} with {prev_bin} (count: {merged_count})")
                strategy['strategy'] = 'merged'
                strategy['merged_bins'] = [prev_bin, last_bin]
                strategy['bins'] = sorted_bins[:-1] # Remove last, keep merged concept
                return strategy
            else:
                logger.warning(f"Merged bin still has low power ({merged_count}). Deferring.")
                strategy['strategy'] = 'deferred'
                strategy['deferred'] = True
                strategy['reason'] = "insufficient_power_after_merge"
                return strategy
        else:
            # Fallback: if not the last bin, just flag as deferred for now
            strategy['strategy'] = 'deferred'
            strategy['deferred'] = True
            strategy['reason'] = "insufficient_power"
            return strategy

    return strategy

def save_bin_config(strategy: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Save the bin configuration strategy to a JSON file.
    """
    if output_path is None:
        output_path = get_path("data/processed/bin_config.json")
    
    ensure_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(strategy, f, indent=2)
    logger.info(f"Bin config saved to {output_path}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logger.info("Loading bin counts from T019...")
        bin_counts = load_bin_counts_from_t19()
        
        if not bin_counts:
            logger.warning("No bin counts found. Exiting.")
            return
        
        logger.info(f"Bin counts: {bin_counts}")
        
        logger.info("Determining bin strategy...")
        strategy = determine_bin_strategy(bin_counts)
        
        logger.info(f"Strategy: {strategy}")
        
        logger.info("Saving bin config...")
        save_bin_config(strategy)
        
        logger.info("Bin preparation complete.")
        
    except Exception as e:
        logger.error(f"Error in bin_utils main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
