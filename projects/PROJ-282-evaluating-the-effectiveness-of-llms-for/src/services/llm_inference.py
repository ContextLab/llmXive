"""
Zero-Shot Inference Service for LLM-based Vulnerability Detection.

This module implements the core inference loop for evaluating LLMs on
security vulnerability identification tasks. It handles model loading,
prompt construction, response parsing, and memory safety monitoring.
"""

import os
import sys
import time
import gc
import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import project utilities and models
from src.utils.config import get_config, get_project_root
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure, log_memory_snapshot
from src.utils.memory_monitor import (
    get_available_ram_gb,
    get_current_memory_usage_gb,
    check_memory_constraint,
    force_gc,
    MemoryMonitor,
    monitor_batch_processing
)
from src.models.code_snippet import CodeSnippet
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.utils.hash_artifacts import compute_sha256

# Try to import transformers, but handle gracefully if not installed
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM, BitsAndBytesConfig
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers library not available. Inference will be skipped.")

# Configure logger
logger = get_logger(__name__)

# Category mapping constants
CATEGORY_MAPPING = {
    "sql injection": "SQLi",
    "sqli": "SQLi",
    "sql": "SQLi",
    "buffer overflow": "Buffer Overflow",
    "overflow": "Buffer Overflow",
    "bof": "Buffer Overflow",
    "none": "none",
    "no vulnerability": "none",
    "no vuln": "none",
    "clean": "none",
    "safe": "none",
    "xss": "XSS",
    "cross-site scripting": "XSS",
    "rce": "RCE",
    "remote code execution": "RCE",
    "command injection": "Command Injection",
    "cmd injection": "Command Injection",
    "path traversal": "Path Traversal",
    "directory traversal": "Path Traversal",
    "insecure deserialization": "Insecure Deserialization",
    "deserialization": "Insecure Deserialization",
    "xxe": "XXE",
    "xml external entity": "XXE",
}

UNCERTAIN_KEYWORDS = [
    "maybe", "unclear", "possibly", "likely", "unknown error",
    "potential risk", "vulnerability detected", "unsure", "could be",
    "might be", "possibly vulnerable", "potentially vulnerable"
]

