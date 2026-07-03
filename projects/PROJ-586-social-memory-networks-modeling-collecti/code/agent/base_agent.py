"""
BaseAgent implementation for the Social Memory Networks project.

This module implements the base agent abstraction using the CPU-only `transformers`
library (specifically the `opt-125m` model in float32 precision) as required by FR-002.
It replaces the previous deterministic string generation with a real inference pipeline
that processes prompts and generates token-based observations.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str = "BaseAgent"
    temperature: float = 0.7
    max_new_tokens: int = 50
    model_name: str = "facebook/opt-125m"
    device: str = "cpu"
    dtype: str = "float32"

class BaseAgent:
    """
    Simple CPU‑only transformer‑based agent.

    This agent uses the OPT-125M model in float32 precision on CPU.
    It maintains an internal memory buffer and can generate an
    observation for a given game based on the agent's identifier and the
    game context.
    """

    _id_counter = 0
    _model_cache: Dict[str, Any] = {}
    _tokenizer_cache: Dict[str, Any] = {}

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        # Assign a unique identifier to each agent instance
        self.agent_id = BaseAgent._id_counter
        BaseAgent._id_counter += 1
        
        # Initialize model and tokenizer (with caching to avoid reloading)
        self._load_model()
        
        # Placeholder for internal state (e.g., past observations)
        self.history: List[str] = []

    def _load_model(self) -> None:
        """Load the model and tokenizer, using a cache to avoid reloading."""
        cache_key = f"{self.config.model_name}_{self.config.dtype}"
        
        if cache_key not in BaseAgent._model_cache:
            # Determine dtype
            if self.config.dtype == "float32":
                dtype = torch.float32
            elif self.config.dtype == "float16":
                dtype = torch.float16
            else:
                raise ValueError(f"Unsupported dtype: {self.config.dtype}")
            
            # Determine device
            device = self.config.device
            if device == "cuda" and not torch.cuda.is_available():
                device = "cpu"
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=True
            )
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                torch_dtype=dtype,
                device_map=device,
                trust_remote_code=True
            )
            
            BaseAgent._model_cache[cache_key] = (model, tokenizer)
            BaseAgent._tokenizer_cache[cache_key] = tokenizer
        
        self.model, self.tokenizer = BaseAgent._model_cache[cache_key]

    def generate_observation(self, game_id: Optional[int] = None, prompt: Optional[str] = None) -> str:
        """
        Produce an observation string using the transformer model.

        Parameters
        ----------
        game_id : int, optional
            Identifier of the current game simulation.
        prompt : str, optional
            Custom prompt to use for generation. If None, a default prompt
            based on agent_id and game_id is used.

        Returns
        -------
        str
            Generated observation string.
        """
        # Build prompt
        if prompt is None:
            prompt = f"Agent {self.agent_id} observing game {game_id}."
            if game_id is not None:
                prompt = f"Agent {self.agent_id} observing game {game_id}. What is happening?"
            else:
                prompt = f"Agent {self.agent_id} is active. What is the current situation?"
        
        # Ensure model is on correct device
        device = self.config.device
        if device == "cuda" and torch.cuda.is_available():
            self.model = self.model.to("cuda")
        else:
            self.model = self.model.to("cpu")
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                temperature=self.config.temperature,
                do_sample=True if self.config.temperature > 0 else False,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract generated part (remove prompt)
        if full_text.startswith(prompt):
            generated_text = full_text[len(prompt):].strip()
        else:
            generated_text = full_text.strip()
        
        observation = f"{generated_text}"
        
        # Record observation for potential debugging / analysis
        self.history.append(observation)
        return observation

    # Additional placeholder methods that may be used by the simulation
    def process_memory_action(self, action: str) -> None:
        """
        Process a memory‑action token. This updates the agent's history.
        """
        self.history.append(f"action:{action}")

    def reset(self) -> None:
        """Reset the agent's internal history."""
        self.history.clear()

    def __del__(self):
        """Cleanup: model is cached globally, so we don't delete it here."""
        pass
