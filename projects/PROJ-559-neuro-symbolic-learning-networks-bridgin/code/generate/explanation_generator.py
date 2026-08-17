"""
Explanation Generator Orchestrator.

Orchestrates the generation of neural, symbolic, and neuro-symbolic explanations
for a given problem. Includes validation to ensure neural and symbolic outputs
are distinct (similarity <= 0.95) as per FR-002.
"""
import os
import sys
import json
import logging
import argparse
import time
from typing import Dict, Any, List, Optional, Tuple

# Import generators from sibling modules
from generate.neural_explanation import generate_neural_explanation
from generate.symbolic_explanation import generate_symbolic_explanation
from generate.neuro_symbolic_explanation import generate_neuro_symbolic_explanation
from generate.validate_distinctness import validate_distinctness, calculate_jaccard_similarity

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExplanationGenerator:
    """
    Orchestrator for generating and validating explanation artifacts.
    """

    def __init__(self, output_dir: str = "data/derived"):
        self.output_dir = output_dir
        self.similarity_threshold = 0.95
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_problem_context(self, problem_id: str, problem_type: str) -> Dict[str, Any]:
        """
        Constructs a problem context dictionary.
        In a real scenario, this might fetch from a database or file.
        For this implementation, we construct a representative context based on ID/Type.
        """
        # Placeholder logic to create a problem object that the generators can consume
        # The symbolic generator expects specific structures for rules
        context = {
            "problem_id": problem_id,
            "type": problem_type,
            "statement": f"Problem {problem_id}: Solve the {problem_type} equation.",
            "variables": ["x", "y"],
            "constraints": []
        }
        
        if problem_type == "algebra":
            context["equation"] = "2x + 3 = 11"
            context["solution"] = "x = 4"
        elif problem_type == "geometry":
            context["shape"] = "triangle"
            context["properties"] = {"sides": 3, "angles_sum": 180}
        else:
            context["equation"] = f"Unknown {problem_type} problem"
            context["solution"] = "N/A"
        
        return context

    def generate_all(self, problem_id: str, problem_type: str = "algebra") -> Dict[str, str]:
        """
        Generates neural, symbolic, and neuro-symbolic explanations.
        Validates distinctness between neural and symbolic outputs.
        
        Args:
            problem_id: Unique identifier for the problem.
            problem_type: Type of problem (e.g., 'algebra', 'geometry').
        
        Returns:
            Dict containing paths to generated files.
        
        Raises:
            SystemExit: If neural and symbolic explanations are too similar (> 0.95).
        """
        logger.info(f"Starting generation for Problem ID: {problem_id}, Type: {problem_type}")
        context = self._get_problem_context(problem_id, problem_type)
        
        # 1. Generate Symbolic Explanation
        logger.info("Generating symbolic explanation...")
        try:
            symbolic_result = generate_symbolic_explanation(context)
            symbolic_text = symbolic_result.get("explanation", "No symbolic explanation generated.")
        except Exception as e:
            logger.error(f"Symbolic generation failed: {e}")
            symbolic_text = f"ERROR: Symbolic generation failed - {e}"
        
        # 2. Generate Neural Explanation
        logger.info("Generating neural explanation...")
        try:
            neural_result = generate_neural_explanation(context)
            neural_text = neural_result.get("explanation", "No neural explanation generated.")
        except Exception as e:
            logger.error(f"Neural generation failed: {e}")
            neural_text = f"ERROR: Neural generation failed - {e}"

        # 3. Validate Distinctness (FR-002)
        logger.info("Validating distinctness between neural and symbolic explanations...")
        is_distinct, similarity_score = validate_distinctness(neural_text, symbolic_text)
        
        if not is_distinct:
            logger.error(f"Distinctness check FAILED. Similarity score: {similarity_score:.4f} (Threshold: {self.similarity_threshold})")
            logger.error("Neural and Symbolic explanations are too similar. Aborting per FR-002.")
            # Write error report
            error_report = {
                "problem_id": problem_id,
                "status": "FAILED_DISTINCTNESS",
                "similarity_score": similarity_score,
                "threshold": self.similarity_threshold,
                "message": "Neural and Symbolic outputs are identical or too similar."
            }
            report_path = os.path.join(self.output_dir, f"distinctness_error_{problem_id}.json")
            with open(report_path, 'w') as f:
                json.dump(error_report, f, indent=2)
            sys.exit(1)
        
        logger.info(f"Distinctness check PASSED. Similarity score: {similarity_score:.4f}")

        # 4. Generate Neuro-Symbolic Explanation
        logger.info("Generating neuro-symbolic explanation...")
        try:
            neuro_symbolic_result = generate_neuro_symbolic_explanation(context, symbolic_result, neural_result)
            neuro_symbolic_text = neuro_symbolic_result.get("explanation", "No neuro-symbolic explanation generated.")
        except Exception as e:
            logger.error(f"Neuro-symbolic generation failed: {e}")
            neuro_symbolic_text = f"ERROR: Neuro-symbolic generation failed - {e}"

        # 5. Save Artifacts
        logger.info("Saving artifacts...")
        files = {}
        
        # Save Neural
        neural_path = os.path.join(self.output_dir, "explanation_neural.txt")
        with open(neural_path, 'w') as f:
            f.write(neural_text)
        files['neural'] = neural_path

        # Save Symbolic
        symbolic_path = os.path.join(self.output_dir, "explanation_symbolic.txt")
        with open(symbolic_path, 'w') as f:
            f.write(symbolic_text)
        files['symbolic'] = symbolic_path

        # Save Neuro-Symbolic
        ns_path = os.path.join(self.output_dir, "explanation_neuro_symbolic.txt")
        with open(ns_path, 'w') as f:
            f.write(neuro_symbolic_text)
        files['neuro_symbolic'] = ns_path

        # Save Metadata
        metadata = {
            "problem_id": problem_id,
            "problem_type": problem_type,
            "similarity_score": similarity_score,
            "distinctness_passed": True,
            "generated_files": files,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        meta_path = os.path.join(self.output_dir, f"generation_metadata_{problem_id}.json")
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Successfully generated explanations for {problem_id}.")
        logger.info(f"Files saved to: {self.output_dir}")
        return files

def main():
    """
    CLI entry point for the explanation generator.
    """
    parser = argparse.ArgumentParser(description="Orchestrate explanation generation.")
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/derived",
        help="Directory to save generated explanation files."
    )
    parser.add_argument(
        "--problem-id",
        type=str,
        required=True,
        help="Unique identifier for the problem to explain."
    )
    parser.add_argument(
        "--problem-type",
        type=str,
        default="algebra",
        help="Type of problem (e.g., 'algebra', 'geometry')."
    )

    args = parser.parse_args()

    try:
        generator = ExplanationGenerator(output_dir=args.output_dir)
        generator.generate_all(
            problem_id=args.problem_id,
            problem_type=args.problem_type
        )
        logger.info("Pipeline completed successfully.")
    except SystemExit as e:
        # Re-raise system exit codes (e.g., from distinctness failure)
        raise e
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()