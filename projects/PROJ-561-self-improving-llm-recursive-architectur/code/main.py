import os
import sys
import time
import json
import gc
import traceback
from typing import List, Dict, Any, Optional

from config import get_config, PathConfig
from pipeline.model import (
    load_gpt_124m,
    get_model_param_count,
    apply_architectural_modification,
    generate_modification_proposal,
    get_modification_history,
    validate_modification_distinctness,
    save_model_state,
    load_model_state,
    compute_and_record_flops
)
from pipeline.trainer import run_training_cycle_with_timeout, train_epoch
from pipeline.evaluator import run_all_benchmarks
from pipeline.stats import paired_bootstrap_test
from pipeline.memory import get_memory_usage_gb, enforce_ram_limit, MemoryWatchdog
from results.trajectory_schema import write_trajectory, TrajectoryEntry
from schemas.modification_proposal import ModificationProposal
from utils.logging import init_cycle_logger, update_cycle_log, log_cycle_summary

# Import retry logic components (T035)
from pipeline.trainer import run_training_cycle

class ResourceMonitor:
    def __init__(self, limit_gb: float = 7.0):
        self.limit_gb = limit_gb
        self.watchdog = MemoryWatchdog(limit_gb)

    def check_memory(self) -> bool:
        current = get_memory_usage_gb()
        if current > self.limit_gb:
            return False
        return True

def run_single_cycle_with_timeout(
    cycle_number: int,
    model,
    config,
    timeout_seconds: int = 3600
) -> Optional[Dict[str, Any]]:
    """
    Executes a single refinement cycle with timeout enforcement.
    Returns metrics dict or None if timeout/failure.
    """
    start_time = time.time()
    log_path = f"results/logs/cycle_{cycle_number}.log"
    
    try:
        # 1. Propose modification
        proposal = generate_modification_proposal(model)
        
        # 2. Validate distinctness against history
        history = get_modification_history()
        if not validate_modification_distinctness(proposal, history):
            # Re-prompt logic handled inside generate_modification_proposal loop
            # If it returns a non-distinct one despite retries, we log and skip
            print(f"Cycle {cycle_number}: Proposal not distinct after retries. Skipping.")
            return None

        # 3. Apply modification
        model = apply_architectural_modification(model, proposal)
        
        # 4. Train with timeout
        metrics = run_training_cycle_with_timeout(
            model, 
            config, 
            timeout_seconds=timeout_seconds
        )
        
        if metrics is None:
            print(f"Cycle {cycle_number}: Training timed out or failed.")
            return None

        # 5. Evaluate
        eval_results = run_all_benchmarks(model, config)
        
        # 6. Compare stats (baseline vs current)
        # Assuming baseline is cycle 0 or stored separately
        # For now, just record metrics
        metrics.update(eval_results)
        metrics['cycle_number'] = cycle_number
        metrics['timestamp'] = time.time()
        
        # 7. Record FLOPs
        flops = compute_and_record_flops(model)
        metrics['flops'] = flops
        
        # 8. Save trajectory
        entry = TrajectoryEntry(
            cycle_number=cycle_number,
            param_count=get_model_param_count(model),
            gsm8k_accuracy=metrics.get('gsm8k_accuracy', 0.0),
            arc_accuracy=metrics.get('arc_accuracy', 0.0),
            wikitext2_ece=metrics.get('wikitext2_ece', 0.0),
            flops=flops,
            training_time=metrics.get('training_time', 0.0),
            modification_type=proposal.modification_type,
            modification_magnitude=proposal.magnitude
        )
        write_trajectory(entry)
        
        # 9. Save checkpoint
        checkpoint_path = os.path.join(config.path_config.checkpoints, f"cycle_{cycle_number}.pt")
        save_model_state(model, checkpoint_path)
        
        # 10. Log summary
        log_cycle_summary(cycle_number, metrics)
        
        return metrics

    except Exception as e:
        print(f"Cycle {cycle_number} failed: {e}")
        traceback.print_exc()
        return None

