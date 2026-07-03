import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from generate.neural_explanation import generate_neural_explanation, NeuralExplanationGenerator
from generate.symbolic_explanation import generate_symbolic_explanation, SymbolicSolver
from generate.neuro_symbolic_explanation import generate_neuro_symbolic_explanation, NeuroSymbolicExplanationGenerator
from utils.validation import validate_explanation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExplanationGenerator:
    """
    Orchestrator for generating neural, symbolic, and neuro-symbolic explanations.
    
    This class coordinates the three explanation generation pipelines (T013, T014, T015)
    and handles error states, ensuring robust execution even if individual generators fail.
    """

    def __init__(self, output_dir: str = "data/explanations"):
        """
        Initialize the ExplanationGenerator.
        
        Args:
            output_dir: Directory where explanation artifacts will be saved.
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
        logger.info(f"ExplanationGenerator initialized with output directory: {output_dir}")

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")

    def _save_artifact(self, content: str, filename: str) -> str:
        """
        Save explanation content to a file.
        
        Args:
            content: The explanation text or JSON content.
            filename: The name of the file to save.
        
        Returns:
            The full path to the saved file.
        """
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved artifact: {filepath}")
        return filepath

    def generate_all(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate all three types of explanations for a given problem.
        
        This is the main orchestrator method that:
        1. Calls the symbolic explanation generator (T013)
        2. Calls the neural explanation generator (T014)
        3. Calls the neuro-symbolic explanation generator (T015)
        4. Handles errors from each generator without failing the entire process
        5. Returns a dictionary with all generated explanations and their statuses
        
        Args:
            problem_data: A dictionary containing problem information (problem_id, 
                         question_text, expected_answer, etc.)
        
        Returns:
            A dictionary with keys:
                - 'symbolic': {'status': 'success'|'error', 'content': str, 'path': str}
                - 'neural': {'status': 'success'|'error', 'content': str, 'path': str}
                - 'neuro_symbolic': {'status': 'success'|'error', 'content': str, 'path': str}
                - 'problem_id': str
                - 'generation_time': float (seconds)
        """
        start_time = time.time()
        problem_id = problem_data.get('problem_id', 'unknown')
        logger.info(f"Starting explanation generation for problem: {problem_id}")
        
        results = {
            'problem_id': problem_id,
            'symbolic': {'status': 'error', 'content': None, 'path': None, 'error': None},
            'neural': {'status': 'error', 'content': None, 'path': None, 'error': None},
            'neuro_symbolic': {'status': 'error', 'content': None, 'path': None, 'error': None},
            'generation_time': 0.0
        }

        # 1. Generate Symbolic Explanation (T013)
        try:
            logger.info(f"Generating symbolic explanation for {problem_id}")
            symbolic_content, symbolic_trace = generate_symbolic_explanation(problem_data)
            
            # Validate the symbolic explanation
            if not validate_explanation(symbolic_content, 'symbolic'):
                logger.warning(f"Symbolic explanation validation failed for {problem_id}")
                results['symbolic']['error'] = "Validation failed"
            else:
                filename = f"explanation_symbolic_{problem_id}.txt"
                filepath = self._save_artifact(symbolic_content, filename)
                results['symbolic'] = {
                    'status': 'success',
                    'content': symbolic_content,
                    'path': filepath,
                    'trace': symbolic_trace
                }
                logger.info(f"Symbolic explanation generated successfully for {problem_id}")
        
        except Exception as e:
            error_msg = f"Symbolic generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['symbolic']['error'] = error_msg

        # 2. Generate Neural Explanation (T014)
        try:
            logger.info(f"Generating neural explanation for {problem_id}")
            neural_content = generate_neural_explanation(problem_data)
            
            # Validate the neural explanation
            if not validate_explanation(neural_content, 'neural'):
                logger.warning(f"Neural explanation validation failed for {problem_id}")
                results['neural']['error'] = "Validation failed"
            else:
                filename = f"explanation_neural_{problem_id}.txt"
                filepath = self._save_artifact(neural_content, filename)
                results['neural'] = {
                    'status': 'success',
                    'content': neural_content,
                    'path': filepath
                }
                logger.info(f"Neural explanation generated successfully for {problem_id}")
        
        except Exception as e:
            error_msg = f"Neural generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['neural']['error'] = error_msg

        # 3. Generate Neuro-Symbolic Explanation (T015)
        try:
            logger.info(f"Generating neuro-symbolic explanation for {problem_id}")
            neuro_symbolic_content = generate_neuro_symbolic_explanation(problem_data)
            
            # Validate the neuro-symbolic explanation
            if not validate_explanation(neuro_symbolic_content, 'neuro_symbolic'):
                logger.warning(f"Neuro-symbolic explanation validation failed for {problem_id}")
                results['neuro_symbolic']['error'] = "Validation failed"
            else:
                filename = f"explanation_neuro_symbolic_{problem_id}.txt"
                filepath = self._save_artifact(neuro_symbolic_content, filename)
                results['neuro_symbolic'] = {
                    'status': 'success',
                    'content': neuro_symbolic_content,
                    'path': filepath
                }
                logger.info(f"Neuro-symbolic explanation generated successfully for {problem_id}")
        
        except Exception as e:
            error_msg = f"Neuro-symbolic generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['neuro_symbolic']['error'] = error_msg

        # Calculate total generation time
        results['generation_time'] = time.time() - start_time
        
        # Log summary
        success_count = sum(1 for k in ['symbolic', 'neural', 'neuro_symbolic'] 
                          if results[k]['status'] == 'success')
        logger.info(f"Completed explanation generation for {problem_id}: {success_count}/3 successful")
        
        return results

    def generate_batch(self, problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate explanations for a batch of problems.
        
        Args:
            problems: List of problem dictionaries.
        
        Returns:
            List of result dictionaries (one per problem).
        """
        logger.info(f"Starting batch generation for {len(problems)} problems")
        results = []
        
        for i, problem_data in enumerate(problems):
            logger.info(f"Processing problem {i+1}/{len(problems)}")
            result = self.generate_all(problem_data)
            results.append(result)
            
            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i+1}/{len(problems)} problems")
        
        return results


def main():
    """
    Main entry point for running the explanation generator.
    
    This function:
    1. Loads problem data from a JSON file (or uses a sample if none provided)
    2. Initializes the ExplanationGenerator
    3. Generates explanations for all problems
    4. Saves a summary report to data/explanations/generation_summary.json
    
    Usage:
        python -m code.generate.explanation_generator [--input data/problems.json]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate explanations for problems')
    parser.add_argument('--input', type=str, default='data/problems.json',
                      help='Path to JSON file containing problems')
    parser.add_argument('--output-dir', type=str, default='data/explanations',
                      help='Output directory for explanation artifacts')
    args = parser.parse_args()

    # Load problems
    problems = []
    if os.path.exists(args.input):
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
                problems = data.get('problems', []) if isinstance(data, dict) else data
            logger.info(f"Loaded {len(problems)} problems from {args.input}")
        except Exception as e:
            logger.error(f"Failed to load problems from {args.input}: {e}")
            # Fallback to a minimal sample problem if file loading fails
            logger.warning("Using a sample problem for demonstration")
            problems = [{
                'problem_id': 'sample_001',
                'question_text': 'Solve: 3 + 5 * 2',
                'expected_answer': '13',
                'problem_type': 'arithmetic',
                'difficulty': 'medium'
            }]
    else:
        logger.warning(f"Input file {args.input} not found. Using sample problem.")
        problems = [{
            'problem_id': 'sample_001',
            'question_text': 'Solve: 3 + 5 * 2',
            'expected_answer': '13',
            'problem_type': 'arithmetic',
            'difficulty': 'medium'
        }]

    # Initialize generator
    generator = ExplanationGenerator(output_dir=args.output_dir)
    
    # Generate explanations
    results = generator.generate_batch(problems)
    
    # Save summary report
    summary_path = os.path.join(args.output_dir, 'generation_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_problems': len(problems),
            'successful_generations': sum(1 for r in results 
                                        if r['symbolic']['status'] == 'success' and 
                                           r['neural']['status'] == 'success' and 
                                           r['neuro_symbolic']['status'] == 'success'),
            'results': results
        }, f, indent=2)
    
    logger.info(f"Summary report saved to {summary_path}")
    return results


if __name__ == '__main__':
    main()