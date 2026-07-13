import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from generate.symbolic_explanation import generate_symbolic_explanation
from generate.neural_explanation import generate_neural_explanation
from generate.neuro_symbolic_explanation import generate_neuro_symbolic_explanation
from utils.validation import validate_explanation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExplanationGenerator:
    """
    Orchestrates the generation of three explanation types:
    1. Symbolic (Rule-based)
    2. Neural (LLM-based)
    3. Neuro-Symbolic (Hybrid)

    Handles error states, logging, and validation for each generation step.
    """

    def __init__(self, output_dir: str = "data/explanations"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"ExplanationGenerator initialized. Output dir: {self.output_dir}")

    def _save_explanation(self, problem_id: str, explanation_type: str, content: str, metadata: Optional[Dict] = None):
        """
        Saves an explanation to a JSON file in the output directory.
        File naming convention: explanation_{problem_id}_{type}.json
        """
        filename = f"explanation_{problem_id}_{explanation_type}.json"
        filepath = os.path.join(self.output_dir, filename)

        record = {
            "problem_id": problem_id,
            "type": explanation_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "content": content,
            "metadata": metadata or {}
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record, f, indent=2)
            logger.info(f"Saved {explanation_type} explanation for problem {problem_id} to {filepath}")
            return True
        except IOError as e:
            logger.error(f"Failed to write explanation file {filepath}: {e}")
            return False

    def generate_symbolic(self, problem_data: Dict[str, Any], problem_id: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Generates a symbolic explanation using the rule-based engine.
        Returns (success, content, metadata)
        """
        logger.info(f"Generating symbolic explanation for problem {problem_id}...")
        start_time = time.time()
        try:
            content, metadata = generate_symbolic_explanation(problem_data)
            duration = time.time() - start_time
            metadata['generation_time_seconds'] = duration
            
            # Validate content
            if not content or len(content.strip()) == 0:
                logger.error(f"Symbolic generator returned empty content for {problem_id}")
                return False, None, metadata

            # Optional: validate against schema if needed
            # is_valid = validate_explanation(content, "symbolic")
            
            self._save_explanation(problem_id, "symbolic", content, metadata)
            return True, content, metadata
        except Exception as e:
            logger.exception(f"Symbolic generation failed for {problem_id}: {e}")
            return False, None, {"error": str(e)}

    def generate_neural(self, problem_data: Dict[str, Any], problem_id: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Generates a neural explanation using the LLM.
        Returns (success, content, metadata)
        """
        logger.info(f"Generating neural explanation for problem {problem_id}...")
        start_time = time.time()
        try:
            content, metadata = generate_neural_explanation(problem_data)
            duration = time.time() - start_time
            metadata['generation_time_seconds'] = duration

            if not content or len(content.strip()) == 0:
                logger.error(f"Neural generator returned empty content for {problem_id}")
                return False, None, metadata

            self._save_explanation(problem_id, "neural", content, metadata)
            return True, content, metadata
        except Exception as e:
            logger.exception(f"Neural generation failed for {problem_id}: {e}")
            return False, None, {"error": str(e)}

    def generate_neuro_symbolic(self, problem_data: Dict[str, Any], problem_id: str, 
                                symbolic_trace: Optional[str] = None, 
                                neural_narrative: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Generates a neuro-symbolic explanation.
        Can accept pre-computed traces/narratives or generate them internally if not provided.
        Returns (success, content, metadata)
        """
        logger.info(f"Generating neuro-symbolic explanation for problem {problem_id}...")
        start_time = time.time()
        try:
            content, metadata = generate_neuro_symbolic_explanation(
                problem_data, 
                symbolic_trace=symbolic_trace, 
                neural_narrative=neural_narrative
            )
            duration = time.time() - start_time
            metadata['generation_time_seconds'] = duration

            if not content or len(content.strip()) == 0:
                logger.error(f"Neuro-symbolic generator returned empty content for {problem_id}")
                return False, None, metadata

            self._save_explanation(problem_id, "neuro_symbolic", content, metadata)
            return True, content, metadata
        except Exception as e:
            logger.exception(f"Neuro-symbolic generation failed for {problem_id}: {e}")
            return False, None, {"error": str(e)}

    def generate_all(self, problem_data: Dict[str, Any], problem_id: str) -> Dict[str, Any]:
        """
        Orchestrates the generation of all three explanation types.
        
        Strategy:
        1. Generate Symbolic first (as it is the ground truth structure).
        2. Generate Neural independently.
        3. Generate Neuro-Symbolic, optionally passing the generated symbolic trace 
           to ensure the narrative is grounded in the rules.
        
        Returns a summary report of the execution.
        """
        logger.info(f"--- Starting full generation pipeline for problem {problem_id} ---")
        results = {
            "problem_id": problem_id,
            "status": "in_progress",
            "symbolic": {"success": False, "error": None},
            "neural": {"success": False, "error": None},
            "neuro_symbolic": {"success": False, "error": None}
        }

        # 1. Symbolic Generation
        sym_success, sym_content, sym_meta = self.generate_symbolic(problem_data, problem_id)
        results["symbolic"]["success"] = sym_success
        results["symbolic"]["error"] = None if sym_success else "Generation failed"
        
        # 2. Neural Generation
        neu_success, neu_content, neu_meta = self.generate_neural(problem_data, problem_id)
        results["neural"]["success"] = neu_success
        results["neural"]["error"] = None if neu_success else "Generation failed"

        # 3. Neuro-Symbolic Generation
        # Pass the generated symbolic trace to ensure grounding, even if symbolic failed 
        # (it will be None, allowing the generator to handle fallback or error)
        ns_success, ns_content, ns_meta = self.generate_neuro_symbolic(
            problem_data, 
            problem_id, 
            symbolic_trace=sym_content if sym_success else None,
            neural_narrative=neu_content if neu_success else None
        )
        results["neuro_symbolic"]["success"] = ns_success
        results["neuro_symbolic"]["error"] = None if ns_success else "Generation failed"

        # Summary
        success_count = sum([sym_success, neu_success, ns_success])
        total_count = 3
        
        if success_count == total_count:
            results["status"] = "complete"
            logger.info(f"--- Pipeline complete for {problem_id}: {success_count}/{total_count} successful ---")
        else:
            results["status"] = "partial"
            logger.warning(f"--- Pipeline partial for {problem_id}: {success_count}/{total_count} successful ---")

        return results

def main():
    """
    CLI entry point for running the explanation generator on a specific problem.
    Usage: python -m generate.explanation_generator --problem_id <id> [--data <json_path>]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Orchestrate explanation generation")
    parser.add_argument("--problem_id", type=str, required=True, help="ID of the problem to process")
    parser.add_argument("--data", type=str, default=None, help="Path to JSON file containing problem data. If None, generates synthetic test data.")
    parser.add_argument("--output_dir", type=str, default="data/explanations", help="Output directory for artifacts")
    
    args = parser.parse_args()

    # Load or create problem data
    if args.data and os.path.exists(args.data):
        logger.info(f"Loading problem data from {args.data}")
        with open(args.data, 'r', encoding='utf-8') as f:
            problem_data = json.load(f)
    else:
        logger.warning("No valid data file provided. Generating synthetic test data.")
        # Synthetic fallback for demonstration/CI if real data is missing
        problem_data = {
            "question": "If 3x + 5 = 20, what is x?",
            "type": "algebra",
            "difficulty": "medium",
            "context": "Linear equation solving"
        }

    generator = ExplanationGenerator(output_dir=args.output_dir)
    results = generator.generate_all(problem_data, args.problem_id)

    # Print summary to stdout
    print(json.dumps(results, indent=2))

    # Return exit code 1 if no explanations were generated
    if not any([results["symbolic"]["success"], results["neural"]["success"], results["neuro_symbolic"]["success"]]):
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()