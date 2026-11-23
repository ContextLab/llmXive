"""
Metrics calculation module for lottery draw analysis.

Implements valid metrics (birthday_cluster_ratio, consecutive_pattern_count)
to replace the scientifically invalid per-draw Chi-Square.

Handles missing `total_sales` data gracefully by logging warnings and
excluding from sales-dependent checks while retaining rows for frequency analysis.
"""
from typing import List, Union, Optional, Dict, Any
import json
import os
import logging
import numpy as np
from constants import BIRTHDAY_THRESHOLD, NUMBERS_PER_DRAW
from data_utils import load_draws_csv
from exceptions import MissingSalesError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_birthday_ratio(draw_numbers: List[int]) -> float:
    """
    Calculate the birthday cluster ratio for a single draw.
    
    This metric measures the proportion of numbers in a draw that fall
    within the "birthday" range (1-31), which is a common heuristic for
    analyzing number selection patterns.
    
    Args:
        draw_numbers: List of integers representing the numbers in a draw.
        
    Returns:
        float: Ratio of numbers in the draw that are <= BIRTHDAY_THRESHOLD (0.0 to 1.0).
    """
    if not draw_numbers:
        return 0.0
    
    if len(draw_numbers) != NUMBERS_PER_DRAW:
        logger.warning(f"Draw has {len(draw_numbers)} numbers, expected {NUMBERS_PER_DRAW}")
    
    birthday_count = sum(1 for num in draw_numbers if num <= BIRTHDAY_THRESHOLD)
    return birthday_count / len(draw_numbers)

def calculate_consecutive_ratio(draw_numbers: List[int]) -> float:
    """
    Calculate the consecutive pattern ratio for a single draw.
    
    This metric measures the proportion of consecutive number pairs in a sorted draw.
    For a draw of N numbers, there are N-1 possible consecutive pairs.
    
    Args:
        draw_numbers: List of integers representing the numbers in a draw.
        
    Returns:
        float: Ratio of consecutive pairs found (0.0 to 1.0).
    """
    if not draw_numbers or len(draw_numbers) < 2:
        return 0.0
    
    sorted_nums = sorted(draw_numbers)
    consecutive_pairs = 0
    
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i + 1] - sorted_nums[i] == 1:
            consecutive_pairs += 1
    
    max_pairs = len(sorted_nums) - 1
    return consecutive_pairs / max_pairs if max_pairs > 0 else 0.0

def process_draws_for_metrics(draws_df) -> List[Dict[str, Any]]:
    """
    Process a DataFrame of draws to calculate metrics for each draw.
    
    Handles missing `total_sales` by logging a warning and excluding
    from sales-dependent checks, while retaining the row for frequency analysis.
    
    Args:
        draws_df: pandas DataFrame containing draw data with columns:
                  - 'numbers': list of integers
                  - 'total_sales': optional sales amount
                  - 'jackpot_amount': jackpot amount
                  - 'draw_date': date of draw
                
    Returns:
        List of dictionaries containing draw metrics and metadata.
    """
    results = []
    missing_sales_count = 0
    
    for idx, row in draws_df.iterrows():
        draw_numbers = row.get('numbers')
        total_sales = row.get('total_sales')
        jackpot_amount = row.get('jackpot_amount')
        draw_date = row.get('draw_date')
        
        if draw_numbers is None:
            logger.warning(f"Row {idx}: Missing draw numbers, skipping")
            continue
        
        # Calculate primary metrics (independent of sales data)
        birthday_ratio = calculate_birthday_ratio(draw_numbers)
        consecutive_ratio = calculate_consecutive_ratio(draw_numbers)
        
        # Determine if majority of numbers are birthdays
        is_majority_birthday = birthday_ratio > 0.5
        
        # Handle missing total_sales
        has_sales_data = total_sales is not None and not (isinstance(total_sales, float) and np.isnan(total_sales))
        
        if not has_sales_data:
            missing_sales_count += 1
            logger.warning(
                f"Row {idx}: Missing total_sales for draw on {draw_date}. "
                "Excluding from sales-dependent checks but retaining for frequency analysis."
            )
        
        result = {
            'draw_index': idx,
            'draw_date': str(draw_date) if draw_date else None,
            'numbers': draw_numbers,
            'birthday_cluster_ratio': round(birthday_ratio, 6),
            'consecutive_pattern_count': round(consecutive_ratio, 6),
            'is_majority_birthday': is_majority_birthday,
            'jackpot_amount': jackpot_amount,
            'has_sales_data': has_sales_data,
            'total_sales': total_sales if has_sales_data else None
        }
        
        results.append(result)
    
    if missing_sales_count > 0:
        logger.info(f"Total draws with missing sales data: {missing_sales_count} "
                   f"({100*missing_sales_count/len(draws_df):.1f}% of total)")
    
    return results

def save_metrics_to_json(metrics_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save calculated metrics to a JSON file.
    
    Args:
        metrics_data: List of metric dictionaries from process_draws_for_metrics
        output_path: Path to save the JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    summary = {
        'total_draws': len(metrics_data),
        'draws_with_sales_data': sum(1 for m in metrics_data if m['has_sales_data']),
        'draws_without_sales_data': sum(1 for m in metrics_data if not m['has_sales_data']),
        'metrics': metrics_data
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"Metrics saved to {output_path}")

def main():
    """
    Main entry point for running the metrics calculation pipeline.
    
    Loads raw draw data, calculates metrics for each draw, and saves
    the results to data/processed/metrics.json.
    """
    input_path = 'data/raw/lottery_draws.csv'
    output_path = 'data/processed/metrics.json'
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run code/ingestion.py first to download the data.")
        sys.exit(1)
    
    logger.info(f"Loading draw data from {input_path}")
    try:
        draws_df = load_draws_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load draw data: {e}")
        sys.exit(1)
    
    logger.info(f"Processing {len(draws_df)} draws for metrics calculation")
    metrics_data = process_draws_for_metrics(draws_df)
    
    if not metrics_data:
        logger.error("No valid metrics calculated. Check input data format.")
        sys.exit(1)
    
    save_metrics_to_json(metrics_data, output_path)
    
    # Log summary statistics
    avg_birthday_ratio = np.mean([m['birthday_cluster_ratio'] for m in metrics_data])
    avg_consecutive_ratio = np.mean([m['consecutive_pattern_count'] for m in metrics_data])
    majority_birthday_count = sum(1 for m in metrics_data if m['is_majority_birthday'])
    
    logger.info(f"=== Metrics Summary ===")
    logger.info(f"Total draws processed: {len(metrics_data)}")
    logger.info(f"Draws with sales data: {sum(1 for m in metrics_data if m['has_sales_data'])}")
    logger.info(f"Draws without sales data: {sum(1 for m in metrics_data if not m['has_sales_data'])}")
    logger.info(f"Average birthday_cluster_ratio: {avg_birthday_ratio:.4f}")
    logger.info(f"Average consecutive_pattern_count: {avg_consecutive_ratio:.4f}")
    logger.info(f"Draws with majority birthday numbers: {majority_birthday_count} ({100*majority_birthday_count/len(metrics_data):.1f}%)")
    logger.info(f"=======================")

if __name__ == '__main__':
    main()
