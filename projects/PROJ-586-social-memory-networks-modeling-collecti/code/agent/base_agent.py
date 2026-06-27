"""Base agent abstraction for social memory networks.

This module implements the core Agent abstraction using CPU-only transformers
with opt-125m model at float32 precision, as specified in FR-002.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class BaseAgent:
    """
    Base agent abstraction using CPU-only transformers with opt-125m model.

    This agent serves as the foundation for multi-agent social memory networks,
    providing a consistent interface for memory operations and text generation.

    Attributes:
        agent_id: Unique identifier for this agent
        model_name: Name of the transformer model (default: opt-125m)
        device: Device to run inference on (default: cpu)
        tokenizer: HuggingFace tokenizer
        model: HuggingFace model instance
        memory_buffer: External memory buffer reference
        temperature: Sampling temperature for generation
        max_length: Maximum generation length
    """

    def __init__(
        self,
        agent_id: str,
        model_name: str = "facebook/opt-125m",
        device: str = "cpu",
        memory_buffer: Optional[Any] = None,
        temperature: float = 0.7,
        max_length: int = 512,
        load_model: bool = True
    ):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique identifier for this agent
            model_name: Name of the transformer model
            device: Device to run inference on
            memory_buffer: External memory buffer reference (optional)
            temperature: Sampling temperature for generation
            max_length: Maximum generation length
            load_model: Whether to load the model immediately
        """
        self.agent_id = agent_id
        self.model_name = model_name
        self.device = device
        self.memory_buffer = memory_buffer
        self.temperature = temperature
        self.max_length = max_length

        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None

        if load_model:
            self.load_model()

    def load_model(self) -> None:
        """
        Load the transformer model on CPU with float32 precision.

        Uses opt-125m model with explicit float32 dtype to ensure
        compatibility with CPU-only inference environments.
        """
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )

        # Load model with float32 precision for CPU compatibility
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,
            device_map=self.device,
            low_cpu_mem_usage=True
        )

        # Ensure model is in evaluation mode
        self.model.eval()

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 100,
        memory_context: Optional[str] = None
    ) -> str:
        """
        Generate text response given a prompt.

        Args:
            prompt: Input prompt for the agent
            max_new_tokens: Maximum number of tokens to generate
            memory_context: Optional memory context to prepend

        Returns:
            Generated text response
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Build full prompt with optional memory context
        if memory_context:
            full_prompt = f"<MEMORY_CONTEXT>\n{memory_context}\n</MEMORY_CONTEXT>\n\n{prompt}"
        else:
            full_prompt = prompt

        # Tokenize input
        inputs = self.tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate with temperature sampling
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # Decode and return response
        response = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        # Strip the original prompt from response
        if response.startswith(full_prompt):
            response = response[len(full_prompt):].strip()

        return response

    def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store content in external memory buffer.

        Args:
            content: Content to store
            metadata: Optional metadata for the memory entry

        Returns:
            Memory entry ID if successful, None if no buffer
        """
        if self.memory_buffer is None:
            return None

        entry = {
            'agent_id': self.agent_id,
            'content': content,
            'metadata': metadata or {}
        }
        return self.memory_buffer.store(entry)

    def retrieve_memory(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memory entries from external buffer.

        Args:
            query: Query string for retrieval
            top_k: Number of entries to retrieve

        Returns:
            List of memory entries (empty if no buffer)
        """
        if self.memory_buffer is None:
            return []

        return self.memory_buffer.retrieve(query, top_k=top_k)

    def process_memory_action(self, action_text: str) -> Optional[str]:
        """
        Process a <MEMORY_ACTION> token instruction.

        Args:
            action_text: The action text to process

        Returns:
            Result of the action or None if invalid
        """
        # Parse action format: <STORE|RETRIEVE|CLEAR> <content>
        parts = action_text.strip().split(None, 1)
        if len(parts) < 2:
            return None

        action_type, content = parts[0].upper(), parts[1]

        if action_type == "STORE":
            entry_id = self.store_memory(content)
            return f"Stored memory: {entry_id}" if entry_id else "Failed to store"
        elif action_type == "RETRIEVE":
            results = self.retrieve_memory(content, top_k=5)
            return f"Retrieved {len(results)} memories"
        elif action_type == "CLEAR":
            if self.memory_buffer is not None:
                self.memory_buffer.clear()
            return "Memory cleared"
        else:
            return None

    def get_context_window(self) -> int:
        """Return the model's context window size."""
        if self.tokenizer is None:
            return self.max_length
        return getattr(self.tokenizer, 'model_max_length', self.max_length)

    def __repr__(self) -> str:
        return (
            f"BaseAgent(id={self.agent_id}, "
            f"model={self.model_name}, "
            f"device={self.device})"
        )
