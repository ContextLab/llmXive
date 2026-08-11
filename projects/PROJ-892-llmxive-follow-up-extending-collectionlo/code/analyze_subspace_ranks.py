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

def load_subspace_ranks(file_path: str = "data/subspace_ranks.json") -> Dict[str, Any]:
    """
    Load per-effect LoRA subspace ranks from the JSON file produced by T009.
    
    Args:
        file_path: Path to the subspace_ranks.json file.
        
    Returns:
        Dictionary containing effect names as keys and their subspace ranks as values.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Subspace ranks file not found: {path}")
    
    logger.info(f"Loading subspace ranks from {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Validate structure
    if not isinstance(data, dict):
        raise ValueError(f"Expected dictionary in {path}, got {type(data)}")
        
    logger.info(f"Loaded {len(data)} subspace rank entries")
    return data

def prepare_correlation_data(subspace_ranks: Dict[str, Any], results_path: str = "data/results.csv") -> List[Dict[str, Any]]:
    """
    Prepare data for correlation analysis by merging subspace ranks with results.
    
    This function loads the results from data/results.csv and merges them with
    the subspace ranks from the provided dictionary. It filters out entries
    where either the subspace rank or the concept bleeding metric is missing.
    
    Args:
        subspace_ranks: Dictionary of effect names to subspace ranks.
        results_path: Path to the results CSV file.
        
    Returns:
        List of dictionaries containing merged data points ready for correlation analysis.
        Each dict contains: {'effect': str, 'subspace_rank': int, 'concept_bleeding': float}
    """
    import csv
    
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    
    logger.info(f"Loading results from {path} to prepare correlation data")
    
    # Read results CSV
    data_points = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            effect = row.get('effect')
            if not effect:
                continue
            
            # Get subspace rank for this effect
            rank = subspace_ranks.get(effect)
            if rank is None:
                logger.warning(f"No subspace rank found for effect: {effect}")
                continue
            
            # Get concept bleeding metric (CESR)
            # The results.csv should have a column for concept bleeding (e.g., 'cesr_score' or 'concept_bleeding')
            concept_bleeding = None
            for key in ['cesr_score', 'concept_bleeding', 'bleeding']:
                if key in row:
                    try:
                        concept_bleeding = float(row[key])
                        break
                    except (ValueError, TypeError):
                        continue
            
            if concept_bleeding is None:
                logger.warning(f"No concept bleeding metric found for effect: {effect}")
                continue
            
            data_points.append({
                'effect': effect,
                'subspace_rank': int(rank),
                'concept_bleeding': concept_bleeding
            })
    
    logger.info(f"Prepared {len(data_points)} data points for correlation analysis")
    return data_points

def main():
    """
    Main entry point for the subspace ranks analysis script.
    
    This script loads subspace ranks from data/subspace_ranks.json,
    prepares data for correlation analysis by merging with results,
    and outputs the prepared data to a JSON file for further analysis.
    """
    try:
        # Load subspace ranks
        subspace_ranks = load_subspace_ranks("data/subspace_ranks.json")
        
        # Prepare correlation data
        correlation_data = prepare_correlation_data(
            subspace_ranks, 
            "data/results.csv"
        )
        
        if not correlation_data:
            logger.warning("No data points prepared for correlation analysis.")
            return 1
        
        # Save prepared data for correlation analysis
        output_path = Path("data/correlation_analysis_data.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(correlation_data, f, indent=2)
        
        logger.info(f"Saved {len(correlation_data)} correlation data points to {output_path}")
        
        # Print summary
        print(f"\nCorrelation Analysis Data Summary:")
        print(f"  Effects analyzed: {len(correlation_data)}")
        print(f"  Subspace ranks range: {min(d['subspace_rank'] for d in correlation_data)} - {max(d['subspace_rank'] for d in correlation_data)}")
        print(f"  Concept bleeding range: {min(d['concept_bleeding'] for d in correlation_data):.4f} - {max(d['concept_bleeding'] for d in correlation_data):.4f}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in subspace ranks analysis: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
