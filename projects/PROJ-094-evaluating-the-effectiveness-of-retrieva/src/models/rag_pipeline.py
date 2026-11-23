"""
RAG Pipeline Implementation for Code Search Evaluation.

This module implements a Retrieval-Augmented Generation pipeline using
Salesforce/codegen-mono for code generation based on retrieved snippets.

Critical Requirement (FR-003):
If the model fails to load on CPU due to OOM, the system MUST automatically
attempt to offload to a GPU environment (Kaggle) using device="cuda" and
load_in_8bit=True. If GPU offload is unavailable, raise RuntimeError.
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
from accelerate import Accelerator

from src.data.models import CodeSnippet, RetrievalMethod
from src.models.retriever_bm25 import BM25Retriever
from src.models.retriever_neural import NeuralRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SYSTEM_PROMPT_TEMPLATE = """Below is a natural language query about code.
Based on the following retrieved code snippets, generate a Python function that solves the problem.

Query: {query}

Retrieved Code Snippets:
{retrieved_snippets}

Generated Code:
"""

DEFAULT_MODEL_NAME = "Salesforce/codegen-mono-350M"
DEFAULT_TEMP = 0.0
DEFAULT_TOP_K = 5
MAX_MEMORY_GB = 1.05  # Threshold for triggering fallback

def get_available_ram_gb() -> float:
    """Get available RAM in GB using psutil."""
    try:
        virtual_memory = psutil.virtual_memory()
        return virtual_memory.available / (1024 ** 3)
    except Exception as e:
        logger.warning(f"Could not determine available RAM: {e}")
        return 4.0  # Default safe value

def load_generator_model(
    model_name: str = DEFAULT_MODEL_NAME,
    use_8bit: bool = False,
    device: str = "cpu"
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the generator model with specified configuration.

    Args:
        model_name: HuggingFace model identifier
        use_8bit: Whether to use 8-bit quantization
        device: Target device ("cpu" or "cuda")

    Returns:
        Tuple of (model, tokenizer)

    Raises:
        RuntimeError: If model cannot be loaded on requested device
    """
    try:
        logger.info(f"Loading model {model_name} on {device}...")

        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )

        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch.float32 if device == "cpu" else torch.float16,
            "device_map": "auto" if device == "cuda" else None
        }

        if use_8bit:
            model_kwargs["load_in_8bit"] = True
            model_kwargs["device_map"] = "auto"

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **model_kwargs
        )

        if device == "cpu":
            model = model.to("cpu")
        elif device == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA requested but not available")
            model = model.to("cuda")

        logger.info(f"Model loaded successfully on {device}")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model on {device}: {e}")
        raise RuntimeError(f"Model loading failed on {device}: {e}")

