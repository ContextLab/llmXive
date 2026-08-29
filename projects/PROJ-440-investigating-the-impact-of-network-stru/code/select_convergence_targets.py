"""
Select representative topologies for convergence testing.

This script loads the generated network metrics from data/raw/networks.csv,
selects one representative graph per topological class based on median average
degree, and outputs the selected graph IDs to data/analysis/convergence_targets.json.

Selection criteria:
1. Calculate median average degree for each topological class.
2. Select the graph whose average degree is closest to the class median.
3. If ties exist, select the graph with the lowest graph ID.
"""

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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_network_metrics(csv_path: str) -> pd.DataFrame:
    """
    Load network metrics from CSV file.

    Args:
        csv_path: Path to the networks.csv file

    Returns:
        DataFrame containing network metrics
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Network metrics file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} network records from {csv_path}")
    return df

def select_representative_graphs(df: pd.DataFrame) -> list:
    """
    Select one representative graph per topological class.

    Selection strategy:
    1. Group by topological class
    2. For each class, calculate the median average degree
    3. Select the graph whose average degree is closest to the median
    4. If ties, select the graph with the lowest ID

    Args:
        df: DataFrame with network metrics including 'class' and 'avg_degree'

    Returns:
        List of selected graph IDs
    """
    classes = df['class'].unique()
    logger.info(f"Found {len(classes)} topological classes: {sorted(classes)}")

    selected_ids = []

    for cls in classes:
        class_df = df[df['class'] == cls].copy()
        logger.info(f"Processing class '{cls}': {len(class_df)} graphs")

        if len(class_df) == 0:
            logger.warning(f"No graphs found for class '{cls}', skipping")
            continue

        # Calculate median average degree for this class
        median_degree = class_df['avg_degree'].median()
        logger.info(f"  Median average degree for '{cls}': {median_degree:.4f}")

        # Calculate distance from median for each graph
        class_df['degree_distance'] = (class_df['avg_degree'] - median_degree).abs()

        # Sort by distance (ascending), then by ID (ascending) for tie-breaking
        # Ensure ID is treated as numeric for proper sorting
        class_df_sorted = class_df.sort_values(
            by=['degree_distance', 'id'],
            ascending=[True, True]
        )

        # Select the top graph (closest to median, lowest ID on tie)
        selected_row = class_df_sorted.iloc[0]
        selected_id = selected_row['id']

        logger.info(f"  Selected graph ID {selected_id} (avg_degree={selected_row['avg_degree']:.4f}, distance={selected_row['degree_distance']:.4f})")
        selected_ids.append(selected_id)

    return sorted(selected_ids)

def save_convergence_targets(selected_ids: list, output_path: str) -> None:
    """
    Save selected graph IDs to JSON file.

    Args:
        selected_ids: List of selected graph IDs
        output_path: Path for the output JSON file
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    target_data = {
        "convergence_targets": selected_ids,
        "count": len(selected_ids),
        "description": "One representative graph per topological class selected by median average degree"
    }

    with open(output_path, 'w') as f:
        json.dump(target_data, f, indent=2)

    logger.info(f"Saved {len(selected_ids)} convergence targets to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Select representative topologies for convergence testing"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/networks.csv",
        help="Path to networks.csv (default: data/raw/networks.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/analysis/convergence_targets.json",
        help="Path for output JSON (default: data/analysis/convergence_targets.json)"
    )

    args = parser.parse_args()

    try:
        # Load network metrics
        df = load_network_metrics(args.input)

        # Validate required columns
        required_cols = ['id', 'class', 'avg_degree']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Select representative graphs
        selected_ids = select_representative_graphs(df)

        # Save results
        save_convergence_targets(selected_ids, args.output)

        logger.info(f"Successfully selected {len(selected_ids)} representative graphs")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
