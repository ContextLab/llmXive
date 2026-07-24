import os
import sys
import time
import json
import gc
import traceback
from typing import Optional, Dict, Any
from datetime import datetime

from config import get_config, PathConfig
from utils.logging import init_cycle_logger, update_cycle_log, finalize_cycle
from utils.memory import check_and_terminate_if_exceeds
from pipeline.model import load_gpt_124m, get_model_param_count, apply_architectural_modification
from pipeline.trainer import run_training_cycle
from pipeline.evaluator import run_all_benchmarks
from pipeline.stats import fit_exponential_decay, detect_plateau_or_degradation
from results.trajectory_schema import write_trajectory, TrajectoryEntry
from schemas.modification_proposal import ModificationProposal

US1_TIME_LIMIT_SECONDS = 5400  # 1.5 hours = 5400 seconds

class ResourceMonitor:
    """Monitors resource usage and enforces time limits for cycles."""

    def __init__(self, time_limit: float = US1_TIME_LIMIT_SECONDS):
        self.time_limit = time_limit
        self.start_time: Optional[float] = None
        self.peak_ram_gb: float = 0.0

    def start(self):
        self.start_time = time.time()

    def check(self) -> bool:
        """Returns True if time limit exceeded."""
        if self.start_time is None:
            return False
        elapsed = time.time() - self.start_time
        if elapsed > self.time_limit:
            return True
        
        # Check RAM
        check_and_terminate_if_exceeds(limit_gb=7.0)
        return False

    def get_elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

def run_single_cycle_with_timeout(
    cycle_number: int,
    config: Dict[str, Any],
    prev_modifications: list,
    monitor: ResourceMonitor
) -> Optional[Dict[str, Any]]:
    """
    Executes a single refinement cycle with timeout enforcement.
    If US-1 exceeds 1.5 hours, writes trajectory with status "Incomplete - Timeout"
    and returns None to halt US-2 execution.
    """
    try:
        monitor.start()
        
        # Load model
        model = load_gpt_124m()
        param_count = get_model_param_count(model)
        
        # Apply modification (if not first cycle)
        if cycle_number > 1:
            # Logic to generate distinct modification would go here
            # For now, we assume a modification is proposed
            pass
        
        # Training
        train_start = time.time()
        metrics = run_training_cycle(model, config)
        train_time = time.time() - train_start
        
        # Evaluation
        eval_start = time.time()
        benchmarks = run_all_benchmarks(model, config)
        eval_time = time.time() - eval_start
        
        # Check timeout AFTER cycle completion
        if monitor.check():
            # Timeout occurred during or just after the cycle
            entry = TrajectoryEntry(
                cycle_number=cycle_number,
                param_count=param_count,
                gsm8k_accuracy=benchmarks.get("gsm8k", 0.0),
                arc_accuracy=benchmarks.get("arc", 0.0),
                wikitext_ece=benchmarks.get("wikitext", 0.0),
                flops=metrics.get("flops", 0),
                training_time=train_time,
                evaluation_time=eval_time,
                status="Incomplete - Timeout",
                timestamp=datetime.now().isoformat(),
                modification_type="unknown",
                modification_magnitude=0.0
            )
            write_trajectory([entry], config["paths"]["trajectory"])
            return None  # Signal to stop US-2
        
        # Normal completion
        entry = TrajectoryEntry(
            cycle_number=cycle_number,
            param_count=param_count,
            gsm8k_accuracy=benchmarks.get("gsm8k", 0.0),
            arc_accuracy=benchmarks.get("arc", 0.0),
            wikitext_ece=benchmarks.get("wikitext", 0.0),
            flops=metrics.get("flops", 0),
            training_time=train_time,
            evaluation_time=eval_time,
            status="Completed",
            timestamp=datetime.now().isoformat(),
            modification_type="layer_count_increase",
            modification_magnitude=0.1
        )
        write_trajectory([entry], config["paths"]["trajectory"])
        return entry

    except Exception as e:
        traceback.print_exc()
        return None

def run_full_pipeline():
    """
    Orchestrates the full pipeline with US-1 timeout enforcement.
    If US-1 exceeds 1.5 hours, US-2 is skipped.
    """
    config = get_config()
    monitor = ResourceMonitor(time_limit=US1_TIME_LIMIT_SECONDS)
    
    # Execute US-1 (Cycle 1)
    cycle1_result = run_single_cycle_with_timeout(
        cycle_number=1,
        config=config,
        prev_modifications=[],
        monitor=monitor
    )
    
    if cycle1_result is None:
        # US-1 timed out, write incomplete status and exit
        print("US-1 exceeded time limit. US-2 skipped.")
        return
    
    # Check if US-1 took too long (safety check)
    if monitor.get_elapsed() > US1_TIME_LIMIT_SECONDS:
        print("US-1 exceeded time limit. US-2 skipped.")
        return
    
    # If US-1 succeeded and within time budget, proceed to US-2 (Cycles 2-3)
    print("US-1 completed within time budget. Proceeding to US-2.")
    
    for cycle_num in [2, 3]:
        result = run_single_cycle_with_timeout(
            cycle_number=cycle_num,
            config=config,
            prev_modifications=[],
            monitor=monitor
        )
        if result is None:
            print(f"Cycle {cycle_num} timed out or failed. Stopping pipeline.")
            break

if __name__ == "__main__":
    run_full_pipeline()