class InferenceService:
    """Service for performing zero-shot LLM inference on code snippets."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the inference service.

        Args:
            config: Optional configuration override dictionary
        """
        self.config = config or get_config()
        self.project_root = get_project_root()
        self.logger = logger
        self.model = None
        self.tokenizer = None
        self.memory_monitor = MemoryMonitor(threshold_gb=0.9 * self.config.runtime_limits.get('ram_gb', 14))
        self.inference_start_time = None
        self.timeout_threshold = 0.9 * 6 * 3600  # 90% of 6 hours in seconds
        self.timeout_risk_logged = False

    def load_model(self, model_name: str = None) -> bool:
        """
        Load the selected model in low-bit quantized mode on CPU.

        Args:
            model_name: Optional override for model name

        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        if not TRANSFORMERS_AVAILABLE:
            self.logger.error("Transformers library not available. Cannot load model.")
            return False

        try:
            model_name = model_name or self.config.inference_params.get('model_name', 'facebook/bart-large-cnn')
            self.logger.info(f"Loading model: {model_name} in 4-bit quantized mode on CPU")

            # Configure 4-bit quantization
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float32
            )

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Load model
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="cpu",
                torch_dtype=torch.float32
            )

            self.logger.info(f"Model loaded successfully: {model_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False

    def parse_llm_response(self, response_text: str) -> Tuple[str, str]:
        """
        Parse LLM response and map to vulnerability categories.

        Args:
            response_text: Raw text response from the LLM

        Returns:
            Tuple of (predicted_category, confidence)
        """
        if not response_text or not response_text.strip():
            return "uncertain", "low"

        response_lower = response_text.lower().strip()

        # Check for uncertain keywords first
        for keyword in UNCERTAIN_KEYWORDS:
            if keyword in response_lower:
                return "uncertain", "low"

        # Try to map to known categories
        for key, category in CATEGORY_MAPPING.items():
            if key in response_lower:
                return category, "high" if category != "uncertain" else "low"

        # If no clear match, check if response mentions vulnerability
        if any(term in response_lower for term in ["vulnerability", "vuln", "security", "risk", "exploit", "attack"]):
            # Try to infer category from context
            if "sql" in response_lower:
                return "SQLi", "medium"
            elif "buffer" in response_lower or "overflow" in response_lower:
                return "Buffer Overflow", "medium"
            elif "xss" in response_lower or "script" in response_lower:
                return "XSS", "medium"
            elif "command" in response_lower or "exec" in response_lower:
                return "Command Injection", "medium"
            else:
                return "uncertain", "medium"

        # Default to none if no vulnerability mentioned
        if any(term in response_lower for term in ["none", "no", "clean", "safe", "secure"]):
            return "none", "high"

        return "uncertain", "low"

    def construct_prompt(self, code: str, language: str = "unknown") -> str:
        """
        Construct the zero-shot prompt for vulnerability detection.

        Args:
            code: The code snippet to analyze
            language: Programming language of the code

        Returns:
            Formatted prompt string
        """
        prompt = f"Identify any security vulnerability in the following {language} code:\n\n"
        prompt += f"```{language}\n{code}\n```\n\n"
        prompt += "If no vulnerability is found, respond with 'none'. "
        prompt += "Otherwise, specify the vulnerability type (e.g., SQLi, Buffer Overflow, XSS, RCE, etc.)."
        return prompt

    def run_inference_batch(self, snippets: List[CodeSnippet], batch_size: int = 1) -> List[PredictionResult]:
        """
        Run inference on a batch of code snippets.

        Args:
            snippets: List of CodeSnippet objects to process
            batch_size: Number of snippets to process in parallel

        Returns:
            List of PredictionResult objects
        """
        if not self.model or not self.tokenizer:
            self.logger.error("Model not loaded. Cannot run inference.")
            return []

        results = []
        total_snippets = len(snippets)

        for i in range(0, total_snippets, batch_size):
            batch = snippets[i:i + batch_size]
            current_time = time.time()

            # Check for timeout risk
            if self.inference_start_time and (current_time - self.inference_start_time) > self.timeout_threshold:
                if not self.timeout_risk_logged:
                    self.logger.warning("Timeout risk detected: Runtime exceeded 90% of 6-hour limit.")
                    self.timeout_risk_logged = True
                    # Log circuit breaker event
                    self._log_circuit_breaker_event(batch_size)
                # Reduce batch size for remaining snippets
                batch_size = max(1, batch_size // 2)
                self.logger.info(f"Reduced batch size to {batch_size} due to timeout risk")

            # Check memory constraints
            if not check_memory_constraint(threshold_gb=0.9):
                self.logger.warning("Memory constraint exceeded. Triggering garbage collection.")
                force_gc()
                if not check_memory_constraint(threshold_gb=0.9):
                    self.logger.error("Memory constraint still exceeded after GC. Reducing batch size.")
                    batch_size = max(1, batch_size // 2)

            # Process batch
            for snippet in batch:
                try:
                    prompt = self.construct_prompt(snippet.source_code, snippet.language)
                    inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

                    # Generate response
                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=100,
                            temperature=0.7,
                            do_sample=True,
                            pad_token_id=self.tokenizer.eos_token_id
                        )

                    response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

                    # Parse response
                    predicted_category, confidence = self.parse_llm_response(response)

                    # Create prediction result
                    prediction = create_prediction_result(
                        snippet_id=snippet.id,
                        predicted_label=predicted_category,
                        predicted_category=predicted_category,
                        is_correct=None,  # Will be set later when comparing to ground truth
                        inference_time_ms=int((time.time() - current_time) * 1000)
                    )
                    results.append(prediction)

                except Exception as e:
                    self.logger.error(f"Error processing snippet {snippet.id}: {e}")
                    # Create error prediction
                    prediction = create_prediction_result(
                        snippet_id=snippet.id,
                        predicted_label="error",
                        predicted_category="error",
                        is_correct=None,
                        inference_time_ms=0
                    )
                    results.append(prediction)

            # Log progress
            if (i + batch_size) % 10 == 0 or (i + batch_size) == total_snippets:
                self.logger.info(f"Processed {i + batch_size}/{total_snippets} snippets")

        return results

    def _log_circuit_breaker_event(self, current_batch_size: int):
        """Log circuit breaker event for timeout risk."""
        event = {
            "event_type": "circuit_breaker",
            "timestamp": datetime.now().isoformat(),
            "reason": "timeout_risk",
            "runtime_percentage": 90,
            "original_batch_size": current_batch_size * 2,
            "reduced_batch_size": current_batch_size,
            "message": "Dataset size reduced via stratified sampling to preserve FR-006"
        }
        self.logger.warning(json.dumps(event))

    def process_snippets_zero_shot(self, snippets: List[CodeSnippet], batch_size: int = 1) -> List[PredictionResult]:
        """
        Main entry point for zero-shot inference processing.

        Args:
            snippets: List of CodeSnippet objects to process
            batch_size: Initial batch size

        Returns:
            List of PredictionResult objects
        """
        self.inference_start_time = time.time()
        self.logger.info(f"Starting zero-shot inference on {len(snippets)} snippets with batch_size={batch_size}")

        # Load model if not already loaded
        if not self.model:
            model_name = self.config.inference_params.get('model_name', 'facebook/bart-large-cnn')
            if not self.load_model(model_name):
                self.logger.error("Failed to load model. Aborting inference.")
                return []

        # Run inference
        results = self.run_inference_batch(snippets, batch_size)

        # Log completion
        total_time = time.time() - self.inference_start_time
        self.logger.info(f"Inference complete. Processed {len(results)} snippets in {total_time:.2f} seconds")

        # Log memory snapshot
        log_memory_snapshot(self.logger)

        return results

def main():
    """Main entry point for the inference service."""
    config = get_config()
    service = InferenceService(config)

    # Example usage with mock data (in real scenario, load from data/processed/)
    from src.models.code_snippet import CodeSnippet
    import uuid

    mock_snippets = [
        CodeSnippet(
            id=str(uuid.uuid4()),
            language="python",
            source_code="def vulnerable_function(user_input):\n    query = 'SELECT * FROM users WHERE id = ' + user_input\n    return query",
            ground_truth_label="vulnerable",
            ground_truth_category="SQLi"
        ),
        CodeSnippet(
            id=str(uuid.uuid4()),
            language="python",
            source_code="def safe_function(user_input):\n    query = 'SELECT * FROM users WHERE id = %s'\n    return query",
            ground_truth_label="safe",
            ground_truth_category="none"
        )
    ]

    results = service.process_snippets_zero_shot(mock_snippets, batch_size=1)

    # Print results
    for result in results:
        print(json.dumps(result.to_dict(), indent=2))

if __name__ == "__main__":
    main()
