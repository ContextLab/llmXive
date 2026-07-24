import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_subspace_ranks(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load per-effect LoRA subspace ranks from the JSON file produced by T009.
    
    Args:
        filepath: Path to the subspace ranks JSON file. Defaults to 'data/subspace_ranks.json'.
        
    Returns:
        A dictionary containing the subspace rank data.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    if filepath is None:
        filepath = "data/subspace_ranks.json"
    
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Subspace ranks file not found: {filepath}")
    
    logger.info(f"Loading subspace ranks from {filepath}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} effect subspace ranks")
    return data

def prepare_correlation_data(ranks_data: Dict[str, Any], results_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Prepare data for correlation analysis by merging subspace ranks with quantization results.
    
    This function loads the main results CSV (data/results.csv) and merges it with
    the subspace rank data to create a unified dataset for statistical analysis.
    
    Args:
        ranks_data: The dictionary loaded from subspace_ranks.json.
        results_path: Path to the results CSV file. Defaults to 'data/results.csv'.
        
    Returns:
        A list of dictionaries, each containing effect name, subspace rank, and quantization metrics.
        
    Raises:
        FileNotFoundError: If the results CSV file does not exist.
    """
    if results_path is None:
        results_path = "data/results.csv"
    
    results_file = Path(results_path)
    if not results_file.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    logger.info(f"Preparing correlation data from {results_path}")
    
    import csv
    results_data = []
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results_data.append(row)
    
    # Merge subspace ranks with results
    # Expecting ranks_data to have structure: {"effects": [{"name": "...", "rank": ...}, ...]}
    # or a flat dict: {"effect_name": rank_value, ...}
    
    merged_data = []
    ranks_map = {}
    
    # Handle different possible structures of ranks_data
    if "effects" in ranks_data:
        # List of effects
        for effect in ranks_data["effects"]:
          if isinstance(effect, dict) and "name" in effect and "rank" in effect:
              ranks_map[effect["name"]] = effect["rank"]
          elif isinstance(effect, dict):
              # Try to find name and rank keys with common variations
              name_key = next((k for k in effect.keys() if k in ["name", "effect_name", "effect"]), None)
              rank_key = next((k for k in effect.keys() if k in ["rank", "subspace_rank", "effective_rank"]), None)
              if name_key and rank_key:
                  ranks_map[effect[name_key]] = effect[rank_key]
    elif isinstance(ranks_data, dict):
        # Flat dictionary: {"effect_name": rank, ...}
        ranks_map = ranks_data
    
    # Merge with results
    for result in results_data:
        effect_name = result.get("effect", result.get("effect_name", result.get("prompt", None)))
        if effect_name is None:
            logger.warning(f"Could not identify effect name in result: {result}")
            continue
            
        if effect_name in ranks_map:
            merged_entry = {
                "effect": effect_name,
                "subspace_rank": ranks_map[effect_name],
                "quantization_level": result.get("quantization_level", "unknown"),
                "cosine_similarity": float(result.get("cosine_similarity", 0)),
                "cesr_score": float(result.get("cesr_score", 0)),
                "lpips_distance": float(result.get("lpips_distance", 0)),
                "delta_similarity": float(result.get("delta_similarity", 0))
            }
            merged_data.append(merged_entry)
        else:
            logger.warning(f"Effect '{effect_name}' not found in subspace ranks data")
    
    logger.info(f"Prepared {len(merged_data)} merged entries for correlation analysis")
    return merged_data

def main():
    """
    Main entry point for subspace rank analysis and correlation data preparation.
    
    This script loads subspace ranks, merges them with quantization results,
    and prepares the data for the Bayesian Hierarchical Model analysis in T025.
    """
    try:
        # Load subspace ranks
        ranks_data = load_subspace_ranks()
        
        # Prepare correlation data
        correlation_data = prepare_correlation_data(ranks_data)
        
        # Save prepared data for downstream analysis
        output_path = "data/correlation_input.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(correlation_data, f, indent=2)
        
        logger.info(f"Saved correlation input data to {output_path}")
        logger.info(f"Sample of prepared data: {correlation_data[:3] if len(correlation_data) >= 3 else correlation_data}")
        
        return correlation_data
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in subspace ranks file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during correlation data preparation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()