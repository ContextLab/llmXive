"""
Neuro-Symbolic Explanation Generator.

This module implements the combination of neural narrative with symbolic trace,
ensuring that symbolic rules govern the structure of the explanation.
It addresses Turing's concern about "post-hoc rationalization" by making the
symbolic trace the authoritative source of truth and the neural component
a fluent interpreter of that structure.

Dependencies:
  - code/generate/symbolic_explanation.py (SymbolicSolver)
  - code/generate/neural_explanation.py (NeuralExplanationGenerator)
  - code/generate/neural_symbolic_interface.py (NeuroSymbolicInterface)
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

# Import from sibling modules
from generate.symbolic_explanation import SymbolicSolver, generate_symbolic_explanation
from generate.neural_explanation import NeuralExplanationGenerator, generate_neural_explanation
from generate.neural_symbolic_interface import NeuroSymbolicInterface, convert_neural_to_symbolic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NeuroSymbolicExplanationGenerator:
    """
    Orchestrates the generation of neuro-symbolic explanations.

    The core logic is:
    1. Generate a rigorous symbolic trace (the "ground truth" of the solution).
    2. Generate a neural narrative (fluent but potentially hallucinated).
    3. Use the NeuroSymbolicInterface to align the neural narrative with the
       symbolic trace, ensuring the final output respects the symbolic structure.
    """

    def __init__(self, problem_type: str = "algebra"):
        self.symbolic_solver = SymbolicSolver(problem_type=problem_type)
        self.neural_generator = NeuralExplanationGenerator()
        self.interface = NeuroSymbolicInterface()
        self.problem_type = problem_type

    def generate(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a combined neuro-symbolic explanation.

        Args:
            problem_data: Dictionary containing 'problem_id', 'problem_text',
                          'problem_type', and 'ground_truth' (if available).

        Returns:
            Dictionary containing:
                - 'neural_narrative': The raw neural explanation.
                - 'symbolic_trace': The raw symbolic trace.
                - 'combined_explanation': The final aligned explanation.
                - 'alignment_score': A metric of how well the neural narrative
                                   matched the symbolic structure before alignment.
        """
        logger.info(f"Starting neuro-symbolic generation for problem {problem_data.get('problem_id')}")
        start_time = time.time()

        # 1. Generate Symbolic Trace (The Authority)
        try:
            symbolic_trace = generate_symbolic_explanation(problem_data)
            logger.info(f"Symbolic trace generated with {len(symbolic_trace.get('steps', []))} steps.")
        except Exception as e:
            logger.error(f"Symbolic generation failed: {e}")
            raise

        # 2. Generate Neural Narrative (The Interpreter)
        try:
            # We pass the problem text to the neural generator
            neural_narrative = generate_neural_explanation(problem_data)
            logger.info("Neural narrative generated.")
        except Exception as e:
            logger.error(f"Neural generation failed: {e}")
            raise

        # 3. Align and Combine using the Interface
        # This step ensures the "governance" of the symbolic layer over the final output.
        try:
            combined_explanation, alignment_score = self.interface.align_and_combine(
                symbolic_trace=symbolic_trace,
                neural_narrative=neural_narrative,
                problem_data=problem_data
            )
            logger.info(f"Alignment complete. Score: {alignment_score:.4f}")
        except Exception as e:
            logger.error(f"Alignment failed: {e}")
            raise

        elapsed = time.time() - start_time
        logger.info(f"Neuro-symbolic generation completed in {elapsed:.2f}s")

        return {
            "problem_id": problem_data.get("problem_id"),
            "neural_narrative": neural_narrative,
            "symbolic_trace": symbolic_trace,
            "combined_explanation": combined_explanation,
            "alignment_score": alignment_score,
            "generation_time_seconds": elapsed
        }

def generate_neuro_symbolic_explanation(problem_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to generate a neuro-symbolic explanation.

    Args:
        problem_data: Dictionary with problem details.

    Returns:
        Dictionary with explanation components.
    """
    generator = NeuroSymbolicExplanationGenerator(problem_type=problem_data.get("problem_type", "algebra"))
    return generator.generate(problem_data)

def main():
    """
    Main entry point for CLI execution.

    Expects a JSON file path via --input or a problem ID via --problem-id.
    If --problem-id is used, it attempts to load a sample problem from a
    local cache or generates a deterministic sample for demonstration if
    the dataset is not yet fetched.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate Neuro-Symbolic Explanations")
    parser.add_argument("--input", type=str, help="Path to JSON file containing problem data")
    parser.add_argument("--problem-id", type=str, help="Problem ID to fetch/generate (for testing)")
    parser.add_argument("--output", type=str, default="data/derived/neuro_symbolic_output.json",
                        help="Path to save the output JSON")
    parser.add_argument("--problem-type", type=str, default="algebra",
                        help="Type of problem (algebra, geometry)")

    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    problem_data = None

    if args.input:
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)
        with open(args.input, 'r') as f:
            problem_data = json.load(f)
    elif args.problem_id:
        # Fallback to generating a deterministic sample problem if no input file
        # This is necessary for the run-book to work without the full dataset
        logger.info(f"Generating sample problem for ID: {args.problem_id}")
        problem_data = {
            "problem_id": args.problem_id,
            "problem_text": f"Solve for x: 2x + 5 = 15",
            "problem_type": args.problem_type,
            "ground_truth": "x=5"
        }
    else:
        logger.error("Either --input or --problem-id must be provided.")
        sys.exit(1)

    try:
        result = generate_neuro_symbolic_explanation(problem_data)
        
        # Save result
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Output saved to {args.output}")
        print(json.dumps({"status": "success", "output_path": args.output}))
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()