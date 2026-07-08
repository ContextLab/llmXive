import os
import csv
import logging
from typing import List, Dict, Any, Tuple, Optional
from config import RESULTS_DIR, PERMUTATION_COUNT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_p_value(
    observed_score: float,
    null_scores: List[float],
    method: str = "standard"
) -> float:
    """
    Calculate the p-value for an observed score against a null distribution.

    Args:
        observed_score: The actual metric score from the original ranking.
        null_scores: List of metric scores from permuted rankings.
        method: Calculation method (default: standard).

    Returns:
        The p-value calculated as (r + 1) / (N + 1), where r is the count
        of null scores >= observed score, and N is the number of permutations.
    """
    if not null_scores:
        logger.warning("Null distribution is empty. Returning 1.0 as p-value.")
        return 1.0

    # Count how many null scores are greater than or equal to the observed score
    # This assumes a one-tailed test where higher is better (e.g., NDCG, MAP)
    r = sum(1 for score in null_scores if score >= observed_score)
    n = len(null_scores)

    # Standard p-value calculation with correction to avoid zero
    p_value = (r + 1) / (n + 1)
    return p_value

def process_null_distributions(
    null_distributions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Process a list of null distributions to calculate p-values for each.

    Args:
        null_distributions: List of dicts containing:
            - query_id: The query identifier
            - metric: The metric name (e.g., 'NDCG@10', 'MAP')
            - observed_score: The original score
            - null_scores: List of permuted scores

    Returns:
        List of dicts containing query_id, metric, observed_score, and p_value.
    """
    results = []
    for item in null_distributions:
        query_id = item['query_id']
        metric = item['metric']
        observed_score = item['observed_score']
        null_scores = item['null_scores']

        p_value = calculate_p_value(observed_score, null_scores)

        results.append({
            'query_id': query_id,
            'metric': metric,
            'observed_score': observed_score,
            'p_value': p_value
        })
        logger.info(f"Query {query_id} ({metric}): observed={observed_score:.4f}, p={p_value:.4f}")

    return results

def run_p_value_calculation(
    null_distributions_dir: Optional[str] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Load null distributions from disk, calculate p-values, and save results.

    This function fulfills task T018 by saving raw p-values to
    `results/p_values/raw_p_values.csv`.

    Args:
        null_distributions_dir: Directory containing null distribution CSVs.
            Defaults to `results/null_distributions/` if not provided.
        output_path: Path for the output CSV. Defaults to
            `results/p_values/raw_p_values.csv` if not provided.

    Returns:
        List of dicts containing the calculated p-values.
    """
    if null_distributions_dir is None:
        null_distributions_dir = os.path.join(RESULTS_DIR, "null_distributions")

    if output_path is None:
        output_path = os.path.join(RESULTS_DIR, "p_values", "raw_p_values.csv")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Load all null distribution CSVs
    all_null_data = []
    if not os.path.exists(null_distributions_dir):
        logger.error(f"Null distributions directory not found: {null_distributions_dir}")
        # Return empty list if directory doesn't exist
        return []

    csv_files = [f for f in os.listdir(null_distributions_dir) if f.endswith('.csv')]
    if not csv_files:
        logger.warning(f"No CSV files found in {null_distributions_dir}")
        return []

    for csv_file in csv_files:
        file_path = os.path.join(null_distributions_dir, csv_file)
        try:
            with open(file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # Extract observed score (usually the first row or marked explicitly)
                # We assume the file format: query_id, metric, score
                # The first row is the observed score, subsequent rows are null
                if not rows:
                    continue
                
                # Parse the first row as observed
                first_row = rows[0]
                query_id = int(first_row['query_id'])
                metric = first_row['metric']
                observed_score = float(first_row['score'])
                
                # Parse the rest as null scores
                null_scores = [float(row['score']) for row in rows[1:]]
                
                all_null_data.append({
                    'query_id': query_id,
                    'metric': metric,
                    'observed_score': observed_score,
                    'null_scores': null_scores
                })
        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
            continue

    if not all_null_data:
        logger.warning("No valid null distribution data found to process.")
        # Create empty output file
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'observed_score', 'p_value'])
            writer.writeheader()
        return []

    # Calculate p-values
    p_value_results = process_null_distributions(all_null_data)

    # Save to CSV
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['query_id', 'metric', 'observed_score', 'p_value']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(p_value_results)

    logger.info(f"Saved {len(p_value_results)} p-values to {output_path}")
    return p_value_results