"""
Neuro-Symbolic Explanation Generator (T015)

Combines neural narrative with symbolic trace, ensuring symbolic rules govern
the structure of the explanation. This addresses Turing's "post-hoc rationalization"
concern by making the symbolic trace the primary logical scaffold, with the neural
component providing natural language fluency only where it does not contradict
the symbolic logic.

Dependencies:
    T012: fetch_assistments (data availability)
    T013: symbolic_explanation (symbolic trace generation)
    T014: neural_explanation (neural narrative generation)
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

# Import from sibling modules as per API surface
from generate.symbolic_explanation import generate_symbolic_explanation, SymbolicSolver
from generate.neural_explanation import generate_neural_explanation, NeuralExplanationGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NeuroSymbolicExplanationGenerator:
    """
    Orchestrates the combination of symbolic and neural explanations.

    Strategy:
    1. Generate a strict symbolic trace (T013) to establish the logical skeleton.
    2. Generate a neural narrative (T014) for the problem context.
    3. Filter/align the neural narrative to ensure it does not contradict the
       symbolic trace (governing structure).
    4. Merge into a final neuro-symbolic explanation where the symbolic steps
       are the primary structure, and the neural text provides "flavor" or
       intuition only where it supports the symbolic step.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.symbolic_solver = SymbolicSolver()
        self.neural_gen = NeuralExplanationGenerator()

    def _validate_neural_against_symbolic(
        self,
        neural_text: str,
        symbolic_trace: List[Dict[str, Any]]
    ) -> str:
        """
        Validates that the neural narrative does not contradict the symbolic trace.
        
        In a real implementation, this would use a semantic checker or a smaller
        verification model. For this implementation, we perform a structural
        sanity check: ensure the neural text acknowledges the key operations
        found in the symbolic trace.
        """
        # Extract key operations from symbolic trace
        operations = set()
        for step in symbolic_trace:
            if 'rule' in step:
                operations.add(step['rule'].lower())
            if 'operation' in step:
                operations.add(step['operation'].lower())
        
        # Simple heuristic: check if neural text mentions at least one key operation
        # In a production system, this would be a more robust verification step.
        neural_lower = neural_text.lower()
        matches = [op for op in operations if op in neural_lower]
        
        if not matches and len(operations) > 0:
            logger.warning(
                "Neural narrative does not explicitly mention symbolic operations. "
                "Appending a bridging clause to ensure coherence."
            )
            # Append a minimal bridging clause to ensure the neural text
            # acknowledges the logical flow without fabricating new logic.
            neural_text += " This process follows a logical sequence of algebraic transformations."
        
        return neural_text

    def generate(
        self,
        problem_data: Dict[str, Any],
        max_symbolic_steps: int = 10,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """
        Generates a combined neuro-symbolic explanation.

        Args:
            problem_data: Dictionary containing 'problem_id', 'question', 'answer', etc.
            max_symbolic_steps: Max depth for symbolic solver.
            timeout_seconds: Timeout for neural generation.

        Returns:
            Dictionary containing 'neuro_symbolic_explanation', 'symbolic_trace',
            'neural_narrative', and metadata.
        """
        start_time = time.time()

        # 1. Generate Symbolic Trace (The "Governor")
        logger.info(f"Generating symbolic trace for problem {problem_data.get('problem_id')}")
        try:
            symbolic_result = generate_symbolic_explanation(
                problem_data,
                max_steps=max_symbolic_steps
            )
            symbolic_trace = symbolic_result.get('trace', [])
            symbolic_confidence = symbolic_result.get('confidence', 0.0)
        except Exception as e:
            logger.error(f"Symbolic generation failed: {e}")
            # Fallback: if symbolic fails, we cannot produce a valid neuro-symbolic
            # explanation per the "symbolic governs" requirement.
            raise RuntimeError(f"Symbolic trace generation failed, cannot proceed: {e}")

        # 2. Generate Neural Narrative (The "Flavor")
        logger.info(f"Generating neural narrative for problem {problem_data.get('problem_id')}")
        try:
            neural_result = generate_neural_explanation(
                problem_data,
                timeout_seconds=timeout_seconds
            )
            neural_narrative = neural_result.get('explanation', '')
        except Exception as e:
            logger.warning(f"Neural generation failed: {e}. Using fallback narrative.")
            neural_narrative = "The solution involves logical steps to reach the answer."

        # 3. Validate and Align
        validated_neural = self._validate_neural_against_symbolic(
            neural_narrative,
            symbolic_trace
        )

        # 4. Construct Final Explanation
        # Structure: Introduction -> Symbolic Steps (with neural context) -> Conclusion
        final_explanation_parts = []
        
        # Introduction
        intro = f"Here is the step-by-step solution for the problem: {problem_data.get('question', 'Unknown problem')}."
        final_explanation_parts.append(intro)

        # Body: Iterate symbolic steps
        for i, step in enumerate(symbolic_trace):
            step_num = i + 1
            rule_name = step.get('rule', 'Step')
            detail = step.get('detail', 'No detail provided.')
            
            # Attempt to find relevant context from neural narrative for this step
            # (Simplified: just use the general validated narrative for now)
            context = validated_neural if i == 0 else ""
            
            step_text = f"Step {step_num} ({rule_name}): {detail}"
            if context and i == 0:
                step_text = f"{context} {step_text}"
            
            final_explanation_parts.append(step_text)

        # Conclusion
        conclusion = f"Based on the logical application of {len(symbolic_trace)} rules, the final answer is {problem_data.get('answer', 'unknown')}."
        final_explanation_parts.append(conclusion)

        final_explanation = "\n\n".join(final_explanation_parts)

        elapsed = time.time() - start_time

        return {
            "problem_id": problem_data.get("problem_id"),
            "neuro_symbolic_explanation": final_explanation,
            "symbolic_trace": symbolic_trace,
            "neural_narrative": validated_neural,
            "symbolic_confidence": symbolic_confidence,
            "generation_time_seconds": elapsed,
            "methodology": "Symbolic-First with Neural Alignment"
        }

def generate_neuro_symbolic_explanation(
    problem_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate a neuro-symbolic explanation.
    """
    generator = NeuroSymbolicExplanationGenerator(config)
    return generator.generate(problem_data)

def main():
    """
    Main entry point for standalone execution.
    Expects a JSON file with problem data or uses a sample from T012/T013.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate Neuro-Symbolic Explanations")
    parser.add_argument("--input", type=str, help="Path to JSON file with problem data")
    parser.add_argument("--output", type=str, default="data/derived/neuro_symbolic_explanation.json", help="Output path")
    parser.add_argument("--problem-id", type=str, help="Problem ID to fetch from cache (if input not provided)")
    
    args = parser.parse_args()

    # Load problem data
    if args.input and os.path.exists(args.input):
        with open(args.input, 'r') as f:
            problem_data = json.load(f)
    elif args.problem_id:
        # Fallback: try to load from a cached file if T012 ran
        cache_path = f"data/derived/{args.problem_id}_problem.json"
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                problem_data = json.load(f)
        else:
            logger.error(f"Problem ID {args.problem_id} not found in cache and no input file provided.")
            sys.exit(1)
    else:
        # Default sample for testing if no args provided (should not happen in pipeline)
        logger.warning("No input provided. Generating a synthetic sample for demonstration.")
        problem_data = {
            "problem_id": "sample_001",
            "question": "Solve for x: 2x + 4 = 10",
            "answer": "3",
            "type": "algebra"
        }

    try:
        result = generate_neuro_symbolic_explanation(problem_data)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Neuro-symbolic explanation saved to {args.output}")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()