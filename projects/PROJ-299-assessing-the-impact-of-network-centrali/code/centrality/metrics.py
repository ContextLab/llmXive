"""
Centrality metric calculation for brain networks.

Implements FR-004: Calculate degree, betweenness, and closeness centrality
for every ROI using networkx. Stores raw ROI-level metrics.
"""
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import networkx as nx
import numpy as np

# Ensure imports work when run as script or imported as module
try:
    from code.centrality.connectivity import compute_correlation_matrix
except ImportError:
    from centrality.connectivity import compute_correlation_matrix


def load_connectivity_matrix(matrix_path: str) -> np.ndarray:
    """
    Load a precomputed correlation matrix from a CSV file.

    Args:
        matrix_path: Path to the CSV file containing the correlation matrix.

    Returns:
        A 2D numpy array representing the connectivity matrix.
    """
    if not os.path.exists(matrix_path):
        raise FileNotFoundError(f"Connectivity matrix not found at: {matrix_path}")

    matrix = []
    with open(matrix_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                matrix.append([float(val) for val in row])
            except ValueError:
                # Skip header rows if they exist
                continue

    if not matrix:
        raise ValueError(f"Connectivity matrix file {matrix_path} is empty or invalid.")

    return np.array(matrix)


def load_roi_labels(labels_path: str) -> List[str]:
    """
    Load ROI labels from a JSON or CSV file.

    Args:
        labels_path: Path to the file containing ROI labels.

    Returns:
        A list of ROI labels (strings).
    """
    if not os.path.exists(labels_path):
        raise FileNotFoundError(f"ROI labels file not found at: {labels_path}")

    if labels_path.endswith('.json'):
        with open(labels_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Expecting a list of labels or a dict with a 'labels' key
            if isinstance(data, list):
                return [str(label) for label in data]
            elif isinstance(data, dict) and 'labels' in data:
                return [str(label) for label in data['labels']]
            else:
                raise ValueError(f"Invalid JSON structure in {labels_path}")
    elif labels_path.endswith('.csv'):
        labels = []
        with open(matrix_path, 'r', newline='', encoding='utf-8') as f:
            # Assuming the first column contains labels
            reader = csv.reader(f)
            for row in reader:
                if row:
                    labels.append(row[0].strip())
        return labels
    else:
        raise ValueError(f"Unsupported labels file format: {labels_path}")


def calculate_centrality_metrics(matrix: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate degree, betweenness, and closeness centrality for a connectivity matrix.

    Args:
        matrix: A 2D numpy array representing the connectivity matrix (correlations).

    Returns:
        A dictionary mapping metric names to arrays of values per ROI.
    """
    n_nodes = matrix.shape[0]
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Connectivity matrix must be square.")

    # Create a weighted undirected graph from the correlation matrix
    # We threshold small values to avoid numerical issues, but keep the full matrix for weighted analysis
    # NetworkX expects a graph object. We'll use a complete graph with edge weights.
    G = nx.from_numpy_array(matrix, create_using=nx.Graph)

    # Calculate degree centrality (weighted)
    # NetworkX's degree_centrality normalizes by (n-1), which is standard.
    # For weighted graphs, it sums the weights.
    degree_centrality = nx.degree_centrality(G)

    # Calculate betweenness centrality (weighted)
    # Using weight='weight' to consider edge weights
    betweenness_centrality = nx.betweenness_centrality(G, weight='weight', normalized=True)

    # Calculate closeness centrality (weighted)
    # NetworkX's closeness_centrality uses the inverse of the average shortest path length.
    # For weighted graphs, it uses the edge weights as distances.
    # Note: Closeness can be problematic if the graph is not fully connected.
    # We'll use the default normalized version.
    try:
        closeness_centrality = nx.closeness_centrality(G, distance='weight')
    except nx.NetworkXError:
        # If the graph is disconnected, closeness might be undefined for some nodes.
        # In that case, we can set them to 0 or handle it differently.
        # For now, we'll catch the error and return zeros for affected nodes.
        closeness_centrality = {node: 0.0 for node in G.nodes()}

    # Convert to arrays ordered by node index (0 to n-1)
    # NetworkX nodes are 0-indexed by default when created from numpy array
    degree_array = np.array([degree_centrality[i] for i in range(n_nodes)])
    betweenness_array = np.array([betweenness_centrality[i] for i in range(n_nodes)])
    closeness_array = np.array([closeness_centrality[i] for i in range(n_nodes)])

    return {
        'degree': degree_array,
        'betweenness': betweenness_array,
        'closeness': closeness_array
    }


def process_participant_centrality(
    matrix_path: str,
    labels_path: str,
    output_path: str,
    participant_id: str
) -> Dict[str, Any]:
    """
    Calculate centrality metrics for a single participant and save to CSV.

    Args:
        matrix_path: Path to the participant's connectivity matrix CSV.
        labels_path: Path to the ROI labels file.
        output_path: Path to the output CSV file for centrality metrics.
        participant_id: The ID of the participant.

    Returns:
        A dictionary containing the calculated metrics for logging.
    """
    # Load data
    matrix = load_connectivity_matrix(matrix_path)
    roi_labels = load_roi_labels(labels_path)

    if len(roi_labels) != matrix.shape[0]:
        raise ValueError(f"Mismatch between number of ROI labels ({len(roi_labels)}) "
                         f"and matrix size ({matrix.shape[0]}).")

    # Calculate metrics
    metrics = calculate_centrality_metrics(matrix)

    # Prepare output data
    output_data = []
    for i, label in enumerate(roi_labels):
        row = {
            'participant_id': participant_id,
            'roi_label': label,
            'roi_index': i,
            'degree': float(metrics['degree'][i]),
            'betweenness': float(metrics['betweenness'][i]),
            'closeness': float(metrics['closeness'][i])
        }
        output_data.append(row)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write to CSV
    fieldnames = ['participant_id', 'roi_label', 'roi_index', 'degree', 'betweenness', 'closeness']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)

    return {
        'participant_id': participant_id,
        'num_rois': len(roi_labels),
        'output_file': output_path
    }


def run_centrality_pipeline(
    input_dir: str,
    labels_path: str,
    output_dir: str
) -> List[Dict[str, Any]]:
    """
    Run centrality calculation for all participants in the input directory.

    Args:
        input_dir: Directory containing connectivity matrix CSVs.
        labels_path: Path to the ROI labels file.
        output_dir: Directory to save the centrality metrics CSVs.

    Returns:
        A list of dictionaries containing results for each participant.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all connectivity matrix files
    matrix_files = sorted(input_path.glob("*.csv"))
    if not matrix_files:
        raise FileNotFoundError(f"No connectivity matrix files found in {input_dir}")

    results = []
    for matrix_file in matrix_files:
        # Extract participant ID from filename (assuming format: corr_matrix_<participant_id>.csv)
        # Or just use the stem as ID if no specific pattern
        participant_id = matrix_file.stem.replace("corr_matrix_", "")

        output_file = output_path / f"centrality_{participant_id}.csv"

        try:
            result = process_participant_centrality(
                matrix_path=str(matrix_file),
                labels_path=labels_path,
                output_path=str(output_file),
                participant_id=participant_id
            )
            results.append(result)
            print(f"Processed {participant_id}: {result['num_rois']} ROIs -> {output_file}")
        except Exception as e:
            print(f"Error processing {participant_id}: {e}", file=sys.stderr)
            results.append({
                'participant_id': participant_id,
                'error': str(e)
            })

    return results


def main():
    """
    Main entry point for the centrality metrics calculation script.

    Usage:
        python -m code.centrality.metrics --input data/processed/connectivity --labels code/config/roi_labels.json --output data/analysis/centrality
    """
    import argparse

    parser = argparse.ArgumentParser(description="Calculate centrality metrics for brain networks.")
    parser.add_argument('--input', type=str, required=True, help='Input directory containing connectivity matrices.')
    parser.add_argument('--labels', type=str, required=True, help='Path to ROI labels file (JSON or CSV).')
    parser.add_argument('--output', type=str, required=True, help='Output directory for centrality metrics.')

    args = parser.parse_args()

    print(f"Starting centrality calculation pipeline...")
    print(f"Input directory: {args.input}")
    print(f"Labels file: {args.labels}")
    print(f"Output directory: {args.output}")

    results = run_centrality_pipeline(
        input_dir=args.input,
        labels_path=args.labels,
        output_dir=args.output
    )

    print(f"Pipeline completed. Processed {len(results)} participants.")
    for res in results:
        if 'error' in res:
            print(f"  - {res['participant_id']}: FAILED - {res['error']}")
        else:
            print(f"  - {res['participant_id']}: SUCCESS")


if __name__ == '__main__':
    main()
