"""
Explanation Generator Orchestrator with File I/O and Artifact Naming.

This module orchestrates the generation of three distinct explanation types
(neural, symbolic, neuro-symbolic) for a given problem and saves them to disk
with standardized naming conventions.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

# Import existing generators from sibling modules
from generate.neural_explanation import generate_neural_explanation, NeuralExplanationGenerator
from generate.symbolic_explanation import generate_symbolic_explanation, SymbolicSolver
from generate.neuro_symbolic_explanation import generate_neuro_symbolic_explanation, NeuroSymbolicExplanationGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExplanationGenerator:
    """
    Orchestrates the generation of neural, symbolic, and neuro-symbolic explanations.
    Handles file I/O and artifact naming for all generated outputs.
    """

    def __init__(self, output_dir: str = "data/explanations"):
        """
        Initialize the ExplanationGenerator.

        Args:
            output_dir: Directory where explanation artifacts will be saved.
        """
        self.output_dir = output_dir
        self._ensure_output_dirs()

    def _ensure_output_dirs(self) -> None:
        """Create output directories if they do not exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Created output directory: {self.output_dir}")

    def _get_artifact_path(self, problem_id: str, explanation_type: str, extension: str) -> str:
        """
        Generate the full file path for an explanation artifact.

        Args:
            problem_id: Unique identifier for the problem.
            explanation_type: Type of explanation ('neural', 'symbolic', 'neuro_symbolic').
            extension: File extension (e.g., '.txt', '.json').

        Returns:
            Full path to the artifact file.
        """
        # Sanitize problem_id to ensure valid filename
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in problem_id)
        filename = f"explanation_{explanation_type}_{safe_id}{extension}"
        return os.path.join(self.output_dir, filename)

    def generate_all(
        self,
        problem_data: Dict[str, Any],
        problem_id: str,
        save_artifacts: bool = True
    ) -> Dict[str, str]:
        """
        Generate all three explanation types for a given problem.

        Args:
            problem_data: Dictionary containing problem details (stem, type, answer, etc.).
            problem_id: Unique identifier for the problem.
            save_artifacts: If True, save generated explanations to disk.

        Returns:
            Dictionary mapping explanation type to file path (or None if not saved).
        """
        logger.info(f"Starting explanation generation for problem: {problem_id}")
        start_time = time.time()

        results = {}

        # 1. Generate Symbolic Explanation
        logger.info(f"Generating symbolic explanation for {problem_id}")
        try:
            symbolic_result = generate_symbolic_explanation(problem_data)
            if save_artifacts:
                path = self._save_symbolic_explanation(symbolic_result, problem_id)
                results['symbolic'] = path
                logger.info(f"Saved symbolic explanation to: {path}")
            else:
                results['symbolic'] = None
        except Exception as e:
            logger.error(f"Failed to generate symbolic explanation: {e}")
            results['symbolic'] = None

        # 2. Generate Neural Explanation
        logger.info(f"Generating neural explanation for {problem_id}")
        try:
            neural_result = generate_neural_explanation(problem_data)
            if save_artifacts:
                path = self._save_neural_explanation(neural_result, problem_id)
                results['neural'] = path
                logger.info(f"Saved neural explanation to: {path}")
            else:
                results['neural'] = None
        except Exception as e:
            logger.error(f"Failed to generate neural explanation: {e}")
            results['neural'] = None

        # 3. Generate Neuro-Symbolic Explanation
        logger.info(f"Generating neuro-symbolic explanation for {problem_id}")
        try:
            neuro_symbolic_result = generate_neuro_symbolic_explanation(
                problem_data,
                symbolic_result.get('trace') if symbolic_result else None,
                neural_result.get('narrative') if neural_result else None
            )
            if save_artifacts:
                path = self._save_neuro_symbolic_explanation(neuro_symbolic_result, problem_id)
                results['neuro_symbolic'] = path
                logger.info(f"Saved neuro-symbolic explanation to: {path}")
            else:
                results['neuro_symbolic'] = None
        except Exception as e:
            logger.error(f"Failed to generate neuro-symbolic explanation: {e}")
            results['neuro_symbolic'] = None

        elapsed = time.time() - start_time
        logger.info(f"Completed generation for {problem_id} in {elapsed:.2f}s")

        return results

    def _save_symbolic_explanation(self, result: Dict[str, Any], problem_id: str) -> str:
        """
        Save the symbolic explanation trace to a JSON file.

        Args:
            result: Dictionary containing the symbolic trace and metadata.
            problem_id: Unique identifier for the problem.

        Returns:
            Path to the saved file.
        """
        path = self._get_artifact_path(problem_id, "symbolic", ".json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return path

    def _save_neural_explanation(self, result: Dict[str, Any], problem_id: str) -> str:
        """
        Save the neural explanation narrative to a text file.

        Args:
            result: Dictionary containing the neural narrative and metadata.
            problem_id: Unique identifier for the problem.

        Returns:
            Path to the saved file.
        """
        path = self._get_artifact_path(problem_id, "neural", ".txt")
        narrative = result.get('narrative', 'No narrative generated.')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(narrative)
        return path

    def _save_neuro_symbolic_explanation(self, result: Dict[str, Any], problem_id: str) -> str:
        """
        Save the neuro-symbolic explanation to a text file.

        Args:
            result: Dictionary containing the combined explanation and metadata.
            problem_id: Unique identifier for the problem.

        Returns:
            Path to the saved file.
        """
        path = self._get_artifact_path(problem_id, "neuro_symbolic", ".txt")
        explanation_text = result.get('explanation', 'No explanation generated.')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(explanation_text)
        return path

    def run_batch(
        self,
        problems: List[Dict[str, Any]],
        save_artifacts: bool = True
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate explanations for a batch of problems.

        Args:
            problems: List of problem dictionaries.
            save_artifacts: If True, save generated explanations to disk.

        Returns:
            Dictionary mapping problem_id to generation results.
        """
        all_results = {}
        for problem in problems:
            pid = problem.get('problem_id', 'unknown')
            try:
                results = self.generate_all(problem, pid, save_artifacts)
                all_results[pid] = results
            except Exception as e:
                logger.error(f"Batch processing failed for {pid}: {e}")
                all_results[pid] = {'error': str(e)}
        return all_results


def main():
    """
    Main entry point for running the explanation generator.
    Demonstrates usage with a sample problem if no arguments are provided.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate neuro-symbolic explanations")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/explanations",
        help="Directory to save generated explanations"
    )
    parser.add_argument(
        "--problem-id",
        type=str,
        default="sample_problem_001",
        help="ID of the problem to generate explanations for"
    )
    parser.add_argument(
        "--problem-type",
        type=str,
        default="algebra",
        help="Type of problem (e.g., algebra, geometry)"
    )
    args = parser.parse_args()

    # Create a sample problem for demonstration if running standalone
    sample_problem = {
        "problem_id": args.problem_id,
        "problem_type": args.problem_type,
        "stem": "Solve for x: 2x + 5 = 15",
        "answer": "5",
        "steps": [
            "Subtract 5 from both sides: 2x = 10",
            "Divide by 2: x = 5"
        ],
        "metadata": {
            "difficulty": "easy",
            "topic": "linear_equations"
        }
    }

    generator = ExplanationGenerator(output_dir=args.output_dir)
    results = generator.generate_all(sample_problem, sample_problem["problem_id"])

    print("\nGenerated Artifacts:")
    for exp_type, path in results.items():
        if path:
            print(f"  {exp_type}: {path}")
        else:
            print(f"  {exp_type}: FAILED")

    # Verify files exist
    success = True
    for exp_type, path in results.items():
        if path and not os.path.exists(path):
            logger.error(f"Artifact missing: {path}")
            success = False

    if success:
        print("\nAll artifacts successfully generated and saved.")
        sys.exit(0)
    else:
        print("\nSome artifacts failed to generate.")
        sys.exit(1)


if __name__ == "__main__":
    main()