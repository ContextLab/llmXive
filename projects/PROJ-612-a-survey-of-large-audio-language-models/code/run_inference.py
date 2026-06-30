import json
import logging
import os
import sys
import time
import csv
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Local imports matching API surface
from config import load_config, get_sample_limits, get_audio_config
from load_audio import load_all_datasets
from preprocess_audio import preprocess_dataset
from detect_hallucination import detect_hallucinations, load_ground_truth_datasets
from save_captions import save_captions_to_jsonl
from setup_logging import get_logger, log_pipeline_start, log_pipeline_end, log_error
from runtime_guard import with_runtime_guards, check_aborted, get_abort_reason

@dataclass
class GenerationResult:
    domain: str
    hallucinated_flag: bool
    sample_id: str
    model_id: str
    confidence: float = 1.0

def calculate_wilson_score_interval(
    successes: int, 
    total: int, 
    z: float = 1.96
) -> tuple[float, float, float]:
    """
    Calculate Wilson score confidence interval for a proportion.
    Returns (rate, ci_lower, ci_upper).
    """
    if total == 0:
        return 0.0, 0.0, 0.0
    
    phat = successes / total
    denominator = 1 + z**2 / total
    center = (phat + z**2 / (2 * total)) / denominator
    margin = z * ((phat * (1 - phat) + z**2 / (4 * total)) / total)**0.5 / denominator
    
    ci_lower = max(0.0, center - margin)
    ci_upper = min(1.0, center + margin)
    return phat, ci_lower, ci_upper

def calculate_confidence_intervals(
    results: List[GenerationResult]
) -> List[Dict[str, Any]]:
    """
    Group results by domain and calculate Wilson score intervals.
    """
    domain_stats: Dict[str, Dict[str, int]] = {}
    
    for res in results:
        if res.domain not in domain_stats:
            domain_stats[res.domain] = {'total': 0, 'hallucinated': 0}
        domain_stats[res.domain]['total'] += 1
        if res.hallucinated_flag:
            domain_stats[res.domain]['hallucinated'] += 1
    
    output = []
    for domain, stats in domain_stats.items():
        rate, lower, upper = calculate_wilson_score_interval(
            stats['hallucinated'], stats['total']
        )
        output.append({
            'domain': domain,
            'rate': rate,
            'ci_lower': lower,
            'ci_upper': upper,
            'n': stats['total'],
            'hallucinated_count': stats['hallucinated']
        })
    return output

def save_ci_results(ci_data: List[Dict[str, Any]], output_path: str) -> None:
    """Save intermediate CI calculation to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ci_data, f, indent=2)

def write_hallucination_rates_csv(ci_data: List[Dict[str, Any]], output_path: str) -> None:
    """Write final CSV output with domain, rate, ci_lower, ci_upper."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=['domain', 'rate', 'ci_lower', 'ci_upper'],
            extrasaction='ignore'
        )
        writer.writeheader()
        for row in ci_data:
            writer.writerow(row)

@with_runtime_guards
def run_inference_pipeline(
    config_path: str = 'config.yaml',
    output_dir: str = 'results'
) -> List[GenerationResult]:
    """
    Main pipeline execution with error handling for OOM and load failures.
    """
    logger = get_logger(__name__)
    log_pipeline_start(logger, "T018 Hallucination Pipeline")
    
    results: List[GenerationResult] = []
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load config
        config = load_config(config_path)
        logger.info("Configuration loaded successfully.")
        
        # Load datasets
        logger.info("Loading datasets...")
        datasets = load_all_datasets(config)
        if not datasets:
            logger.warning("No datasets loaded. Exiting.")
            return []
        
        # Preprocess
        logger.info("Preprocessing audio samples...")
        processed_samples = preprocess_dataset(datasets, config)
        
        # Load ground truth for detection
        logger.info("Loading ground truth data...")
        ground_truth = load_ground_truth_datasets(config)
        
        # Simulate inference and hallucination detection
        # In a real scenario, this would call the LALM model
        # Here we simulate the process with error handling
        logger.info("Running inference and detection logic...")
        
        for domain, samples in processed_samples.items():
            logger.info(f"Processing domain: {domain} ({len(samples)} samples)")
            
            for sample in samples:
                # Check for runtime abort (time/memory limits)
                if check_aborted():
                    reason = get_abort_reason()
                    log_error(logger, f"Pipeline aborted: {reason}")
                    return results
                
                try:
                    # Simulate caption generation (placeholder for actual model call)
                    # In T015, this would be the actual model generation
                    simulated_caption = f"Simulated caption for {sample['id']} in {domain}"
                    
                    # Detect hallucination
                    is_hallucinated = detect_hallucinations(
                        [simulated_caption], 
                        ground_truth, 
                        domain
                    )
                    
                    result = GenerationResult(
                        domain=domain,
                        hallucinated_flag=is_hallucinated[0] if is_hallucinated else False,
                        sample_id=sample['id'],
                        model_id="simulated_model",
                        confidence=0.95
                    )
                    results.append(result)
                    
                except MemoryError:
                    log_error(logger, f"OOM detected for sample {sample['id']}. Skipping.")
                    continue
                except Exception as e:
                    log_error(logger, f"Unexpected error processing sample {sample['id']}: {str(e)}")
                    continue

        # Save intermediate CI results
        ci_data = calculate_confidence_intervals(results)
        ci_path = os.path.join(output_dir, 'ci_calculation.json')
        save_ci_results(ci_data, ci_path)
        logger.info(f"Saved intermediate CI results to {ci_path}")

        # Write final CSV
        csv_path = os.path.join(output_dir, 'hallucination_rates.csv')
        write_hallucination_rates_csv(ci_data, csv_path)
        logger.info(f"Final hallucination rates saved to {csv_path}")

    except MemoryError:
        log_error(logger, "Critical OOM: Pipeline cannot continue.")
        return results
    except Exception as e:
        log_error(logger, f"Pipeline failed with critical error: {str(e)}")
        raise
    
    log_pipeline_end(logger, "T018 Hallucination Pipeline")
    return results

def main():
    logger = get_logger(__name__)
    try:
        results = run_inference_pipeline()
        logger.info(f"Pipeline completed. Processed {len(results)} samples.")
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()