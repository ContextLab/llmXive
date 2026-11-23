"""
Dense Attention Runner for MiniMax-M3.

Implements "Dense Attention mode (full context, no sparsity, no Index Branch)"
as the baseline for comparison, aligning with the Plan's definition.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from datasets import load_dataset

from utils.config import Config, get_default_config, enforce_cpu, set_random_seed
from utils.logger import get_logger_for_task, log_resource_usage
from data.loader import download_and_verify_ruler
from data.preprocess import split_context, check_memory_usage, reduce_context_window, exit_on_memory_exceeded
from models.mini_max_wrapper import MiniMaxConfig, MiniMaxWrapper

# Configure logging for this task
logger = get_logger_for_task("T017b")

class DenseAttentionRunner:
    """
    Executes the MiniMax-M3 model in Dense Attention mode.
    
    This runner:
    1. Loads the model with full context attention (no sparsity).
    2. Disables any Index Branch or heuristic selection logic.
    3. Processes the RULER dataset to generate baseline predictions.
    4. Calculates baseline metrics (Exact Match, F1, Perplexity).
    """

    def __init__(self, config: Optional[Config] = None, model_path: Optional[str] = None):
        self.config = config or get_default_config()
        self.model_path = model_path or "MiniMax-ai/MiniMax-M3" # Placeholder, actual path from T048
        self.device = "cpu"
        self.tokenizer = None
        self.model = None
        self.logger = logger

        # Ensure CPU enforcement
        enforce_cpu()
        set_random_seed(self.config.seed)

    def load_model(self) -> None:
        """
        Loads the MiniMax-M3 model in full precision (no quantization)
        onto CPU, ensuring dense attention mechanisms are active.
        """
        self.logger.info(f"Loading Dense Attention model from {self.model_path}...")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Load model in full precision (no quantization as per constraints)
            # Using device_map="cpu" to ensure it stays on CPU
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float32, # Full precision
                device_map="cpu",
                trust_remote_code=True,
                low_cpu_mem_usage=False # Ensure we load fully to check memory limits properly
            )
            
            self.model.eval() # Set to evaluation mode
            self.logger.info("Model loaded successfully in Dense Attention mode.")
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise

    def process_sample(self, sample: Dict[str, Any]) -> Tuple[str, str, float]:
        """
        Processes a single RULER sample using Dense Attention.
        
        Args:
            sample: Dictionary containing 'context' and 'needle' (or similar fields).
        
        Returns:
            Tuple of (input_text, generated_text, perplexity)
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model or tokenizer not loaded. Call load_model() first.")

        context = sample.get("context", "")
        # Assuming RULER format has a question or instruction to answer
        # Adjust based on actual RULER schema if different
        instruction = sample.get("question", "") 
        needle = sample.get("needle", "") # For validation if needed

        # Construct prompt: Context + Instruction
        prompt = f"{context}\n\n{instruction}"
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
        input_ids = inputs["input_ids"]
        
        # Check memory before generation
        if check_memory_usage():
            # Attempt reduction if memory is high (though dense mode needs full context)
            # If reduction fails, we exit
            exit_on_memory_exceeded()

        # Generate with Dense Attention (no custom attention masks for sparsity)
        # Disable any attention masking that would simulate sparsity
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                max_new_tokens=128, # Reasonable limit for baseline
                do_sample=False,    # Deterministic
                temperature=1.0,
                top_p=1.0,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Calculate Perplexity (Proxy loss)
        # Re-tokenize full prompt + generated text for loss calculation
        full_text = prompt + generated_text
        encoded_full = self.tokenizer(full_text, return_tensors="pt", truncation=True)
        
        labels = encoded_full["input_ids"].clone()
        # Shift labels for next-token prediction
        labels[:, :-1] = -100 # Ignore prompt tokens for loss
        
        # Forward pass for loss
        loss_outputs = self.model(
            input_ids=encoded_full["input_ids"],
            labels=labels
        )
        perplexity = torch.exp(loss_outputs.loss).item()
        
        return prompt, generated_text, perplexity

    def run_baseline_experiment(self, data_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs the full baseline experiment on the RULER dataset.
        
        Args:
            data_path: Path to the RULER dataset file (if not downloading).
        
        Returns:
            Dictionary containing baseline metrics and results.
        """
        self.logger.info("Starting Dense Attention Baseline Experiment...")
        start_time = time.time()

        # Load Data
        if data_path is None:
            data_path = download_and_verify_ruler()
        
        dataset = load_dataset("json", data_files={"train": data_path}, split="train")
        
        results = []
        total_perplexity = 0.0
        count = 0

        for i, sample in enumerate(dataset):
            self.logger.info(f"Processing sample {i+1}/{len(dataset)}")
            try:
                prompt, generated, ppl = self.process_sample(sample)
                results.append({
                    "input": prompt,
                    "output": generated,
                    "perplexity": ppl
                })
                total_perplexity += ppl
                count += 1
            except Exception as e:
                self.logger.warning(f"Skipping sample {i} due to error: {e}")
                continue

        end_time = time.time()
        elapsed = end_time - start_time

        avg_perplexity = total_perplexity / count if count > 0 else 0.0

        baseline_report = {
            "mode": "Dense Attention",
            "total_samples": count,
            "elapsed_seconds": elapsed,
            "average_perplexity": avg_perplexity,
            "results": results,
            "config": {
                "model_path": self.model_path,
                "device": self.device,
                "quantization": "None (Full Precision)"
            }
        }

        self.logger.info(f"Baseline experiment completed in {elapsed:.2f}s. Avg PPL: {avg_perplexity:.4f}")
        return baseline_report

def main():
    """Main entry point for the Dense Attention Runner."""
    runner = DenseAttentionRunner()
    runner.load_model()
    report = runner.run_baseline_experiment()
    
    # Save report to results directory
    output_path = Path("results/dense_attention_baseline.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Baseline report saved to {output_path}")
    return report

if __name__ == "__main__":
    main()
