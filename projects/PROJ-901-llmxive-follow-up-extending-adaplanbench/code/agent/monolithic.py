"""
Monolithic Agent implementation.
A baseline agent that generates plans without explicit constraint tracking.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import torch

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agent.base import TaskContext, ExecutionResult, ViolationType

@dataclass
class MonolithicAgentConfig:
    """Configuration for the Monolithic Agent."""
    model_name: str = "microsoft/phi-2"
    max_tokens: int = 2048
    temperature: float = 0.7
    device: str = "cpu"
    precision: str = "float32"

class MonolithicAgent:
    """
    Monolithic Agent that generates plans in a single pass.
    Does not explicitly track or validate constraints during generation.
    """
    
    def __init__(self, config: MonolithicAgentConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the model and tokenizer."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            print(f"Loading model: {self.config.model_name}")
            
            # Try primary model
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
                model_kwargs = {
                    "torch_dtype": getattr(torch, self.config.precision),
                    "device_map": self.config.device
                }
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.config.model_name,
                    **model_kwargs
                )
            except Exception as primary_error:
                print(f"Failed to load primary model: {primary_error}", file=sys.stderr)
                
                # Try fallback model
                fallback_model = "microsoft/phi-3-mini"
                print(f"Attempting fallback model: {fallback_model}")
                self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
                model_kwargs = {
                    "torch_dtype": getattr(torch, self.config.precision),
                    "device_map": self.config.device
                }
                self.model = AutoModelForCausalLM.from_pretrained(
                    fallback_model,
                    **model_kwargs
                )
                self.config.model_name = fallback_model
            
            if self.model.device.type == 'cuda':
                print(f"Model loaded on GPU: {self.model.device}")
            else:
                print(f"Model loaded on CPU: {self.model.device}")
                
        except ImportError as e:
            print(f"Transformers library not available: {e}", file=sys.stderr)
            print("Running in mock mode (no actual model inference).", file=sys.stderr)
            self.model = None
            self.tokenizer = None
        except Exception as e:
            print(f"Error loading model: {e}", file=sys.stderr)
            print("Running in mock mode (no actual model inference).", file=sys.stderr)
            self.model = None
            self.tokenizer = None

    def execute(self, context: TaskContext) -> ExecutionResult:
        """
        Execute the monolithic agent on the given task context.
        
        Args:
            context: Task context containing prompt and constraints.
            
        Returns:
            ExecutionResult with generated plan and violation information.
        """
        # Construct prompt
        prompt = f"""You are a planning agent. Generate a step-by-step plan for the following household task.
        
Task: {context.raw_prompt}

Constraints to consider:
{chr(10).join(f'- {c}' for c in context.constraints) if context.constraints else 'None'}

Generate your plan below. Each step should be on a new line.
Plan:
"""
        
        generated_plan = ""
        final_score = 0.0
        violations = []
        
        if self.model is not None and self.tokenizer is not None:
            try:
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=self.config.max_tokens,
                        temperature=self.config.temperature,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                
                full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract plan (everything after "Plan:")
                if "Plan:" in full_response:
                    generated_plan = full_response.split("Plan:", 1)[1].strip()
                else:
                    generated_plan = full_response.strip()
                
                # Simple heuristic scoring (placeholder for real evaluation)
                # In a real implementation, this would evaluate constraint adherence
                plan_steps = [s.strip() for s in generated_plan.split('\n') if s.strip()]
                final_score = min(1.0, len(plan_steps) * 0.1)
                
                # Check for obvious constraint violations (simple string matching)
                for constraint in context.constraints:
                    if constraint and constraint.lower() not in generated_plan.lower():
                        violations.append(ViolationType(
                            type="constraint_violation",
                            constraint=constraint,
                            reason=f"Constraint not reflected in plan: {constraint}"
                        ))
                
            except Exception as e:
                print(f"Inference error: {e}", file=sys.stderr)
                generated_plan = "Error during plan generation"
                final_score = 0.0
        else:
            # Mock mode - generate a simple plan
            generated_plan = f"Step 1: Understand the task: {context.raw_prompt}\n"
            generated_plan += f"Step 2: Identify key constraints: {len(context.constraints)} found\n"
            generated_plan += "Step 3: Execute plan steps sequentially\n"
            generated_plan += "Step 4: Verify completion"
            
            final_score = 0.5
            
            # Mock violations for demonstration
            if context.constraints:
                violations.append(ViolationType(
                    type="constraint_violation",
                    constraint=context.constraints[0] if context.constraints else "",
                    reason="Mock violation: constraint not explicitly addressed"
                ))
        
        return ExecutionResult(
            generated_plan=generated_plan,
            final_score=final_score,
            violations=violations
        )

    def main():
        """CLI entry point for testing the monolithic agent."""
        import argparse
        from agent.base import TaskContext
        
        parser = argparse.ArgumentParser(description="Test Monolithic Agent")
        parser.add_argument("--prompt", type=str, default="Prepare a simple breakfast",
                            help="Task prompt")
        parser.add_argument("--constraints", type=str, nargs="*", default=[],
                            help="List of constraints")
        parser.add_argument("--model", type=str, default="microsoft/phi-2",
                            help="Model name")
        args = parser.parse_args()
        
        config = MonolithicAgentConfig(model_name=args.model)
        agent = MonolithicAgent(config)
        
        context = TaskContext(
            task_id="test_001",
            raw_prompt=args.prompt,
            constraints=args.constraints,
            constraint_count=len(args.constraints)
        )
        
        result = agent.execute(context)
        
        print("\n=== Execution Result ===")
        print(f"Generated Plan:\n{result.generated_plan}")
        print(f"\nFinal Score: {result.final_score}")
        print(f"Violations: {len(result.violations)}")
        for v in result.violations:
            print(f"  - {v.reason}")

if __name__ == "__main__":
    MonolithicAgent.main()