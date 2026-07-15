"""
Teacher model implementation for generating Chain-of-Thought (CoT) traces.

This module provides a lightweight, CPU-only mock LLM class designed to
generate 10-step CoT traces for synthetic logic and arithmetic problems.
It strictly adheres to the project's constraint of no GPU usage.
"""
import random
from typing import List, Dict, Any, Optional

from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger
from config import get_config

logger = get_logger(__name__)

class Teacher:
    """
    A lightweight mock LLM class that generates 10-step Chain-of-Thought (CoT) traces.
    
    This class simulates a teacher model for knowledge distillation. It operates
    entirely on CPU and does not utilize any GPU-specific flags or libraries.
    
    Attributes:
        seed (int): Random seed for reproducibility.
        max_steps (int): Fixed number of steps in the CoT trace (10).
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the Teacher model.
        
        Args:
            seed: Optional random seed. If None, uses the seed from Config.
        """
        config = get_config()
        self.seed = seed if seed is not None else config.seed
        random.seed(self.seed)
        self.max_steps = 10
        logger.info(f"Teacher initialized with seed {self.seed}")

    def _generate_step_premise_logic(self, problem: SyntheticProblem, step_idx: int) -> str:
        """Generate a logical reasoning step for propositional problems."""
        premises = problem.premises
        operators = problem.operators
        
        if not premises:
            return f"Step {step_idx}: No premises available for inference."

        # Select a premise to work with
        premise = random.choice(premises)
        
        # Simulate a logical operation based on available operators
        if operators and step_idx < len(operators):
            op = operators[step_idx % len(operators)]
            return f"Step {step_idx}: Analyzing '{premise}' using operator '{op}'."
        else:
            return f"Step {step_idx}: Deductive inference from '{premise}'."

    def _generate_step_arithmetic_logic(self, problem: SyntheticProblem, step_idx: int) -> str:
        """Generate an arithmetic reasoning step."""
        premises = problem.premises
        
        if not premises:
            return f"Step {step_idx}: No numerical data provided."

        # Simulate a calculation step
        val_a = random.randint(1, 100)
        val_b = random.randint(1, 100)
        ops = ['+', '-', '*', '/']
        op = random.choice(ops)
        
        return f"Step {step_idx}: Calculating {val_a} {op} {val_b} based on context '{premises[0]}'."

    def _generate_conclusion(self, problem: SyntheticProblem) -> str:
        """Generate the final conclusion step."""
        solution = problem.solution
        return f"Step {self.max_steps}: Final conclusion derived: '{solution}'."

    def generate_trace(self, problem: SyntheticProblem) -> List[str]:
        """
        Generate a 10-step CoT trace for a given SyntheticProblem.
        
        Args:
            problem: The synthetic problem instance containing premises, operators, and solution.
        
        Returns:
            A list of 10 strings representing the reasoning steps.
        
        Raises:
            ValueError: If the problem structure is invalid for trace generation.
        """
        if not isinstance(problem, SyntheticProblem):
            raise ValueError("Input must be a SyntheticProblem instance.")
        
        trace = []
        
        # Determine problem type based on operators or premises content
        # Simple heuristic: if operators look like math symbols, treat as arithmetic
        is_arithmetic = any(op in ['+', '-', '*', '/', '%'] for op in problem.operators) if problem.operators else False

        for step in range(1, self.max_steps):
            if is_arithmetic:
                step_text = self._generate_step_arithmetic_logic(problem, step)
            else:
                step_text = self._generate_step_premise_logic(problem, step)
            trace.append(step_text)
        
        # Always add the conclusion as the final step (index 9, which is step 10)
        trace.append(self._generate_conclusion(problem))
        
        logger.debug(f"Generated {len(trace)}-step trace for problem ID: {problem.id}")
        return trace

    def get_teacher_trace_for_batch(self, problems: List[SyntheticProblem]) -> List[List[str]]:
        """
        Generate traces for a batch of problems.
        
        Args:
            problems: List of SyntheticProblem instances.
        
        Returns:
            List of trace lists.
        """
        all_traces = []
        for p in problems:
            all_traces.append(self.generate_trace(p))
        return all_traces

def main():
    """
    Main entry point for testing the Teacher model generation.
    This function creates a dummy problem, generates a trace, and prints it.
    """
    # Initialize config to ensure seed is set
    _ = get_config()
    
    # Create a sample problem for demonstration
    sample_problem = SyntheticProblem(
        id="demo-problem-001",
        premises=["All humans are mortal.", "Socrates is a human."],
        operators=["AND", "IMPLIES"],
        solution="Socrates is mortal.",
        entropy_level="medium",
        metadata={"source": "test"}
    )
    
    teacher = Teacher(seed=42)
    trace = teacher.generate_trace(sample_problem)
    
    print(f"Generated Trace for Problem ID: {sample_problem.id}")
    print("-" * 40)
    for line in trace:
        print(line)
    print("-" * 40)
    print(f"Total steps: {len(trace)}")

if __name__ == "__main__":
    main()