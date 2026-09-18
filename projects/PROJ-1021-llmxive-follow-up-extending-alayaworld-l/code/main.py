import json
import os
import sys
import time
import random
from datetime import datetime, timezone
from pathlib import Path

# Import from existing API surface
from utils.seed_manager import set_seed, load_seed_config
from utils.resource_logger import ResourceMonitor, log_resource_usage
from symbolic_engine import SymbolicEngine
from hybrid_generator import HybridGenerator
from hybrid_controller import HybridController
from metrics import calculate_drift_score, DriftMetrics

# Constants
NUM_SEEDS = 10
SEQUENCES_PER_SEED = 10
TOTAL_ENTRIES = NUM_SEEDS * SEQUENCES_PER_SEED
LOGS_DIR = Path("data/logs")
OUTPUT_FILE = Path("data/hybrid_scores.json")
CV_VALIDATION_FILE = Path("data/cv_validation_report.json")

def check_cv_validation() -> bool:
    """Check if CV validation passed before proceeding."""
    if not CV_VALIDATION_FILE.exists():
        print(f"ERROR: CV validation report not found at {CV_VALIDATION_FILE}")
        return False
    
    with open(CV_VALIDATION_FILE, 'r') as f:
        report = json.load(f)
    
    if report.get("status") != "PASS":
        print(f"ERROR: CV validation failed with status: {report.get('status')}")
        return False
    
    return True

def run_sequence(seed: int, seq_id: int, generator: HybridGenerator, 
                 symbolic_engine: SymbolicEngine, controller: HybridController,
                 monitor: ResourceMonitor) -> dict:
    """Run a single sequence with hybrid correction enabled."""
    set_seed(seed)
    
    start_time = time.time()
    monitor.start_monitoring()
    
    try:
        # Generate sequence with hybrid correction
        sequence_data = generator.generate_sequence(
            seed=seed,
            seq_id=seq_id,
            controller=controller
        )
        
        # Run symbolic engine on the same actions
        symbolic_log = symbolic_engine.process_actions(
            sequence_data.get("actions", [])
        )
        
        # Calculate drift score
        drift_score = calculate_drift_score(
            symbolic_log=symbolic_log,
            visual_log=sequence_data.get("visual_states", [])
        )
        
        end_time = time.time()
        wall_clock = end_time - start_time
        
        # Log resource usage
        resource_log = log_resource_usage(
            monitor=monitor,
            seq_id=seq_id,
            wall_clock_seconds=wall_clock
        )
        
        # Save real-time resource log
        log_file = LOGS_DIR / f"realtime_seq_{seq_id}.json"
        with open(log_file, 'w') as f:
            json.dump(resource_log, f, indent=2)
        
        return {
            "seed": seed,
            "seq_id": seq_id,
            "score": drift_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wall_clock_seconds": wall_clock
        }
        
    except Exception as e:
        print(f"ERROR: Sequence {seq_id} failed: {str(e)}")
        raise
    finally:
        monitor.stop_monitoring()

def main():
    """Orchestrate Hybrid Run for 10 seeds, 10 sequences each (100 total)."""
    print("Starting Hybrid Run orchestration...")
    
    # Check CV validation first
    if not check_cv_validation():
        print("Aborting: CV validation not passed")
        sys.exit(1)
    
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    symbolic_engine = SymbolicEngine()
    controller = HybridController()
    generator = HybridGenerator()
    
    # Initialize resource monitor
    monitor = ResourceMonitor()
    
    # Load seed configuration if available
    seed_config = load_seed_config()
    seeds = seed_config.get("seeds", list(range(NUM_SEEDS)))
    
    # Run sequences
    all_scores = []
    total_start = time.time()
    
    print(f"Running {NUM_SEEDS} seeds x {SEQUENCES_PER_SEED} sequences = {TOTAL_ENTRIES} total entries")
    
    for seed in seeds:
        print(f"Processing seed {seed}...")
        for seq_idx in range(SEQUENCES_PER_SEED):
            seq_id = f"{seed}_{seq_idx}"
            print(f"  Running sequence {seq_id}...")
            
            result = run_sequence(
                seed=seed,
                seq_id=seq_id,
                generator=generator,
                symbolic_engine=symbolic_engine,
                controller=controller,
                monitor=monitor
            )
            
            all_scores.append({
                "seed": result["seed"],
                "score": result["score"],
                "timestamp": result["timestamp"]
            })
            
            # Verify we're on track
            if len(all_scores) % 10 == 0:
                print(f"    Completed {len(all_scores)}/{TOTAL_ENTRIES} entries")
    
    total_time = time.time() - total_start
    
    # Validate total entries
    if len(all_scores) != TOTAL_ENTRIES:
        print(f"ERROR: Expected {TOTAL_ENTRIES} entries, got {len(all_scores)}")
        sys.exit(1)
    
    # Write output
    output_data = {
        "scores": all_scores,
        "total_entries": len(all_scores),
        "total_time_seconds": total_time,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Hybrid Run completed successfully!")
    print(f"Output written to: {OUTPUT_FILE}")
    print(f"Total entries: {len(all_scores)}")
    print(f"Total time: {total_time:.2f} seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())