"""
Neural Explanation Generator using a distilled CPU-tractable LLM.

Implements T014: Generates neural explanations for ASSISTments problems
using a small language model (TinyLlama-1.1B or similar) in default precision.
Designed to run within CPU constraints (≤7GB RAM) as per FR-008.

The neural explanation provides a fluent, narrative-style reasoning trace
that complements the formal symbolic trace from T013.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MAX_MODEL_SIZE_PARAMS = 1_100_000_000  # 1.1B parameters
CPU_DEVICE = "cpu"
OUTPUT_DIR = "data/explanations"
OUTPUT_FILE_TEMPLATE = "explanation_neural_{problem_id}.json"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


class NeuralExplanationGenerator:
    """
    Generates natural language explanations for math/logic problems
    using a distilled language model optimized for CPU inference.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: str = CPU_DEVICE):
        """
        Initialize the neural explanation generator.

        Args:
            model_name: Name of the HuggingFace model to use.
            device: Device to run inference on ('cpu' or 'cuda').
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None
        self._model_loaded = False

        logger.info(f"Initialized NeuralExplanationGenerator with model: {model_name}")
        logger.info(f"Target device: {device}")

    def _load_model(self) -> None:
        """
        Load the model and tokenizer. Lazy loading to conserve memory.
        Uses default precision (float32) for CPU compatibility.
        """
        if self._model_loaded:
            return

        logger.info(f"Loading model: {self.model_name} on {self.device}")
        start_time = time.time()

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # Add padding token if missing
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model in default precision (float32) for CPU
            # Using low_cpu_mem_usage=True to stay within RAM constraints
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype="auto",  # Use default precision
                low_cpu_mem_usage=True,
                device_map="auto" if self.device == "cuda" else None
            )

            # Ensure model is on correct device and in eval mode
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            self.model.eval()

            elapsed = time.time() - start_time
            logger.info(f"Model loaded successfully in {elapsed:.2f} seconds")
            self._model_loaded = True

        except ImportError as e:
            logger.error(f"Failed to import transformers: {e}")
            logger.error("Please install: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _build_prompt(self, problem_data: Dict[str, Any]) -> str:
        """
        Build a structured prompt for the neural explanation.

        Args:
            problem_data: Dictionary containing problem information.

        Returns:
            Formatted prompt string for the model.
        """
        problem_text = problem_data.get('question', problem_data.get('problem_text', ''))
        problem_id = problem_data.get('problem_id', 'unknown')
        subject = problem_data.get('subject', 'math')

        prompt = f"""You are an educational AI assistant. Provide a clear, step-by-step explanation for solving the following {subject} problem.

Problem ID: {problem_id}
Problem: {problem_text}

Instructions:
1. Break down the problem into logical steps.
2. Explain the reasoning behind each step in natural language.
3. Keep the explanation concise but thorough.
4. Use simple language suitable for a student learning the concept.

