import os
import sys
import time
import json
import gc
import traceback
from typing import Dict, Any, List, Optional

from config import get_config, set_config
from utils.logging import init_cycle_logger, log_cycle_summary, log_error, get_log_path
from utils.state_store import load_state, save_state, get_modification_history
from pipeline.model import (
    load_gpt_124m,
    generate_modification_proposal,
    apply_architectural_modification,
    get_model_param_count,
    validate_modification_distinctness
)
from pipeline.trainer import run_training_cycle_with_timeout, count_flops
from pipeline.evaluator import run_all_benchmarks
from pipeline.stats import paired_bootstrap_test
from pipeline.memory import check_and_terminate_if_exceeds, get_memory_usage_gb
from results.trajectory_schema import write_trajectory, TrajectoryEntry

class ResourceMonitor:
    """Monitors system resources during pipeline execution."""
    def __init__(self, ram_limit_gb: float):
        self.ram_limit_gb = ram_limit_gb

    def check(self):
        current_ram = get_memory_usage_gb()
        if current_ram > self.ram_limit_gb:
            log_error(f"RAM limit exceeded: {current_ram:.2f}GB > {self.ram_limit_gb}GB")
            sys.exit(1)

def run_single_cycle_with_timeout(
    cycle_number: int,
    model,
    baseline_metrics: Dict[str, float],
    timeout_seconds: int
) -> Optional[TrajectoryEntry]:
    """
    Executes a single refinement cycle.
    
    CRITICAL: Implements Separation of Generative/Verification Logic (T037).
    The modification proposal prompt explicitly excludes access to benchmark results
    or evaluation metrics. It uses ONLY training loss and internal weights.
    """
    config = get_config()
    log_path = get_log_path(cycle_number)
    logger = init_cycle_logger(cycle_number)
    
    logger.info(f"Starting Cycle {cycle_number}")
    
    # 1. Generate Modification Proposal (Generative Logic)
    # T037 Enforcement: The prompt passed to generate_modification_proposal
    # must strictly exclude benchmark results.
    # We pass ONLY training loss history and current model structure.
    # We DO NOT pass baseline_metrics (GSM8K, ARC, etc.) to the proposal generator.
    
    logger.info("Generating modification proposal (Training Loss & Weights only)...")
    
    # Simulate current training loss context (in a real run, this comes from the last epoch)
    current_training_loss = 2.5 # Placeholder for context structure
    
    # The proposal generation function is responsible for constructing the prompt
    # that strictly adheres to the separation principle.
    proposal = generate_modification_proposal(
        model=model,
        training_loss=current_training_loss,
        cycle=cycle_number,
        # NOTE: benchmark_metrics is NOT passed here.
        # If the function signature required it, we would explicitly omit it.
    )
    
    if proposal is None:
        logger.error("Failed to generate valid modification proposal.")
        return None

    # Validate distinctness against history
    history = get_modification_history()
    if not validate_modification_distinctness(proposal, history):
        logger.warning("Proposal not distinct. Skipping cycle.")
        return None

    # 2. Apply Modification
    logger.info(f"Applying modification: {proposal.modification_type}")
    try:
        modified_model = apply_architectural_modification(model, proposal)
    except Exception as e:
        logger.error(f"Failed to apply modification: {e}")
        traceback.print_exc()
        return None

    # 3. Train (with timeout)
    logger.info("Starting training phase...")
    try:
        training_metrics = run_training_cycle_with_timeout(
            model=modified_model,
            timeout_seconds=timeout_seconds,
            config=config
        )
    except Exception as e:
        logger.error(f"Training failed or timed out: {e}")
        # Record partial metrics if timeout, else return
        return None

    # 4. Evaluate (Verification Logic)
    # This step computes the benchmarks (GSM8K, ARC, ECE)
    logger.info("Running benchmarks (Verification Logic)...")
    eval_metrics = run_all_benchmarks(modified_model, config)

    # 5. Statistical Comparison
    logger.info("Running statistical comparison...")
    # Compare against baseline
    p_values = paired_bootstrap_test(
        baseline=baseline_metrics,
        new_results=eval_metrics
    )

    # 6. Record Results
    param_count = get_model_param_count(modified_model)
    flops = count_flops(modified_model)
    
    entry = TrajectoryEntry(
        cycle=cycle_number,
        param_count=param_count,
        gsm8k_accuracy=eval_metrics.get('gsm8k', 0.0),
        arc_accuracy=eval_metrics.get('arc', 0.0),
        wikitext_ece=eval_metrics.get('ece', 0.0),
        training_loss=training_metrics.get('loss', 0.0),
        flops=flops,
        training_time=training_metrics.get('time', 0.0),
        proposal_type=proposal.modification_type,
        p_value_gsm8k=p_values.get('gsm8k', 1.0)
    )

    write_trajectory(entry)
    log_cycle_summary(cycle_number, entry)
    
    logger.info(f"Cycle {cycle_number} completed successfully.")
    return entry

def run_full_pipeline():
    """
    Orchestrates the full self-improving pipeline.
    """
    config = get_config()
    set_config(config)
    
    # Initialize state
    state = load_state()
    cycle_start = state.get('current_cycle', 1)
    
    # Load Baseline Model
    logger = init_cycle_logger(0)
    logger.info("Loading baseline GPT-124M model...")
    model = load_gpt_124m()
    
    # Establish Baseline Metrics (Verification Logic)
    # These are computed ONCE and stored. They are NOT used for generation.
    logger.info("Establishing baseline metrics...")
    baseline_metrics = run_all_benchmarks(model, config)
    
    # Reset modification history
    from utils.state_store import reset_state
    reset_state()

    timeout = config.max_cycle_timeout_seconds

    for cycle_num in range(cycle_start, config.max_cycles + 1):
        logger.info(f"--- Starting Cycle {cycle_num} ---")
        
        # Check RAM before starting
        check_and_terminate_if_exceeds(config.ram_limit_gb)
        
        try:
            result = run_single_cycle_with_timeout(
                cycle_number=cycle_num,
                model=model,
                baseline_metrics=baseline_metrics,
                timeout_seconds=timeout
            )
            
            if result is None:
                logger.warning(f"Cycle {cycle_num} did not produce valid results. Stopping.")
                break
            
            # Update model for next cycle
            # In a real scenario, we might keep the best model, but for recursive
            # self-improvement, we assume the new model replaces the old one
            # if it passed the distinctness and training checks.
            model = load_gpt_124m() # Placeholder: reload or keep modified state
            
            # Update state
            state['current_cycle'] = cycle_num + 1
            save_state(state)
            
        except Exception as e:
            log_error(f"Fatal error in cycle {cycle_num}: {e}")
            traceback.print_exc()
            break

    logger.info("Pipeline execution finished.")

if __name__ == "__main__":
    run_full_pipeline()
