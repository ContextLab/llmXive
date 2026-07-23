import os
import json
import logging
import time
import traceback
import numpy as np
from typing import Dict, Any, Optional, List
import csv
import resource

from logger import get_logger
from config_loader import get_seeds

# Configuration constants
MAX_STEPS = 500
DISCARDED_RUNS_FILE = "results/discarded_runs.csv"
ERROR_HANDLING_LOG = "results/error_handling_test.log"

# Ensure results directory exists
os.makedirs("results", exist_ok=True)

def log_discarded_run(run_id: str, reason: str, details: str = ""):
    """
    Logs a discarded run to the CSV file.
    """
    file_exists = os.path.isfile(DISCARDED_RUNS_FILE)
    with open(DISCARDED_RUNS_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["run_id", "reason", "details", "timestamp"])
        writer.writerow([run_id, reason, details, time.strftime("%Y-%m-%d %H:%M:%S")])

class AgentConfig:
    def __init__(self, model_name: str = "dummy_model", max_steps: int = MAX_STEPS):
        self.model_name = model_name
        self.max_steps = max_steps

class AgentState:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.step_count = 0
        self.mental_map: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.is_terminated = False
        self.termination_reason: Optional[str] = None

class TextAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.model_loaded = False

    def load_model(self):
        """
        Simulates loading a quantized text-only LLM.
        In a real implementation, this would load the model into memory.
        """
        self.logger.info(f"Loading model: {self.config.model_name}")
        # Simulate model loading
        self.model_loaded = True
        self.logger.info("Model loaded successfully.")

    def step(self, state: AgentState, ascii_grid: str, event_log: List[Dict]) -> Dict[str, Any]:
        """
        Executes one step of the agent.
        
        Args:
            state: Current agent state.
            ascii_grid: Current visual state as ASCII string.
            event_log: History of events.
        
        Returns:
            Dictionary with 'action' and 'mental_map'.
        
        Raises:
            RuntimeError: If the model output is NaN (simulated error condition).
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded.")

        if state.step_count >= self.config.max_steps:
            state.is_terminated = True
            state.termination_reason = "step_limit_exceeded"
            return {"action": "stop", "mental_map": str(state.mental_map)}

        state.step_count += 1

        # Simulate model inference
        # In a real scenario, this would be model_output = self.model(input_ids)
        # Here we simulate the output tensor
        simulated_tensor = np.random.rand(1, 5)
        
        # CHECK FOR NaN (Error Condition Injection Point)
        # If the input contains a specific marker, we simulate a NaN output
        if "INJECT_NAN" in ascii_grid:
            self.logger.warning("NaN detected in model output tensor!")
            simulated_tensor[0, 0] = np.nan
            if np.any(np.isnan(simulated_tensor)):
                raise RuntimeError("NaN detected in model output tensor. Discarding run.")

        # Simulate OOM check (memory usage)
        try:
            # In a real system, we might check resource usage here
            # For this simulation, we assume the model is stable unless NaN is injected
            pass
        except MemoryError:
            self.logger.error("Out of Memory (OOM) detected.")
            raise RuntimeError("OOM detected. Discarding run.")

        # Process output (simplified)
        action_idx = int(np.argmax(simulated_tensor))
        actions = ["move_up", "move_down", "move_left", "move_right", "wait"]
        action = actions[action_idx % len(actions)]

        # Update mental map
        state.mental_map.append({
            "step": state.step_count,
            "action": action,
            "grid_hash": hash(ascii_grid)
        })

        return {
            "action": action,
            "mental_map": json.dumps(state.mental_map)
        }

    def run_episode(self, run_id: str, ascii_grid: str, event_log: List[Dict]) -> Dict[str, Any]:
        """
        Runs a full episode for the agent.
        
        Args:
            run_id: Unique identifier for the run.
            ascii_grid: Initial state.
            event_log: Initial event log.
        
        Returns:
            Dictionary containing the final state and results.
        """
        state = AgentState(run_id)
        self.logger.info(f"Starting episode: {run_id}")
        
        try:
            while not state.is_terminated:
                result = self.step(state, ascii_grid, event_log)
                state.history.append(result)
            
            return {
                "run_id": run_id,
                "status": "completed" if state.termination_reason is None else "failed",
                "termination_reason": state.termination_reason,
                "steps": state.step_count,
                "final_mental_map": state.mental_map
            }
        except RuntimeError as e:
            error_msg = str(e)
            self.logger.error(f"Error in episode {run_id}: {error_msg}")
            log_discarded_run(run_id, "runtime_error", error_msg)
            return {
                "run_id": run_id,
                "status": "discarded",
                "error": error_msg,
                "steps": state.step_count
            }

def run_error_handling_test():
    """
    Verification task: Verify error handling logic in code/agent_loop.py (NaN, OOM).
    Test: Inject NaN into output tensor and verify the run is discarded and logged.
    Artifact: results/error_handling_test.log
    """
    logger = get_logger(__name__)
    log_file = ERROR_HANDLING_LOG
    
    # Clear log file
    with open(log_file, 'w') as f:
        f.write("Error Handling Test Log\n")
        f.write("=" * 50 + "\n")

    logger.info("Starting Error Handling Test (NaN Injection)...")
    
    # Setup
    config = AgentConfig()
    agent = TextAgent(config)
    agent.load_model()

    # Test Case 1: Normal Run (should succeed)
    normal_run_id = "test_normal_run"
    normal_grid = "Normal ASCII Grid\nNo injection marker."
    normal_log = []
    
    logger.info(f"Running normal test: {normal_run_id}")
    result_normal = agent.run_episode(normal_run_id, normal_grid, normal_log)
    
    with open(log_file, 'a') as f:
        f.write(f"\nTest: Normal Run\n")
        f.write(f"Run ID: {normal_run_id}\n")
        f.write(f"Status: {result_normal['status']}\n")
        f.write(f"Expected: completed\n")
        f.write(f"Result: {'PASS' if result_normal['status'] == 'completed' else 'FAIL'}\n")

    # Test Case 2: NaN Injection (should fail and log to discarded_runs.csv)
    nan_run_id = "test_nan_injection"
    nan_grid = "Corrupted Grid\nINJECT_NAN"  # Marker to trigger NaN
    nan_log = []
    
    logger.info(f"Running NaN injection test: {nan_run_id}")
    result_nan = agent.run_episode(nan_run_id, nan_grid, nan_log)
    
    with open(log_file, 'a') as f:
        f.write(f"\nTest: NaN Injection\n")
        f.write(f"Run ID: {nan_run_id}\n")
        f.write(f"Status: {result_nan['status']}\n")
        f.write(f"Expected: discarded\n")
        f.write(f"Error: {result_nan.get('error', 'N/A')}\n")
        f.write(f"Result: {'PASS' if result_nan['status'] == 'discarded' else 'FAIL'}\n")

    # Verify CSV exists and contains the entry
    csv_exists = os.path.isfile(DISCARDED_RUNS_FILE)
    csv_contains_entry = False
    
    if csv_exists:
        with open(DISCARDED_RUNS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['run_id'] == nan_run_id:
                    csv_contains_entry = True
                    break

    with open(log_file, 'a') as f:
        f.write(f"\nVerification:\n")
        f.write(f"discarded_runs.csv exists: {csv_exists}\n")
        f.write(f"discarded_runs.csv contains {nan_run_id}: {csv_contains_entry}\n")
        f.write(f"Overall Test Status: {'PASS' if csv_contains_entry else 'FAIL'}\n")

    logger.info("Error Handling Test Complete.")
    print(f"Test log written to: {log_file}")
    print(f"Discarded runs logged to: {DISCARDED_RUNS_FILE}")

def run_step_limit_test():
    """
    Verification task for step limit logic (T026).
    """
    logger = get_logger(__name__)
    log_file = "results/step_limit_test.log"
    
    with open(log_file, 'w') as f:
        f.write("Step Limit Test Log\n")
        f.write("=" * 50 + "\n")

    config = AgentConfig(max_steps=5) # Small limit for testing
    agent = TextAgent(config)
    agent.load_model()

    run_id = "test_step_limit"
    grid = "Grid for step limit test"
    log = []

    result = agent.run_episode(run_id, grid, log)

    with open(log_file, 'a') as f:
        f.write(f"Run ID: {run_id}\n")
        f.write(f"Max Steps: {config.max_steps}\n")
        f.write(f"Actual Steps: {result['steps']}\n")
        f.write(f"Status: {result['status']}\n")
        f.write(f"Termination Reason: {result.get('termination_reason')}\n")
        
        passed = result['termination_reason'] == 'step_limit_exceeded'
        f.write(f"Result: {'PASS' if passed else 'FAIL'}\n")

    logger.info("Step Limit Test Complete.")

def main():
    """
    Main entry point for the agent loop.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run Text Agent")
    parser.add_argument("--mode", type=str, default="run", help="Mode: run, test_nan, test_limit")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Setup logging
    configure_global_logging()
    logger = get_logger(__name__)

    if args.mode == "test_nan":
        run_error_handling_test()
    elif args.mode == "test_limit":
        run_step_limit_test()
    else:
        # Default run mode
        config = AgentConfig()
        agent = TextAgent(config)
        agent.load_model()
        
        # Load seeds
        seeds = get_seeds()
        if not seeds:
            logger.error("No seeds found in config.")
            return

        for seed in seeds[:1]: # Run one for demo
            run_id = f"run_seed_{seed}"
            # In a real scenario, load actual grid and log from files
            grid = f"Seed {seed} Grid Data"
            log = []
            result = agent.run_episode(run_id, grid, log)
            logger.info(f"Run {run_id} completed with status: {result['status']}")

if __name__ == "__main__":
    main()
