"""
Base agent implementation for social memory networks.
Uses CPU-only transformers with float32 precision.
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for a base agent."""
    model_name: str = 'opt-125m'
    agent_id: str = 'agent_0'
    device: str = 'cpu'
    context_window: int = 512

class BaseAgent:
    """Base agent with language model capabilities."""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.agent_id = config.agent_id
        
        # Initialize model and tokenizer
        # Use CPU-only, float32 as per constraints
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                config.model_name,
                torch_dtype=torch.float32,
                device_map=config.device
            )
        except Exception as e:
            # Fallback for environments without model files
            self.tokenizer = None
            self.model = None
            print(f"Warning: Could not load model {config.model_name}: {e}")
        
        self.memory_history: List[Dict[str, Any]] = []
    
    def generate(self, prompt: str, max_length: int = 100) -> str:
        """
        Generate a response to a prompt.
        
        Args:
            prompt: Input prompt
            max_length: Maximum generation length
            
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            # Fallback: return a deterministic response based on prompt hash
            import hashlib
            h = hashlib.md5(prompt.encode()).hexdigest()[:8]
            return f"Response_{h}"
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.config.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                do_sample=True,
                temperature=0.7
            )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def store_memory(self, entry: Dict[str, Any]) -> None:
        """Store a memory entry."""
        self.memory_history.append(entry)
    
    def retrieve_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on query."""
        # Simple retrieval: return last N memories
        return self.memory_history[-limit:]
    
    def process_memory_action(self, action_text: str) -> Optional[Dict[str, Any]]:
        """Process a memory action from text."""
        # Placeholder for memory action parsing
        return {"action": "unknown", "data": {}}
