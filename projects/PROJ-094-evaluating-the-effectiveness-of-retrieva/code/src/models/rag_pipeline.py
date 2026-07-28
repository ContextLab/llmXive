"""
RAG Pipeline Implementation for Code Search Evaluation.

This module implements a Retrieval-Augmented Generation pipeline using
Salesforce/codegen-350M-mono as the primary generator, with a fallback
to microsoft/phi-1.5 under strict memory constraints.

The pipeline:
1. Retrieves top-k code snippets based on a query using a provided retriever.
2. Constructs a prompt with the query and retrieved context.
3. Generates a code completion using the language model.
4. Returns the generated text along with metadata.

Fallback Logic:
- Attempts to load 'Salesforce/codegen-350M-mono' in CPU mode.
- If loading fails due to memory constraints (detected via psutil or exception),
  falls back to 'microsoft/phi-1.5' with 4-bit quantization and device_map='cpu'.
- No synthetic fallbacks are permitted; if both fail, the process raises an error.
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import psutil
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

from src.data.models import CodeSnippet, QueryResult
from src.lib.utils import set_random_seed

# Configure logging
logger = logging.getLogger(__name__)

# Constants
PRIMARY_MODEL_ID = "Salesforce/codegen-350M-mono"
FALLBACK_MODEL_ID = "microsoft/phi-1.5"
MAX_RAM_GB = 7.0
TEMPERATURE = 0.0
TOP_K = 5
MAX_NEW_TOKENS = 256
SYSTEM_PROMPT_TEMPLATE = """Below is a query about code functionality. Use the provided context snippets to generate a relevant code snippet or explanation.

Query: {query}

Context:
{context}

Response:
"""


def get_available_ram_gb() -> float:
    """Get available system RAM in GB."""
    try:
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    except Exception as e:
        logger.warning(f"Could not determine available RAM: {e}. Assuming safe default.")
        return 8.0  # Assume safe default if check fails


def load_generator_model(
    model_id: str,
    use_quantization: bool = False
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load a transformer model with specific configurations.

    Args:
        model_id: HuggingFace model identifier.
        use_quantization: If True, attempt 4-bit quantization (requires bitsandbytes).

    Returns:
        Tuple of (model, tokenizer).

    Raises:
        RuntimeError: If model fails to load.
    """
    logger.info(f"Attempting to load model: {model_id}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Ensure padding token is set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        device_map = "cpu"
        torch_dtype = torch.float32

        load_kwargs = {
            "device_map": device_map,
            "torch_dtype": torch_dtype,
        }

        if use_quantization:
            try:
                from transformers import BitsAndBytesConfig
                logger.info("Attempting 4-bit quantization load...")
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16
                )
                load_kwargs["quantization_config"] = bnb_config
                load_kwargs["torch_dtype"] = torch.float16 # Required for 4-bit
                load_kwargs["device_map"] = "auto" # Auto handles CPU/GPU mapping for quantized
            except ImportError:
                logger.warning("bitsandbytes not installed. Falling back to standard float32 load.")
            except Exception as e:
                logger.warning(f"Quantization failed: {e}. Falling back to standard load.")

        model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
        model.eval()

        logger.info(f"Successfully loaded model: {model_id}")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {e}")
        traceback.print_exc()
        raise RuntimeError(f"Model loading failed for {model_id}: {e}")