def run_full_pipeline(max_cycles: int = 3, timeout_per_cycle: int = 3600):
    """
    Orchestrates multiple refinement cycles, ensuring distinct modifications.
    Implements T025: distinct modification constraint across cycles.
    """
    config = get_config()
    model = load_gpt_124m(config)
    
    # Track modification history in memory (T025 requirement)
    modification_history: List[ModificationProposal] = []
    
    results = []
    
    for cycle_num in range(1, max_cycles + 1):
        print(f"Starting Cycle {cycle_num}...")
        
        # Retry logic for training failures (T035)
        success = False
        retry_count = 0
        max_retries = 2
        
        while not success and retry_count <= max_retries:
            try:
                # Generate proposal with distinctness check
                # We loop here until we get a distinct proposal or hit system timeout
                proposal = None
                attempts = 0
                max_attempts = 10
                
                while proposal is None and attempts < max_attempts:
                    candidate = generate_modification_proposal(model)
                    if validate_modification_distinctness(candidate, modification_history):
                        proposal = candidate
                    else:
                        attempts += 1
                        print(f"Proposal not distinct (attempt {attempts}), re-prompting...")
                
                if proposal is None:
                    print(f"Could not generate distinct proposal after {max_attempts} attempts.")
                    break
                
                # Apply modification
                model = apply_architectural_modification(model, proposal)
                
                # Run training with timeout
                metrics = run_training_cycle_with_timeout(
                    model, 
                    config, 
                    timeout_seconds=timeout_per_cycle
                )
                
                if metrics is not None:
                    success = True
                    modification_history.append(proposal)
                    
                    # Evaluate
                    eval_results = run_all_benchmarks(model, config)
                    metrics.update(eval_results)
                    
                    # Record trajectory
                    entry = TrajectoryEntry(
                        cycle_number=cycle_num,
                        param_count=get_model_param_count(model),
                        gsm8k_accuracy=metrics.get('gsm8k_accuracy', 0.0),
                        arc_accuracy=metrics.get('arc_accuracy', 0.0),
                        wikitext2_ece=metrics.get('wikitext2_ece', 0.0),
                        flops=metrics.get('flops', 0),
                        training_time=metrics.get('training_time', 0.0),
                        modification_type=proposal.modification_type,
                        modification_magnitude=proposal.magnitude
                    )
                    write_trajectory(entry)
                    
                    # Save checkpoint
                    checkpoint_path = os.path.join(config.path_config.checkpoints, f"cycle_{cycle_num}.pt")
                    save_model_state(model, checkpoint_path)
                    
                    results.append(metrics)
                    print(f"Cycle {cycle_num} completed successfully.")
                else:
                    retry_count += 1
                    print(f"Cycle {cycle_num} training failed, retry {retry_count}/{max_retries}...")
                    
            except Exception as e:
                retry_count += 1
                print(f"Cycle {cycle_num} exception: {e}, retry {retry_count}/{max_retries}...")
                traceback.print_exc()
        
        if not success:
            print(f"Cycle {cycle_num} failed after {max_retries} retries. Proceeding to next cycle.")
            # Proceed to next cycle with new proposal (T035 spec)
            continue
        
        # Early termination check (T039)
        if cycle_num > 1 and len(results) >= 2:
            baseline = results[0]
            current = results[-1]
            # Check degradation >= 5%
            if baseline.get('gsm8k_accuracy', 0) > 0:
                degradation = (baseline['gsm8k_accuracy'] - current.get('gsm8k_accuracy', 0)) / baseline['gsm8k_accuracy']
                if degradation >= 0.05:
                    print(f"Early Stop: Degradation {degradation:.2%} >= 5%.")
                    save_model_state(model, os.path.join(config.path_config.checkpoints, f"degradation_cycle_{cycle_num}.pt"))
                    break
    
    return results

if __name__ == "__main__":
    # Example execution
    config = get_config()
    print("Starting full pipeline...")
    results = run_full_pipeline(max_cycles=3, timeout_per_cycle=1800)
    print(f"Pipeline finished. Results: {len(results)} cycles.")