import random
from typing import List, Dict, Any, Optional
from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger
from config import get_config

logger = get_logger("teacher")

class Teacher:
    """
    A lightweight mock LLM teacher that generates 10-step CoT traces.
    CPU-only, no GPU dependencies.
    """
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.seed = seed
        self.step_templates = [
            "Step {}: Analyze premise: {}",
            "Step {}: Apply operator: {}",
            "Step {}: Derive intermediate conclusion: {}",
            "Step {}: Check consistency: {}",
            "Step {}: Combine facts: {}",
            "Step {}: Resolve contradiction: {}",
            "Step {}: Simplify expression: {}",
            "Step {}: Verify solution path: {}",
            "Step {}: Finalize reasoning: {}",
            "Step {}: Output solution: {}"
        ]
        
        logger.info(f"Initialized Teacher with seed {seed}")
    
    def generate_trace(
        self,
        problem: SyntheticProblem,
        max_steps: int = 10
    ) -> List[str]:
        """
        Generate a Chain-of-Thought trace for the given problem.
        
        Args:
            problem: The synthetic problem to solve
            max_steps: Maximum number of trace steps
            
        Returns:
            List of trace step strings
        """
        trace = []
        
        premises_str = " | ".join(problem.premises) if problem.premises else "None"
        operators_str = " | ".join(problem.operators) if problem.operators else "None"
        
        for i in range(min(max_steps, 10)):
            template_idx = i % len(self.step_templates)
            template = self.step_templates[template_idx]
            
            # Generate step content based on problem elements
            if "premise" in template:
                content = random.choice(problem.premises) if problem.premises else "empty"
            elif "operator" in template:
                content = random.choice(problem.operators) if problem.operators else "empty"
            elif "solution" in template:
                content = problem.solution
            else:
                content = f"intermediate_result_{i}"
            
            step = template.format(i + 1, content)
            trace.append(step)
        
        return trace

def main():
    """Test the teacher model."""
    from models.synthetic_problem import SyntheticProblem
    
    teacher = Teacher(seed=42)
    
    test_problem = SyntheticProblem(
        id="test_001",
        premises=["P1: A is true", "P2: B is false"],
        operators=["AND", "NOT"],
        solution="S1: C is true",
        entropy_level="high",
        metadata={}
    )
    
    trace = teacher.generate_trace(test_problem)
    print("Generated trace:")
    for step in trace:
        print(f"  {step}")

if __name__ == "__main__":
    main()
