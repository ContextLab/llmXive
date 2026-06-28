"""
Base agent abstraction for social memory networks.

This module provides the BaseAgent class that handles:
- LLM model loading (CPU-only, float32 precision)
- Memory buffer interactions
- Turn-based game processing
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for agent initialization."""
    model_name: str = "opt-125m"
    device: str = "cpu"
    dtype: str = "float32"
    seed: int = 42
    max_tokens: int = 512

class BaseAgent:
    """
    Base agent class for multi-agent social memory experiments.
    
    This agent wraps a language model and provides interfaces for:
    - Processing game turns with memory context
    - Generating memory actions
    - Handling shared memory buffer interactions
    """
    
    def __init__(
        self,
        model_name: str = "opt-125m",
        agent_id: int = 0,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            model_name: HuggingFace model name
            agent_id: Unique agent identifier
            config: Configuration dictionary
        """
        self.agent_id = agent_id
        self.model_name = model_name
        
        # Extract config
        if config is None:
            config = {}
        
        self.device = config.get("device", "cpu")
        self.dtype = config.get("dtype", "float32")
        self.seed = config.get("seed", 42)
        
        # Set random seed for reproducibility
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        
        # Load model (CPU-only, float32)
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the language model and tokenizer."""
        try:
            # Load model
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                device_map=self.device,
                trust_remote_code=True
            )
            
            # Move to device
            if self.device != "cpu":
                self.model = self.model.to(self.device)
            
            self.model.eval()
            
        except Exception as e:
            # Fallback for testing without model
            self.tokenizer = None
            self.model = None
            print(f"Warning: Could not load model {self.model_name}: {e}")
            print("Running in mock mode")
    
    def process_turn(
        self,
        context: str,
        memory_buffer: Any,
        turn: int,
        agent_id: Optional[int] = None
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Process a game turn with memory context.
        
        Args:
            context: Game context string
            memory_buffer: Shared memory buffer
            turn: Current turn number
            agent_id: Agent identifier (defaults to self.agent_id)
        
        Returns:
            Tuple of (response, memory_action)
        """
        agent_id = agent_id or self.agent_id
        
        # Generate response (mock for testing without model)
        if self.model is None:
            response = f"Agent {agent_id} response for turn {turn}"
            memory_action = {
                "agent_id": agent_id,
                "action": "store",
                "content": f"Memory from agent {agent_id} at turn {turn}"
            }
        else:
            # Real model inference
            inputs = self.tokenizer(context, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    do_sample=False
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            memory_action = {
                "agent_id": agent_id,
                "action": "store",
                "content": response[:100]
            }
        
        return response, memory_action
    
    def generate_memory_action(
        self,
        content: str,
        action_type: str = "store"
    ) -> Dict[str, Any]:
        """
        Generate a memory action for the shared buffer.
        
        Args:
            content: Memory content
            action_type: Type of action (store/retrieve/delete)
        
        Returns:
            Memory action dictionary
        """
        return {
            "agent_id": self.agent_id,
            "action": action_type,
            "content": content
        }

if __name__ == "__main__":
    # Test agent
    agent = BaseAgent(model_name="opt-125m", agent_id=0)
    print(f"Agent initialized: {agent.agent_id}")
    print(f"Model loaded: {agent.model is not None}")
