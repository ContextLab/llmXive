import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/convergence_targets.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def load_network_metrics(input_path: str) -> pd.DataFrame:
    """
    Load network metrics from the generated CSV file.
    
    Args:
        input_path: Path to the networks CSV file (data/raw/networks.csv)
        
    Returns:
        DataFrame containing network metrics
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If required columns are missing
    """
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise ValueError(f"Failed to read CSV: {e}")
    
    required_columns = ['id', 'class', 'average_degree', 'clustering_coefficient', 'average_path_length']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} networks from {input_path}")
    return df

def select_representative_graphs(df: pd.DataFrame) -> list:
    """
    Select one representative graph per topological class.
    
    Selection criteria:
    1. Calculate the median average_degree for each class.
    2. Select the graph whose average_degree is closest to the median.
    3. If ties exist (same distance to median), select the graph with the lowest ID.
    
    Args:
        df: DataFrame containing network metrics
        
    Returns:
        List of selected graph IDs (one per class)
    """
    if df.empty:
        logger.warning("Input DataFrame is empty")
        return []
    
    classes = df['class'].unique()
    logger.info(f"Processing {len(classes)} topological classes: {classes}")
    
    selected_ids = []
    
    for cls in classes:
        class_df = df[df['class'] == cls].copy()
        if class_df.empty:
            logger.warning(f"No graphs found for class: {cls}")
            continue
        
        # Calculate median average_degree
        median_degree = class_df['average_degree'].median()
        logger.debug(f"Class '{cls}': median average_degree = {median_degree}")
        
        # Calculate absolute difference from median
        class_df['diff_from_median'] = (class_df['average_degree'] - median_degree).abs()
        
        # Sort by difference (ascending) then by ID (ascending) to handle ties
        # Ensure ID is treated as numeric or string consistently for sorting
        # Assuming ID format is "graph_0001" or similar, sort lexicographically if string
        # If ID is numeric, convert to int for proper sorting
        try:
            class_df['sort_id'] = class_df['id'].apply(lambda x: int(x.split('_')[-1]) if '_' in str(x) else int(x))
            class_df = class_df.sort_values(by=['diff_from_median', 'sort_id'])
        except (ValueError, AttributeError):
            # Fallback to string sorting if ID format is unexpected
            class_df = class_df.sort_values(by=['diff_from_median', 'id'])
        
        # Select the top one
        selected_row = class_df.iloc[0]
        selected_id = selected_row['id']
        selected_ids.append(selected_id)
        
        logger.info(f"Selected graph '{selected_id}' for class '{cls}' "
                    f"(avg_degree={selected_row['average_degree']:.4f}, "
                    f"diff_from_median={selected_row['diff_from_median']:.4f})")
    
    return selected_ids

def save_convergence_targets(selected_ids: list, output_path: str) -> None:
    """
    Save the list of selected graph IDs to a JSON file.
    
    Args:
        selected_ids: List of selected graph IDs
        output_path: Path for the output JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "convergence_targets": selected_ids,
        "count": len(selected_ids),
        "description": "One representative graph per topological class selected by median average degree"
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(selected_ids)} convergence targets to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write JSON file: {e}")
        raise IOError(f"Failed to write JSON file: {e}")

def main():
    """Main entry point for selecting convergence targets."""
    parser = argparse.ArgumentParser(
        description='Select representative topologies for convergence testing.'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/raw/networks.csv',
        help='Path to the input networks CSV file (default: data/raw/networks.csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/analysis/convergence_targets.json',
        help='Path for the output JSON file (default: data/analysis/convergence_targets.json)'
    )
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting convergence target selection...")
        logger.info(f"Input: {args.input}")
        logger.info(f"Output: {args.output}")
        
        # Load data
        df = load_network_metrics(args.input)
        
        # Select representatives
        selected_ids = select_representative_graphs(df)
        
        if not selected_ids:
            logger.error("No graphs were selected. Check input data.")
            sys.exit(1)
        
        # Save results
        save_convergence_targets(selected_ids, args.output)
        
        logger.info("Convergence target selection completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except IOError as e:
        logger.error(f"File I/O error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