class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline for Code Search.

    Handles retrieval context construction and generation.
    """

    def __init__(self, retriever: Any, random_seed: int = 42):
        """
        Initialize the RAG pipeline.

        Args:
            retriever: An object with a `retrieve(query, top_k)` method returning List[CodeSnippet].
            random_seed: Seed for reproducibility.
        """
        self.retriever = retriever
        self.random_seed = random_seed
        self.model = None
        self.tokenizer = None
        self.generator_config = None
        self._model_loaded = False

        set_random_seed(random_seed)

    def _load_model_if_needed(self) -> None:
        """Load the generator model with fallback logic if not already loaded."""
        if self._model_loaded:
            return

        logger.info("Initializing RAG Generator Model...")
        available_ram = get_available_ram_gb()
        logger.info(f"Available RAM: {available_ram:.2f} GB (Threshold: {MAX_RAM_GB} GB)")

        primary_failed = False
        fallback_failed = False

        # Attempt Primary Model
        try:
            if available_ram < MAX_RAM_GB:
                logger.warning(f"Available RAM ({available_ram:.2f} GB) is below threshold ({MAX_RAM_GB} GB). "
                               f"Primary model {PRIMARY_MODEL_ID} might fail. Attempting anyway first.")
            
            self.model, self.tokenizer = load_generator_model(PRIMARY_MODEL_ID, use_quantization=False)
            self._model_loaded = True
            logger.info("Primary model loaded successfully.")
            return
        except Exception as e:
            logger.warning(f"Primary model {PRIMARY_MODEL_ID} failed to load: {e}")
            primary_failed = True

        # Attempt Fallback Model if Primary failed or RAM is critically low
        if primary_failed or available_ram < (MAX_RAM_GB * 0.8):
            logger.info(f"Attempting fallback model: {FALLBACK_MODEL_ID} with 4-bit quantization...")
            try:
                self.model, self.tokenizer = load_generator_model(FALLBACK_MODEL_ID, use_quantization=True)
                self._model_loaded = True
                logger.info("Fallback model loaded successfully with quantization.")
                return
            except Exception as e:
                logger.error(f"Fallback model {FALLBACK_MODEL_ID} also failed: {e}")
                fallback_failed = True

        # If both failed, raise a critical error
        raise RuntimeError(
            f"Failed to load any generator model. "
            f"Primary ({PRIMARY_MODEL_ID}) failed. "
            f"Fallback ({FALLBACK_MODEL_ID}) failed. "
            f"System RAM: {available_ram:.2f} GB. "
            "Cannot proceed with RAG generation."
        )

    def _construct_prompt(self, query: str, snippets: List[CodeSnippet]) -> str:
        """
        Construct the prompt for the language model.

        Args:
            query: The user's search query.
            snippets: List of retrieved code snippets.

        Returns:
            Formatted prompt string.
        """
        context_parts = []
        for i, snippet in enumerate(snippets):
            # Format: [Snippet {i+1}] (language: {lang})\n{code}\n
            lang = snippet.language if hasattr(snippet, 'language') else "unknown"
            code = snippet.code if hasattr(snippet, 'code') else str(snippet)
            context_parts.append(f"[Snippet {i+1}] (lang: {lang})\n{code}\n")

        context_text = "\n".join(context_parts)
        
        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            query=query,
            context=context_text
        )
        return prompt

    def generate(self, query: str, top_k: int = TOP_K) -> QueryResult:
        """
        Execute the RAG pipeline for a single query.

        1. Retrieve top-k snippets.
        2. Construct prompt.
        3. Generate text.

        Args:
            query: The search query string.
            top_k: Number of snippets to retrieve.

        Returns:
            QueryResult object containing the query, retrieved snippets, and generated text.
        """
        if not self._model_loaded:
            self._load_model_if_needed()

        # 1. Retrieve
        logger.debug(f"Retrieving top-{top_k} snippets for query: {query[:50]}...")
        retrieved_snippets = self.retriever.retrieve(query, top_k=top_k)
        
        if not retrieved_snippets:
            logger.warning(f"No snippets retrieved for query: {query}")
            return QueryResult(
                query=query,
                retrieved_snippets=[],
                generated_text="",
                method="RAG",
                status="no_context"
            )

        # 2. Construct Prompt
        prompt = self._construct_prompt(query, retrieved_snippets)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        # 3. Generate
        logger.debug("Generating response...")
        with torch.no_grad():
            generation_config = GenerationConfig(
                temperature=TEMPERATURE,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            output_ids = self.model.generate(
                **inputs,
                generation_config=generation_config
            )
            
            # Decode only the new tokens
            generated_ids = output_ids[0][inputs['input_ids'].shape[1]:]
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        return QueryResult(
            query=query,
            retrieved_snippets=retrieved_snippets,
            generated_text=generated_text,
            method="RAG",
            status="success"
        )

def create_rag_pipeline(retriever: Any, random_seed: int = 42) -> RAGPipeline:
    """
    Factory function to create a configured RAGPipeline.

    Args:
        retriever: An instance of a retriever (BM25 or Neural).
        random_seed: Seed for reproducibility.

    Returns:
        Configured RAGPipeline instance.
    """
    return RAGPipeline(retriever=retriever, random_seed=random_seed)
