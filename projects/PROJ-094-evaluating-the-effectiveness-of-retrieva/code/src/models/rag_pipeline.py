import os
import sys
import logging
import traceback
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logging.warning("torch or transformers not installed. RAG pipeline will fail on load.")

from src.data.models import CodeSnippet

# Configuration constants
PRIMARY_MODEL = "Salesforce/codegen-350M-mono"
FALLBACK_MODEL = "microsoft/phi-1.5"
SYSTEM_PROMPT_TEMPLATE = (
    "You are an expert code search system. Given a natural language query, "
    "identify the most relevant code snippet from the provided context.\n\n"
    "Query: {query}\n\n"
    "Context:\n{context}\n\n"
    "Answer:"
)
DEFAULT_TOP_K = 10
DEFAULT_TEMPERATURE = 0.0
MEMORY_THRESHOLD_GB = 7.0
QUANTIZATION_BIT = 4

logger = logging.getLogger(__name__)

def get_available_ram_gb() -> float:
    """
    Estimate available RAM in Gigabytes using psutil.
    Returns the available memory in GB.
    """
    if not HAS_TORCH:
        # Fallback if psutil/transformers not available for estimation
        return 0.0
    
    try:
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    except Exception as e:
        logger.error(f"Failed to estimate RAM: {e}")
        return 0.0

