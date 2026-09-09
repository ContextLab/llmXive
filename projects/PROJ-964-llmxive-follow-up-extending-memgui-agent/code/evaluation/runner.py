"""
Baseline execution runner for the llmXive project.

This module implements the BaselineRunner class which executes the 
standard MemGUI-SFT agent (CPU-only, 4-bit quantized) on the synthetic benchmark.
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

from evaluation.interfaces import RunnerProtocol
from utils.execution_log import ExecutionLog, TrajectoryExecutionLog
from agents.base_conact import BaseConActAgent
from utils.memory_profiler import profile_memory_latency, log_metrics
from utils.config import set_seed
from agents.model_checker import verify_model, get_project_root, read_plan_md

class BaselineRunner(RunnerProtocol):
    """
    Executes the baseline ConAct agent on trajectories and logs results.
    
    This runner:
    - Uses CPU-only execution with 4-bit quantization
    - Profiles memory and latency for each trajectory
    - Attributes failures to missing context from steps >10 indices prior
    - Outputs logs to data/results/baseline_execution_logs.jsonl
    """
    
    def __init__(self, model_id: str, seed: int = 42):
        """
        Initialize the BaselineRunner.
        
        Args:
            model_id: The model identifier to use (verified by model_checker)
            seed: Random seed for reproducibility
        """
        set_seed(seed)
        self.model_id = model_id
        self.agent = BaseConActAgent(model_id=model_id, cpu_only=True)
        self.logs: List[TrajectoryExecutionLog] = []
        self.project_root = get_project_root()
        
    def run_trajectory(self, trajectory: Dict[str, Any]) -> TrajectoryExecutionLog:
        """
        Execute a single trajectory and return the execution log.
        
        Args:
            trajectory: A trajectory dictionary containing steps and metadata
        
        Returns:
            TrajectoryExecutionLog with step-level results and memory metrics
        """
        trajectory_id = trajectory.get("id", "unknown")
        steps = trajectory.get("steps", [])
        
        # Profile memory and latency for the entire trajectory
        with profile_memory_latency("baseline_agent", {"trajectory_id": trajectory_id}) as results:
            step_results = []
            success_count = 0
            
            for step_idx, step in enumerate(steps):
                step_start = time.perf_counter()
                
                try:
                    # Execute the step using the base ConAct agent
                    result = self.agent.execute_step(step, trajectory_id, step_idx)
                    step_success = result.get("success", False)
                    step_output = result.get("output", "")
                    
                    if step_success:
                        success_count += 1
                    
                    step_latency = (time.perf_counter() - step_start) * 1000
                    
                    step_results.append({
                        "step_index": step_idx,
                        "success": step_success,
                        "output": step_output,
                        "latency_ms": round(step_latency, 2),
                        "memory_snapshot": None  # Detailed memory per step not tracked
                    })
                    
                    # Check for information decay attribution
                    if not step_success and step_idx > 10:
                        # Look back 10+ steps to find the missing context
                        for lookback in range(10, min(step_idx + 1, 20)):
                            prev_step_idx = step_idx - lookback
                            if 0 <= prev_step_idx < len(step_results):
                                prev_step = step_results[prev_step_idx]
                                if not prev_step["success"]:
                                    # Attribute failure to this earlier failure
                                    step_results[-1]["failure_attribution"] = {
                                        "cause_step": prev_step_idx,
                                        "reason": "Information decay from step >10 indices prior",
                                        "missing_context": step.get("required_context", [])
                                    }
                                    break
                    
                except Exception as e:
                    step_results.append({
                        "step_index": step_idx,
                        "success": False,
                        "output": f"Error: {str(e)}",
                        "latency_ms": 0.0,
                        "failure_attribution": {
                            "reason": f"Exception during execution: {str(e)}"
                        }
                    })
            
            # Calculate overall success rate for this trajectory
            overall_success = success_count == len(steps) if steps else False
            
        # Create the trajectory execution log
        log_entry = TrajectoryExecutionLog(
            trajectory_id=trajectory_id,
            agent_type="baseline_conact",
            success=overall_success,
            step_results=step_results,
            peak_memory_mb=results["peak_memory_mb"],
            total_latency_ms=results["latency_ms"],
            step_count=len(steps),
            success_rate=success_count / len(steps) if steps else 0.0
        )
        
        self.logs.append(log_entry)
        return log_entry
    
    def run_benchmark(self, trajectories_path: str) -> List[TrajectoryExecutionLog]:
        """
        Run the baseline agent on all trajectories in the benchmark file.
        
        Args:
            trajectories_path: Path to the JSONL file containing trajectories
        
        Returns:
            List of TrajectoryExecutionLog objects
        """
        trajectories_file = Path(trajectories_path)
        if not trajectories_file.exists():
            raise FileNotFoundError(f"Trajectories file not found: {trajectories_path}")
        
        self.logs = []
        
        with open(trajectories_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    trajectory = json.loads(line)
                    self.run_trajectory(trajectory)
        
        return self.logs
    
    def get_logs(self) -> List[TrajectoryExecutionLog]:
        """
        Get all execution logs.
        
        Returns:
            List of TrajectoryExecutionLog objects
        """
        return self.logs
    
    def save_logs(self, output_path: str) -> None:
        """
        Save all execution logs to a JSONL file.
        
        Args:
            output_path: Path to save the logs
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for log in self.logs:
                f.write(json.dumps(log.to_dict()) + '\n')

def main():
    """Main entry point for running the baseline benchmark."""
    # Verify model before execution
    plan_content = read_plan_md()
    model_id = verify_model(plan_content)
    
    # Initialize runner
    runner = BaselineRunner(model_id=model_id, seed=42)
    
    # Define paths
    project_root = get_project_root()
    trajectories_path = project_root / "data" / "synthetic_benchmark" / "trajectories.jsonl"
    output_path = project_root / "data" / "results" / "baseline_execution_logs.jsonl"
    
    if not trajectories_path.exists():
        print(f"Error: Trajectories file not found at {trajectories_path}")
        sys.exit(1)
    
    print(f"Running baseline agent on {trajectories_path}...")
    
    # Run the benchmark
    logs = runner.run_benchmark(str(trajectories_path))
    
    # Save results
    runner.save_logs(str(output_path))
    
    # Log memory metrics for the entire run
    total_memory = sum(log.peak_memory_mb for log in logs) / len(logs) if logs else 0
    total_latency = sum(log.total_latency_ms for log in logs) / len(logs) if logs else 0
    
    log_metrics(
        peak_memory_mb=total_memory,
        latency_ms=total_latency,
        agent_type="baseline_conact",
        metadata={"trajectory_count": len(logs)}
    )
    
    print(f"Baseline execution complete. Results saved to {output_path}")
    print(f"Total trajectories: {len(logs)}")
    if logs:
        avg_success_rate = sum(log.success_rate for log in logs) / len(logs)
        print(f"Average success rate: {avg_success_rate:.2%}")
        print(f"Average memory usage: {total_memory:.2f} MB")
        print(f"Average latency: {total_latency:.2f} ms")

if __name__ == "__main__":
    main()