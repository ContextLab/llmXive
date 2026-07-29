import os
import sys
import csv
import json
import logging
import argparse
import gc
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Project imports
from config import load_config, NoiseSweepConfig, DataConfig
from data_loader import (
    load_reasoning_dataset,
    pair_questions_by_task_type,
    verify_data_integrity,
    ConfigurationError,
    DataIntegrityError
)
from model_utils import load_frozen_model, extract_thought_vector, normalize_vector
from perturbation import inject_and_project
from validity_check import (
    get_sbert,
    check_input_drift_incremental,
    check_output_validity,
    check_validity_collapse,
    SBERTLoadError
)
from streaming_utils import stream_dataset, batch_iterator
from memory_monitor import (
    reset_memory_tracker,
    get_peak_memory_mb,
    save_memory_profile,
    check_memory_limit,
    MemoryLimitExceeded
)
from sweep_logging import (
    ensure_logs_directory,
    SweepLogger,
    log_sweep_start,
    log_sweep_step,
    log_sweep_complete,
    log_sweep_error
)
from analysis import NoValidSigmaError, aggregate_global_results

# Constants
VALIDITY_THRESHOLD = 0.90
INPUT_DRIFT_THRESHOLD = 0.95
OUTPUT_VALIDITY_THRESHOLD = 0.85
MAX_RSS_MB = 7000  # 7GB limit

