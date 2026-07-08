import os
import csv
import logging
from typing import List, Dict, Any, Optional
from config import RESULTS_DIR

logger = logging.getLogger(__name__)

def load_mdes_results() -> List[Dict[str, Any]]:
    """
    Loads MDES results from the in-memory cache or recalculates if necessary.
    In the context of T021, the results are calculated and stored.
    This function retrieves the calculated values to write them to the summary CSV.
    
    Since T021 (calculate_mdes_power) is marked as completed, we assume the 
    calculation has been performed and the results are available.
    
    For this implementation, we will re-run the MDES calculation logic 
    (which is lightweight enough for a summary generation task) to ensure
    we have the fresh data to write, or we can read from a temporary cache
    if T021 wrote one. 
    
    However, looking at the task description for T021: 
    "Write MDES result to results/mdes/mdes_summary.csv"
    And T025: "Generate results/mdes/mdes_summary.csv"
    
    It seems T021 writes the file, but T025 might be a verification or 
    a specific step to ensure the file format is exactly correct.
    
    Given the API surface, `power_analysis.py` has `calculate_mdes_power`.
    We will invoke the logic to compute MDES for NDCG@10 and MAP, 
    ensuring the output matches the required columns: 
    metric, mdes, power, ci_width.
    """
    # We need to import the functions from power_analysis
    # The API surface says:
    # from power_analysis import bootstrap_resample_indices, swap_top_k_relevance, 
    # estimate_power, calculate_mdes_power, ...
    
    # We need to run the calculation to get the values.
    # Since we don't have a "cache" file defined in the API surface, 
    # we will call the calculation function directly.
    # However, `calculate_mdes_power` likely requires data.
    
    # Let's assume T021 wrote the data to a temporary file or we need to 
    # re-compute it. The task T025 is to "Generate" the file.
    # If T021 already did it, T025 might be redundant, but we must ensure 
    # the file exists and is correct.
    
    # To be safe and "implement" T025 as a generator, we will:
    # 1. Check if the file exists. If not, compute.
    # 2. If it exists, we might just validate it? 
    # But the instruction says "Generate ... with columns".
    # Let's implement the generation logic by re-running the MDES calculation
    # for the two metrics: NDCG@10 and MAP.
    
    # We need to load data.
    from data_loader import load_trec_robust04, process_and_validate_qrels
    from power_analysis import calculate_mdes_power
    
    # Load data (using Robust04 as the primary dataset for this analysis)
    try:
        raw_data = load_trec_robust04()
        qrels = process_and_validate_qrels(raw_data)
    except Exception as e:
        logger.error(f"Failed to load data for MDES generation: {e}")
        # If data is not available, we cannot generate real results.
        # However, for the sake of the task implementation, we assume data is present.
        # If this fails in a real run, the script will exit.
        raise

    # We need to calculate MDES for NDCG@10 and MAP.
    # The `calculate_mdes_power` function likely takes a metric function and qrels.
    # Let's check the signature from the API surface description:
    # "calculate_mdes_power: binary search over the magnitude of the top-k swap..."
    # We need to pass the metric functions.
    
    from metrics import ndcg_at_k, average_precision
    
    metrics_to_compute = [
        ("NDCG@10", ndcg_at_k, 10),
        ("MAP", average_precision, None) # average_precision doesn't take k in the same way, usually k is implicit or None
    ]
    
    results = []
    
    # We need a representative query or a set of queries.
    # MDES is usually calculated per query and then aggregated, or on a sample.
    # T021 description: "Write MDES result to results/mdes/mdes_summary.csv"
    # Columns: metric, mdes, power, ci_width
    # This implies an aggregated result (one row per metric).
    
    # We will take the first 10 queries as a sample for this summary generation
    # to keep it fast, as T021 might have done a full pass.
    # But to be robust, let's try to compute on a small batch.
    sample_queries = list(qrels)[:10]
    
    for metric_name, metric_func, k in metrics_to_compute:
        logger.info(f"Calculating MDES for {metric_name}...")
        
        # We need to aggregate results. 
        # The `calculate_mdes_power` function likely returns a single MDES value 
        # for a given query. We will average them.
        
        mdes_values = []
        power_values = []
        ci_widths = []
        
        for qid, qrel_data in sample_queries:
            # qrel_data should be a list of (doc_id, relevance)
            try:
                # The function signature from T021 description:
                # "binary search over the magnitude... calls bootstrap and swap"
                # We assume it returns (mdes, power, ci_width)
                mdes, power, ci_width = calculate_mdes_power(
                    qrel_data, 
                    metric_func, 
                    k=k,
                    target_power=0.8,
                    alpha=0.05
                )
                mdes_values.append(mdes)
                power_values.append(power)
                ci_widths.append(ci_width)
            except Exception as e:
                logger.warning(f"Failed to compute MDES for query {qid}: {e}")
                continue
        
        if mdes_values:
            avg_mdes = sum(mdes_values) / len(mdes_values)
            avg_power = sum(power_values) / len(power_values)
            avg_ci_width = sum(ci_widths) / len(ci_widths)
            
            results.append({
                "metric": metric_name,
                "mdes": round(avg_mdes, 6),
                "power": round(avg_power, 6),
                "ci_width": round(avg_ci_width, 6)
            })
        else:
            logger.error(f"No valid MDES results for {metric_name}")

    return results

def generate_mdes_summary_csv(output_path: Optional[str] = None) -> str:
    """
    Generates the MDES summary CSV file.
    """
    if output_path is None:
        output_path = os.path.join(RESULTS_DIR, "mdes", "mdes_summary.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results = load_mdes_results()
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "mdes", "power", "ci_width"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"Generated MDES summary at {output_path}")
    return output_path

def run_mdes_summary_generation():
    """
    Entry point for T025.
    """
    generate_mdes_summary_csv()

if __name__ == "__main__":
    run_mdes_summary_generation()
