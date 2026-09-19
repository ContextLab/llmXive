"""
Augmented Agent Implementation.
Executes tasks with access to failure signatures for recovery.
"""
import os
import re
import time
import json
from typing import Any, Dict, List, Optional, Tuple
from agents.base import BaseAgent
from utils.config import get_path, get_hyperparameter

class AugmentedAgent(BaseAgent):
    """
    Augmented agent that checks for known failure signatures post-invocation
    and triggers recovery strategies.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        super().__init__()
        self.model_name = model_name or get_hyperparameter("model")
        self.max_tokens = get_hyperparameter("max_tokens")
        self.temperature = get_hyperparameter("temperature")
        self.seed = get_hyperparameter("seed")
        
        # Path to failure signatures index
        self.signatures_path = get_path("failure_signatures")
        
        # Ensure data directories exist
        get_path("data_logs").mkdir(parents=True, exist_ok=True)
        get_path("data_derived").mkdir(parents=True, exist_ok=True)
        
        # Log file path
        self.log_path = get_path("augmented_log")
        
        # Load signatures
        self.signatures = self._load_signatures()

    def _load_signatures(self) -> Dict[str, Any]:
        """
        Loads the failure signatures index from the configured path.
        Returns an empty dict if the file is missing (failures will not be detected).
        """
        if not self.signatures_path.exists():
            return {}
        
        with open(self.signatures_path, 'r') as f:
            return json.load(f)

    def _check_signatures(self, tool_output: str) -> Optional[str]:
        """
        Checks if the tool output matches any known failure signature.
        
        Matching Logic:
        1. If the pattern contains wildcards ('*' or '?'), convert to regex and search.
        2. Otherwise, enforce 100% exact string match (substring match is NOT sufficient).
        
        Args:
            tool_output: The output string from a tool invocation.
            
        Returns:
            The matched signature key if found, otherwise None.
        """
        for pattern, metadata in self.signatures.items():
            # Check if pattern contains wildcards
            if '*' in pattern or '?' in pattern:
                # Simple glob-to-regex conversion
                regex_pattern = pattern.replace('*', '.*').replace('?', '.')
                if re.search(regex_pattern, tool_output):
                    return pattern
            else:
                # STRICT 100% Exact Match required for non-wildcard patterns
                # The entire tool_output must match the pattern exactly.
                if tool_output == pattern:
                    return pattern
        return None

    def _recover(self, task: Dict[str, Any], error_pattern: str) -> Dict[str, Any]:
        """
        Executes a recovery strategy (re-plan or tool substitution).
        
        Args:
            task: The original task.
            error_pattern: The matched error pattern.
            
        Returns:
            Recovery result dictionary containing the action taken and details.
            Does NOT return ground truth directly.
        """
        # Determine strategy from metadata or default to 'replan'
        metadata = self.signatures.get(error_pattern, {})
        strategy = metadata.get("recovery_strategy", "replan")
        
        # Simulate recovery logic
        # In a real implementation, this would re-invoke the LLM with a new prompt
        # or substitute the failing tool based on the strategy.
        
        recovery_result = {
            "recovery_action": strategy,
            "status": "attempted",
            "details": f"Executed '{strategy}' strategy for pattern: {error_pattern}",
            "original_task_id": task.get("task_id")
        }
        
        # If strategy is 'replan', we might generate a new plan
        if strategy == "replan":
            recovery_result["new_plan_generated"] = True
        elif strategy == "substitute":
            recovery_result["tool_substituted"] = True
        
        return recovery_result

    def _simulate_llm_call(self, prompt: str) -> str:
        """
        Simulates an LLM call for the purpose of this implementation.
        In a full implementation, this would call the actual model.
        """
        # For testing purposes, we return a deterministic response based on the prompt
        # to ensure reproducibility without external dependencies.
        return f"Response to: {prompt}"

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a single task with signature checking.
        
        Workflow:
        1. Simulate LLM invocation to get a response/tool output.
        2. Check the response against loaded failure signatures.
        3. If a match is found, trigger recovery.
        4. Return the result with status and recovery info.
        """
        start_time = time.time()
        
        prompt = f"Task: {task.get('instruction', '')}"
        response = self._simulate_llm_call(prompt)
        
        # Check for failure signatures in the response/tool outputs
        # The response is treated as the tool output for this simplified agent
        matched_pattern = self._check_signatures(response)
        
        recovery_info = None
        final_status = "completed"
        
        if matched_pattern:
            # Trigger recovery strategy
            recovery_info = self._recover(task, matched_pattern)
            # Update status to reflect that a failure was detected and handled
            final_status = "recovered"
        
        execution_time = time.time() - start_time
        
        result = {
            "task_id": task.get("task_id"),
            "status": final_status,
            "response": response,
            "execution_time": execution_time,
            "agent_type": "augmented",
            "signature_detected": matched_pattern is not None,
            "signature_pattern": matched_pattern,
            "recovery_info": recovery_info
        }
        
        return result

    def run(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Runs the agent on a list of tasks.
        
        Args:
            tasks: List of task dictionaries.
            
        Returns:
            List of result dictionaries.
        """
        results = []
        for task in tasks:
            result = self.execute_task(task)
            results.append(result)
        return results
