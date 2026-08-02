"""
Inference runner for User Story 3.
Uses llama.cpp in CPU mode with Q4_K_M quantization.
Implements retry logic for transient failures.
"""
import subprocess
import json
import time
import os
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class InferenceRunner:
    """Handles CPU-only inference via llama.cpp with retry logic."""

    def __init__(
        self,
        model_path: str,
        max_tokens: int = 512,
        threads: int = 4,
        retry_count: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 300
    ):
        """
        Initialize the inference runner.

        Args:
            model_path: Path to the Q4_K_M quantized model file.
            max_tokens: Maximum number of tokens to generate.
            threads: Number of CPU threads to use.
            retry_count: Number of retry attempts on failure.
            retry_delay: Delay in seconds between retries.
            timeout: Timeout in seconds for the subprocess.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.threads = threads
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.timeout = timeout

    def _run_single_inference(self, prompt: str) -> Dict[str, Any]:
        """
        Executes the llama-cli command for a single prompt.
        
        Args:
            prompt: The full prompt string including few-shot examples.
        
        Returns:
            Dictionary containing completion, latency, and status.
        
        Raises:
            subprocess.TimeoutExpired: If the inference exceeds the timeout.
            subprocess.CalledProcessError: If the inference process fails.
        """
        start_time = time.time()
        
        # Construct command for llama-cli
        # Using CPU-only flags and Q4_K_M quantization (assumed by model_path)
        cmd = [
            "llama-cli",
            "-m", self.model_path,
            "-p", prompt,
            "-n", str(self.max_tokens),
            "--color", "0",
            "-t", str(self.threads),
            "--temp", "0.0",  # Deterministic decoding for evaluation
            "--no-display-prefix"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"llama-cli failed with code {result.returncode}: {result.stderr}"
                )

            # llama-cli typically outputs the prompt first, then the completion.
            # We need to extract the generated part.
            # Standard behavior: The output contains the prompt, then the completion.
            # We'll assume the completion starts after the last occurrence of the prompt
            # or simply take the tail if the prompt is not repeated.
            # For robustness, we split by the last known prompt occurrence if possible,
            # but often the simplest approach is to return the full stdout and let
            # the analyzer handle extraction if the prompt is consistent.
            # However, to be precise, we look for the prompt in the output.
            output_text = result.stdout.strip()
            
            completion = output_text
            if prompt in output_text:
                # Split on the last occurrence of the prompt to get the completion
                parts = output_text.rsplit(prompt, 1)
                if len(parts) > 1:
                    completion = parts[1].strip()
            
            # Remove any trailing "Answer:" or similar prefixes if the model repeats them
            # (Optional cleanup, keeping it raw for now as per spec "completion")
            
            return {
                "status": "success",
                "completion": completion,
                "latency": time.time() - start_time,
                "raw_output": output_text
            }

        except subprocess.TimeoutExpired:
            logger.warning(f"Inference timed out after {self.timeout}s")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Process failed: {e.stderr}")
            raise

    def run_inference(self, prompt: str) -> Dict[str, Any]:
        """
        Runs inference on a single prompt with retry logic.
        
        Args:
            prompt: The full prompt string.
        
        Returns:
            Dictionary with status, completion, latency, and error (if failed).
        """
        last_error = None
        
        for attempt in range(1, self.retry_count + 1):
            try:
                logger.info(f"Running inference (attempt {attempt}/{self.retry_count})")
                result = self._run_single_inference(prompt)
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt} failed: {e}. "
                    f"Retrying in {self.retry_delay}s..."
                )
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
        
        logger.error(f"All {self.retry_count} attempts failed.")
        return {
            "status": "failed",
            "error": str(last_error),
            "latency": 0.0,
            "completion": ""
        }

    def run_batch(self, prompts: List[str]) -> List[Dict]:
        """
        Runs inference on a batch of prompts sequentially.
        
        Args:
            prompts: List of prompt strings.
        
        Returns:
            List of result dictionaries.
        """
        results = []
        for i, p in enumerate(prompts):
            logger.info(f"Processing batch item {i+1}/{len(prompts)}")
            result = self.run_inference(p)
            results.append(result)
        return results

def main():
    """
    Entry point for running inference when executed as a script.
    Expects arguments: --model, --prompt-file, --output-file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run llama.cpp inference")
    parser.add_argument("--model", required=True, help="Path to model file")
    parser.add_argument("--prompt-file", required=True, help="Path to JSON file with prompts")
    parser.add_argument("--output-file", required=True, help="Path to save results JSON")
    parser.add_argument("--threads", type=int, default=4, help="CPU threads")
    parser.add_argument("--max-tokens", type=int, default=512, help="Max tokens")
    
    args = parser.parse_args()
    
    # Load prompts
    prompts_dir = Path(args.prompt_file)
    if not prompts_dir.exists():
        raise FileNotFoundError(f"Prompt file not found: {args.prompt_file}")
    
    with open(args.prompt_file, 'r') as f:
        data = json.load(f)
    
    prompts = data.get("prompts", [])
    if not prompts:
        logger.warning("No prompts found in input file.")
        prompts = []
    
    runner = InferenceRunner(
        model_path=args.model,
        threads=args.threads,
        max_tokens=args.max_tokens
    )
    
    results = runner.run_batch(prompts)
    
    # Save results
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
