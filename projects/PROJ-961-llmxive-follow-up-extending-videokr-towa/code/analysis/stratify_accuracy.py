"""
Stratify accuracy calculations by hop count bins.
"""
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


def load_annotated_data(
    file_path: Union[str, Path]
) -> List[Dict[str, Any]]:
    """
    Load annotated data from a CSV file.
    
    Args:
        file_path (Union[str, Path]): Path to the CSV file.
        
    Returns:
        List[Dict[str, Any]]: List of row dictionaries.
    """
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    data = []
    
    with open(path_obj, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    return data


def bin_hop_length(hop_length: int) -> str:
    """
    Bin hop length into categories.
    
    Args:
        hop_length (int): Hop length value.
        
    Returns:
        str: Binned category.
    """
    if hop_length == 1:
        return '1'
    elif hop_length == 2:
        return '2'
    else:
        return '3+'


def calculate_accuracy_by_bin(
    data: List[Dict[str, Any]],
    hop_column: str = 'chain_length',
    correctness_column: str = 'correctness'
) -> Dict[str, Dict[str, int]]:
    """
    Calculate accuracy by hop bin.
    
    Args:
        data (List[Dict[str, Any]]): Annotated data rows.
        hop_column (str): Column name for hop length.
        correctness_column (str): Column name for correctness.
        
    Returns:
        Dict[str, Dict[str, int]]: Dictionary mapping bins to counts.
    """
    bin_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'correct': 0, 'total': 0})
    
    for row in data:
        try:
            hop_length = int(row[hop_column])
            bin_label = bin_hop_length(hop_length)
            correctness = row.get(correctness_column, '0')
            
            bin_stats[bin_label]['total'] += 1
            if correctness.lower() in ['1', 'true', 'yes']:
                bin_stats[bin_label]['correct'] += 1
        except (ValueError, KeyError) as e:
            logging.warning(f"Skipping invalid row: {row}, error: {e}")
    
    return dict(bin_stats)


def write_results(
    bin_stats: Dict[str, Dict[str, int]],
    output_path: Union[str, Path]
) -> None:
    """
    Write accuracy results to a JSON file.
    
    Args:
        bin_stats (Dict[str, Dict[str, int]]): Accuracy statistics by bin.
        output_path (Union[str, Path]): Path for the output file.
    """
    output_obj = Path(output_path) if isinstance(output_path, str) else output_path
    
    results = {}
    for bin_label, stats in bin_stats.items():
        total = stats['total']
        correct = stats['correct']
        accuracy = correct / total if total > 0 else 0.0
        
        results[bin_label] = {
            'total': total,
            'correct': correct,
            'accuracy': accuracy
        }
    
    with open(output_obj, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def main() -> None:
    """Main entry point for stratify accuracy module."""
    pass


if __name__ == "__main__":
    main()
