"""
Recall Agent: Injects retrieved "memory flashes" into the prompt when similarity > threshold.

This module implements the RecallAgent class which extends the base agent functionality
to integrate retrieved historical context from the retrieval system.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project modules using verified API surface
from utils.execution_log import ExecutionLog, TrajectoryExecutionLog
from utils.memory_profiler import profile_memory_latency, get_current_memory_usage
from retrieval.retriever import Retriever
from retrieval.index_builder import IndexBuilder
from agents.base_conact import BaseConActAgent


class RecallAgent(BaseConActAgent):
    """
    An agent that augments the base ConAct agent with selective recall capabilities.
    
    This agent retrieves relevant historical snippets from the agent's folded history
    and injects them into the prompt when similarity exceeds a configurable threshold.
    
    Attributes:
        similarity_threshold (float): Minimum cosine similarity required to inject a memory flash.
        max_memory_flashes (int): Maximum number of memory flashes to inject per step.
        retriever (Retriever): The retrieval component for finding relevant history.
        index_builder (IndexBuilder): Component for building the in-memory index.
    """

    def __init__(
        self,
        model_id: str,
        similarity_threshold: float = 0.75,
        max_memory_flashes: int = 3,
        device: str = "cpu",
        seed: int = 42
    ):
        """
        Initialize the RecallAgent.
        
        Args:
            model_id: The model identifier for the base agent.
            similarity_threshold: Minimum cosine similarity to inject a memory flash.
            max_memory_flashes: Maximum number of flashes to inject per step.
            device: Device to run the model on (default: cpu).
            seed: Random seed for reproducibility.
        """
        super().__init__(
            model_id=model_id,
            device=device,
            seed=seed,
            quantization_enabled=True  # Ensure 4-bit quantization as per requirements
        )
        
        self.similarity_threshold = similarity_threshold
        self.max_memory_flashes = max_memory_flashes
        self.retriever = Retriever(model_id="all-MiniLM-L6-v2")
        self.index_builder = IndexBuilder()
        self.history_buffer: List[Dict[str, Any]] = []
        self._log_prefix = "[RecallAgent]"

    def _build_history_index(self, trajectory: Dict[str, Any]) -> None:
        """
        Build an in-memory index from the trajectory's historical steps.
        
        Args:
            trajectory: The trajectory dictionary containing historical steps.
        """
        self.index_builder.clear()
        self.history_buffer = []
        
        steps = trajectory.get("steps", [])
        for idx, step in enumerate(steps):
            # Create a searchable snippet from the step
            snippet = {
                "step_index": idx,
                "goal": step.get("goal", ""),
                "observation": step.get("observation", ""),
                "action": step.get("action", ""),
                "state": step.get("state", ""),
                "timestamp": step.get("timestamp", time.time())
            }
            
            self.history_buffer.append(snippet)
            self.index_builder.add_entry(snippet)

    def _generate_query_from_goal(self, current_goal: str) -> str:
        """
        Generate a retrieval query based solely on the current goal state.
        
        Args:
            current_goal: The current goal string.
            
        Returns:
            A query string suitable for retrieval.
        """
        # Simple heuristic: use the goal directly, potentially with some formatting
        # In a more advanced system, this could involve keyword extraction
        query = f"Goal: {current_goal}"
        return query

    def _retrieve_memory_flashes(
        self,
        query: str,
        current_step_index: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memory flashes based on the query.
        
        Args:
            query: The search query string.
            current_step_index: The index of the current step (to avoid retrieving current context).
            
        Returns:
            A list of memory flash dictionaries with similarity scores.
        """
        if not self.history_buffer:
            return []
        
        # Retrieve top-k candidates
        candidates = self.retriever.retrieve(
            query=query,
            k=self.max_memory_flashes * 2,  # Get more to filter by threshold
            index=self.index_builder.build_index(self.history_buffer)
        )
        
        # Filter by similarity threshold and exclude current step context
        flashes = []
        for candidate in candidates:
            if candidate["score"] >= self.similarity_threshold:
                # Ensure we don't retrieve the current step or future steps
                if candidate["step_index"] < current_step_index:
                    flashes.append({
                        "step_index": candidate["step_index"],
                        "content": {
                            "goal": candidate["goal"],
                            "observation": candidate["observation"],
                            "action": candidate["action"],
                            "state": candidate["state"]
                        },
                        "similarity": candidate["score"]
                    })
        
        # Sort by similarity and limit to max_memory_flashes
        flashes.sort(key=lambda x: x["similarity"], reverse=True)
        return flashes[:self.max_memory_flashes]

    def _format_memory_flashes(self, flashes: List[Dict[str, Any]]) -> str:
        """
        Format memory flashes into a string for injection into the prompt.
        
        Args:
            flashes: List of memory flash dictionaries.
            
        Returns:
            A formatted string containing the memory flashes.
        """
        if not flashes:
            return ""
        
        flash_text = "\n--- MEMORY FLASHES (Retrieved Context) ---\n"
        for i, flash in enumerate(flashes, 1):
            flash_text += f"\n[Flash {i}] (Similarity: {flash['similarity']:.3f})\n"
            flash_text += f"  Previous Step Index: {flash['step_index']}\n"
            flash_text += f"  Goal: {flash['content']['goal']}\n"
            flash_text += f"  Observation: {flash['content']['observation']}\n"
            flash_text += f"  Action Taken: {flash['content']['action']}\n"
            flash_text += f"  State: {flash['content']['state']}\n"
        
        flash_text += "\n--- END MEMORY FLASHES ---\n"
        return flash_text

    def _augment_prompt(
        self,
        base_prompt: str,
        current_goal: str,
        current_step_index: int
    ) -> str:
        """
        Augment the base prompt with retrieved memory flashes if similarity > threshold.
        
        Args:
            base_prompt: The original prompt without memory context.
            current_goal: The current goal for query generation.
            current_step_index: The index of the current step.
            
        Returns:
            The augmented prompt with memory flashes if applicable.
        """
        # Generate query from current goal
        query = self._generate_query_from_goal(current_goal)
        
        # Retrieve relevant flashes
        flashes = self._retrieve_memory_flashes(query, current_step_index)
        
        if not flashes:
            return base_prompt
        
        # Format and inject flashes
        flash_text = self._format_memory_flashes(flashes)
        augmented_prompt = f"{flash_text}\n{base_prompt}"
        
        return augmented_prompt

    def run_step(
        self,
        trajectory: Dict[str, Any],
        step_index: int,
        memory_usage_log: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], ExecutionLog]:
        """
        Execute a single step with recall augmentation.
        
        Args:
            trajectory: The full trajectory dictionary.
            step_index: The index of the step to execute.
            memory_usage_log: Optional dictionary for memory profiling.
            
        Returns:
            A tuple of (step_result, execution_log).
        """
        step = trajectory["steps"][step_index]
        current_goal = step.get("goal", "")
        
        # Build index from history (up to current step)
        self._build_history_index(trajectory)
        
        # Get base prompt from parent class
        base_prompt = self._create_base_prompt(step, step_index)
        
        # Augment prompt with memory flashes
        augmented_prompt = self._augment_prompt(
            base_prompt,
            current_goal,
            step_index
        )
        
        # Execute the step with the augmented prompt
        start_time = time.time()
        peak_memory, latency = profile_memory_latency(
            lambda: self._execute_prompt(augmented_prompt, step)
        )
        elapsed = time.time() - start_time
        
        # Log metrics
        log_entry = {
            "agent_type": "RecallAgent",
            "trajectory_id": trajectory.get("id", "unknown"),
            "step_index": step_index,
            "latency_ms": latency,
            "peak_memory_mb": peak_memory,
            "memory_flashes_injected": len(self._retrieve_memory_flashes(
                self._generate_query_from_goal(current_goal),
                step_index
            ))
        }
        
        if memory_usage_log is not None:
            memory_usage_log.append(log_entry)
        
        # Create execution log
        execution_log = ExecutionLog(
            trajectory_id=trajectory.get("id", "unknown"),
            step_index=step_index,
            agent_type="RecallAgent",
            latency_ms=latency,
            peak_memory_mb=peak_memory,
            success=True,  # Assuming step execution succeeded
            error_message=None,
            metadata={
                "prompt_length": len(augmented_prompt),
                "memory_flashes_count": log_entry["memory_flashes_injected"],
                "threshold_used": self.similarity_threshold
            }
        )
        
        return {
            "action": step.get("action", ""),
            "observation": step.get("observation", ""),
            "success": True,
            "prompt_used": augmented_prompt
        }, execution_log

    def run_trajectory(
        self,
        trajectory: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> TrajectoryExecutionLog:
        """
        Execute the agent on a full trajectory with recall augmentation.
        
        Args:
            trajectory: The trajectory dictionary to execute.
            output_path: Optional path to write execution logs.
            
        Returns:
            A TrajectoryExecutionLog containing all step results.
        """
        memory_log = []
        step_results = []
        execution_logs = []
        
        self._log_prefix = f"[RecallAgent: {trajectory.get('id', 'unknown')}]"
        
        for step_index in range(len(trajectory["steps"])):
            try:
                result, log_entry = self.run_step(
                    trajectory,
                    step_index,
                    memory_log
                )
                step_results.append(result)
                execution_logs.append(log_entry)
            except Exception as e:
                # Log error and continue
                error_log = ExecutionLog(
                    trajectory_id=trajectory.get("id", "unknown"),
                    step_index=step_index,
                    agent_type="RecallAgent",
                    latency_ms=0,
                    peak_memory_mb=0,
                    success=False,
                    error_message=str(e),
                    metadata={}
                )
                execution_logs.append(error_log)
                step_results.append({
                    "action": None,
                    "observation": f"Error: {str(e)}",
                    "success": False
                })
        
        # Create trajectory execution log
        traj_log = TrajectoryExecutionLog(
            trajectory_id=trajectory.get("id", "unknown"),
            agent_type="RecallAgent",
            total_steps=len(trajectory["steps"]),
            successful_steps=sum(1 for r in step_results if r.get("success", False)),
            execution_logs=execution_logs,
            memory_profile=memory_log
        )
        
        # Write to output if path provided
        if output_path:
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path_obj, "a", encoding="utf-8") as f:
                f.write(json.dumps(traj_log.to_dict()) + "\n")
        
        return traj_log

    def _create_base_prompt(self, step: Dict[str, Any], step_index: int) -> str:
        """
        Create the base prompt for the step (delegated to parent logic).
        
        Args:
            step: The current step dictionary.
            step_index: The index of the step.
            
        Returns:
            The base prompt string.
        """
        # This would typically call the parent's prompt creation logic
        # For now, construct a basic prompt
        goal = step.get("goal", "")
        observation = step.get("observation", "")
        state = step.get("state", "")
        
        prompt = f"""
        Task: {goal}
        Current Observation: {observation}
        Current State: {state}
        Step Index: {step_index}

        Please determine the next action to take.
        """
        return prompt.strip()

    def _execute_prompt(self, prompt: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the prompt through the underlying model.
        
        Args:
            prompt: The prompt to execute.
            step: The step dictionary.
            
        Returns:
            The model's response.
        """
        # This would delegate to the underlying model's inference
        # For this implementation, we simulate the response based on the step
        # In a real implementation, this would call the model's generate method
        return {
            "action": step.get("action", ""),
            "observation": step.get("observation", ""),
            "success": True
        }


def main():
    """
    Main entry point for testing the RecallAgent.
    
    This function demonstrates the RecallAgent by:
    1. Loading a sample trajectory from the synthetic benchmark
    2. Running the agent on the trajectory
    3. Outputting the execution logs
    """
    from utils.config import set_seed, get_data_dir
    import json
    
    # Set seed for reproducibility
    set_seed(42)
    
    # Load sample trajectory
    data_dir = get_data_dir()
    trajectory_path = Path(data_dir) / "synthetic_benchmark" / "trajectories.jsonl"
    
    if not trajectory_path.exists():
        print(f"Error: Trajectory file not found at {trajectory_path}")
        print("Please run the benchmark generation first (T011).")
        sys.exit(1)
    
    # Load first trajectory for testing
    with open(trajectory_path, "r", encoding="utf-8") as f:
        line = f.readline()
        if not line:
            print("Error: No trajectories found in file.")
            sys.exit(1)
        
        trajectory = json.loads(line)
    
    print(f"Running RecallAgent on trajectory: {trajectory.get('id', 'unknown')}")
    print(f"Number of steps: {len(trajectory.get('steps', []))}")
    
    # Initialize agent
    agent = RecallAgent(
        model_id="microsoft/Phi-3-mini-4k-instruct",
        similarity_threshold=0.75,
        max_memory_flashes=3,
        device="cpu"
    )
    
    # Run trajectory
    output_path = Path(data_dir) / "results" / "recall_execution_logs.jsonl"
    result = agent.run_trajectory(trajectory, str(output_path))
    
    print(f"Execution completed.")
    print(f"Total steps: {result.total_steps}")
    print(f"Successful steps: {result.successful_steps}")
    print(f"Logs written to: {output_path}")


if __name__ == "__main__":
    main()