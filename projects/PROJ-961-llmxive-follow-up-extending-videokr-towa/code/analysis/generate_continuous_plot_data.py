"""
Generate continuous plot data for accuracy vs hop count.

This script processes the raw annotated data from T013 to generate a CSV file
containing raw data points and mean accuracy per hop count for the continuous plot.

Output: data/processed/accuracy_vs_hop_raw.csv
"""
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_annotated_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the raw annotated data from T013 output.
    
    Args:
        input_path: Path to data/processed/annotated_videokr.csv
        
    Returns:
        List of dictionaries containing the raw data rows
    """
    data = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert chain_length to int, correctness to float
                try:
                    row['chain_length'] = int(row['chain_length'])
                    # Handle correctness column - could be 'True', 'False', '1', '0', or actual float
                    correctness_val = row.get('correctness', '0')
                    if isinstance(correctness_val, str):
                        if correctness_val.lower() in ['true', '1', 'yes']:
                            row['correctness'] = 1.0
                        elif correctness_val.lower() in ['false', '0', 'no']:
                            row['correctness'] = 0.0
                        else:
                            row['correctness'] = float(correctness_val)
                    else:
                        row['correctness'] = float(correctness_val)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping row due to conversion error: {e}")
                    continue
                data.append(row)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        raise
    
    return data

def calculate_mean_accuracy_by_hop(data: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Calculate mean accuracy and count for each hop count.
    
    Args:
        data: List of raw data rows
        
    Returns:
        Dictionary mapping hop_count -> {mean_accuracy, count, std_accuracy, min_accuracy, max_accuracy}
    """
    hop_stats = defaultdict(lambda: {'accuracies': [], 'count': 0})
    
    for row in data:
        hop = row['chain_length']
        accuracy = row['correctness']
        hop_stats[hop]['accuracies'].append(accuracy)
        hop_stats[hop]['count'] += 1
    
    result = {}
    for hop, stats in sorted(hop_stats.items()):
        accs = stats['accuracies']
        n = stats['count']
        mean_acc = sum(accs) / n if n > 0 else 0.0
        # Calculate standard deviation
        if n > 1:
            variance = sum((x - mean_acc) ** 2 for x in accs) / (n - 1)
            std_acc = variance ** 0.5
        else:
            std_acc = 0.0
        min_acc = min(accs) if accs else 0.0
        max_acc = max(accs) if accs else 0.0
        
        result[hop] = {
            'mean_accuracy': mean_acc,
            'count': n,
            'std_accuracy': std_acc,
            'min_accuracy': min_acc,
            'max_accuracy': max_acc
        }
    
    return result

def generate_plot_data_csv(
    raw_data: List[Dict[str, Any]],
    mean_stats: Dict[int, Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate the CSV file with raw data points and mean accuracy per hop count.
    
    Args:
        raw_data: List of raw data rows
        mean_stats: Dictionary of mean accuracy statistics per hop
        output_path: Path to write the output CSV
    """
    ensure_dir(output_path.parent)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'hop_count', 
            'record_id', 
            'question', 
            'answer', 
            'correctness',
            'mean_accuracy_for_hop',
            'std_accuracy_for_hop',
            'count_for_hop'
        ])
        
        # Write raw data points with aggregated stats
        for row in raw_data:
            hop = row['chain_length']
            stats = mean_stats.get(hop, {})
            writer.writerow([
                hop,
                row.get('id', ''),
                row.get('question', ''),
                row.get('answer', ''),
                row['correctness'],
                stats.get('mean_accuracy', 0.0),
                stats.get('std_accuracy', 0.0),
                stats.get('count', 0)
            ])
    
    logger.info(f"Generated plot data CSV with {len(raw_data)} rows: {output_path}")

def main() -> int:
    """Main entry point for the script."""
    try:
        # Get project root and paths
        project_root = get_project_root()
        input_path = get_path(project_root, 'data/processed/annotated_videokr.csv')
        output_path = get_path(project_root, 'data/processed/accuracy_vs_hop_raw.csv')
        
        logger.info(f"Loading raw annotated data from: {input_path}")
        raw_data = load_raw_annotated_data(input_path)
        logger.info(f"Loaded {len(raw_data)} records")
        
        if not raw_data:
            logger.error("No data loaded from input file")
            return 1
        
        logger.info("Calculating mean accuracy by hop count...")
        mean_stats = calculate_mean_accuracy_by_hop(raw_data)
        
        logger.info("Generating plot data CSV...")
        generate_plot_data_csv(raw_data, mean_stats, output_path)
        
        # Log summary statistics
        logger.info("Summary statistics by hop count:")
        for hop, stats in sorted(mean_stats.items()):
            logger.info(f"  Hop {hop}: n={stats['count']}, mean_acc={stats['mean_accuracy']:.3f}, "
                      f"std={stats['std_accuracy']:.3f}")
        
        logger.info(f"Successfully generated {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())