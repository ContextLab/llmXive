"""
Monolithic SLM Agent for AdaPlanBench.

Implements a direct prompt-based approach using a CPU-tractable small model
(e.g., Phi-2) in default precision to solve planning tasks without explicit
constraint tracking or correction modules.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

# Local imports
from config import Paths, ModelConfig, set_all_seeds
from agent.base import BaseAgent, TaskContext, ExecutionResult, ViolationType

@dataclass
class MonolithicAgentConfig:
    """Configuration for the Monolithic Agent."""
    model_name: str = "microsoft/phi-2"
    max_new_tokens: int = 512
    temperature: float = 0.7
    do_sample: bool = True
    # Precision settings (default float16 for CPU efficiency if supported, else float32)
    torch_dtype: torch.dtype = torch.float32 
    device: str = "cpu"

class MonolithicAgent(BaseAgent):
    """
    A monolithic agent that relies solely on the SLM's internal reasoning
    to plan and execute tasks. It does not use an external constraint store
    or a rule-based resolver.
    """
    
    def __init__(self, config: MonolithicAgentConfig = None):
        self.config = config or MonolithicAgentConfig()
        self.tokenizer = None
        self.model = None
        self._loaded = False

    def load_model(self) -> None:
        """Load the SLM model and tokenizer."""
        if self._loaded:
            return

        # Set seeds for reproducibility
        set_all_seeds(42)

        print(f"Loading model: {self.config.model_name}...")
        
        # Determine dtype based on availability and config
        dtype = self.config.torch_dtype
        if torch.cuda.is_available():
            self.config.device = "cuda"
            # Optional: use bfloat16 if supported, else float16
            if torch.cuda.is_bf16_supported():
                dtype = torch.bfloat16
            else:
                dtype = torch.float16
        elif torch.backends.mps.is_available():
            self.config.device = "mps"
            dtype = torch.float32 # MPS often prefers float32

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=True
            )
            # Phi-2 tokenizer might not have pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                torch_dtype=dtype,
                device_map=self.config.device,
                trust_remote_code=True
            )
            
            self.model.eval()
            self._loaded = True
            print(f"Model loaded successfully on {self.config.device}.")
        except Exception as e:
            raise RuntimeError(f"Failed to load model {self.config.model_name}: {e}") from e

    def _build_prompt(self, task_context: TaskContext) -> str:
        """Construct the prompt for the monolithic agent."""
        # Format: Task Description + Constraints + "Plan:"
        # We assume the task description includes the goal and initial state.
        # Constraints are appended as additional context.
        
        base_prompt = f"""
        You are an AI assistant tasked with planning a sequence of actions to achieve a specific goal.
        
        Task Description:
        {task_context.task_description}
        
        Constraints (must be strictly followed):
        {task_context.constraints}
        
        Provide a step-by-step plan to achieve the goal. Do not include any conversational filler.
        Start your response immediately with the plan.
        """
        return base_prompt.strip()

    def _parse_response(self, raw_output: str) -> List[str]:
        """Parse the raw model output into a list of action steps."""
        # Simple heuristic: split by newlines and strip whitespace
        # In a production system, this might involve more robust parsing
        lines = raw_output.strip().split('\n')
        steps = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("Plan:"):
                # Remove numbering if present (e.g., "1. Step")
                if stripped[0].isdigit() and '. ' in stripped:
                    stripped = stripped.split('. ', 1)[1]
                steps.append(stripped)
        return steps

    def execute(self, task_context: TaskContext) -> ExecutionResult:
        """
        Execute the task using the monolithic approach.
        
        Returns an ExecutionResult with the plan and potential violations.
        Since this is monolithic, violations are only detected if the model
        explicitly fails to follow constraints in its output (which we can't
        perfectly detect without a resolver, so we assume success unless
        the output is malformed or obviously violates a constraint string).
        """
        if not self._loaded:
            self.load_model()

        try:
            # Build prompt
            prompt = self._build_prompt(task_context)
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.config.device)
            
            # Generate
            generation_config = GenerationConfig(
                max_new_tokens=self.config.max_new_tokens,
                temperature=self.config.temperature,
                do_sample=self.config.do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    generation_config=generation_config
                )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the generated part (remove the prompt)
            # Since the prompt is part of the input, we need to slice it out.
            # A simpler way is to just take the text after the prompt ends.
            # However, for simplicity in this implementation, we assume the 
            # model generates the continuation.
            
            # We'll just take the whole decoded text and split at the prompt end
            # This is a bit fragile but works for the demo structure.
            # A better approach: use input_ids length to slice.
            input_len = inputs['input_ids'].shape[1]
            generated_tokens = outputs[0][input_len:]
            raw_output = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            # Parse steps
            steps = self._parse_response(raw_output)
            
            # Determine violations (Monolithic agent has no explicit resolver)
            # We perform a basic check: if the output is empty or too short
            if not steps or len(' '.join(steps)) < 10:
                violations = [ViolationType.EXECUTION_FAILURE]
                success = False
            else:
                # Monolithic agent assumes success unless it clearly fails to generate
                # Note: In a real scenario, we'd need a verifier. 
                # For this task, we log "NO_VIOLATION" if steps exist, 
                # acknowledging the limitation that constraint checking is implicit.
                violations = []
                success = True

            return ExecutionResult(
                steps=steps,
                success=success,
                violations=violations,
                raw_output=raw_output
            )

        except Exception as e:
            # Log error and return failure
            return ExecutionResult(
                steps=[],
                success=False,
                violations=[ViolationType.EXECUTION_FAILURE],
                raw_output=f"Error during execution: {str(e)}"
            )

def main():
    """Entry point for testing the MonolithicAgent."""
    print("Starting Monolithic Agent Test...")
    
    # Create a mock task context for testing
    # In a real run, this would come from the dataset loader
    mock_context = TaskContext(
        task_id="test_task_001",
        task_description="Plan a way to make a sandwich.",
        constraints=["Do not use peanut butter.", "Must use bread.", "Must use cheese."],
        initial_state={},
        goal_state={}
    )
    
    agent = MonolithicAgent()
    result = agent.execute(mock_context)
    
    print(f"Success: {result.success}")
    print(f"Steps: {result.steps}")
    print(f"Violations: {result.violations}")
    print("Test completed.")

if __name__ == "__main__":
    main()