Provide your explanation below:
"""
        return prompt

    def generate_explanation(
        self,
        problem_data: Dict[str, Any],
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        do_sample: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a neural explanation for a given problem.

        Args:
            problem_data: Dictionary containing problem information.
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature (0.0 = greedy, >0.0 = sampling).
            do_sample: Whether to use sampling for generation.

        Returns:
            Dictionary containing:
            - problem_id: The problem identifier
            - explanation_text: The generated neural explanation
            - model_name: The model used
            - generation_time: Time taken for generation
            - token_count: Number of tokens generated
        """
        if not self._model_loaded:
            self._load_model()

        problem_id = problem_data.get('problem_id', 'unknown')
        logger.info(f"Generating neural explanation for problem: {problem_id}")

        start_time = time.time()

        try:
            # Build prompt
            prompt = self._build_prompt(problem_data)

            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=1024
            )

            # Move to device
            if self.device == "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    top_p=0.95,  # Nucleus sampling
                    top_k=50,    # Top-k sampling
                    repetition_penalty=1.1
                )

            # Decode
            full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract just the generated part (remove prompt)
            explanation_text = full_text[len(prompt):].strip()

            generation_time = time.time() - start_time
            token_count = len(outputs[0]) - len(inputs['input_ids'][0])

            logger.info(f"Generated explanation in {generation_time:.2f}s ({token_count} tokens)")

            return {
                'problem_id': problem_id,
                'explanation_text': explanation_text,
                'model_name': self.model_name,
                'generation_time': generation_time,
                'token_count': token_count,
                'device': self.device,
                'parameters': {
                    'max_new_tokens': max_new_tokens,
                    'temperature': temperature,
                    'do_sample': do_sample
                }
            }

        except Exception as e:
            logger.error(f"Error generating explanation for {problem_id}: {e}")
            raise

    def save_explanation(self, explanation_data: Dict[str, Any], output_dir: Optional[str] = None) -> str:
        """
        Save the generated explanation to a JSON file.

        Args:
            explanation_data: Dictionary containing the explanation data.
            output_dir: Directory to save the file (default: OUTPUT_DIR).

        Returns:
            Path to the saved file.
        """
        if output_dir is None:
            output_dir = OUTPUT_DIR

        os.makedirs(output_dir, exist_ok=True)

        problem_id = explanation_data.get('problem_id', 'unknown')
        filename = OUTPUT_FILE_TEMPLATE.format(problem_id=problem_id)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(explanation_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved neural explanation to: {filepath}")
        return filepath


def generate_neural_explanation(
    problem_data: Dict[str, Any],
    model_name: str = DEFAULT_MODEL_NAME,
    output_dir: str = OUTPUT_DIR
) -> Dict[str, Any]:
    """
    Convenience function to generate and save a neural explanation.

    Args:
        problem_data: Dictionary containing problem information.
        model_name: Name of the model to use.
        output_dir: Directory to save the explanation file.

    Returns:
        Dictionary containing the generated explanation data.
    """
    generator = NeuralExplanationGenerator(model_name=model_name)
    explanation_data = generator.generate_explanation(problem_data)
    generator.save_explanation(explanation_data, output_dir)
    return explanation_data


def main():
    """
    Main entry point for standalone execution.
    Demonstrates neural explanation generation on sample problems.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Generate neural explanations for problems')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL_NAME,
                        help='HuggingFace model name')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                        help='Output directory for explanations')
    parser.add_argument('--sample', action='store_true',
                        help='Run on sample problems instead of loading from file')
    parser.add_argument('--input-file', type=str,
                        help='Path to JSON file containing problem data')

    args = parser.parse_args()

    # Sample problems for demonstration
    sample_problems = [
        {
            'problem_id': 'sample_001',
            'question': 'If 3x + 5 = 20, what is the value of x?',
            'subject': 'algebra'
        },
        {
            'problem_id': 'sample_002',
            'question': 'Simplify: 2(a + 3) - 4',
            'subject': 'algebra'
        },
        {
            'problem_id': 'sample_003',
            'question': 'What is 15% of 80?',
            'subject': 'arithmetic'
        }
    ]

    generator = NeuralExplanationGenerator(model_name=args.model)

    if args.sample:
        problems_to_process = sample_problems
    elif args.input_file:
        if not os.path.exists(args.input_file):
            logger.error(f"Input file not found: {args.input_file}")
            sys.exit(1)
        with open(args.input_file, 'r', encoding='utf-8') as f:
            problems_to_process = json.load(f)
        if not isinstance(problems_to_process, list):
            problems_to_process = [problems_to_process]
    else:
        logger.error("Please provide --sample or --input-file")
        sys.exit(1)

    logger.info(f"Processing {len(problems_to_process)} problems")

    results = []
    for problem in problems_to_process:
        try:
            result = generator.generate_explanation(problem)
            generator.save_explanation(result, args.output_dir)
            results.append(result)
            logger.info(f"Completed: {problem.get('problem_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to generate explanation for {problem.get('problem_id', 'unknown')}: {e}")
            results.append({
                'problem_id': problem.get('problem_id', 'unknown'),
                'error': str(e)
            })

    # Save summary
    summary_path = os.path.join(args.output_dir, 'neural_explanation_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_processed': len(problems_to_process),
            'successful': len([r for r in results if 'error' not in r]),
            'failed': len([r for r in results if 'error' in r]),
            'results': results
        }, f, indent=2)

    logger.info(f"Summary saved to: {summary_path}")


if __name__ == '__main__':
    main()