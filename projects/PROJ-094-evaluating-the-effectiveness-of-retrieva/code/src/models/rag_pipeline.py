"""
RAG Pipeline Implementation for Code Search Evaluation.

This module implements the Retrieval-Augmented Generation pipeline using
Salesforce/codegen-mono as the generator. It includes logic for:
1. Loading the generator model with CPU/GPU fallback strategies.
2. Memory monitoring using psutil.
3. Constructing prompts and generating code completions.
4. Handling OOM scenarios by attempting GPU offload.

Critical Requirement (FR-003): If CPU loading fails, the system MUST attempt
GPU offload. If both fail, it MUST raise a RuntimeError.
"""

import os
import sys
import logging
import traceback
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from accelerate import init_empty_weights, infer_auto_device_map, load_checkpoint_in_model

# Import existing project utilities
# Note: These are defined in T003 (utils.py) which is already completed
try:
    from src.lib.utils import set_fixed_seed, setup_logging
except ImportError:
    # Fallback if utils.py is not yet available in the path
    def set_fixed_seed(seed: int = 42):
        import random
        import numpy as np
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def setup_logging(level=logging.INFO):
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

# Constants
MODEL_NAME = "Salesforce/codegen-mono-350M"  # Using a smaller variant for feasibility, or the full one if available
# Note: The task specifies "Salesforce/codegen-mono". We will try to load the 350M version first as it's more common,
# but the logic supports the full model if resources permit.
# If the specific 350M is not intended and the full 16B is required, the OOM logic will trigger.
# To strictly follow "Salesforce/codegen-mono", we default to the base identifier which usually resolves to the smallest,
# but we will explicitly try the 350M for a balanced approach, falling back to 2B/16B if needed by the user's config.
# For this implementation, we use the 350M as the default "codegen-mono" variant often used in research to fit in RAM.
# If the task implies the full 16B, the OOM logic is critical.
DEFAULT_MODEL_PATH = "Salesforce/codegen-350M-mono" 

SYSTEM_PROMPT_TEMPLATE = """Below is a query describing a code snippet. Generate the code that satisfies the query.

Query: {query}

Code:
"""

logger = logging.getLogger(__name__)


def get_available_ram_gb() -> float:
    """
    Returns the available RAM in GB using psutil.
    """
    try:
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    except Exception as e:
        logger.warning(f"Could not read available RAM via psutil: {e}. Assuming 2GB safe limit.")
        return 2.0


def load_generator_model(
    model_path: str = DEFAULT_MODEL_PATH,
    force_gpu: bool = False,
    load_8bit: bool = False
) -> Tuple[Any, Any]:
    """
    Loads the generator model with fallback logic for OOM.

    Strategy:
    1. Try loading on CPU (default).
    2. If OOM occurs (detected by exception or memory check), try GPU with 8-bit if available.
    3. If GPU is unavailable or 8-bit fails, raise RuntimeError.

    Args:
        model_path: HuggingFace model identifier.
        force_gpu: If True, skip CPU attempt and go straight to GPU.
        load_8bit: If True, attempt 8-bit loading (requires bitsandbytes).

    Returns:
        Tuple of (model, tokenizer)
    """
    set_fixed_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # Ensure pad token is set if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = None
    device = "cpu"

    # Check if GPU is available
    cuda_available = torch.cuda.is_available()
    gpu_memory_gb = 0
    if cuda_available:
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        logger.info(f"GPU detected: {torch.cuda.get_device_name(0)} with {gpu_memory_gb:.2f} GB VRAM")

    try:
        logger.info(f"Attempting to load model {model_path} on CPU...")
        
        # Check RAM before loading
        available_ram = get_available_ram_gb()
        logger.info(f"Available RAM: {available_ram:.2f} GB")
        
        # Heuristic: 350M model needs ~1-2GB, 2B needs ~4GB, 16B needs ~32GB+
        # We attempt to load with appropriate dtype based on available RAM
        if available_ram < 3.0:
            # Likely need 8-bit or GPU if RAM is tight
            logger.warning("Low RAM detected. Attempting CPU loading with float16 or error.")
            # Force float16 to save memory if possible
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="cpu",
                low_cpu_mem_usage=True
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="cpu",
                low_cpu_mem_usage=True
            )
        
        device = "cpu"
        logger.info("Model loaded successfully on CPU.")

    except (torch.cuda.OutOfMemoryError, OSError, ValueError) as e:
        # Check if it's specifically an OOM or loading error
        error_msg = str(e)
        logger.warning(f"Failed to load model on CPU: {error_msg}")

        if cuda_available and (force_gpu or "CPU" in error_msg or "OOM" in error_msg or "Memory" in error_msg):
            logger.info("Attempting GPU offload with 8-bit quantization...")
            try:
                if load_8bit:
                    # Requires bitsandbytes
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        load_in_8bit=True,
                        device_map="auto",
                        torch_dtype=torch.float16
                    )
                else:
                    # Try standard GPU loading
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        device_map="auto",
                        torch_dtype=torch.float16
                    )
                device = "cuda"
                logger.info("Model loaded successfully on GPU.")
            except Exception as gpu_e:
                logger.error(f"GPU offload also failed: {gpu_e}")
                raise RuntimeError(f"RAG execution failed: CPU OOM and GPU offload unavailable.") from gpu_e
        else:
            if not cuda_available:
                raise RuntimeError("RAG execution failed: CPU OOM and no GPU available.") from e
            else:
                # GPU available but not forced/needed, re-raise or try GPU?
                # Per task: MUST attempt offload.
                logger.info("Retrying with GPU offload as CPU failed...")
                try:
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        device_map="auto",
                        torch_dtype=torch.float16
                    )
                    device = "cuda"
                    logger.info("Model loaded successfully on GPU.")
                except Exception as gpu_e:
                    raise RuntimeError("RAG execution failed: CPU OOM and GPU offload unavailable.") from gpu_e

    if model is None:
        raise RuntimeError("RAG execution failed: Model loading failed on all devices.")

    return model, tokenizer