def setup_logging():
    """Configure logging for the pipeline."""
    ensure_logs_directory()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def ensure_output_directory(path: str):
    """Ensure the output directory exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

def verify_data_fetch_integrity(config: DataConfig, logger: logging.Logger):
    """Verify that the dataset has been fetched and passed integrity checks."""
    logger.info("Verifying data fetch integrity...")
    try:
        verify_data_integrity(config.dataset_path, config.checksums_path, logger)
    except DataIntegrityError as e:
        logger.error(f"Data integrity check failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Dataset file not found: {e}")
        sys.exit(1)

def run_baseline_extraction(config: DataConfig, model, tokenizer, logger: logging.Logger, sweep_logger: SweepLogger):
    """
    Run baseline hidden state extraction (T021).
    Produces: data/processed/baseline_vectors.csv, data/processed/pairing_config.json
    """
    logger.info("Starting baseline extraction...")
    start_time = time.time()
    
    # Load and pair data
    try:
        dataset = load_reasoning_dataset(config.dataset_path, logger)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    paired_data = pair_questions_by_task_type(dataset, logger)
    
    # Save pairing config
    pairing_config_path = "data/processed/pairing_config.json"
    ensure_output_directory(pairing_config_path)
    with open(pairing_config_path, 'w') as f:
        json.dump(paired_data['config'], f, indent=2)
    logger.info(f"Saved pairing config to {pairing_config_path}")

    # Extract vectors
    baseline_vectors_path = "data/processed/baseline_vectors.csv"
    ensure_output_directory(baseline_vectors_path)
    
    with open(baseline_vectors_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['pair_id', 'task_type', 'vector_base64', 'norm_status'])
        
        processed_count = 0
        for item in paired_data['pairs']:
            pair_id = item['pair_id']
            task_type = item['task_type']
            input_ids = item['input_ids']
            
            # Convert to tensor
            input_tensor = torch.tensor([input_ids])
            
            # Extract hidden state (assuming 'thought' token is at a specific position, e.g., -1 or defined by config)
            # For this implementation, we assume the last token of the input represents the 'thought'
            thought_pos = len(input_ids) - 1 
            
            try:
                vector = extract_thought_vector(model, input_tensor, thought_pos, logger)
                normalized_vec = normalize_vector(vector)
                
                # Base64 encode
                import base64
                import numpy as np
                vec_bytes = normalized_vec.cpu().numpy().tobytes()
                vec_b64 = base64.b64encode(vec_bytes).decode('utf-8')
                
                writer.writerow([pair_id, task_type, vec_b64, 'L2_NORMALIZED'])
                processed_count += 1
                
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} baseline pairs...")
                    # Log progress
                    sweep_logger.log_progress('baseline', processed_count, len(paired_data['pairs']))
                    
            except Exception as e:
                logger.error(f"Error extracting vector for pair {pair_id}: {e}")
                continue

    elapsed = time.time() - start_time
    logger.info(f"Baseline extraction complete. Processed {processed_count} pairs in {elapsed:.2f}s.")
    
    # Check memory
    peak_rss = get_peak_memory_mb()
    if peak_rss > MAX_RSS_MB:
        raise MemoryLimitExceeded(f"Baseline extraction exceeded memory limit: {peak_rss}MB > {MAX_RSS_MB}MB")
    
    return paired_data['pairs']

def run_sweep(config: NoiseSweepConfig, data_config: DataConfig, model, tokenizer, 
              baseline_pairs: List[Dict], logger: logging.Logger, sweep_logger: SweepLogger):
    """
    Implement T029: Perturbation sweep loop logic.
    - Iterate sigma
    - Perturb inputs
    - Extract vectors
    - Run validity checks (Input Drift, Output Validity)
    - Calculate pass-rate, detect collapse point
    - Save validity_log.csv immediately (incremental write)
    """
    logger.info("Starting perturbation sweep loop (T029)...")
    
    sigma_min = config.sigma_min
    sigma_max = config.sigma_max
    step = config.step
    
    # Load embedding matrix for projection
    embedding_matrix = model.get_input_embeddings().weight.data
    
    # Prepare output files
    validity_log_path = "data/processed/validity_log.csv"
    ensure_output_directory(validity_log_path)
    
    # Headers
    headers = ['task_type', 'sigma', 'pass_rate', 'collapse_point', 'pairs_total', 'pairs_passed']
    
    # We need to track results per task type to detect collapse
    task_type_stats = {} # { task_type: {'collapsed': False, 'collapse_sigma': None} }
    
    # Initialize CSV writer (append mode for incremental write)
    file_exists = os.path.exists(validity_log_path)
    
    # Get unique task types
    task_types = list(set(p['task_type'] for p in baseline_pairs))
    logger.info(f"Task types to process: {task_types}")
    
    # Iterate Sigma
    sigmas = []
    current_sigma = sigma_min
    while current_sigma <= sigma_max + 1e-9: # Floating point tolerance
        sigmas.append(current_sigma)
        current_sigma += step
    
    logger.info(f"Sweeping sigma from {sigma_min} to {sigma_max} with step {step} ({len(sigmas)} steps)")
    
    sbert_model = None
    try:
        sbert_model = get_sbert()
    except SBERTLoadError as e:
        logger.error(f"Failed to load SBERT model: {e}")
        sys.exit(1)

    for sigma in sigmas:
        logger.info(f"--- Processing Sigma: {sigma:.4f} ---")
        log_sweep_step(sweep_logger, sigma, 'processing')
        
        # Reset per-sigma counters
        sigma_task_results = {} # { task_type: {'total': 0, 'passed': 0} }
        
        # Iterate over task types
        for task_type in task_types:
            # Skip if this task type already collapsed
            if task_type in task_type_stats and task_type_stats[task_type]['collapsed']:
                logger.info(f"Task type {task_type} already collapsed at {task_type_stats[task_type]['collapse_sigma']:.4f}. Skipping.")
                # Record the collapse point again for the log to show it was skipped
                with open(validity_log_path, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(headers)
                        file_exists = True
                    writer.writerow([task_type, f"{sigma:.4f}", 0.0, True, 0, 0])
                continue
            
            # Filter pairs for this task type
            task_pairs = [p for p in baseline_pairs if p['task_type'] == task_type]
            
            total_pairs = len(task_pairs)
            passed_pairs = 0
            
            # Process pairs in batches for efficiency
            batch_size = 10
            for i in range(0, total_pairs, batch_size):
                batch = task_pairs[i:i+batch_size]
                batch_passed = 0
                
                for pair in batch:
                    pair_id = pair['pair_id']
                    original_input_ids = pair['input_ids']
                    expected_answer = pair.get('expected_answer', '')
                    
                    try:
                        # 1. Inject Noise and Project
                        input_tensor = torch.tensor([original_input_ids]).to(model.device)
                        # Get embeddings
                        with torch.no_grad():
                            embeddings = model.get_input_embeddings()(input_tensor)
                        
                        # Inject noise
                        noise = torch.randn_like(embeddings) * sigma
                        perturbed_embeddings = embeddings + noise
                        
                        # Project to nearest valid token
                        perturbed_token_ids, _ = inject_and_project(
                            perturbed_embeddings, 
                            sigma, 
                            embedding_matrix, 
                            logger
                        )
                        
                        # 2. Check Input Drift (T026)
                        # Convert ids back to text for SBERT comparison
                        baseline_text = tokenizer.decode(original_input_ids, skip_special_tokens=True)
                        perturbed_text = tokenizer.decode(perturbed_token_ids[0], skip_special_tokens=True)
                        
                        # Check drift
                        drift_score = check_input_drift_incremental(
                            baseline_text, 
                            perturbed_text, 
                            sbert_model, 
                            logger
                        )
                        
                        if drift_score < INPUT_DRIFT_THRESHOLD:
                            # Failed input drift
                            continue
                        
                        # 3. Check Output Validity (T027)
                        # Run model on perturbed input to get output
                        with torch.no_grad():
                            outputs = model.generate(
                                perturbed_token_ids, 
                                max_new_tokens=50, 
                                do_sample=False,
                                pad_token_id=tokenizer.eos_token_id
                            )
                        
                        model_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        
                        # Check if model output matches expected answer (semantic similarity)
                        # Note: T027 uses BERTScore. We simulate the check here by calling the function if available
                        # or implementing a simple check. Since T027 is a helper, we assume it returns a score.
                        # For this implementation, we'll assume check_output_validity returns a boolean or score.
                        # Let's assume it returns a score >= 0.85 is valid.
                        output_score = check_output_validity(model_output, expected_answer, logger)
                        
                        if output_score >= OUTPUT_VALIDITY_THRESHOLD:
                            batch_passed += 1
                            passed_pairs += 1
                        
                    except Exception as e:
                        logger.warning(f"Error processing pair {pair_id} at sigma {sigma}: {e}")
                        continue
                
                # Incremental write for this batch? 
                # T029 says "MUST record... IMMEDIATELY upon detection... and BEFORE breaking".
                # And "incremental write strategy... write per-step".
                # We will write the aggregate for this task_type/sigma after processing the batch if we want true incremental,
                # but usually we wait for the whole task_type/sigma to finish to calculate pass_rate.
                # However, to prevent data loss on crash, we can write a "partial" status or just rely on the final write of the loop.
                # Given the constraint "write per-step... rather than accumulating", we will write the result for the task_type/sigma 
                # immediately after processing all pairs for that task_type/sigma.
                
            # Calculate pass rate for this task_type/sigma
            if total_pairs > 0:
                pass_rate = passed_pairs / total_pairs
            else:
                pass_rate = 0.0
            
            # Check for collapse
            is_collapse = check_validity_collapse(pass_rate, VALIDITY_THRESHOLD)
            
            # Record result
            with open(validity_log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(headers)
                    file_exists = True
                writer.writerow([task_type, f"{sigma:.4f}", f"{pass_rate:.4f}", is_collapse, total_pairs, passed_pairs])
            
            logger.info(f"Task {task_type}, Sigma {sigma:.4f}: Pass Rate {pass_rate:.2%} (Collapse: {is_collapse})")
            
            if is_collapse:
                task_type_stats[task_type] = {
                    'collapsed': True,
                    'collapse_sigma': sigma,
                    'collapse_pass_rate': pass_rate
                }
                logger.warning(f"Validity collapse detected for {task_type} at sigma {sigma:.4f}")
                # Break the sigma loop for this task type? 
                # T029: "stop processing higher sigma values for a task type immediately upon detection"
                # We handle this by setting the flag and skipping in subsequent sigma iterations.
                # No need to break the inner loop here as we are already at the end of the task_type loop.
        
        # Garbage collection after each sigma step to prevent memory leak
        gc.collect()
        peak_rss = get_peak_memory_mb()
        if peak_rss > MAX_RSS_MB:
            raise MemoryLimitExceeded(f"Sweep exceeded memory limit at sigma {sigma:.4f}: {peak_rss}MB")
        
        # Log progress
        log_sweep_step(sweep_logger, sigma, 'completed', {'task_type_stats': task_type_stats})

    logger.info("Perturbation sweep loop completed.")
    return task_type_stats

def run_final_analysis(task_type_stats: Dict, logger: logging.Logger):
    """
    Run final analysis (T037, T039, etc.) after the sweep.
    This orchestrates the analysis phase.
    """
    logger.info("Starting final analysis...")
    
    # Check for no valid sigma scenario
    # (Implementation depends on analysis.py functions)
    # For now, we call the aggregate function
    try:
        aggregate_global_results(task_type_stats, logger)
    except NoValidSigmaError as e:
        logger.warning(f"No valid sigma found: {e}")
        # Handle inconclusive report
    except Exception as e:
        logger.error(f"Final analysis failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="LLM Noise Injection Pipeline")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--dry-run', action='store_true', help='Run without model inference')
    args = parser.parse_args()

    logger = setup_logging()
    logger.info("Pipeline started.")

    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Pre-flight checks
    verify_data_fetch_integrity(config.data, logger)

    # Memory monitoring
    reset_memory_tracker()
    start_monitoring()

    # Initialize model
    if not args.dry_run:
        model, tokenizer = load_frozen_model(config.model, logger)
    else:
        logger.info("Dry run: Skipping model load.")
        model, tokenizer = None, None

    # Initialize sweep logger
    sweep_logger = SweepLogger()
    log_sweep_start(sweep_logger, config.noise_sweep)

    # Phase 1: Baseline Extraction (T021)
    baseline_pairs = []
    if not args.dry_run:
        baseline_pairs = run_baseline_extraction(config.data, model, tokenizer, logger, sweep_logger)
    else:
        logger.info("Dry run: Skipping baseline extraction.")
        # In dry run, we might need mock data or just skip
        # For T029 implementation, we assume baseline data exists or is generated
        # But per T029 description, it depends on T021.
        # If dry run, we can't run the sweep without data.
        # We will assume the user has run baseline extraction or we skip T029 in dry run.
        # For now, we exit if dry run and no baseline.
        if not os.path.exists("data/processed/baseline_vectors.csv"):
            logger.error("Baseline vectors missing and dry-run mode. Cannot proceed with sweep.")
            sys.exit(1)

    # Phase 2: Perturbation Sweep (T029)
    task_type_stats = {}
    if not args.dry_run:
        task_type_stats = run_sweep(
            config.noise_sweep, 
            config.data, 
            model, 
            tokenizer, 
            baseline_pairs, 
            logger, 
            sweep_logger
        )
    else:
        logger.info("Dry run: Skipping perturbation sweep.")

    # Phase 3: Final Analysis (T037, T039)
    if not args.dry_run:
        run_final_analysis(task_type_stats, logger)

    # Save memory profile
    save_memory_profile("data/processed/memory_profile.json")

    log_sweep_complete(sweep_logger)
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    import torch
    main()
