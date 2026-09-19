import os
import time
from typing import Any, Dict, List, Optional
from agents.base import BaseAgent
from utils.config import get_path, get_hyperparameter

class BaselineAgent(BaseAgent):
    """
    Baseline agent that uses internal LLM reasoning only.
    It does NOT access the failure signature index.
    """

    def __init__(self, model: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.model = model or get_hyperparameter("model", "llama-3-8b-quantized")
        self.max_tokens = get_hyperparameter("max_tokens", 512)
        self.temperature = get_hyperparameter("temperature", 0.7)
        
        # IMPORTANT: Do NOT load failure_signatures.json here or anywhere.
        # This agent is isolated from the recovery mechanism.

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Simulate LLM call. In a real implementation, this would call the model.
        For testing/isolation verification, we return a mock response.
        """
        # In a real scenario, this would be:
        # response = llm_model.generate(prompt, max_tokens=self.max_tokens, temperature=self.temperature)
        # return parse_response(response)
        
        # Mock response for demonstration/testing
        return {
            "thought": "I am planning...",
            "action": "move",
            "observation": "success",
            "final_answer": "completed"
        }

    def plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a plan for the given task without using external signatures.
        """
        prompt = f"Plan for task: {task.get('goal', 'unknown')}"
        response = self._call_llm(prompt)
        return response

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task using the baseline agent logic.
        """
        start_time = time.time()
        plan = self.plan(task)
        duration = time.time() - start_time
        
        return {
            "task_id": task.get("id"),
            "status": "success" if plan.get("final_answer") == "completed" else "failure",
            "plan": plan,
            "duration": duration,
            "used_signatures": False  # Explicitly false for baseline
        }
