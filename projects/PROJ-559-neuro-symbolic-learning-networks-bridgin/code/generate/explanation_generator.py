"""
Explanation Generator Orchestrator

Orchestrates the generation of neural, symbolic, and neuro-symbolic explanations
for a given problem. Includes validation to ensure distinctness between neural
and symbolic outputs as per FR-002.
"""
import os
import sys
import json
import logging
import argparse
import time
import argparse
from typing import Dict, Any, List, Optional, Tuple

# Import from existing API surface
from generate.symbolic_explanation import generate_symbolic_explanation, SymbolicSolver
from generate.neural_explanation import generate_neural_explanation, NeuralExplanationGenerator
from generate.neuro_symbolic_explanation import generate_neuro_symbolic_explanation, NeuroSymbolicExplanationGenerator
from generate.validate_distinctness import calculate_jaccard_similarity, validate_distinctness

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExplanationGenerator:
    """
    Orchestrator for generating multiple explanation types.

    Ensures that generated explanations are distinct and valid before saving.
    """

    def __init__(self, output_dir: str = "data/generated"):
        self.output_dir = output_dir
        self.symbolic_generator = SymbolicSolver()
        self.neural_generator = NeuralExplanationGenerator()
        self.neuro_symbolic_generator = NeuroSymbolicExplanationGenerator()
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all(
        self,
        problem_id: str,
        problem_type: str,
        problem_statement: str,
        problem_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate all three explanation types for a given problem.

        Args:
            problem_id: Unique identifier for the problem
            problem_type: Type of problem (e.g., 'algebra', 'geometry')
            problem_statement: Text description of the problem
            problem_data: Optional structured data about the problem

        Returns:
            Dictionary with keys 'neural', 'symbolic', 'neuro_symbolic' containing
            the generated explanations.

        Raises:
            ValueError: If explanations are not distinct enough (similarity > 0.95)
            RuntimeError: If any generator fails
        """
        logger.info(f"Starting explanation generation for problem {problem_id} ({problem_type})")
        start_time = time.time()

        try:
            # Generate symbolic explanation
            logger.info("Generating symbolic explanation...")
            symbolic_start = time.time()
            symbolic_explanation = generate_symbolic_explanation(
                problem_id=problem_id,
                problem_type=problem_type,
                problem_statement=problem_statement,
                problem_data=problem_data
            )
            symbolic_duration = time.time() - symbolic_start
            logger.info(f"Symbolic explanation generated in {symbolic_duration:.2f}s")

            # Generate neural explanation
            logger.info("Generating neural explanation...")
            neural_start = time.time()
            neural_explanation = generate_neural_explanation(
                problem_id=problem_id,
                problem_type=problem_type,
                problem_statement=problem_statement,
                problem_data=problem_data
            )
            neural_duration = time.time() - neural_start
            logger.info(f"Neural explanation generated in {neural_duration:.2f}s")

            # Validate distinctness BEFORE generating neuro-symbolic
            logger.info("Validating distinctness between neural and symbolic explanations...")
            similarity = calculate_jaccard_similarity(
                neural_explanation,
                symbolic_explanation
            )
            logger.info(f"Similarity between neural and symbolic: {similarity:.4f}")

            if similarity > 0.95:
                error_msg = (
                    f"CRITICAL: Neural and symbolic explanations are too similar "
                    f"(similarity={similarity:.4f} > 0.95). This violates FR-002 "
                    f"requiring distinct explanations. "
                    f"Problem ID: {problem_id}, Type: {problem_type}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Generate neuro-symbolic explanation
            logger.info("Generating neuro-symbolic explanation...")
            neuro_symbolic_start = time.time()
            neuro_symbolic_explanation = generate_neuro_symbolic_explanation(
                problem_id=problem_id,
                problem_type=problem_type,
                problem_statement=problem_statement,
                neural_explanation=neural_explanation,
                symbolic_explanation=symbolic_explanation,
                problem_data=problem_data
            )
            neuro_symbolic_duration = time.time() - neuro_symbolic_start
            logger.info(f"Neuro-symbolic explanation generated in {neuro_symbolic_duration:.2f}s")

            total_duration = time.time() - start_time
            logger.info(f"All explanations generated successfully in {total_duration:.2f}s")

            return {
                'neural': neural_explanation,
                'symbolic': symbolic_explanation,
                'neuro_symbolic': neuro_symbolic_explanation
            }

        except Exception as e:
            logger.error(f"Error during explanation generation: {str(e)}")
            raise

    def save_explanations(
        self,
        problem_id: str,
        explanations: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Save explanations to disk.

        Args:
            problem_id: Unique identifier for the problem
            explanations: Dictionary of explanation types to content

        Returns:
            Dictionary mapping explanation type to file path
        """
        saved_files = {}
        
        for exp_type, content in explanations.items():
            filename = f"explanation_{exp_type}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files[exp_type] = filepath
            logger.info(f"Saved {exp_type} explanation to {filepath}")
        
        return saved_files

    def run_with_problem_id(
        self,
        problem_id: str,
        problem_type: str = "algebra",
        problem_statement: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the full generation pipeline for a specific problem ID.

        Args:
            problem_id: The problem identifier
            problem_type: Type of problem (default: algebra)
            problem_statement: Optional problem statement text

        Returns:
            Dictionary with generation results and file paths
        """
        # If no problem statement provided, use a default based on problem_id
        if problem_statement is None:
            problem_statement = f"Problem {problem_id} of type {problem_type}"
            logger.warning(f"No problem statement provided, using default: {problem_statement}")

        try:
            explanations = self.generate_all(
                problem_id=problem_id,
                problem_type=problem_type,
                problem_statement=problem_statement
            )
            
            saved_files = self.save_explanations(problem_id, explanations)
            
            return {
                'success': True,
                'problem_id': problem_id,
                'files': saved_files,
                'explanations': explanations
            }
            
        except ValueError as e:
            # Distinctness validation failed
            logger.error(f"Distinctness validation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'exit_code': 1
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'exit_code': 1
            }

        logger.info(f"Successfully generated explanations for {problem_id}.")
        logger.info(f"Files saved to: {self.output_dir}")
        return files

def main():
    """
    Main entry point for the explanation generator CLI.

    Usage:
        python code/generate/explanation_generator.py --problem-id sample_001 --problem-type algebra
    """
    parser = argparse.ArgumentParser(
        description='Generate neural, symbolic, and neuro-symbolic explanations for problems.'
    )
    parser.add_argument(
        '--problem-id',
        type=str,
        required=True,
        help='Unique identifier for the problem'
    )
    parser.add_argument(
        '--problem-type',
        type=str,
        default='algebra',
        help='Type of problem (e.g., algebra, geometry)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/generated',
        help='Directory to save generated explanations'
    )
    parser.add_argument(
        '--problem-statement',
        type=str,
        default=None,
        help='Optional problem statement text'
    )

    args = parser.parse_args()

    logger.info(f"Explanation Generator started for problem {args.problem_id}")

    generator = ExplanationGenerator(output_dir=args.output_dir)
    result = generator.run_with_problem_id(
        problem_id=args.problem_id,
        problem_type=args.problem_type,
        problem_statement=args.problem_statement
    )

    if result['success']:
        logger.info("Explanation generation completed successfully")
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        logger.error(f"Explanation generation failed: {result.get('error', 'Unknown error')}")
        print(json.dumps(result, indent=2))
        sys.exit(result.get('exit_code', 1))


if __name__ == '__main__':
    main()