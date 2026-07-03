"""
Explanation Generator Orchestrator
Orchestrates the generation of neural, symbolic, and neuro-symbolic explanations
and handles file I/O for artifact storage.
"""
import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

# Import existing generators from sibling modules
from generate.neural_explanation import generate_neural_explanation
from generate.symbolic_explanation import generate_symbolic_explanation
from generate.neuro_symbolic_explanation import generate_neuro_symbolic_explanation
from utils.validation import validate_explanation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExplanationGenerator:
    """
    Orchestrates explanation generation and manages artifact storage.
    """

    def __init__(self, output_dir: str = "data/explanations"):
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)

    def _sanitize_filename(self, problem_id: str) -> str:
        """Sanitize problem ID for use in filenames."""
        # Replace common problematic characters
        return problem_id.replace("/", "_").replace("\\", "_").replace(":", "_")

    def _save_artifact(self, problem_id: str, artifact_type: str, content: Any):
        """
        Save an explanation artifact to disk.

        Args:
            problem_id: The ID of the problem this explanation addresses
            artifact_type: One of 'neural', 'symbolic', 'neuro_symbolic'
            content: The explanation content (dict or string)
        """
        sanitized_id = self._sanitize_filename(problem_id)

        if artifact_type == 'neural':
            filename = f"explanation_neural_{sanitized_id}.txt"
            # Neural explanations are typically text strings
            if isinstance(content, dict):
                content = content.get('explanation', str(content))
        elif artifact_type == 'symbolic':
            filename = f"explanation_symbolic_{sanitized_id}.txt"
            # Symbolic explanations include the trace
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
        elif artifact_type == 'neuro_symbolic':
            filename = f"explanation_neuro_symbolic_{sanitized_id}.txt"
            # Neuro-symbolic explanations combine both
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
        else:
            raise ValueError(f"Unknown artifact type: {artifact_type}")

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(content))
            logger.info(f"Saved {artifact_type} explanation to {filepath}")
        except IOError as e:
            logger.error(f"Failed to save {artifact_type} explanation to {filepath}: {e}")
            raise

    def generate_all(
        self,
        problem_data: Dict[str, Any],
        problem_id: str,
        validate: bool = True
    ) -> Dict[str, str]:
        """
        Generate all three types of explanations for a given problem and save them.

        Args:
            problem_data: Dictionary containing problem details (question, answer, etc.)
            problem_id: Unique identifier for the problem
            validate: Whether to validate explanations against schema

        Returns:
            Dictionary mapping artifact types to their file paths
        """
        start_time = time.time()
        results = {}

        logger.info(f"Starting explanation generation for problem: {problem_id}")

        try:
            # Generate Neural Explanation
            logger.info("Generating neural explanation...")
            neural_content = generate_neural_explanation(problem_data)
            if validate:
                validate_explanation(neural_content, "neural")
            self._save_artifact(problem_id, 'neural', neural_content)
            results['neural'] = os.path.join(
                self.output_dir,
                f"explanation_neural_{self._sanitize_filename(problem_id)}.txt"
            )

            # Generate Symbolic Explanation
            logger.info("Generating symbolic explanation...")
            symbolic_content = generate_symbolic_explanation(problem_data)
            if validate:
                validate_explanation(symbolic_content, "symbolic")
            self._save_artifact(problem_id, 'symbolic', symbolic_content)
            results['symbolic'] = os.path.join(
                self.output_dir,
                f"explanation_symbolic_{self._sanitize_filename(problem_id)}.txt"
            )

            # Generate Neuro-Symbolic Explanation
            logger.info("Generating neuro-symbolic explanation...")
            neuro_symbolic_content = generate_neuro_symbolic_explanation(
                problem_data,
                neural_content,
                symbolic_content
            )
            if validate:
                validate_explanation(neuro_symbolic_content, "neuro_symbolic")
            self._save_artifact(problem_id, 'neuro_symbolic', neuro_symbolic_content)
            results['neuro_symbolic'] = os.path.join(
                self.output_dir,
                f"explanation_neuro_symbolic_{self._sanitize_filename(problem_id)}.txt"
            )

            elapsed = time.time() - start_time
            logger.info(f"Successfully generated all explanations in {elapsed:.2f}s")

            return results

        except Exception as e:
            logger.error(f"Error during explanation generation: {e}")
            raise

    def generate_batch(
        self,
        problems: List[Dict[str, Any]],
        validate: bool = True
    ) -> Dict[str, List[str]]:
        """
        Generate explanations for a batch of problems.

        Args:
            problems: List of problem dictionaries
            validate: Whether to validate explanations

        Returns:
            Dictionary mapping problem IDs to lists of generated file paths
        """
        batch_results = {}

        for problem in problems:
            problem_id = problem.get('problem_id', problem.get('id', 'unknown'))
            try:
                results = self.generate_all(problem, problem_id, validate)
                batch_results[problem_id] = list(results.values())
            except Exception as e:
                logger.error(f"Failed to generate explanations for problem {problem_id}: {e}")
                batch_results[problem_id] = []

        return batch_results


def main():
    """
    Main entry point for running the explanation generator.
    Demonstrates usage with a sample problem from the ASSISTments dataset.
    """
    # Check if we have data from the fetcher
    data_file = "data/raw/assistments_sample.csv"
    if not os.path.exists(data_file):
        # Try to fetch data first
        logger.info("No raw data found. Attempting to fetch ASSISTments dataset...")
        from download.fetch_assistments import fetch_assistments_dataset
        try:
            fetch_assistments_dataset()
        except Exception as e:
            logger.error(f"Failed to fetch dataset: {e}")
            sys.exit(1)

    # Load sample data
    try:
        import pandas as pd
        df = pd.read_csv(data_file)

        # Use first row as sample problem
        sample_row = df.iloc[0]
        problem_data = {
            'problem_id': str(sample_row.get('problem_id', 'sample_001')),
            'question': str(sample_row.get('question', 'What is 2+2?')),
            'answer': str(sample_row.get('answer', '4')),
            'subject': str(sample_row.get('subject', 'math')),
            'grade_level': str(sample_row.get('grade_level', 'K-12'))
        }

        logger.info(f"Processing problem: {problem_data['problem_id']}")

        # Initialize generator
        generator = ExplanationGenerator(output_dir="data/explanations")

        # Generate all explanations
        results = generator.generate_all(problem_data, problem_data['problem_id'])

        # Print results
        print("\n=== Explanation Generation Complete ===")
        for artifact_type, filepath in results.items():
            print(f"{artifact_type.upper()}: {filepath}")

    except FileNotFoundError:
        logger.error("Could not find data file. Ensure data has been fetched.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()