def load_generator_model(model_name: str, use_quantization: bool = False) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load a generator model with optional 4-bit quantization.
    
    Args:
        model_name: HuggingFace model ID.
        use_quantization: If True, attempts 4-bit quantization (requires bitsandbytes).
        
    Returns:
        Tuple of (model, tokenizer).
        
    Raises:
        RuntimeError: If the model fails to load or RAM is insufficient.
    """
    if not HAS_TORCH:
        raise RuntimeError("Torch/Transformers dependencies are missing.")

    logger.info(f"Loading model: {model_name} (quantization={use_quantization})")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Configure device map for CPU mode as per task requirements
    device_map = "cpu"
    
    load_kwargs = {
        "device_map": device_map,
        "torch_dtype": torch.float32,
    }
    
    if use_quantization:
        try:
            # Attempt to load with 4-bit quantization
            # Note: requires bitsandbytes which might not be installed
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
            load_kwargs["quantization_config"] = bnb_config
            logger.info("Applying 4-bit quantization configuration.")
        except ImportError:
            logger.warning("bitsandbytes not found, proceeding without 4-bit quantization.")
            # Fallback to standard loading if quantization libs missing
            load_kwargs.pop("quantization_config", None)
    
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
        logger.info(f"Successfully loaded model: {model_name}")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise RuntimeError(f"Model load failed: {e}")

class RAGPipeline:
    """
    RAG Pipeline for Code Search.
    
    Integrates a retriever (BM25 or Neural) and a generator model to
    refine search results based on natural language queries.
    """
    
    def __init__(self, retriever, generator_model: AutoModelForCausalLM, 
                 tokenizer: AutoTokenizer, top_k: int = DEFAULT_TOP_K):
        self.retriever = retriever
        self.generator = generator_model
        self.tokenizer = tokenizer
        self.top_k = top_k
        self.temperature = DEFAULT_TEMPERATURE
        
        # Ensure deterministic behavior
        self.generator.eval()
        if hasattr(self.generator, 'config') and hasattr(self.generator.config, 'pad_token_id'):
            if self.generator.config.pad_token_id is None:
                self.generator.config.pad_token_id = self.tokenizer.eos_token_id

    def _construct_prompt(self, query: str, context: str) -> str:
        """
        Construct the prompt for the generator model.
        
        Args:
            query: The natural language search query.
            context: The retrieved code snippets context.
        
        Returns:
            Formatted prompt string.
        """
        return SYSTEM_PROMPT_TEMPLATE.format(query=query, context=context)

    def _retrieve_context(self, query: str, k: int) -> str:
        """
        Retrieve top-k snippets and format them as context.
        
        Args:
            query: The search query.
            k: Number of snippets to retrieve.
        
        Returns:
            Concatenated string of retrieved snippets.
        """
        # Assuming retriever has a method `search(query, k)` that returns list of CodeSnippet
        # Adjust based on actual retriever implementation (BM25Retriever or NeuralRetriever)
        # Based on task context, we assume retriever exposes a search method.
        # If the retriever is a class, we call it.
        
        # Mocking the retrieval call for this specific pipeline logic
        # In a real execution, `self.retriever` would be the instance from T009/T010
        # We assume it has a `search` method returning CodeSnippets.
        
        try:
            results = self.retriever.search(query, k)
            if not results:
                return "No relevant code snippets found."
            
            context_parts = []
            for i, snippet in enumerate(results):
                # CodeSnippet structure from src.data.models
                code = snippet.code if hasattr(snippet, 'code') else str(snippet)
                context_parts.append(f"[{i+1}] {code}")
            
            return "\n\n".join(context_parts)
        except AttributeError as e:
            logger.error(f"Retriever method 'search' not found or incorrect: {e}")
            return "Retriever error."

    def generate_ranked_response(self, query: str, k: int = None) -> str:
        """
        Main entry point for RAG inference.
        
        Args:
            query: Natural language query.
            k: Optional override for top-k context snippets.
        
        Returns:
            Generated text response.
        """
        if k is None:
            k = self.top_k
        
        context = self._retrieve_context(query, k)
        prompt = self._construct_prompt(query, context)
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.generator.device)
        
        with torch.no_grad():
            outputs = self.generator.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False, # temp=0.0 equivalent
                temperature=self.temperature,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Strip the prompt from the output to get just the answer
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):]
        
        return generated_text.strip()

def create_rag_pipeline(retriever, primary_model: str = PRIMARY_MODEL, 
                        fallback_model: str = FALLBACK_MODEL, 
                        top_k: int = DEFAULT_TOP_K) -> RAGPipeline:
    """
    Creates a RAG Pipeline with fallback logic for model loading.
    
    Logic:
    1. Check available RAM.
    2. Try loading PRIMARY model (Salesforce/codegen-350M-mono).
    3. If RAM < 7GB or load fails, try FALLBACK model (microsoft/phi-1.5) with 4-bit quantization.
    4. If both fail, raise RuntimeError.
    
    Args:
        retriever: An initialized retriever instance (BM25 or Neural).
        primary_model: HuggingFace ID for the primary model.
        fallback_model: HuggingFace ID for the fallback model.
        top_k: Number of snippets to retrieve.
    
    Returns:
        RAGPipeline instance.
    
    Raises:
        RuntimeError: If no model can be loaded.
    """
    available_ram = get_available_ram_gb()
    logger.info(f"Available RAM: {available_ram:.2f} GB")
    
    model_to_load = None
    use_quantization = False
    
    # Decision logic based on RAM threshold
    if available_ram < MEMORY_THRESHOLD_GB:
        logger.warning(f"RAM ({available_ram:.2f}GB) below threshold ({MEMORY_THRESHOLD_GB}GB). "
                       f"Attempting fallback with quantization.")
        model_to_load = fallback_model
        use_quantization = True
    else:
        logger.info(f"RAM ({available_ram:.2f}GB) sufficient. Attempting primary model.")
        model_to_load = primary_model
        
        # Try primary first
        try:
            model, tokenizer = load_generator_model(model_to_load, use_quantization=False)
        except RuntimeError:
            logger.warning(f"Primary model {model_to_load} failed. Falling back to {fallback_model}.")
            model_to_load = fallback_model
            use_quantization = True
    
    # Attempt to load the selected model
    try:
        model, tokenizer = load_generator_model(model_to_load, use_quantization=use_quantization)
    except RuntimeError as e:
        raise RuntimeError(f"Failed to load both primary and fallback models: {e}")
    
    return RAGPipeline(retriever, model, tokenizer, top_k=top_k)