class RAGPipeline:
    """
    RAG Pipeline for code generation and evaluation.

    This pipeline:
    1. Retrieves code snippets using BM25 or Neural retrievers
    2. Constructs a prompt with the query and retrieved snippets
    3. Generates code using the Salesforce/codegen-mono model
    4. Returns the generated code and metadata
    """

    def __init__(
        self,
        retriever: Any,
        retriever_type: RetrievalMethod,
        model_name: str = DEFAULT_MODEL_NAME,
        temperature: float = DEFAULT_TEMP,
        top_k: int = DEFAULT_TOP_K,
        use_8bit: bool = False,
        device: str = "cpu"
    ):
        """
        Initialize the RAG pipeline.

        Args:
            retriever: BM25 or Neural retriever instance
            retriever_type: Type of retrieval method used
            model_name: Generator model name
            temperature: Sampling temperature (0.0 for deterministic)
            top_k: Number of snippets to retrieve
            use_8bit: Whether to use 8-bit quantization
            device: Target device for the model
        """
        self.retriever = retriever
        self.retriever_type = retriever_type
        self.model_name = model_name
        self.temperature = temperature
        self.top_k = top_k
        self.use_8bit = use_8bit
        self.device = device
        self.model = None
        self.tokenizer = None
        self._model_loaded = False

    def _load_model(self) -> None:
        """Load the generator model, attempting GPU offload if CPU fails."""
        if self._model_loaded:
            return

        try:
            # First attempt: CPU
            logger.info("Attempting to load model on CPU...")
            self.model, self.tokenizer = load_generator_model(
                model_name=self.model_name,
                use_8bit=False,
                device="cpu"
            )
            self._model_loaded = True
            return

        except RuntimeError as cpu_error:
            logger.warning(f"CPU load failed: {cpu_error}")

            # Check if OOM or similar memory issue
            if "OOM" in str(cpu_error) or "memory" in str(cpu_error).lower():
                logger.info("Detected memory issue, attempting GPU offload...")

                # Check for available GPU
                if not torch.cuda.is_available():
                    raise RuntimeError(
                        "RAG execution failed: CPU OOM and GPU offload unavailable."
                    )

                try:
                    # Second attempt: GPU with 8-bit quantization
                    self.model, self.tokenizer = load_generator_model(
                        model_name=self.model_name,
                        use_8bit=True,
                        device="cuda"
                    )
                    self._model_loaded = True
                    logger.info("Successfully offloaded to GPU with 8-bit quantization")
                    return

                except Exception as gpu_error:
                    raise RuntimeError(
                        f"RAG execution failed: CPU OOM and GPU offload unavailable. "
                        f"GPU error: {gpu_error}"
                    )
            else:
                # Not an OOM error, re-raise
                raise

    def construct_prompt(self, query: str, retrieved_snippets: List[str]) -> str:
        """
        Construct the prompt for the generator.

        Args:
            query: Natural language query
            retrieved_snippets: List of retrieved code snippets

        Returns:
            Formatted prompt string
        """
        snippets_text = "\n\n".join(retrieved_snippets)

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            query=query,
            retrieved_snippets=snippets_text
        )

        return prompt

    def generate(self, query: str, retrieved_snippets: List[str]) -> str:
        """
        Generate code given a query and retrieved snippets.

        Args:
            query: Natural language query
            retrieved_snippets: List of retrieved code snippets

        Returns:
            Generated code string
        """
        if not self._model_loaded:
            self._load_model()

        prompt = self.construct_prompt(query, retrieved_snippets)

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )

        if self.device == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_new_tokens=256,
                pad_token_id=self.tokenizer.pad_token_id,
                do_sample=self.temperature > 0.0
            )

            outputs = self.model.generate(
                **inputs,
                generation_config=generation_config
            )

        # Decode generated text
        generated_text = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        )

        return generated_text

    def process_query(
        self,
        query: str,
        ground_truth_snippets: Optional[List[CodeSnippet]] = None
    ) -> Dict[str, Any]:
        """
        Process a single query through the RAG pipeline.

        Args:
            query: Natural language query
            ground_truth_snippets: Optional ground truth for evaluation

        Returns:
            Dictionary with query, retrieved snippets, generated code, and metrics
        """
        if not self._model_loaded:
            self._load_model()

        # Retrieve snippets
        retrieved_results = self.retriever.search(query, k=self.top_k)

        retrieved_snippets = [
            snippet.code if isinstance(snippet, CodeSnippet) else snippet
            for snippet in retrieved_results[:self.top_k]
        ]

        # Generate code
        generated_code = self.generate(query, retrieved_snippets)

        # Prepare result
        result = {
            "query": query,
            "retrieved_snippets": retrieved_snippets,
            "generated_code": generated_code,
            "retrieval_method": self.retriever_type.value,
            "top_k": self.top_k,
            "temperature": self.temperature
        }

        if ground_truth_snippets:
            result["ground_truth"] = [
                snippet.code for snippet in ground_truth_snippets
            ]

        return result

def create_rag_pipeline(
    retriever: Any,
    retriever_type: RetrievalMethod,
    model_name: str = DEFAULT_MODEL_NAME,
    temperature: float = DEFAULT_TEMP,
    top_k: int = DEFAULT_TOP_K
) -> RAGPipeline:
    """
    Factory function to create a RAG pipeline.

    Args:
        retriever: BM25 or Neural retriever instance
        retriever_type: Type of retrieval method
        model_name: Generator model name
        temperature: Sampling temperature
        top_k: Number of snippets to retrieve

    Returns:
        Configured RAGPipeline instance
    """
    return RAGPipeline(
        retriever=retriever,
        retriever_type=retriever_type,
        model_name=model_name,
        temperature=temperature,
        top_k=top_k
    )

def main():
    """
    Main entry point for testing the RAG pipeline.

    This function:
    1. Loads a sample query and retrieved snippets
    2. Initializes the RAG pipeline
    3. Generates code
    4. Outputs the result
    """
    logging.basicConfig(level=logging.INFO)

    # Check available RAM
    available_ram = get_available_ram_gb()
    logger.info(f"Available RAM: {available_ram:.2f} GB")

    # Create a mock retriever for testing
    class MockRetriever:
        def search(self, query: str, k: int = 5) -> List[CodeSnippet]:
            return [
                CodeSnippet(
                    code=f"def mock_function_{i}():\n    return {i}",
                    query="mock query",
                    docstring=f"Mock function {i}"
                )
                for i in range(k)
            ]

    # Initialize pipeline
    retriever = MockRetriever()
    pipeline = create_rag_pipeline(
        retriever=retriever,
        retriever_type=RetrievalMethod.RAG,
        top_k=3
    )

    # Test query
    test_query = "Write a function to calculate the sum of two numbers"

    try:
        result = pipeline.process_query(test_query)
        logger.info(f"Generated code:\n{result['generated_code']}")
    except RuntimeError as e:
        logger.error(f"RAG execution failed: {e}")
        raise

if __name__ == "__main__":
    main()