class RAGPipeline:
    """
    RAG Pipeline for Code Search.
    
    Takes a query, retrieves top-k snippets (using an external retriever),
    constructs a prompt, and generates code.
    """
    
    def __init__(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        retriever: Any,
        k: int = 5,
        max_new_tokens: int = 256,
        temperature: float = 0.0
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.retriever = retriever
        self.k = k
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        
        # Set generation config
        self.generation_config = GenerationConfig(
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            do_sample=self.temperature > 0.0,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )

    def construct_prompt(self, query: str, retrieved_snippets: List[Dict[str, Any]]) -> str:
        """
        Constructs the prompt by concatenating the query and retrieved snippets.
        """
        context = "\n\n".join([
            f"Reference {i+1}:\n{snippet.get('code', snippet.get('text', ''))}"
            for i, snippet in enumerate(retrieved_snippets)
        ])
        
        prompt = SYSTEM_PROMPT_TEMPLATE.format(query=query)
        if context:
            prompt += f"\n\nContext:\n{context}"
        
        return prompt

    def generate(self, query: str, retrieved_snippets: List[Dict[str, Any]]) -> str:
        """
        Generates code given a query and retrieved snippets.
        """
        prompt = self.construct_prompt(query, retrieved_snippets)
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Move inputs to device
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=self.generation_config
            )
        
        # Decode
        full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract generated part (remove prompt)
        generated_text = full_text[len(prompt):].strip()
        return generated_text

    def run(self, query: str, ground_truth_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs the full RAG pipeline for a single query.
        1. Retrieves top-k snippets.
        2. Generates code.
        3. Returns results.
        """
        # Retrieve
        retrieved = self.retriever.retrieve(query, self.k)
        
        # Generate
        generated_code = self.generate(query, retrieved)
        
        return {
            "query": query,
            "ground_truth_id": ground_truth_id,
            "retrieved_snippets": retrieved,
            "generated_code": generated_code,
            "method": "RAG"
        }


def create_rag_pipeline(
    retriever: Any,
    model_path: str = DEFAULT_MODEL_PATH,
    k: int = 5,
    force_gpu: bool = False
) -> RAGPipeline:
    """
    Factory function to create and configure the RAG pipeline.
    """
    model, tokenizer = load_generator_model(model_path, force_gpu=force_gpu)
    return RAGPipeline(model, tokenizer, retriever, k=k)


def main():
    """
    Main entry point for testing the RAG pipeline.
    This function is intended to be called by the CLI (T013) or for standalone testing.
    """
    import json
    from src.data.models import CodeSnippet
    
    # Setup logging
    setup_logging()
    
    # Mock retriever for standalone testing if not provided
    # In production, this is injected by the CLI
    class MockRetriever:
        def retrieve(self, query: str, k: int):
            return [
                {"code": f"def mock_func_{i}():\n    pass", "score": 0.9 - i*0.1}
                for i in range(k)
            ]

    try:
        # Load model
        pipeline = create_rag_pipeline(
            retriever=MockRetriever(),
            model_path=DEFAULT_MODEL_PATH,
            k=3
        )
        
        # Test query
        test_query = "Write a function to calculate the factorial of a number"
        result = pipeline.run(test_query)
        
        print(f"Query: {test_query}")
        print(f"Generated Code:\n{result['generated_code']}")
        
    except RuntimeError as e:
        logger.error(f"Critical Error: {e}")
        # Re-raise to ensure the execution stage knows it failed
        raise
    except Exception as e:
        logger.error(f"Unexpected error during RAG execution: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()