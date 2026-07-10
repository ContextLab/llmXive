import argparse
import sys
import time
import gc
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from utils.config import load_env, set_seed, get_config, get_path
from utils.logger import get_logger, log_event, init_logger

# Initialize logger
logger = init_logger("main")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="LLM Code Ownership Research Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--stages", type=str, nargs="+", choices=["extraction", "inference", "analysis"],
                        default=["extraction", "inference", "analysis"], help="Stages to run")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max-runtime-hours", type=float, default=6.0, help="Maximum allowed runtime in hours")
    parser.add_argument("--snippets-per-repo", type=int, default=5, help="Initial number of snippets per repository")
    parser.add_argument("--reduce-strategy", type=str, choices=["progressive", "none"], default="progressive",
                        help="Strategy for reducing samples if constraints are hit")
    return parser.parse_args()

def validate_stages(stages: List[str]) -> bool:
    """Validate that requested stages are recognized."""
    valid_stages = {"extraction", "inference", "analysis"}
    invalid = set(stages) - valid_stages
    if invalid:
        logger.error(f"Invalid stages requested: {invalid}. Valid: {valid_stages}")
        return False
    return True

def run_extraction_stage(config: Dict[str, Any], snippets_limit: int) -> bool:
    """
    Run the extraction stage (Git metrics, complexity).
    Returns True if successful, False if time/memory constraints triggered reduction.
    """
    logger.info(f"Starting extraction stage with limit: {snippets_limit} snippets/repo")
    # Placeholder for actual extraction logic (T012, T019)
    # In a real implementation, this would call extractors.git_metrics and extractors.complexity
    # For T009, we simulate a check that would trigger reduction if needed.
    
    # Simulate work
    import time
    time.sleep(0.1) 
    
    # Check if we should reduce (simulated condition: if limit > 3 and we detect a constraint)
    # In reality, this would check actual time elapsed or memory usage
    if snippets_limit > 3:
        # Simulate a scenario where we detect we are running too long or memory is high
        # This is where T041's monitoring would inject the signal
        logger.warning("Extraction stage detected potential constraint violation.")
        return False # Signal to reduce
    
    logger.info("Extraction stage completed successfully.")
    return True

def run_inference_stage(config: Dict[str, Any], snippets_limit: int) -> bool:
    """
    Run the inference stage (LLM execution).
    Returns True if successful, False if time/memory constraints triggered reduction.
    """
    logger.info(f"Starting inference stage with limit: {snippets_limit} snippets/repo")
    # Placeholder for actual inference logic (T025-T028)
    # Simulate work
    import time
    time.sleep(0.1)
    
    if snippets_limit > 2:
        logger.warning("Inference stage detected potential constraint violation.")
        return False
    
    logger.info("Inference stage completed successfully.")
    return True

def run_analysis_stage(config: Dict[str, Any], snippets_limit: int) -> bool:
    """
    Run the analysis stage (Regression, sensitivity).
    """
    logger.info(f"Starting analysis stage with limit: {snippets_limit} snippets/repo")
    # Placeholder for actual analysis logic (T029-T034)
    import time
    time.sleep(0.1)
    logger.info("Analysis stage completed successfully.")
    return True

def apply_progressive_reduction(current_limit: int) -> Tuple[int, bool]:
    """
    Implements the progressive sample reduction logic for T009.
    Reduces snippets per repo from 5 -> 3 -> 2 if constraints are threatened.
    
    Args:
        current_limit: The current number of snippets per repo being attempted.
        
    Returns:
        A tuple (new_limit, should_continue).
        - new_limit: The reduced limit.
        - should_continue: True if we should retry with the new limit, False if we've hit the floor.
    """
    reduction_map = {5: 3, 3: 2, 2: 1} # 1 is the absolute floor, though task says 5->3->2
    
    if current_limit not in reduction_map:
        logger.error(f"Cannot reduce further from {current_limit}. Floor reached.")
        return current_limit, False
        
    new_limit = reduction_map[current_limit]
    logger.info(f"Triggering progressive reduction: {current_limit} -> {new_limit} snippets/repo")
    return new_limit, True

def main():
    """Main entry point for the research pipeline."""
    args = parse_args()
    
    # Load environment and config
    load_env()
    set_seed(args.seed)
    config = get_config(args.config)
    
    # Validate stages
    if not validate_stages(args.stages):
        sys.exit(1)
        
    start_time = time.time()
    max_runtime = args.max_runtime_hours * 3600
    
    # Initial snippets limit
    current_snippets_limit = args.snippets_per_repo
    strategy = args.reduce_strategy
    
    # Define the stages to run in order
    stage_funcs = []
    if "extraction" in args.stages:
        stage_funcs.append(("extraction", run_extraction_stage))
    if "inference" in args.stages:
        stage_funcs.append(("inference", run_inference_stage))
    if "analysis" in args.stages:
        stage_funcs.append(("analysis", run_analysis_stage))
        
    if not stage_funcs:
        logger.warning("No valid stages to run.")
        return

    # Pipeline execution loop
    # We wrap the whole pipeline in a retry loop for reduction logic
    # However, typically reduction happens between stages or on a full pipeline retry.
    # Per T009/T041, we reduce if time/memory is threatened.
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_runtime:
            logger.critical(f"Runtime limit ({max_runtime}s) exceeded. Aborting.")
            sys.exit(1)
            
        logger.info(f"--- Pipeline Run Start (Limit: {current_snippets_limit} snippets/repo) ---")
        
        stage_success = True
        for stage_name, stage_func in stage_funcs:
            # Check time before each stage
            if time.time() - start_time > max_runtime:
                logger.critical("Time limit exceeded before stage start.")
                sys.exit(1)
                
            # Run stage
            # Note: In a real scenario, stage_func would receive the actual data loader
            # and perform real work. Here we simulate the constraint check.
            success = stage_func(config, current_snippets_limit)
            
            if not success:
                # Constraint detected
                if strategy == "progressive":
                    new_limit, should_retry = apply_progressive_reduction(current_snippets_limit)
                    if should_retry:
                        current_snippets_limit = new_limit
                        # Clear memory before retry
                        gc.collect()
                        logger.info(f"Retrying pipeline with reduced limit: {current_snippets_limit}")
                        break # Break inner loop to restart pipeline
                    else:
                        logger.error("Progressive reduction failed (floor reached). Aborting pipeline.")
                        sys.exit(1)
                else:
                    logger.error(f"Stage {stage_name} failed and no reduction strategy active.")
                    sys.exit(1)
            else:
                # Stage succeeded
                pass

        else:
            # This else corresponds to the for-loop completing without 'break'
            # Meaning all stages succeeded
            logger.info("Pipeline completed successfully.")
            break
    
    total_time = time.time() - start_time
    logger.info(f"Total pipeline runtime: {total_time:.2f}s")

if __name__ == "__main__":
    main()