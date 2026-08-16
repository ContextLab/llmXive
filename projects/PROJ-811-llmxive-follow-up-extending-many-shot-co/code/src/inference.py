"""
Inference runner for llmXive pipeline.
Handles CPU-only inference via llama.cpp and model selection logic.
"""
import subprocess
import json
import time
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from code.src.config import get_config

logger = logging.getLogger(__name__)

# Model Class Definitions
MODEL_CLASS_REASONING = "reasoning"
MODEL_CLASS_NON_REASONING = "non_reasoning"

# Default model mappings (can be overridden by config)
DEFAULT_MODEL_MAP = {
    MODEL_CLASS_REASONING: [
        "meta-llama/Llama-3.1-8B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3"
    ],
    MODEL_CLASS_NON_REASONING: [
        "meta-llama/Llama-3.1-8B",
        "Qwen/Qwen2.5-7B",
        "mistralai/Mistral-7B-v0.3"
    ]
}

class InferenceRunner:
    """
    Manages CPU-only inference using llama.cpp.
    Supports model selection based on 'reasoning' vs 'non-reasoning' classes.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config().to_dict()
        self.llama_cpp_path = self.config.get("llama_cpp_path", "llama-cli")
        self.quantization = self.config.get("quantization", "Q4_K_M")
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.temperature = self.config.get("temperature", 0.0)
        self.timeout = self.config.get("inference_timeout", 300)
        
        # Model selection configuration
        self.model_class_map = self.config.get("model_class_map", DEFAULT_MODEL_MAP)
        self.selected_models = self._load_selected_models()

    def _load_selected_models(self) -> Dict[str, List[str]]:
        """
        Loads the list of models for each class from config or uses defaults.
        Validates that at least one model is defined for each class if needed.
        """
        loaded_map = {}
        for cls_name, models in self.model_class_map.items():
            if not isinstance(models, list) or len(models) == 0:
                logger.warning(f"No models defined for class {cls_name}, using defaults.")
                loaded_map[cls_name] = DEFAULT_MODEL_MAP.get(cls_name, [])
            else:
                loaded_map[cls_name] = models
        return loaded_map

    def get_models_for_class(self, model_class: str) -> List[str]:
        """
        Retrieves the list of models assigned to a specific class.
        
        Args:
            model_class: Either 'reasoning' or 'non_reasoning'.
        
        Returns:
            List of model identifiers/paths.
        
        Raises:
            ValueError: If the model_class is unknown.
        """
        if model_class not in self.model_class_map:
            raise ValueError(f"Unknown model class: {model_class}. "
                             f"Valid classes: {list(self.model_class_map.keys())}")
        return self.model_class_map[model_class]

    def select_model(self, model_class: str, seed: Optional[int] = None) -> str:
        """
        Selects a specific model instance for inference based on the class.
        
        Logic:
        - If only one model exists for the class, return it.
        - If multiple models exist, select one deterministically based on seed 
          (modulo the list length) to ensure reproducibility across seeds.
        
        Args:
            model_class: The class of model to select ('reasoning' or 'non_reasoning').
            seed: Optional seed for deterministic selection if multiple models exist.
        
        Returns:
            The selected model identifier/path.
        """
        models = self.get_models_for_class(model_class)
        
        if not models:
            raise RuntimeError(f"No models available for class '{model_class}'. "
                               "Please update config.yaml with valid model paths.")
        
        if len(models) == 1:
            return models[0]
        
        # Deterministic selection based on seed
        if seed is None:
            # Fallback: pick the first one if no seed provided
            return models[0]
        
        index = seed % len(models)
        selected = models[index]
        logger.debug(f"Seed {seed} selected model index {index}: {selected} from class {model_class}")
        return selected

    def _build_command(self, model_path: str, prompt: str, output_path: Optional[str] = None) -> List[str]:
        """
        Constructs the llama-cli command line arguments.
        """
        cmd = [
            self.llama_cpp_path,
            "-m", model_path,
            "-p", prompt,
            "-n", str(self.max_tokens),
            "-t", str(os.cpu_count() or 4),  # Use all available cores
            "--temp", str(self.temperature),
            "--batch_size", "2048",
            "--ubatch_size", "512",
            "-ngl", "0",  # Force CPU (no GPU layers)
            "--color", "0" # Disable colors for parsing
        ]
        
        # Add quantization flag if supported by the binary version
        # Note: Modern llama.cpp usually handles Q4_K_M via the model file name,
        # but we ensure no GPU offloading is requested.
        
        if output_path:
            cmd.extend(["-o", str(output_path)])
        
        return cmd

    def run_inference(self, prompt: str, model_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a single inference run.
        
        Args:
            prompt: The full prompt string.
            model_path: Path to the quantized model file.
            output_path: Optional path to save raw output.
        
        Returns:
            Dictionary containing 'output_text', 'success', 'duration', 'error'.
        """
        start_time = time.time()
        cmd = self._build_command(model_path, prompt, output_path)
        
        logger.info(f"Running inference with model: {model_path}")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Extract output from stdout (llama-cli prints prompt + response)
                # We need to be careful to extract just the completion if possible,
                # but for now we return the full stdout if no output file is used.
                output_text = result.stdout
                
                return {
                    "success": True,
                    "output_text": output_text,
                    "duration": duration,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "output_text": "",
                    "duration": duration,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "success": False,
                "output_text": "",
                "duration": duration,
                "error": f"Inference timed out after {self.timeout}s"
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "output_text": "",
                "duration": duration,
                "error": str(e)
            }

    def run_batch(self, prompts: List[str], model_class: str, seed: int, output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Runs inference for a batch of prompts using a model selected for the given class.
        
        Args:
            prompts: List of prompt strings.
            model_class: 'reasoning' or 'non_reasoning'.
            seed: Seed for model selection determinism.
            output_dir: Directory to save individual output files.
        
        Returns:
            List of result dictionaries.
        """
        model_path = self.select_model(model_class, seed)
        results = []
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, prompt in enumerate(prompts):
            if output_dir:
                out_file = output_dir / f"seed_{seed}_model_{model_class}_idx_{i}.txt"
            else:
                out_file = None
            
            res = self.run_inference(prompt, model_path, out_file)
            res["prompt_index"] = i
            res["model_class"] = model_class
            res["model_path"] = model_path
            results.append(res)
            
            if not res["success"]:
                logger.error(f"Batch item {i} failed: {res['error']}")
        
        return results

def main():
    """
    CLI entry point for running inference.
    Usage: python -m code.src.inference --model-class reasoning --seed 42
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run inference with model selection logic.")
    parser.add_argument("--model-class", type=str, required=True, 
                        choices=["reasoning", "non_reasoning"],
                        help="Class of model to use (reasoning or non_reasoning).")
    parser.add_argument("--seed", type=int, default=42, 
                        help="Seed for deterministic model selection.")
    parser.add_argument("--prompt-file", type=str, default=None,
                        help="Path to a JSON file containing a list of prompts.")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Directory to save inference outputs.")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    runner = InferenceRunner()
    
    prompts = []
    if args.prompt_file:
        with open(args.prompt_file, 'r') as f:
            prompts = json.load(f)
    else:
        # Demo prompt
        prompts = [
            "What is the capital of France?"
        ]
    
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    results = runner.run_batch(
        prompts=prompts,
        model_class=args.model_class,
        seed=args.seed,
        output_dir=output_dir
    )
    
    # Print summary
    successes = sum(1 for r in results if r["success"])
    logger.info(f"Completed {len(results)} runs. Successes: {successes}")
    
    if output_dir:
        summary_path = output_dir / "inference_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Summary saved to {summary_path}")

if __name__ == "__main__":
    main()